import faiss
import numpy as np
from typing import List, Dict, Optional
from backend.models.schemas import SourceChunk
from backend.utils.logger import logger
from backend.config.settings import settings


class VectorStore:
    def __init__(self):
        # Maps username to their dedicated FAISS index and metadata
        self.indices: Dict[str, faiss.IndexFlatIP] = {}
        self.metadata: Dict[str, List[SourceChunk]] = {}
        # Dimension is derived lazily from the first batch of embeddings added,
        # so it stays correct regardless of which embedding model is configured.
        self.dimension: Optional[int] = None

    def get_or_create_index(self, username: str) -> faiss.IndexFlatIP:
        if username not in self.indices:
            if self.dimension is None:
                raise RuntimeError(
                    "VectorStore dimension not yet initialised — "
                    "call add_documents with at least one embedding first."
                )
            # Using Inner Product since vectors are normalized (≡ Cosine Similarity)
            self.indices[username] = faiss.IndexFlatIP(self.dimension)
            self.metadata[username] = []
        return self.indices[username]

    def add_documents(self, username: str, embeddings: np.ndarray, source_chunks: List[SourceChunk]):
        """Add embeddings and metadata for a given user."""
        if len(embeddings) == 0:
            return

        # Derive dimension from the first real batch — works for any embedding model
        if self.dimension is None:
            self.dimension = embeddings.shape[1]
            logger.info(f"VectorStore dimension set to {self.dimension} from first embedding batch.")

        index = self.get_or_create_index(username)
        # Ensure array is float32
        embeddings_np = np.array(embeddings).astype("float32")

        index.add(embeddings_np)
        self.metadata[username].extend(source_chunks)

        logger.info(f"Added {len(source_chunks)} chunks for user {username}. Total: {index.ntotal}")

    def get_all_repos(self, username: str) -> list[tuple[str, str]]:
        """Return deduplicated (repo_name, repo_url) pairs for every indexed repo of a user."""
        chunks = self.metadata.get(username, [])
        seen = {}
        for chunk in chunks:
            if chunk.repo_name not in seen:
                seen[chunk.repo_name] = chunk.repo_url
        return list(seen.items())

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
