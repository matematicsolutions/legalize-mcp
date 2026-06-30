"""Pydantic response models - every law-bearing model carries the citation contract."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CountryInfo(BaseModel):
    code: str
    name: str
    eu: bool
    repo: str = Field(description="GitHub owner/repo slug for this jurisdiction's corpus.")


class LawMeta(BaseModel):
    """Frontmatter metadata for a single law (Legalize Format Spec v0.2 + extensions)."""

    country: str
    law_id: str = Field(description="Official identifier (the .md filename stem).")
    title: str | None = None
    rank: str | None = Field(default=None, description="Country-specific legal text type.")
    status: str | None = Field(default=None, description="in_force | repealed | ...")
    publication_date: str | None = None
    last_updated: str | None = None
    # citation contract
    source_url: str | None = Field(default=None, description="Official source URL (frontmatter `source`).")
    github_url: str = Field(description="Raw provenance URL on github.com/legalize-dev.")
    human_readable_citation: str | None = None
    extra: dict[str, str] = Field(default_factory=dict, description="Country-specific frontmatter fields.")


class LawText(LawMeta):
    """A law's metadata plus its full Markdown body."""

    content: str = Field(description="Full law text (Markdown, frontmatter stripped).")
    byte_size: int = 0
    sha: str | None = Field(default=None, description="Git commit SHA if a historical version was requested.")


class SearchHit(BaseModel):
    country: str
    law_id: str
    path: str
    github_url: str
    snippet: str | None = None


class Reform(BaseModel):
    """One commit touching a law file - a single legislative reform in its history."""

    sha: str
    date: str | None = None
    message: str | None = None
    github_url: str
