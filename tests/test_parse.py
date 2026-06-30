"""Offline unit tests - pure functions, no network."""

from __future__ import annotations

from legalize_mcp import countries
from legalize_mcp.citations import (
    github_blob_url,
    human_citation,
    is_valid_law_id,
    parse_frontmatter,
    raw_url,
    split_extra,
)

SAMPLE = """\
---
title: "Constitución Española"
identifier: "BOE-A-1978-31229"
country: "es"
rank: "constitucion"
publication_date: "1978-12-29"
last_updated: "2024-02-17"
status: "in_force"
source: "https://www.boe.es/eli/es/c/1978/12/27/(1)"
jurisdiction: "estatal"
---
Artículo 1. España se constituye en un Estado social...
"""


def test_parse_frontmatter_splits_meta_and_body():
    meta, body = parse_frontmatter(SAMPLE)
    assert meta["identifier"] == "BOE-A-1978-31229"
    assert meta["status"] == "in_force"
    assert body.startswith("Artículo 1.")


def test_human_citation():
    meta, _ = parse_frontmatter(SAMPLE)
    assert human_citation(meta) == "Constitución Española (BOE-A-1978-31229)"


def test_split_extra_keeps_only_country_specific_fields():
    meta, _ = parse_frontmatter(SAMPLE)
    extra = split_extra(meta)
    assert extra == {"jurisdiction": "estatal"}


def test_no_frontmatter_returns_empty_meta():
    meta, body = parse_frontmatter("just text, no frontmatter")
    assert meta == {}
    assert body == "just text, no frontmatter"


def test_law_id_validation_blocks_traversal():
    assert is_valid_law_id("BOE-A-1978-31229")
    assert is_valid_law_id("1009476")
    assert not is_valid_law_id("../../etc/passwd")
    assert not is_valid_law_id("foo/bar")
    assert not is_valid_law_id("")


def test_url_builders():
    assert raw_url("es", "BOE-A-1978-31229").endswith("/es/BOE-A-1978-31229.md")
    assert "raw.githubusercontent.com/legalize-dev/legalize-es/main" in raw_url("es", "X")
    assert "github.com/legalize-dev/legalize-ee/blob" in github_blob_url("ee", "1009476")


def test_country_registry():
    assert countries.is_supported("ee")
    assert countries.is_supported("PT")  # case-insensitive
    assert not countries.is_supported("zz")
    assert countries.repo("ee") == "legalize-dev/legalize-ee"
    eu = [c for c in countries.COUNTRIES.values() if c.eu]
    assert len(eu) >= 20
    # our 5 previously-missing EU jurisdictions are now covered
    for code in ("pt", "it", "ee", "gr", "lv"):
        assert countries.is_supported(code)
