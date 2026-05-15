import httpx
from typing import List, Dict, Any, Optional
from backend.config.settings import settings
from backend.utils.logger import logger
import base64

INDEXABLE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs",
    ".cpp", ".c", ".h", ".cs", ".rb", ".php", ".swift", ".kt",
    "requirements.txt", "package.json", "Dockerfile", ".env.example"
}

class GitHubClient:
    def __init__(self):
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if settings.GITHUB_TOKEN:
            self.headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

    async def fetch_user_repos(self, username: str) -> List[Dict[str, Any]]:
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
        url = f"https://api.github.com/repos/{username}/{repo_name}/readme"
        async with httpx.AsyncClient(headers=self.headers) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", "")
                encoding = data.get("encoding", "")
                if encoding == "base64" and content:
                    try:
                        return base64.b64decode(content).decode("utf-8")
                    except Exception as e:
                        logger.warning(f"Failed to decode README for {repo_name}: {e}")
                        return None
            return None

    async def fetch_repo_files(self, username: str, repo_name: str) -> List[Dict[str, str]]:
        """Fetch source code files from a repo recursively."""
        url = f"https://api.github.com/repos/{username}/{repo_name}/git/trees/HEAD"
        files = []
        async with httpx.AsyncClient(headers=self.headers) as client:
            response = await client.get(url, params={"recursive": "1"})
            if response.status_code != 200:
                return files
            tree = response.json().get("tree", [])
            for item in tree:
                if item.get("type") != "blob":
                    continue
                path = item.get("path", "")
                # Check if file extension or name is indexable
                if not any(path.endswith(ext) for ext in INDEXABLE_EXTENSIONS):
                    continue
                # Skip large files (over 100KB)
                if item.get("size", 0) > 100000:
                    continue
                # Fetch file content
                file_url = f"https://api.github.com/repos/{username}/{repo_name}/contents/{path}"
                file_response = await client.get(file_url)
                if file_response.status_code == 200:
                    data = file_response.json()
                    content = data.get("content", "")
                    if content:
                        try:
                            decoded = base64.b64decode(content).decode("utf-8")
                            files.append({"path": path, "content": decoded})
                            logger.info(f"Fetched {path} from {repo_name}")
                        except Exception as e:
                            logger.warning(f"Failed to decode {path}: {e}")
        return files