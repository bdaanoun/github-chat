import openai
from typing import List, Optional
from backend.config.settings import settings
from backend.rag.prompt import PromptBuilder
from backend.models.schemas import SourceChunk
from backend.utils.logger import logger


class LLMClient:
    def __init__(self):
        client_kwargs = {"api_key": settings.OPENAI_API_KEY}
        if settings.OPENAI_API_BASE:
            client_kwargs["base_url"] = settings.OPENAI_API_BASE

        self.client = openai.AsyncOpenAI(**client_kwargs)

    async def generate_answer(
        self,
        question: str,
        context_chunks: List[SourceChunk],
        all_repos: Optional[List[tuple]] = None,
    ) -> str:
        try:
            # System prompt includes the complete repo list so the LLM always
            # knows every indexed repo — not just the ones in the retrieved chunks
            sys_prompt = PromptBuilder.build_system_prompt(all_repos=all_repos)
            user_prompt = PromptBuilder.build_user_prompt(question, context_chunks)

            response = await self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Failed to generate answer from LLM: {e}")
            return f"An error occurred while generating the answer: {str(e)}"
