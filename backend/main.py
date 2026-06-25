from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import profile, ask
from backend.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown lifecycle."""
    logger.info("Starting up GitHub Profile RAG API.")
    yield
    # Gracefully close the shared GitHub HTTP client on shutdown
    await profile.github_client.close()
    logger.info("GitHub HTTP client closed. Shutting down.")


app = FastAPI(title="GitHub Profile RAG API", lifespan=lifespan)

# Setup CORS for local frontend execution
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect Routes
app.include_router(profile.router, prefix="/api", tags=["Profile"])
app.include_router(ask.router, prefix="/api", tags=["Ask"])


@app.get("/")
def root():
    return {"message": "GitHub Profile RAG API is running."}
