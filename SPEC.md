# paper-organizer

AI-powered tool that automatically classifies and tags research papers from a Paperpile/Google Drive folder and generates Obsidian-compatible markdown notes.

## Context

I use Paperpile primarily as a browser extension to save papers. Paperpile syncs PDFs to a Google Drive folder. I symlink that Google Drive folder into my Obsidian vault so I can read and annotate PDFs there. I rarely use the Paperpile webapp for organization, so I want to build my own organization layer on top of the PDFs using an LLM.

All organization lives in YAML frontmatter — not the filesystem. Notes are stored flat in a single folder and organized via Obsidian Bases/Dataview queries using the `category` and `tags` fields.

## Workflow

```
Browser Extension → Paperpile → Google Drive/Paperpile folder (synced locally)
                                        ↓
                              paper-organizer (this tool)
                              (extract text → LLM → assign category/tags)
                                        ↓
                              Obsidian vault/papers/ (flat folder of .md notes)
```
```

## Tech Stack

- Python 3.11+
- `typer` for CLI
- `pypdf` for PDF text extraction
- `anthropic` SDK for classification (Claude Haiku)
- `pyyaml` for config
- YAML frontmatter in generated Obsidian notes
- macOS `launchd` with `WatchPaths` for automatic triggering

## Project Structure

```
paper-organizer/
├── pyproject.toml
├── config.yaml              # User-editable config (paths, taxonomy, model)
├── README.md
├── src/
│   └── paper_organizer/
│       ├── __init__.py
│       ├── cli.py            # Typer CLI entry point
│       ├── config.py         # Load/validate config.yaml
│       ├── extract.py        # PDF text extraction
│       ├── classify.py       # LLM classification
│       ├── notes.py          # Obsidian markdown note generation
│       └── state.py          # Processed file tracking (dedup, log)
└── launchd/
    └── com.paper-organizer.plist  # macOS WatchPaths template
```

## config.yaml

```yaml
# paper-organizer config
# Edit this file to update paths, taxonomy, or model settings.

paperpile_dir: ~/Google Drive/Paperpile
obsidian_vault: ~/vault/papers

model:
  provider: anthropic
  name: claude-haiku-4-5-20251001
  max_input_chars: 8000

# Customize these as your research interests evolve.
# These are passed to the LLM as guidance — not strict enums.
# The hierarchy is for LLM context only; notes are stored flat.
# Category values use slash notation: "deep_learning/computer_vision"
taxonomy:
  folders:
    single_cell_genomics:
      spatial_transcriptomics:
    deep_learning:
      computer_vision:
        classification:
        segmentation:
      natural_language_processing:
      large_language_models:
    neuroscience:
      grid_cells:

  tags:
    - source/article
    - source/blog
    - source/youtube
    - type/dataset
    - type/benchmark
    - type/methodology
    - type/theoretical
    - type/review
    - type/tutorial
    - status/need_figuring_out 
    - status/completed
    - status/reading
    - relevance/high
    - relevance/low

# Email to notify when a new category is created by the LLM.
notification_email: hojae.k.lee@gmail.com
```

## Note on Taxonomy
- The category hierarchy guides the LLM but does NOT map to directories.
  All notes live in a single flat folder.
- If the paper does not fit into any of the current categories, the LLM
  should suggest a new one. The tool creates the note with the new category
  and notifies the user via email so they can update config.yaml if desired.

## CLI Commands

### `paper-organizer run`

Process all new (unprocessed) papers.

- Extract text from first ~5 pages of each PDF via `pypdf`
- Skip files modified within last 60 seconds (Google Drive sync safety)
- Deduplicate by content hash (SHA256 of first 64KB), not filename
- Send extracted text to LLM for classification → returns JSON: `{ folder, tags, one_line_summary }`
- Generate an Obsidian `.md` note with YAML frontmatter in `<obsidian_vault>/<folder>/`
- Log the file hash to `.processed_papers.json`
- If the LLM assigns a category not in config.yaml, log a warning and optionally email the user

Flags:
- `--dry-run`: Show what would be processed without calling LLM or writing files
- `--reprocess <filename>`: Force reclassify a specific paper (skip dedup check)
- `--cost-estimate`: Count tokens and estimate cost before processing

### `paper-organizer status`

Health check that reports:
- Whether paperpile_dir and obsidian_vault paths exist
- Number of PDFs found vs. number already processed
- Number of unprocessed papers waiting
- Whether the configured model is accessible (quick test call)
- Any obvious issues with plain-English fix suggestions

## Automation: macOS WatchPaths

Instead of a persistent background process (watchdog) or periodic cron job,
the tool uses macOS `launchd` with `WatchPaths`. The OS natively watches the
Paperpile folder and only launches the script when a file changes. No background
process runs — the OS handles it and it survives reboots.

### launchd plist template

```xml
<!-- Install to: ~/Library/LaunchAgents/com.paper-organizer.plist -->

<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://purl.apple.com/dtds/PropertyList-1.0.dtd">


    Label
    com.paper-organizer
    ProgramArguments
    
        /path/to/python
        -m
        paper_organizer
        run
    
    WatchPaths
    
        /Users/yourname/Google Drive/My Drive/Paperpile
    
    ThrottleInterval
    60


```

- `WatchPaths`: triggers the script when anything changes in the Paperpile dir
- `ThrottleInterval`: 60 seconds — prevents rapid re-fires during Google Drive sync
  (pairs with the 60-second file stability check in the run command)

### Setup commands

```bash
# Install the plist
cp launchd/com.paper-organizer.plist ~/Library/LaunchAgents/

# Load (activate)
launchctl load ~/Library/LaunchAgents/com.paper-organizer.plist

# Unload (deactivate)
launchctl unload ~/Library/LaunchAgents/com.paper-organizer.plist

# Check status
launchctl list | grep paper-organizer
```

### CLI helper (optional)

The CLI could include an `install` command that generates the plist with the
correct Python path and Paperpile directory from config.yaml:

```
paper-organizer install   # generates and loads the launchd plist
paper-organizer uninstall # unloads and removes the plist

## Obsidian Note Format

All notes are stored flat in the obsidian_vault directory. Organization is
entirely via frontmatter metadata, queryable through Obsidian Bases or Dataview.

Generated notes should look like:

```markdown
---
title: "Attention Is All You Need"
authors:
  - "[[Ashish Vaswani]]"
  - "[[Noam Shazeer]]"
doi: extracted doi
rating: leave blank
category: deep_learning/natural_language_processing
tags:
  - source/article
  - type/methodology
  - relevance/high
summary: "Introduces the Transformer architecture based entirely on attention mechanisms, eliminating recurrence and convolutions."
date_added: 2026-02-22
---

# [[Attention Is All You Need.pdf|Attention Is All You Need]]

> [!tldr] Critical Summary
> Write summary here

```

## LLM Classification Prompt

The system prompt should:
- Receive the taxonomy (folders + tags) from config
- Receive the extracted text (truncated to `max_input_chars`)
- Return structured JSON: `{ "title": str, "authors": list[str], "folder": str, "tags": list[str], "one_line_summary": str }`
- Be instructed to pick the single best folder, but can assign multiple tags
- Be instructed to extract title and authors from the paper text itself
- If no existing category fits, suggest a new one following the same slash notation convention

## Important Design Decisions

1. **Flat storage, metadata-driven organization**: All notes live in a single directory. Categories and tags exist only in YAML frontmatter. Organization is done via Obsidian Bases/Dataview queries, not the filesystem. This means reorganizing papers never requires moving files.

2. **Wikilinks are path-independent**: All `[[pdf_filename.pdf]]` links use filename only, never relative/absolute paths. This works because Obsidian's "Shortest path when possible" setting resolves links vault-wide by filename. Ensure this Obsidian setting is enabled.

3. **Create-only, never overwrite**: If an Obsidian note already exists for a paper, skip it. Manual edits to generated notes must be preserved. Only `--reprocess` should regenerate a note (and it should warn before overwriting).

4. **Dedup by content hash, not filename**: Paperpile sometimes renames files. Hash the first 64KB of the PDF to identify duplicates.

5. **Scanned PDF fallback**: If `pypdf` extracts less than 100 characters, log a warning and skip the file. (Future enhancement: send first page as image to a vision model.)

6. **Config-driven taxonomy**: The taxonomy lives in `config.yaml`, not in code. The LLM prompt is assembled at runtime from the config. The hierarchical structure provides context to the LLM but does not affect file storage.

7. **Idempotent runs**: Running the tool multiple times should be safe. The processed log prevents re-processing, and existing notes are never overwritten.

## Testing & CI

- Tests use `pytest`. Mock all Anthropic API calls — never hit real API in tests.
- Test coverage focuses on: extraction, classification parsing, state/dedup,
  note generation. No end-to-end CLI tests.
- GitHub Actions: single job, runs pytest on push. No matrix builds.
- `config.yaml` is gitignored. `config.example.yaml` is committed with
  placeholder paths.
- Anthropic API key is read from ANTHROPIC_API_KEY env var (SDK default),
  never stored in config or code.

## Future Enhancements (not in scope for v1)

- Vision model fallback for scanned PDFs
- CrossRef/DOI lookup for better metadata
- Obsidian Dataview query examples in README
- Apple Shortcuts integration
- Cost tracking across runs