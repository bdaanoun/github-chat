from typing import List
from backend.config.settings import settings
import re

class TextChunker:
    @staticmethod
    def chunk_text(text: str, chunk_size: int = settings.CHUNK_SIZE, overlap: int = settings.CHUNK_OVERLAP) -> List[str]:
        """
        Split text into overlapping chunks based on approximate word boundaries.
        chunk_size and overlap are loosely treated as word counts for simplicity.
        """
        words = re.findall(r"\S+", text)
        chunks = []
        
        if not words:
            return chunks

        i = 0
        while i < len(words):
            end_idx = min(i + chunk_size, len(words))
            chunk_words = words[i:end_idx]
            chunks.append(" ".join(chunk_words))
            
            if end_idx == len(words):
                break
                
            i += (chunk_size - overlap)
            
        return chunks