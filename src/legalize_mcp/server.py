"""FastMCP entry point - legalize-dev law-as-git corpus (32 jurisdictions).

Run:

    python -m legalize_mcp.server

Configuration via env:

- ``LEGALIZE_AUDIT_DIR`` (default ``~/.matematic/audit``)
- ``GITHUB_TOKEN`` / ``GH_TOKEN`` (optional; required only for ``legalize_search_laws``,
  lifts rate limits on ``legalize_list_reforms``)
"""

from __future__ import annotations

import httpx
from fastmcp import FastMCP
from mcp.types import ToolAnnotations

from . import countries
from .audit import AuditLogger, hash_input, timer
from .citations import (
    github_blob_url,
    human_citation,
    is_valid_law_id,
    parse_frontmatter,
    raw_url,
    split_extra,
)
from .client import LegalizeClient
from .models import CountryInfo, LawMeta, LawText, Reform, SearchHit

INSTRUCTIONS = """\
This MCP server exposes the **legalize-dev** corpus: national legislation for 32 jurisdictions, \
stored as "law-as-git" - one law per Markdown file, every reform a Git commit \
(github.com/legalize-dev, MIT-licensed). Each law carries an 8-field ELI-style frontmatter \
(Legalize Format Spec v0.2). Every response carries the citation contract: the official \
`source_url` (from the law's frontmatter) plus a `github_url` (the verifiable copy we read).

## Call order

1. `legalize_list_countries` - which jurisdictions are available (code, name, EU flag). EU members \
   include at/be/cz/de/ee/es/eu/fi/fr/gr/ie/it/lt/lu/lv/nl/pl/pt/ro/se/sk.
2. `legalize_search_laws(country, query)` - find a law id by keyword (needs `GITHUB_TOKEN`). \
   Returns `law_id` + path + a match snippet.
3. `legalize_get_law(country, law_id)` - the law's metadata AND full text by id (the .md filename \
   stem, e.g. `BOE-A-1978-31229` for ES, a numeric id for EE). Keyless.
4. `legalize_list_reforms(country, law_id)` - the timeline of reforms (commits) to that law.
5. `legalize_get_law(country, law_id, sha=...)` - the historical state of a law at a given commit.

## Hard constraints

- **`law_id` is the filename stem, not a free-text title** - get it from `legalize_search_laws` or \
  an official citation. There is no fuzzy title lookup.
- **Two citation URLs, both real** - `source_url` is the official government source; `github_url` is \
  the legalize-dev provenance. Cite at least the `source_url`. Never invent either.
- **`legalize_search_laws` needs a GitHub token** - without `GITHUB_TOKEN`/`GH_TOKEN` it returns a \
  `config_error`. `legalize_get_law` and `legalize_list_reforms` work keyless (lower rate limits).
- **Audit log JSONL** - every tool call appends to `~/.matematic/audit/legalize-mcp.jsonl`.

## Error iteration

Tools return a structured error with a `[code]` prefix:
- `invalid_arg` - unknown `country` code or malformed `law_id`.
- `config_error` - a required `GITHUB_TOKEN` is missing (search only).
- `not_found` - no law/commit for that id.
- `upstream_error` - a GitHub error (HTTP, timeout, rate limit). Retry once before surfacing.

## Response style

- Cite as `human_readable_citation` with the official source: \
  "Constitución Española (BOE-A-1978-31229), https://www.boe.es/eli/es/c/1978/12/27/(1)".
- NEVER invent a `law_id`, a title, a date or a URL - take each from the tool output.
"""


class ToolError(Exception):
    """Structured error for legalize MCP tools - visible to the LLM with a [code] prefix."""

    VALID_CODES = frozenset({"invalid_arg", "config_error", "not_found", "upstream_error"})

    def __init__(self, code: str, message: str):
        if code not in self.VALID_CODES:
            raise ValueError(f"Unknown ToolError code: {code}. Valid: {sorted(self.VALID_CODES)}")
        self.code = code
        super().__init__(f"[{code}] {message}")


READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    idempotentHint=True,
    destructiveHint=False,
    openWorldHint=True,
)

mcp: FastMCP = FastMCP(name="legalize-mcp", instructions=INSTRUCTIONS)


def _audit() -> AuditLogger:
    return AuditLogger()


def _map_upstream(exc: Exception) -> Exception:
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        if status == 404:
            return ToolError("not_found", "No such law or commit in the legalize-dev corpus.")
        if status in (403, 429):
            return ToolError("upstream_error", "GitHub rate limit hit; set GITHUB_TOKEN or retry later.")
    if isinstance(exc, (httpx.HTTPStatusError, httpx.TransportError, httpx.TimeoutException)):
        return ToolError("upstream_error", f"GitHub error: {type(exc).__name__}: {exc}")
    return exc


def _country(code: str) -> countries.Country:
    c = countries.get(code)
    if c is None:
        raise ToolError(
            "invalid_arg",
            f"country={code!r} is not supported. Call legalize_list_countries for valid codes.",
        )
    return c


def _law_id(law_id: str) -> str:
    lid = (law_id or "").strip()
    if not is_valid_law_id(lid):
        raise ToolError("invalid_arg", f"law_id={law_id!r} is malformed (filename stem; no slashes).")
    return lid


# ---------------------------------------------------------------------------
# legalize_list_countries
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ_ONLY)
async def legalize_list_countries(eu_only: bool = False) -> list[CountryInfo]:
    """List the jurisdictions available in the legalize-dev corpus.

    Args:
        eu_only: if true, restrict to EU member states.

    Returns:
        A list of ``CountryInfo`` (code, name, eu, repo).
    """
    audit = _audit()
    with timer() as t:
        out = [
            CountryInfo(code=c.code, name=c.name, eu=c.eu, repo=countries.repo(c.code))
            for c in countries.COUNTRIES.values()
            if not eu_only or c.eu
        ]
    audit.log(tool="legalize_list_countries", input_hash=hash_input({"eu_only": eu_only}),
              output_count_or_size=len(out), duration_ms=t.duration_ms, status="ok")
    return out


# ---------------------------------------------------------------------------
# legalize_search_laws
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ_ONLY)
async def legalize_search_laws(country: str, query: str, limit: int = 10) -> list[SearchHit]:
    """Search a jurisdiction's laws by keyword (GitHub code search; requires a token).

    Args:
        country: ISO-3166 alpha-2 code (e.g. ``"ee"``, ``"es"``).
        query: keyword(s) to find inside the law texts.
        limit: max hits (1-100, default 10).

    Returns:
        A list of ``SearchHit`` (country, law_id, path, github_url, snippet).
    """
    audit = _audit()
    c = _country(country)
    if not query or not query.strip():
        raise ToolError("invalid_arg", "query must be a non-empty keyword string.")
    limit = max(1, min(limit, 100))
    input_hash = hash_input({"country": c.code, "query": query, "limit": limit})

    with timer() as t:
        async with LegalizeClient() as client:
            if not client.has_token:
                audit.log(tool="legalize_search_laws", input_hash=input_hash, output_count_or_size=0,
                          duration_ms=t.duration_ms if t.duration_ms else 0, status="error",
                          error="config_error")
                raise ToolError(
                    "config_error",
                    "GitHub code search needs a token. Set GITHUB_TOKEN (or GH_TOKEN). "
                    "legalize_get_law and legalize_list_reforms work without one.",
                )
            try:
                items = await client.search_code(c.code, query, limit)
            except Exception as exc:
                audit.log(tool="legalize_search_laws", input_hash=input_hash, output_count_or_size=0,
                          duration_ms=t.duration_ms if t.duration_ms else 0, status="error",
                          error=f"{type(exc).__name__}: {exc}")
                raise _map_upstream(exc) from exc

    hits: list[SearchHit] = []
    for it in items:
        path = it.get("path", "")
        stem = path.rsplit("/", 1)[-1].removesuffix(".md")
        snippet = None
        matches = it.get("text_matches") or []
        if matches:
            snippet = (matches[0].get("fragment") or "").strip()[:300] or None
        hits.append(SearchHit(
            country=c.code, law_id=stem, path=path,
            github_url=github_blob_url(c.code, stem, c.branch), snippet=snippet,
        ))
    audit.log(tool="legalize_search_laws", input_hash=input_hash, output_count_or_size=len(hits),
              duration_ms=t.duration_ms, status="ok")
    return hits


# ---------------------------------------------------------------------------
# legalize_get_law
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ_ONLY)
async def legalize_get_law(country: str, law_id: str, sha: str | None = None) -> LawText:
    """Fetch a law's metadata and full text by id (optionally at a historical commit).

    Args:
        country: ISO-3166 alpha-2 code (e.g. ``"es"``).
        law_id: the filename stem (e.g. ``"BOE-A-1978-31229"``).
        sha: optional commit SHA for a historical version (from ``legalize_list_reforms``).

    Returns:
        ``LawText`` with the citation contract, frontmatter metadata and the full Markdown body.
    """
    audit = _audit()
    c = _country(country)
    lid = _law_id(law_id)
    if sha is not None and not sha.strip().isalnum():
        raise ToolError("invalid_arg", "sha must be an alphanumeric commit hash.")
    input_hash = hash_input({"country": c.code, "law_id": lid, "sha": sha})

    with timer() as t:
        try:
            async with LegalizeClient() as client:
                raw = await client.get_raw(raw_url(c.code, lid, c.branch, sha))
        except Exception as exc:
            audit.log(tool="legalize_get_law", input_hash=input_hash, output_count_or_size=0,
                      duration_ms=t.duration_ms if t.duration_ms else 0, status="error",
                      error=f"{type(exc).__name__}: {exc}")
            raise _map_upstream(exc) from exc

    meta, body = parse_frontmatter(raw)
    result = LawText(
        country=c.code,
        law_id=lid,
        title=meta.get("title"),
        rank=meta.get("rank"),
        status=meta.get("status"),
        publication_date=meta.get("publication_date"),
        last_updated=meta.get("last_updated"),
        source_url=meta.get("source"),
        github_url=github_blob_url(c.code, lid, c.branch, sha),
        human_readable_citation=human_citation(meta),
        extra=split_extra(meta),
        content=body,
        byte_size=len(body.encode("utf-8")),
        sha=sha,
    )
    audit.log(tool="legalize_get_law", input_hash=input_hash, output_count_or_size=result.byte_size,
              duration_ms=t.duration_ms, status="ok")
    return result


# ---------------------------------------------------------------------------
# legalize_get_meta  (lightweight: frontmatter only)
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ_ONLY)
async def legalize_get_meta(country: str, law_id: str) -> LawMeta:
    """Fetch only a law's frontmatter metadata (no body) - cheap for citation checks.

    Args:
        country: ISO-3166 alpha-2 code.
        law_id: the filename stem.

    Returns:
        ``LawMeta`` with the citation contract and frontmatter fields.
    """
    audit = _audit()
    c = _country(country)
    lid = _law_id(law_id)
    input_hash = hash_input({"country": c.code, "law_id": lid})

    with timer() as t:
        try:
            async with LegalizeClient() as client:
                raw = await client.get_raw(raw_url(c.code, lid, c.branch))
        except Exception as exc:
            audit.log(tool="legalize_get_meta", input_hash=input_hash, output_count_or_size=0,
                      duration_ms=t.duration_ms if t.duration_ms else 0, status="error",
                      error=f"{type(exc).__name__}: {exc}")
            raise _map_upstream(exc) from exc

    meta, _ = parse_frontmatter(raw)
    result = LawMeta(
        country=c.code,
        law_id=lid,
        title=meta.get("title"),
        rank=meta.get("rank"),
        status=meta.get("status"),
        publication_date=meta.get("publication_date"),
        last_updated=meta.get("last_updated"),
        source_url=meta.get("source"),
        github_url=github_blob_url(c.code, lid, c.branch),
        human_readable_citation=human_citation(meta),
        extra=split_extra(meta),
    )
    audit.log(tool="legalize_get_meta", input_hash=input_hash, output_count_or_size=1,
              duration_ms=t.duration_ms, status="ok")
    return result


# ---------------------------------------------------------------------------
# legalize_list_reforms
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ_ONLY)
async def legalize_list_reforms(country: str, law_id: str, limit: int = 20) -> list[Reform]:
    """List the reform history (commits) of a law - the legislative timeline.

    Args:
        country: ISO-3166 alpha-2 code.
        law_id: the filename stem.
        limit: max reforms, newest first (1-100, default 20).

    Returns:
        A list of ``Reform`` (sha, date, message, github_url). Pass a ``sha`` back to
        ``legalize_get_law`` to read the law as it stood at that reform.
    """
    audit = _audit()
    c = _country(country)
    lid = _law_id(law_id)
    limit = max(1, min(limit, 100))
    path = f"{c.code}/{lid}.md"
    input_hash = hash_input({"country": c.code, "law_id": lid, "limit": limit})

    with timer() as t:
        try:
            async with LegalizeClient() as client:
                commits = await client.list_commits(c.code, path, limit)
        except Exception as exc:
            audit.log(tool="legalize_list_reforms", input_hash=input_hash, output_count_or_size=0,
                      duration_ms=t.duration_ms if t.duration_ms else 0, status="error",
                      error=f"{type(exc).__name__}: {exc}")
            raise _map_upstream(exc) from exc

    if not commits:
        raise ToolError("not_found", f"No commit history for {path} in legalize-{c.code}.")
    reforms = [
        Reform(
            sha=ci.get("sha", ""),
            date=(ci.get("commit", {}).get("author", {}) or {}).get("date"),
            message=(ci.get("commit", {}) or {}).get("message", "").split("\n", 1)[0] or None,
            github_url=f"https://github.com/{countries.ORG}/legalize-{c.code}/commit/{ci.get('sha', '')}",
        )
        for ci in commits
    ]
    audit.log(tool="legalize_list_reforms", input_hash=input_hash, output_count_or_size=len(reforms),
              duration_ms=t.duration_ms, status="ok")
    return reforms


def main() -> None:
    """Run the MCP server over stdio (default for Claude Code)."""
    mcp.run()


if __name__ == "__main__":
    main()
