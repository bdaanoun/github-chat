import httpx
import asyncio
import base64
import io
import zipfile
from typing import List, Dict, Any, Optional
from backend.config.settings import settings
from backend.utils.logger import logger

INDEXABLE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs",
    ".cpp", ".c", ".h", ".cs", ".rb", ".php", ".swift", ".kt",
    "requirements.txt", "package.json", "Dockerfile", ".env.example"
}

# Respect GitHub's rate limits:
#   Unauthenticated → 60 req/hr  (keep limits very low)
#   Authenticated   → 5 000 req/hr (generous limits are safe)
HAS_TOKEN = bool(settings.GITHUB_TOKEN)

# Pull limits from settings (so they can be tuned via .env).
# 0 = unlimited (authenticated only; never use 0 without a token).
MAX_REPOS         = settings.MAX_REPOS
MAX_FILES_PER_REPO = settings.MAX_FILES_PER_REPO
REQUEST_TIMEOUT   = 20  # seconds
ARCHIVE_TIMEOUT   = 60  # repository archives can be larger than API JSON responses

# Semaphore: max concurrent GitHub API requests in flight at once
_API_SEMAPHORE = asyncio.Semaphore(15 if HAS_TOKEN else 3)


class GitHubAuthenticationError(Exception):
    """Raised when GitHub rejects the configured access token."""


class GitHubClient:
    def __init__(self):
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if settings.GITHUB_TOKEN:
            self.headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

        self._client = httpx.AsyncClient(
            headers=self.headers,
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
        )

    async def close(self) -> None:
        """Close the underlying HTTP client and release connections."""
        await self._client.aclose()

    async def _get(self, url: str, **kwargs) -> Optional[httpx.Response]:
        """Throttled GET request — respects semaphore and handles timeouts."""
        async with _API_SEMAPHORE:
            try:
                response = await self._client.get(url, **kwargs)
                # If rate-limited, log clearly and return None
                if response.status_code == 403:
                    reset = response.headers.get("X-RateLimit-Reset", "unknown")
                    logger.error(
                        f"GitHub rate limit hit! Reset at {reset}. "
                        "Add a GITHUB_TOKEN to your .env for 5000 req/hr."
                    )
                    return None
                return response
            except httpx.TimeoutException:
                logger.warning(f"Timeout: {url}")
                return None
            except Exception as e:
                logger.warning(f"Request failed for {url}: {e}")
                return None

    async def fetch_user_repos(self, username: str) -> List[Dict[str, Any]]:
        url = f"https://api.github.com/users/{username}/repos"
        repos = []
        page = 1

        # If no token, enforce a safe ceiling regardless of settings to protect
        # against accidentally hammering the unauthenticated 60 req/hr limit.
        effective_max = MAX_REPOS
        if not HAS_TOKEN and (effective_max == 0 or effective_max > 10):
            logger.warning(
                "No GITHUB_TOKEN set — capping MAX_REPOS to 10 to respect rate limits. "
                "Add a token to your .env to fetch more."
            )
            effective_max = 10

        while True:
            logger.info(f"Fetching repos for {username}, page {page}")
            response = await self._get(
                url,
                params={"per_page": 100, "page": page, "sort": "pushed", "direction": "desc"},
            )
            if response is None or response.status_code == 404:
                break
            if response.status_code == 401:
                raise GitHubAuthenticationError(
                    "GitHub rejected GITHUB_TOKEN. Check the Hugging Face secret and replace it if it is expired or invalid."
                )
            if response.status_code != 200:
                logger.error(f"Failed to fetch repos: {response.status_code}")
                break
            data = response.json()
            if not data:
                break

            # Ignore forks entirely; only index repositories owned by the user.
            owned_repos = [repo for repo in data if not repo.get("fork", False)]
            repos.extend(owned_repos)
            page += 1
            # 0 = unlimited, so only break early when a positive limit is set
            if effective_max > 0 and len(repos) >= effective_max:
                break

        repos = sorted(repos, key=lambda r: r.get("pushed_at") or "", reverse=True)
        logger.info(f"Fetched {len(repos)} total repos for {username} (limit={effective_max or 'unlimited'})")
        return repos if effective_max == 0 else repos[:effective_max]

    async def fetch_repo_readme(self, username: str, repo_name: str) -> Optional[str]:
        response = await self._get(
            f"https://api.github.com/repos/{username}/{repo_name}/readme"
        )
        if response and response.status_code == 200:
            data = response.json()
            content = data.get("content", "")
            if data.get("encoding") == "base64" and content:
                try:
                    return base64.b64decode(content).decode("utf-8")
                except Exception as e:
                    logger.warning(f"Failed to decode README for {repo_name}: {e}")
        return None

    async def _fetch_single_file(
        self, username: str, repo_name: str, path: str
    ) -> Optional[Dict[str, str]]:
        response = await self._get(
            f"https://api.github.com/repos/{username}/{repo_name}/contents/{path}"
        )
        if response and response.status_code == 200:
            data = response.json()
            content = data.get("content", "")
            if content:
                try:
                    decoded = base64.b64decode(content).decode("utf-8")
                    logger.info(f"Fetched {path} from {repo_name}")
                    return {"path": path, "content": decoded}
                except Exception as e:
                    logger.warning(f"Failed to decode {path}: {e}")
        return None

    async def fetch_repo_files(self, username: str, repo_name: str) -> List[Dict[str, str]]:
        """Download and filter a repository in one archive request.

        The previous implementation made one API request per eligible file.
        GitHub's archive endpoint reduces that to one download per repository.
        """
        response = await self._get(
            f"https://api.github.com/repos/{username}/{repo_name}/zipball/HEAD",
            timeout=ARCHIVE_TIMEOUT,
        )
        if not response or response.status_code != 200:
            logger.warning(f"Failed to download archive for {repo_name}")
            return []

        files: List[Dict[str, str]] = []
        try:
            with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
                for member in archive.infolist():
                    if member.is_dir() or member.file_size > 100_000:
                        continue

                    path = member.filename.split("/", 1)[-1]
                    if not any(path.endswith(ext) for ext in INDEXABLE_EXTENSIONS):
                        continue

                    try:
                        content = archive.read(member).decode("utf-8")
                    except (UnicodeDecodeError, RuntimeError, zipfile.BadZipFile):
                        continue

                    files.append({"path": path, "content": content})
                    if len(files) >= MAX_FILES_PER_REPO:
                        break
        except zipfile.BadZipFile:
            logger.warning(f"Invalid archive received for {repo_name}")
            return []

        logger.info(f"Downloaded {len(files)} files from {repo_name} in one archive")
        return files