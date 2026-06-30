"""Static registry of the legalize-dev country corpora.

Each country's legal corpus lives in its own GitHub repo ``legalize-{code}`` under the
``legalize-dev`` org (MIT-licensed), following the Legalize Format Spec v0.2: one law per
``.md`` file with an 8-field ELI-style YAML frontmatter, every reform a Git commit.

This registry is the source of truth for which jurisdictions this connector serves and how
to address each repo. Empty/stub repos (dk, ua) are intentionally excluded.
"""

from __future__ import annotations

from typing import NamedTuple

ORG = "legalize-dev"


class Country(NamedTuple):
    code: str          # ISO 3166-1 alpha-2 (lowercase), used as repo suffix + folder
    name: str          # English display name
    eu: bool           # EU member state
    branch: str = "main"


# Live corpora confirmed via the GitHub API (2026-06-30). Sizes/counts in README.
_COUNTRIES: tuple[Country, ...] = (
    Country("ad", "Andorra", False),
    Country("ar", "Argentina", False),
    Country("at", "Austria", True),
    Country("be", "Belgium", True),
    Country("ch", "Switzerland", False),
    Country("cl", "Chile", False),
    Country("co", "Colombia", False),
    Country("cz", "Czechia", True),
    Country("de", "Germany", True),
    Country("ee", "Estonia", True),
    Country("es", "Spain", True),
    Country("eu", "European Union", True),
    Country("fi", "Finland", True),
    Country("fr", "France", True),
    Country("gr", "Greece", True),
    Country("ie", "Ireland", True),
    Country("it", "Italy", True),
    Country("kr", "South Korea", False),
    Country("li", "Liechtenstein", False),
    Country("lt", "Lithuania", True),
    Country("lu", "Luxembourg", True),
    Country("lv", "Latvia", True),
    Country("nl", "Netherlands", True),
    Country("no", "Norway", False),
    Country("pl", "Poland", True),
    Country("pt", "Portugal", True),
    Country("ro", "Romania", True),
    Country("se", "Sweden", True),
    Country("sk", "Slovakia", True),
    Country("uk", "United Kingdom", False),
    Country("us", "United States", False),
    Country("uy", "Uruguay", False),
)

# Dedup by code, preserving first occurrence.
COUNTRIES: dict[str, Country] = {}
for _c in _COUNTRIES:
    COUNTRIES.setdefault(_c.code, _c)


def is_supported(code: str) -> bool:
    return code.strip().lower() in COUNTRIES


def get(code: str) -> Country | None:
    return COUNTRIES.get(code.strip().lower())


def repo(code: str) -> str:
    """Full ``owner/repo`` slug for a country code (e.g. ``legalize-dev/legalize-ee``)."""
    return f"{ORG}/legalize-{code.strip().lower()}"
