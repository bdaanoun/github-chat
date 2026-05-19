from typing import List
from backend.models.schemas import SourceChunk

class PromptBuilder:
    @staticmethod
    def build_system_prompt() -> str:
        return """You are a GitHub Profile AI Assistant. 
Your goal is to answer questions about a developer based strictly on their provided repository data.
If the answer is not contained within the provided Context below, say "I don't have enough information to answer that based on the fetched repositories."
Do not hallucinate or make up any information outside of the context. Provide clear, helpful answers."""

    # Safety cap: max words per snippet to stay within Groq's 6 000 TPM limit
    MAX_SNIPPET_WORDS = 200

    @staticmethod
    def build_user_prompt(question: str, context_chunks: List[SourceChunk]) -> str:
        context_text = ""
        for i, chunk in enumerate(context_chunks):
            snippet = chunk.content_snippet
            words = snippet.split()
            if len(words) > PromptBuilder.MAX_SNIPPET_WORDS:
                snippet = " ".join(words[:PromptBuilder.MAX_SNIPPET_WORDS]) + "…"
            context_text += f"---\nSource {i+1}: {chunk.repo_name} ({chunk.repo_url})\n{snippet}\n"

        prompt = f"""Context:
{context_text}

User Question: {question}

Answer based ONLY on the context above."""
        return prompt
