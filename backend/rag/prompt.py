from typing import List, Optional
from backend.models.schemas import SourceChunk


class PromptBuilder:
    @staticmethod
    def build_system_prompt(all_repos: Optional[List[tuple]] = None) -> str:
        base = (
            "You are a GitHub Profile AI Assistant.\n"
            "Your goal is to answer questions about a developer based strictly on their provided repository data.\n"
            "If the answer is not contained within the provided Context below, say "
            "\"I don't have enough information to answer that based on the fetched repositories.\"\n"
            "Do not hallucinate or make up any information outside of the context. "
            "Provide clear, helpful answers."
        )

        if all_repos:
            repo_lines = "\n".join(
                f"  - {name}: https://github.com/{name} ({url})"
                for name, url in all_repos
            )
            base += (
                f"\n\nThe developer has the following {len(all_repos)} indexed repositories "
                f"(use this list when asked to enumerate repos):\n{repo_lines}"
            )

        return base

    # Safety cap: max words per snippet to stay within LLM TPM limits
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

        return f"""Context:
{context_text}

User Question: {question}

Answer based ONLY on the context above and the repository list in the system prompt."""
