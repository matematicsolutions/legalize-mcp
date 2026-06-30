"""HTTP client over the legalize-dev GitHub corpus.

Two access paths, both public:
- ``raw.githubusercontent.com`` for law Markdown (keyless) - the primary read path.
- ``api.github.com`` for commit history (keyless, 60 req/h) and code search
  (requires a token, 30 req/min). A ``GITHUB_TOKEN`` env var lifts both limits.

Self-hostable and RODO-safe: nothing leaves the user's machine except read-only GETs to
GitHub; the official ``source`` URL in each law's frontmatter is preserved for provenance.
"""

from __future__ import annotations

import os

import httpx

from .countries import ORG

RAW_BASE = "https://raw.githubusercontent.com"
API_BASE = "https://api.github.com"
_USER_AGENT = "legalize-mcp (+https://matematic.co)"


def _headers() -> dict[str, str]:
    h = {"User-Agent": _USER_AGENT, "Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


class LegalizeClient:
    def __init__(self, timeout: float = 30.0) -> None:
        self._client = httpx.AsyncClient(
            timeout=timeout, headers=_headers(), follow_redirects=True
        )

    async def __aenter__(self) -> LegalizeClient:
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self._client.aclose()

    async def get_raw(self, url: str) -> str:
        """Fetch a raw law Markdown file. Raises httpx.HTTPStatusError on 4xx/5xx."""
        resp = await self._client.get(url)
        resp.raise_for_status()
        return resp.text

    async def list_commits(self, country: str, path: str, limit: int) -> list[dict]:
        """Commit history for a single file path within legalize-{country}."""
        url = f"{API_BASE}/repos/{ORG}/legalize-{country}/commits"
        resp = await self._client.get(url, params={"path": path, "per_page": min(limit, 100)})
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else []

    async def search_code(self, country: str, query: str, limit: int) -> list[dict]:
        """GitHub code search scoped to legalize-{country}. Requires a token."""
        q = f"{query} repo:{ORG}/legalize-{country}"
        url = f"{API_BASE}/search/code"
        resp = await self._client.get(
            url,
            params={"q": q, "per_page": min(limit, 100)},
            headers={"Accept": "application/vnd.github.text-match+json", **_headers()},
        )
        resp.raise_for_status()
        return resp.json().get("items", [])

    @property
    def has_token(self) -> bool:
        return bool(os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"))
