from fastapi import APIRouter, HTTPException
from backend.models.schemas import ProfileLoadRequest, ProfileLoadResponse, SourceChunk
from backend.github.client import GitHubClient
from backend.github.parser import GitHubParser
from backend.rag.chunker import TextChunker
from backend.rag.embedder import Embedder
from backend.vector.store import vector_store
from backend.utils.logger import logger

router = APIRouter()
github_client = GitHubClient()

@router.post("/profile/load", response_model=ProfileLoadResponse)
async def load_profile(request: ProfileLoadRequest):
    username = request.username
    logger.info(f"Loading profile for {username}")
    
    repos = await github_client.fetch_user_repos(username)
    if not repos:
        raise HTTPException(status_code=404, detail=f"No repositories found for user {username}")
        
    total_chunks = 0
    for repo_data in repos:
        repo_name = repo_data.get("name")
        all_text = ""

        # Fetch README
        readme_content = await github_client.fetch_repo_readme(username, repo_name)
        doc = GitHubParser.parse_repo_data(repo_data, readme_content)
        all_text += doc.get_combined_text()

        # Fetch source code files
        source_files = await github_client.fetch_repo_files(username, repo_name)
        for file in source_files:
            all_text += f"\n\n--- File: {file['path']} ---\n{file['content']}"

        # Chunk combined text
        chunks = TextChunker.chunk_text(all_text)
        if not chunks:
            continue
            
        source_chunks = [
            SourceChunk(
                repo_name=doc.name,
                repo_url=doc.html_url,
                content_snippet=chunk
            ) for chunk in chunks
        ]
        
        embeddings = Embedder.embed_texts(chunks)
        vector_store.add_documents(username, embeddings, source_chunks)
        total_chunks += len(chunks)
        
    logger.info(f"Successfully processed {len(repos)} repos and created {total_chunks} chunks for {username}")
    return ProfileLoadResponse(
        message="Profile loaded successfully",
        username=username,
        repos_indexed=len(repos),
        chunks_created=total_chunks
    )