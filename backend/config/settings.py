from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # GitHub Settings
    GITHUB_TOKEN: str = ""
    
    # LLM Settings (defaults to local Ollama)
    OPENAI_API_KEY: str = "ollama"  # Ollama doesn't require a real key
    OPENAI_API_BASE: str = "http://localhost:11434/v1"  # Ollama OpenAI-compatible endpoint
    LLM_MODEL: str = "llama3"  # Run `ollama pull llama3` to download
    
    # RAG Settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 150       # Kept small to stay within Groq TPM limits
    CHUNK_OVERLAP: int = 20
    TOP_K_RETRIEVAL: int = 3     # 3 chunks × ~150 words ≈ safe for 6k TPM
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
