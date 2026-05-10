from typing import List, Dict, Any, Optional
from backend.utils.logger import logger

class RepoDocument:
    def __init__(self, name: str, html_url: str, description: str, language: str, readme: Optional[str]):
        self.name = name
        self.html_url = html_url
        self.description = description or ""
        self.language = language or "Unknown"
        self.readme = readme or ""

    def get_combined_text(self) -> str:
        """Combine repository metadata and README into a single text document for embedding."""
        parts = []
        parts.append(f"Repository Name: {self.name}")
        parts.append(f"URL: {self.html_url}")
        parts.append(f"Primary Language: {self.language}")
        if self.description:
            parts.append(f"Description: {self.description}")
        if self.readme:
            parts.append(f"\n--- README ---\n{self.readme}")
            
        return "\n".join(parts)


class GitHubParser:
    @staticmethod
    def parse_repo_data(repo_data: Dict[str, Any], readme_content: Optional[str]) -> RepoDocument:
        """Parse raw GitHub repository data and README into a RepoDocument."""
        name = repo_data.get("name", "Unknown Repo")
        html_url = repo_data.get("html_url", "")
        description = repo_data.get("description", "")
        language = repo_data.get("language", "")
        
        return RepoDocument(
            name=name,
            html_url=html_url,
            description=description,
            language=language,
            readme=readme_content
        )
