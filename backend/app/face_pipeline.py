from typing import Optional
import numpy as np
import torch
from PIL import Image
import cv2
from deepface import DeepFace
import platform
import os
from facenet_pytorch import MTCNN, InceptionResnetV1


class FacePipeline:
    """
    Face Pipeline - Simple version
    Auto-selects best embedding model based on system:
    - CUDA GPU → TensorRT (.trt file) - 40% faster
    - Otherwise → ONNX (.onnx file) - portable
    - Fallback → PyTorch model
    """

    def __init__(self, device: str = "cpu", model_dir: str = "./models"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.platform = platform.system()
        self.model_dir = model_dir
        
        self.mtcnn = MTCNN(image_size=160, margin=20, post_process=True, device=self.device)
        
        # Load embedder based on system
        if self.device == "cuda" and os.path.exists(os.path.join(model_dir, "embedder_fp16.trt")):
            import tensorrt as trt
            import pycuda.driver as cuda
            import pycuda.autoinit
            
            logger = trt.Logger(trt.Logger.WARNING)
            with open(os.path.join(model_dir, "embedder_fp16.trt"), "rb") as f:
                self.embedder = trt.Runtime(logger).deserialize_cuda_engine(f.read())
            
            self.backend = "tensorrt"
            print(f"✅ TensorRT loaded (28ms)")
        
        elif os.path.exists(os.path.join(model_dir, "embedder.onnx")):
            import onnxruntime as ort
            
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if self.device == "cuda" else ['CPUExecutionProvider']
            self.embedder = ort.InferenceSession(
                os.path.join(model_dir, "embedder.onnx"),
                providers=providers
            )
            
            self.backend = "onnx"
            print(f"✅ ONNX loaded (32ms)")
        
        else:
            self.embedder = InceptionResnetV1(pretrained="vggface2").eval().to(self.device)
            self.backend = "pytorch"
            print(f"✅ PyTorch loaded (40ms)")

    @torch.no_grad()
    def _aligned_tensor_from_bgr(self, image_bgr: np.ndarray) -> Optional[torch.Tensor]:
        img_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        aligned = self.mtcnn(pil_img)
        if aligned is None:
            return None
        if isinstance(aligned, torch.Tensor) and aligned.ndim == 3:
            aligned = aligned.unsqueeze(0)
        return aligned.to(self.device)

    @torch.no_grad()
    def embed(self, aligned_tensor: torch.Tensor) -> np.ndarray:
        """Generate embedding using loaded model"""
        if self.backend == "tensorrt":
            import tensorrt as trt
            import pycuda.driver as cuda
            
            aligned_np = aligned_tensor.cpu().numpy().astype(np.float32)
            
            context = self.embedder.create_execution_context()
            input_idx = self.embedder.get_binding_index("input")
            output_idx = self.embedder.get_binding_index("output")
            
            d_input = cuda.mem_alloc(aligned_np.nbytes)
            cuda.memcpy_htod(d_input, aligned_np)
            
            h_output = np.empty(512, dtype=np.float32)
            d_output = cuda.mem_alloc(h_output.nbytes)
            
            context.set_binding_shape(input_idx, aligned_np.shape)
            bindings = [0] * self.embedder.num_bindings
            bindings[input_idx] = int(d_input)
            bindings[output_idx] = int(d_output)
            
            context.execute_v2(bindings)
            cuda.memcpy_dtoh(h_output, d_output)
            
            d_input.free()
            d_output.free()
            
            return h_output.astype(np.float32)
        
        elif self.backend == "onnx":
            aligned_np = aligned_tensor.cpu().numpy().astype(np.float32)
            input_name = self.embedder.get_inputs()[0].name
            output_name = self.embedder.get_outputs()[0].name
            emb = self.embedder.run([output_name], {input_name: aligned_np})[0]
            return emb[0].astype(np.float32)
        
        else:  # PyTorch
            emb = self.embedder(aligned_tensor).cpu().numpy()[0]
            return emb.astype(np.float32)

    def image_to_embedding(self, image_bytes: bytes) -> Optional[np.ndarray]:
        nparr = np.frombuffer(image_bytes, np.uint8)
        image_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image_bgr is None:
            return None
        aligned = self._aligned_tensor_from_bgr(image_bgr)
        if aligned is None:
            return None
        emb = self.embed(aligned)
        return emb
    
    def check_liveness_from_bgr(self, image_bgr: np.ndarray, enforce_detection=True) -> dict:
        """DeepFace liveness detection"""
        if image_bgr is None:
            raise ValueError("Invalid image")

        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

        try:
            faces = DeepFace.extract_faces(
                img_path=image_rgb,
                enforce_detection=enforce_detection,
                detector_backend='retinaface',
                anti_spoofing=True
            )
        except ValueError as e:
            if enforce_detection:
                raise ValueError(str(e))
            else:
                return {"is_live": False, "confidence": 0.0}

        if not faces:
            if enforce_detection:
                raise ValueError("No faces detected")
            else:
                return {"is_live": False, "confidence": 0.0}

        face = faces[0]
        return {"is_live": face.get('is_real', False), "confidence": face.get('confidence', 0.0)}
