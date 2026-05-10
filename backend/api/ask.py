from fastapi import APIRouter, HTTPException
from backend.models.schemas import AskRequest, AskResponse
from backend.rag.retriever import Retriever
from backend.rag.llm import LLMClient
from backend.utils.logger import logger

router = APIRouter()
llm_client = LLMClient()

@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    username = request.username
    question = request.question
    
    logger.info(f"Question for {username}: {question}")
    
    # Retrieve context
    context_chunks = Retriever.retrieve_context(username, question)
    
    if not context_chunks:
        # We don't have this user indexed, or empty DB
        return AskResponse(
            answer="I don't have enough information to answer that. Please ensure the profile has been loaded first.",
            sources=[]
        )
        
    # Ask LLM
    answer = await llm_client.generate_answer(question, context_chunks)
    
    # Return answer + sources
    return AskResponse(
        answer=answer,
        sources=context_chunks
    )