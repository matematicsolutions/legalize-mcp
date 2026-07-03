# legalize-mcp

<!-- mcp-name: io.github.matematicsolutions/legalize-mcp -->

**One MCP server, 32 jurisdictions (21 EU).** A read-only [Model Context Protocol](https://modelcontextprotocol.io)
server over the [legalize-dev](https://github.com/legalize-dev) corpus — national legislation stored
as **law-as-git**: one law per Markdown file, every reform a Git commit, each with an 8-field
ELI-style frontmatter (Legalize Format Spec v0.2). MIT-licensed source corpus; this connector is
Apache-2.0.

Built by [Matematic Solutions](https://matematic.co) as part of the `eu-legal-mcp` line. Unlike the
single-country `*-eli-mcp` connectors, this one serves **many jurisdictions from a single server**,
because the underlying corpus is already normalised to one format.

## Why this exists

Every response carries the **citation contract** the rest of the line uses:

- `source_url` — the **official** government source from the law's own frontmatter
  (e.g. `boe.es`, `riigiteataja.ee`, `legifrance.gouv.fr`). Never invented.
- `github_url` — the verifiable legalize-dev copy actually read.
- `human_readable_citation` — `"<title> (<identifier>)"`.

It is **RODO/GDPR-safe and self-hostable**: nothing leaves the user's machine except read-only GETs
to GitHub.

## Jurisdictions

EU: `at be cz de ee es eu fi fr gr ie it lt lu lv nl pl pt ro se sk`
· Other: `ad ar ch cl co kr li no uk us uy`

Call `legalize_list_countries` for the live list (add `eu_only=true` to filter).

## Tools

| Tool | Keyless? | Purpose |
| --- | --- | --- |
| `legalize_list_countries` | ✅ | List jurisdictions (code, name, EU flag, repo). |
| `legalize_search_laws` | needs `GITHUB_TOKEN` | Keyword search inside a country's laws → `law_id` + snippet. |
| `legalize_get_meta` | ✅ | Frontmatter only (cheap citation check). |
| `legalize_get_law` | ✅ | Full metadata + text by `law_id`; pass `sha=` for a historical version. |
| `legalize_list_reforms` | ✅ | Reform timeline (commits) for a law; SHAs feed `legalize_get_law`. |

`law_id` is the Markdown **filename stem** (e.g. `BOE-A-1978-31229` for the Spanish Constitution, a
numeric id for Estonia). Get it from `legalize_search_laws` or an official citation — there is no
fuzzy title lookup.

## Install

```bash
uvx legalize-mcp           # run directly
# or
pip install legalize-mcp
```

Claude Code (`.mcp.json`):

```json
{
  "mcpServers": {
    "legalize": { "command": "uvx", "args": ["legalize-mcp"] }
  }
}
```

`GITHUB_TOKEN` (or `GH_TOKEN`) is **optional** — required only for `legalize_search_laws`, and it
lifts the GitHub rate limit on `legalize_list_reforms`.

## Configuration

| Env var | Default | Purpose |
| --- | --- | --- |
| `GITHUB_TOKEN` / `GH_TOKEN` | — | Enables code search; lifts rate limits. |
| `LEGALIZE_AUDIT_DIR` | `~/.matematic/audit` | JSONL audit log location (AI Act art. 12). |

## Governance

Every tool call appends one line to `~/.matematic/audit/legalize-mcp.jsonl` (input hash, duration,
status — no payloads). All tools are read-only and idempotent. See `CONSTITUTION.md`.

## Development

```bash
python -m venv .venv && .venv/Scripts/python -m pip install -e ".[dev]"
.venv/Scripts/python -m pytest -q          # offline unit tests
.venv/Scripts/python -m ruff check src tests
```

## Attribution

Legislative data © the respective national authorities (see each law's `source`). Corpus
normalisation by the [legalize-dev](https://github.com/legalize-dev) project under the MIT License.
This connector does not redistribute the corpus; it reads it on demand.
