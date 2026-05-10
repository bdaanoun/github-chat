import faiss
import numpy as np
from typing import List, Dict, Any, Tuple
from backend.models.schemas import SourceChunk
from backend.utils.logger import logger
from backend.config.settings import settings

class VectorStore:
    def __init__(self):
        # Maps username to their dedicated FAISS index and metadata
        self.indices: Dict[str, faiss.IndexFlatIP] = {}
        self.metadata: Dict[str, List[SourceChunk]] = {}
        # Assuming embedding size of 384 for all-MiniLM-L6-v2
        self.dimension = 384 

    def get_or_create_index(self, username: str) -> faiss.IndexFlatIP:
        if username not in self.indices:
            # Using Inner Product since vectors are normalized (equivalent to Cosine Similarity)
            self.indices[username] = faiss.IndexFlatIP(self.dimension)
            self.metadata[username] = []
        return self.indices[username]

    def add_documents(self, username: str, embeddings: np.ndarray, source_chunks: List[SourceChunk]):
        """Add embeddings and metadata for a given user."""
        if len(embeddings) == 0:
            return
            
        index = self.get_or_create_index(username)
        # Ensure array is float32
        embeddings_np = np.array(embeddings).astype("float32")
        
        index.add(embeddings_np)
        self.metadata[username].extend(source_chunks)
        
        logger.info(f"Added {len(source_chunks)} chunks for user {username}. Total: {index.ntotal}")

    def search(self, username: str, query_embedding: np.ndarray, top_k: int = settings.TOP_K_RETRIEVAL) -> List[SourceChunk]:
        """Search the vector DB for the most relevant chunks for a given user."""
        if username not in self.indices or self.indices[username].ntotal == 0:
            logger.warning(f"No index found or empty index for user {username}")
            return []

        index = self.indices[username]
        query_np = np.array([query_embedding]).astype("float32")
        
        # Search returns distances and indices
        distances, indices = index.search(query_np, min(top_k, index.ntotal))
        
        results = []
        for i in indices[0]:
            if i != -1 and i < len(self.metadata[username]):
                results.append(self.metadata[username][i])
                
        return results

# Singleton instance
vector_store = VectorStore()
