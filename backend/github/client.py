import httpx
from typing import List, Dict, Any, Optional
from backend.config.settings import settings
from backend.utils.logger import logger
import base64

class GitHubClient:
    def __init__(self):
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if settings.GITHUB_TOKEN:
            self.headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

    async def fetch_user_repos(self, username: str) -> List[Dict[str, Any]]:
        """Fetch all public repositories for a given GitHub user."""
        url = f"https://api.github.com/users/{username}/repos"
        repos = []
        page = 1
        
        async with httpx.AsyncClient(headers=self.headers) as client:
            while True:
                logger.info(f"Fetching repos for {username}, page {page}")
                response = await client.get(url, params={"per_page": 100, "page": page})
                if response.status_code != 200:
                    logger.error(f"Failed to fetch repos: {response.text}")
                    break
                
                data = response.json()
                if not data:
                    break
                
                repos.extend(data)
                page += 1
                
        return repos

    async def fetch_repo_readme(self, username: str, repo_name: str) -> Optional[str]:
        """Fetch the README for a specific repository."""
        url = f"https://api.github.com/repos/{username}/{repo_name}/readme"
        async with httpx.AsyncClient(headers=self.headers) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", "")
                encoding = data.get("encoding", "")
                if encoding == "base64" and content:
                    try:
                        decoded_content = base64.b64decode(content).decode("utf-8")
                        return decoded_content
                    except Exception as e:
                        logger.warning(f"Failed to decode README for {repo_name}: {e}")
                        return None
            else:
                logger.debug(f"No README found for {repo_name} (Status code: {response.status_code})")
                return None