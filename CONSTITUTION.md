# Constitution of mt-eli-mcp

Version: 0.1.0
Date: 2026-06-29
Licence: Apache-2.0

`mt-eli-mcp` is an MCP server for the Maltese legislation portal (`legislation.mt`). It fetches
document metadata and full text with verifiable citations. Case law is not in this MVP.

The 4 principles below are inherited from the `eu-legal-mcp` line Constitution (Article IV).

---

## Art. 1. Public data only

legislation.mt is the official, public source of consolidated Maltese law (open data, keyless).
The server is read-only and sends nothing beyond the requested ELI coordinate.

## Art. 2. Mandatory audit log

Every tool call MUST append one JSON line to `~/.matematic/audit/mt-eli-mcp.jsonl`
(ts / tool / input_hash SHA-256 / output_count_or_size / duration_ms / status). Inability to write =
the tool returns an error, it does not silently skip.

## Art. 3. Vendor neutrality

No tool hardcodes an LLM provider, assumes a model, or adds commercial telemetry. The server talks
only to `legislation.mt` and the local filesystem. Authentication: none; own backoff + cache.

## Art. 4. ELI citations and a human-readable citation are mandatory

Every response MUST carry three fields:
- `eli_uri`: the canonical legislation.mt ELI URL, built from the coordinate and confirmed against
  the page's `legislationIdentifier` (e.g. `https://legislation.mt/eli/cap/586/eng`). NEVER
  invented. Malta is ELI-native (schema.org/ELI JSON-LD).
- `human_readable_citation`: the Maltese convention (e.g. "Data Protection Act (Cap. 586)").
- `source_url`: the same legislation.mt page.

---

## Open points

1. **Text only as PDF** - Malta publishes the consolidated text as PDF; `mt_get_text` downloads
   the official PDF and extracts text with `pypdf`. Layout artefacts are possible; the PDF is
   authoritative. Flagged via `text_note`.
2. **No free-text search** - documents are addressed by ELI coordinate; the on-site search is not
   exposed here.
3. **Case law** - Maltese court decisions are a later feature.

## Ewolucja konstytucji

Changes to art. 1-4 follow SEMVER + an entry in `CHANGELOG.md` + a `pyproject.toml` bump.

First version: 2026-06-29. Author: Wieslaw Mazur / MateMatic.
