from typing import Optional
import numpy as np
import torch
from PIL import Image
import cv2
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
