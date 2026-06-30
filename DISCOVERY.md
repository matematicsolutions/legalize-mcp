# DISCOVERY - legalize-mcp (legalize-dev law-as-git corpus, 37 jurisdictions)

Date: 2026-06-30. Source found via the LegalTech discovery sweep (`legaltech-scout` skill):
`npx skills find legal` surfaced `aradotso/trending-skills@legalize-es-spanish-legislation`, behind
which sits the **legalize-dev** GitHub org. Decision: **WRAP** (the corpus is already normalised; we
add the citation contract + audit + governance).

## Why this corpus, what's clean

legalize-dev stores national legislation as **law-as-git**: one law per Markdown file, every reform a
Git commit, with an 8-field ELI-style YAML frontmatter (Legalize Format Spec v0.2, defined in the root
`legalize-dev/legalize` repo `SPEC.md`). MIT-licensed. This is the cleanest possible substrate - no
scraping, no SPA, no PDF: just raw Markdown with structured metadata and a real commit history.

Unlike the single-country `*-eli-mcp` connectors, **one server serves all 37 jurisdictions**, because
the format is uniform across countries.

## Coverage (probed live via GitHub API, 2026-06-30)

All repos live (commits June 2026). `.md` counts for the five EU jurisdictions previously classified
"scraping/SPA/PDF" in the eu-legal-mcp line - now covered keyless:

| Country | Repo | .md files |
|---|---|---|
| Estonia | legalize-ee | 1 598 |
| Greece | legalize-gr | 6 805 |
| Latvia | legalize-lv | 15 540 |
| Italy | legalize-it | 77 591 |
| Portugal | legalize-pt | 90 667 |

EU set served: at be cz de ee es eu fi fr gr ie it lt lu lv nl pl pt ro se sk (21).

## Access paths

| Purpose | Path | Auth |
|---|---|---|
| Law Markdown | `raw.githubusercontent.com/legalize-dev/legalize-{cc}/main/{cc}/{id}.md` | **keyless** |
| Reform history | `api.github.com/repos/legalize-dev/legalize-{cc}/commits?path=...` | keyless (60/h) |
| Historical version | raw URL at a commit `{sha}` | **keyless** |
| Keyword search | `api.github.com/search/code?q=...+repo:...` | **token required** |
| (alt) Hosted API | `https://legalize.dev/api/v1/{cc}/laws...` + `/at/{sha}` + `/reforms` | free key |

The connector uses the **keyless raw + commits paths** (Path B): self-hostable, RODO/GDPR-safe,
nothing leaves the machine except read-only GETs. The hosted API (free key) is a documented fallback;
`legalize_search_laws` is the only tool needing a `GITHUB_TOKEN`.

## Frontmatter (probed)

Mandatory 8 fields: `title`, `identifier`, `country`, `rank`, `publication_date`, `last_updated`,
`status` (`in_force`/`repealed`/...), `source` (official government URL). Country-specific extensions
welcome (EE adds `department`, `text_type`, RT references; ES adds `jurisdiction`, `rank_code`; etc.) -
surfaced under `extra`.

Probed examples: `ee/1009476` (source riigiteataja.ee), `es/BOE-A-1978-31229` (Constitución Española,
source boe.es; reform history art. 49 (2024), art. 135 (2011), art. 13 (1992); historical version at
the 1992 commit reads as 115 KB vs 119 KB current).

## Citation contract (Art. 4)

- `source_url` = the official government source from the law's own frontmatter (never invented).
- `github_url` = the legalize-dev provenance blob (the verifiable copy actually read).
- `human_readable_citation` = `"<title> (<identifier>)"`.

## Attribution

Corpus © legalize-dev (MIT). Legislative data © respective national authorities (see each law's
`source`). This connector does not redistribute the corpus; it reads it on demand. Courtesy notice to
legalize-dev sent before publication (community-contribution path invited by their hub).
