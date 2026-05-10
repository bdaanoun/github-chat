from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
from backend.config.settings import settings
from backend.utils.logger import logger

class Embedder:
    _model = None

    @classmethod
    def get_model(cls) -> SentenceTransformer:
        if cls._model is None:
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            cls._model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Embedding model loaded successfully.")
        return cls._model

    @staticmethod
    def embed_texts(texts: List[str]) -> np.ndarray:
        """Convert a list of text string chunks into normalized numpy array of embeddings."""
        if not texts:
            return np.array([])
            
        model = Embedder.get_model()
        logger.info(f"Embedding {len(texts)} chunks...")
        embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings

    @staticmethod
    def embed_query(query: str) -> np.ndarray:
        """Convert a single query string into a normalized numpy array embedding."""
        model = Embedder.get_model()
        embedding = model.encode(query, convert_to_numpy=True, normalize_embeddings=True)
        return embedding