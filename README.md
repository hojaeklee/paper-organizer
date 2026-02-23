# paper-organizer

AI-powered tool that classifies research papers from a Paperpile/Google Drive folder and generates Obsidian-compatible markdown notes with structured metadata.

## What it does

paper-organizer watches your Paperpile PDF folder, extracts text from new papers, sends it to Claude for classification, and writes Obsidian notes with YAML frontmatter (category, tags, summary). All notes are stored flat in a single folder — organization lives entirely in metadata, queryable via Obsidian Bases or Dataview.

```
Browser Extension → Paperpile → Google Drive folder (synced locally)
                                        ↓
                              paper-organizer
                              (extract text → LLM → assign category/tags)
                                        ↓
                              Obsidian vault/papers/ (flat .md notes)
```

## Setup

```bash
# Install
uv sync

# Configure
cp config.example.yaml config.yaml
# Edit config.yaml: set paperpile_dir, obsidian_vault, and taxonomy

# Set API key
export ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

```bash
# Process all new papers
uv run paper-organizer run

# Dry run — see what would be processed without calling LLM
uv run paper-organizer run --dry-run

# Reprocess a specific paper
uv run paper-organizer run --reprocess "some paper.pdf"

# Health check
uv run paper-organizer status
```

## Configuration

`config.yaml` controls paths, model settings, and taxonomy. See `config.example.yaml` for the full template.

Key sections:

- **paperpile_dir / obsidian_vault** — local paths to your PDF source and note destination
- **model** — LLM provider and model name (defaults to Claude Haiku)
- **taxonomy.folders** — nested category hierarchy (slash notation: `deep_learning/computer_vision`). Guides the LLM but does not affect file paths.
- **taxonomy.tags** — flat list of tags the LLM can assign (multiple per paper)
- **notification_email** — notified when the LLM creates a category outside your taxonomy

The taxonomy is guidance, not a strict enum. If a paper doesn't fit existing categories, the LLM suggests a new one.

## How it works

1. **Extract** — pulls text from the first ~5 pages of each PDF via `pypdf`
2. **Dedup** — SHA-256 hash of first 64KB prevents reprocessing renamed files
3. **Classify** — sends extracted text + taxonomy to Claude, which returns structured JSON (title, authors, folder, tags, summary)
4. **Write** — generates an Obsidian `.md` note with YAML frontmatter and logs the hash to `.processed_papers.json`

Safety: skips files modified within 60s (Google Drive sync), skips scanned PDFs (<100 chars extracted), never overwrites existing notes.

---

<a href="https://buymeacoffee.com/hojaeklee" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;"></a>
