"""Frontmatter parsing + citation helpers for the legalize-dev corpus.

Each law file is Markdown with a leading YAML frontmatter block (Legalize Format Spec v0.2):

    ---
    title: "..."
    identifier: "..."
    country: "ee"
    rank: "maarus"
    publication_date: "YYYY-MM-DD"
    last_updated: "YYYY-MM-DD"
    status: "in_force"
    source: "https://official-source-url"
    ...country-specific extensions...
    ---
    <body>

Citation contract:
- ``source_url``: the OFFICIAL source from the frontmatter (e.g. riigiteataja.ee). Never invented.
- ``github_url``: the raw provenance on github.com/legalize-dev (the verifiable copy we read).
- ``human_readable_citation``: "<title> (<identifier>)".
"""

from __future__ import annotations

import re
from typing import Any

import yaml

from .countries import ORG

_SPEC_FIELDS = (
    "title", "identifier", "country", "rank",
    "publication_date", "last_updated", "status", "source",
)
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)
# Law ids are filename stems: digits/letters/dot/dash, no slashes or traversal.
_LAW_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-]*$")


def is_valid_law_id(law_id: str) -> bool:
    return bool(_LAW_ID_RE.match(law_id.strip()))


def raw_url(country: str, law_id: str, branch: str = "main", sha: str | None = None) -> str:
    """Raw markdown URL on raw.githubusercontent.com (keyless)."""
    ref = sha or branch
    return f"https://raw.githubusercontent.com/{ORG}/legalize-{country}/{ref}/{country}/{law_id}.md"


def github_blob_url(country: str, law_id: str, branch: str = "main", sha: str | None = None) -> str:
    """Human-facing github.com blob URL for provenance."""
    ref = sha or branch
    return f"https://github.com/{ORG}/legalize-{country}/blob/{ref}/{country}/{law_id}.md"


def parse_frontmatter(raw: str) -> tuple[dict[str, Any], str]:
    """Split a law file into (frontmatter dict, body). Returns ({}, raw) if no frontmatter."""
    m = _FRONTMATTER_RE.match(raw)
    if not m:
        return {}, raw
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}, raw
    if not isinstance(meta, dict):
        return {}, raw
    return meta, m.group(2).strip()


def human_citation(meta: dict[str, Any]) -> str | None:
    title = meta.get("title")
    ident = meta.get("identifier")
    if title and ident:
        return f"{title} ({ident})"
    return title or (str(ident) if ident else None)


def split_extra(meta: dict[str, Any]) -> dict[str, str]:
    """Country-specific frontmatter fields beyond the 8 mandatory ones, stringified."""
    return {
        k: str(v)
        for k, v in meta.items()
        if k not in _SPEC_FIELDS and v is not None
    }
