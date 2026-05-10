from pydantic import BaseModel, Field
from typing import List, Optional

class ProfileLoadRequest(BaseModel):
    username: str = Field(..., description="The GitHub username to track and index")

class ProfileLoadResponse(BaseModel):
    message: str
    username: str
    repos_indexed: int
    chunks_created: int

class AskRequest(BaseModel):
    username: str = Field(..., description="The GitHub username context to query")
    question: str = Field(..., description="The question about the developer's profile or repos")

class SourceChunk(BaseModel):
    repo_name: str
    repo_url: str
    content_snippet: str

class AskResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]
