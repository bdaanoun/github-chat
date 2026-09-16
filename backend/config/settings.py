from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # GitHub Settings
    GITHUB_TOKEN: str = ""

    # LLM Settings (Gemini's OpenAI-compatible endpoint)
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    LLM_MODEL: str = "gemini-2.5-flash"

    # GitHub indexing limits
    # Set MAX_REPOS=0 for unlimited (only safe with a GITHUB_TOKEN)
    # Without a token GitHub allows 60 req/hr → keep limits low
    MAX_REPOS: int = 0           # 0 = all repos (when authenticated)
    MAX_FILES_PER_REPO: int = 50 # files per repo to embed

    # RAG Settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 150       # Kept small to control prompt size
    CHUNK_OVERLAP: int = 20
    TOP_K_RETRIEVAL: int = 10   # chunks per query (more = richer context)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
