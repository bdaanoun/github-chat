from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import profile, ask
from backend.utils.logger import logger

app = FastAPI(title="GitHub Profile RAG API")

# Setup CORS for local frontend execution
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect Routes
app.include_router(profile.router, prefix="/api", tags=["Profile"])
app.include_router(ask.router, prefix="/api", tags=["Ask"])

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up GitHub Profile RAG API.")

@app.get("/")
def root():
    return {"message": "GitHub Profile RAG API is running."}
