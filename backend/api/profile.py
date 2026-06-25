import asyncio
from concurrent.futures import ThreadPoolExecutor
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

# In-memory cache of already-indexed users — avoids full re-fetch on reload
_indexed_users: set = set()

# Thread pool for CPU-bound embedding (avoids blocking the async event loop)
_embed_executor = ThreadPoolExecutor(max_workers=2)


def _embed_sync(chunks: list) -> any:
    """Run embedding synchronously in a thread pool thread."""
    return Embedder.embed_texts(chunks)


@router.post("/profile/load", response_model=ProfileLoadResponse)
async def load_profile(request: ProfileLoadRequest):
    username = request.username.strip().lower()
    logger.info(f"Loading profile for {username}")

    # Return early if user is already indexed in the vector store
    if username in _indexed_users and username in vector_store.indices:
        index = vector_store.indices[username]
        if index.ntotal > 0:
            logger.info(f"Cache hit: {username} already indexed with {index.ntotal} chunks.")
            return ProfileLoadResponse(
                message="Profile already loaded (cached)",
                username=username,
                repos_indexed=0,
                chunks_created=index.ntotal,
            )

    repos = await github_client.fetch_user_repos(username)
    if not repos:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No repositories found for '{username}'. "
                "Check the username, or add a GITHUB_TOKEN to your .env to increase rate limits."
            ),
        )

    async def process_repo(repo_data: dict) -> int:
        repo_name = repo_data.get("name")
        all_text = ""

        # Fetch README and source files in parallel
        readme_content, source_files = await asyncio.gather(
            github_client.fetch_repo_readme(username, repo_name),
            github_client.fetch_repo_files(username, repo_name),
        )

        doc = GitHubParser.parse_repo_data(repo_data, readme_content)
        all_text += doc.get_combined_text()

        for file in source_files:
            all_text += f"\n\n--- File: {file['path']} ---\n{file['content']}"

        chunks = TextChunker.chunk_text(all_text)
        if not chunks:
            return 0

        source_chunks = [
            SourceChunk(
                repo_name=doc.name,
                repo_url=doc.html_url,
                content_snippet=chunk,
            )
            for chunk in chunks
        ]

        # Run the CPU-heavy embedding in a thread so the event loop stays free
        loop = asyncio.get_running_loop()
        embeddings = await loop.run_in_executor(_embed_executor, _embed_sync, chunks)

        vector_store.add_documents(username, embeddings, source_chunks)
        return len(chunks)

    # Process repos concurrently (semaphore in GitHubClient keeps requests sane)
    results = await asyncio.gather(
        *[process_repo(r) for r in repos], return_exceptions=True
    )

    total_chunks = 0
    for r in results:
        if isinstance(r, Exception):
            logger.warning(f"A repo failed to process: {r}")
        else:
            total_chunks += r

    _indexed_users.add(username)
    logger.info(f"Indexed {len(repos)} repos → {total_chunks} chunks for {username}")

    return ProfileLoadResponse(
        message="Profile loaded successfully",
        username=username,
        repos_indexed=len(repos),
        chunks_created=total_chunks,
    )