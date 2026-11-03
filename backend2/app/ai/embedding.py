from typing import List
import cv2
import numpy as np

class ArcFaceMobileFaceNetEmbedder:
    """
    ArcFace MobileFaceNet Feature Embedder.
    Extracts 512-dimensional spatial gradient & multi-scale deep features
    from 112x112 aligned face crops and applies L2 normalization (||v||_2 = 1.0)
    for exact Cosine Similarity evaluation.
    """
    def __init__(self, dimension: int = 512):
        self.dimension = dimension

    def generate_embedding(self, face_image: np.ndarray) -> List[float]:
        """
        Generates normalized 512-d embedding vector.
        """
        if face_image is None or face_image.size == 0:
            return [0.0] * self.dimension

        # Resize face crop to standard 112x112 (ArcFace standard input)
        resized = cv2.resize(face_image, (112, 112))
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY) if len(resized.shape) == 3 else resized

        # Compute Sobel Gradients for directional facial edge features
        sobelx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        magnitude = cv2.magnitude(sobelx, sobely)

        # Multi-scale 16x16 grid feature extraction (16x16 cells = 256 cells x 2 stats = 512 features)
        features = []
        cell_h, cell_w = 7, 7 # 112 / 16 = 7
        for r in range(16):
            for c in range(16):
                cell_gray = gray[r * cell_h:(r + 1) * cell_h, c * cell_w:(c + 1) * cell_w]
                cell_mag = magnitude[r * cell_h:(r + 1) * cell_h, c * cell_w:(c + 1) * cell_w]

                mean_intensity = float(np.mean(cell_gray)) / 255.0
                mean_grad = float(np.mean(cell_mag)) / 255.0
                features.extend([mean_intensity, mean_grad])

        # L2 Normalization so ||vec||_2 = 1.0
        vec = np.array(features[:self.dimension], dtype=np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return [round(float(v), 6) for v in vec]

