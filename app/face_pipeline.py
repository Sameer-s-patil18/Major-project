from typing import Optional
import numpy as np
import torch
from PIL import Image
import cv2
from facenet_pytorch import MTCNN, InceptionResnetV1

class FacePipeline:
    """
    Face detection + alignment: MTCNN (facenet_pytorch)
    Embeddings: InceptionResnetV1 (facenet_pytorch, pretrained='vggface2') -> 512D
    This pairing is well-tested and usually yields higher cosine similarity for same-person pairs.
    """

    def __init__(self, device: str = "cpu"):
        self.device = device
        # MTCNN handles detection and alignment; returns 160x160 aligned face tensors when post_process=True
        self.mtcnn = MTCNN(image_size=160, margin=20, post_process=True, device=self.device)
        # 512D FaceNet-like embedding model
        self.embedder = InceptionResnetV1(pretrained="vggface2").eval().to(self.device)

    @torch.no_grad()
    def _aligned_tensor_from_bgr(self, image_bgr: np.ndarray) -> Optional[torch.Tensor]:
        """
        Convert BGR np.ndarray -> RGB PIL -> aligned face tensor from MTCNN.
        Returns a 3x160x160 tensor (float32) or None if no face detected.
        """
        # Convert BGR to RGB PIL Image
        img_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)

        # MTCNN returns a torch.Tensor (C,H,W) when post_process=True and a face is found
        aligned = self.mtcnn(pil_img)
        if aligned is None:
            return None

        # If a single face is detected, aligned is a torch.Tensor of shape (3,160,160)
        # If multiple faces, with some configurations MTCNN can return a batch; here we assume single best face.
        if isinstance(aligned, torch.Tensor) and aligned.ndim == 3:
            # Ensure batch dimension
            aligned = aligned.unsqueeze(0)  # (1,3,160,160)
        return aligned.to(self.device)

    @torch.no_grad()
    def embed(self, aligned_tensor: torch.Tensor) -> np.ndarray:
        """
        aligned_tensor: torch.Tensor of shape (1,3,160,160), already normalized by MTCNN post_process.
        Returns np.ndarray of shape (512,) float32.
        """
        emb = self.embedder(aligned_tensor).cpu().numpy()[0]  # (512,)
        return emb.astype(np.float32)

    def image_to_embedding(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """
        Decode bytes -> BGR image -> MTCNN aligned tensor -> 512D embedding.
        """
        nparr = np.frombuffer(image_bytes, np.uint8)
        image_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image_bgr is None:
            return None

        aligned = self._aligned_tensor_from_bgr(image_bgr)
        if aligned is None:
            return None

        emb = self.embed(aligned)
        return emb
