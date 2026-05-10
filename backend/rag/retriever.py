from typing import List
from backend.vector.store import vector_store
from backend.rag.embedder import Embedder
from backend.models.schemas import SourceChunk

class Retriever:
    @staticmethod
    def retrieve_context(username: str, question: str) -> List[SourceChunk]:
        """
        Embeds the question and retrieves top matching chunks for the given username.
        """
        query_emb = Embedder.embed_query(question)
        chunks = vector_store.search(username, query_emb)
        return chunks
