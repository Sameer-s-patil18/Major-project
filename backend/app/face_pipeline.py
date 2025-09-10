from typing import Optional
from fastapi import HTTPException
import numpy as np
import torch
from PIL import Image
import cv2
from deepface import DeepFace
from facenet_pytorch import MTCNN, InceptionResnetV1

class FacePipeline:
    """
    Detection+alignment: MTCNN
    Embeddings: InceptionResnetV1 (pretrained='vggface2') -> 512D float32
    """

    def __init__(self, device: str = "cpu"):
        self.device = device
        self.mtcnn = MTCNN(image_size=160, margin=20, post_process=True, device=self.device)
        self.embedder = InceptionResnetV1(pretrained="vggface2").eval().to(self.device)

    @torch.no_grad()
    def _aligned_tensor_from_bgr(self, image_bgr: np.ndarray) -> Optional[torch.Tensor]:
        img_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        aligned = self.mtcnn(pil_img)
        if aligned is None:
            return None
        if isinstance(aligned, torch.Tensor) and aligned.ndim == 3:
            aligned = aligned.unsqueeze(0)  # (1,3,160,160)
        return aligned.to(self.device)

    @torch.no_grad()
    def embed(self, aligned_tensor: torch.Tensor) -> np.ndarray:
        emb = self.embedder(aligned_tensor).cpu().numpy()[0]  # (512,)
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
        """
        Run DeepFace anti-spoofing liveness detection on a BGR image.
        Returns dict with keys: 'is_live' (bool), 'confidence' (float).
        Raises HTTPException on errors if enforce_detection=True.
        """
        if image_bgr is None:
            raise HTTPException(status_code=422, detail="Invalid image content")

        # Convert BGR to RGB as DeepFace expects RGB numpy array
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
                raise HTTPException(status_code=422, detail=str(e))
            else:
                return {"is_live": False, "confidence": 0.0}

        if not faces:
            if enforce_detection:
                raise HTTPException(status_code=422, detail="No faces detected")
            else:
                return {"is_live": False, "confidence": 0.0}

        face = faces[0]
        is_live = face.get('is_real', False)
        confidence = face.get('confidence', 0.0)

        return {"is_live": is_live, "confidence": confidence}

