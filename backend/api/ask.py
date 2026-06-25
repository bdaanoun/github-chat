from fastapi import APIRouter, HTTPException
from backend.models.schemas import AskRequest, AskResponse
from backend.rag.retriever import Retriever
from backend.rag.llm import LLMClient
from backend.vector.store import vector_store
from backend.utils.logger import logger

router = APIRouter()
llm_client = LLMClient()

@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    username = request.username
    question = request.question

    logger.info(f"Question for {username}: {question}")

    # Full list of indexed repos — always injected into the system prompt
    # so the LLM knows every repo by name regardless of which chunks are retrieved
    all_repos = vector_store.get_all_repos(username)

    # Retrieve semantically relevant context chunks
    context_chunks = Retriever.retrieve_context(username, question)

    if not context_chunks and not all_repos:
        return AskResponse(
            answer="I don't have enough information to answer that. Please ensure the profile has been loaded first.",
            sources=[]
        )

    # Ask LLM (all_repos goes into the system prompt, context_chunks into the user prompt)
    answer = await llm_client.generate_answer(question, context_chunks, all_repos=all_repos)

    return AskResponse(
        answer=answer,
        sources=context_chunks
    )