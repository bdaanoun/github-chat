import httpx
import asyncio
import base64
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

# Semaphore: max concurrent GitHub API requests in flight at once
_API_SEMAPHORE = asyncio.Semaphore(15 if HAS_TOKEN else 3)


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
            if response.status_code != 200:
                logger.error(f"Failed to fetch repos: {response.status_code}")
                break
            data = response.json()
            if not data:
                break
            repos.extend(data)
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
        response = await self._get(
            f"https://api.github.com/repos/{username}/{repo_name}/git/trees/HEAD",
            params={"recursive": "1"},
        )
        if not response or response.status_code != 200:
            return []

        tree = response.json().get("tree", [])
        eligible_paths = []
        for item in tree:
            if item.get("type") != "blob":
                continue
            path = item.get("path", "")
            if not any(path.endswith(ext) for ext in INDEXABLE_EXTENSIONS):
                continue
            if item.get("size", 0) > 100_000:
                continue
            eligible_paths.append(path)

        eligible_paths = eligible_paths[:MAX_FILES_PER_REPO]
        if not eligible_paths:
            return []

        tasks = [self._fetch_single_file(username, repo_name, path) for path in eligible_paths]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]