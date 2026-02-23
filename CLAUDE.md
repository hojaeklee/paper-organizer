# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Run

```bash
uv sync                          # Install/update dependencies
uv run paper-organizer run       # Process new papers
uv run paper-organizer status    # Health check
uv run paper-organizer --help    # CLI usage
```

```bash
uv run pytest tests/ -v           # Run tests
```

## Architecture

src-layout Python package using Typer for CLI, installed via hatchling.

**Data flow:** `cli.py` orchestrates the pipeline:

```
config.yaml → config.load_config() → Config
                                        ↓
PDF files → extract.extract_text() → raw text → classify.classify() → Classification
                                                                           ↓
                                    state.mark_processed() ← notes.write_note() ← notes.generate_note()
```

**Key types:**
- `Config` / `ModelConfig` / `TaxonomyConfig` — frozen dataclasses in `config.py`; `folders` is a variable-depth `dict` (nested mappings with null leaves), not a flat list
- `Classification` — mutable dataclass in `classify.py` with `title`, `authors`, `folder`, `tags`, `one_line_summary`

**Design constraints (from SPEC.md):**
- Flat note storage — all Obsidian notes in one directory, organized only via YAML frontmatter
- Categories use slash notation (`deep_learning/computer_vision`), derived from the nested `folders` dict
- Dedup by SHA-256 of first 64KB, not filename
- Create-only: never overwrite existing notes unless `--reprocess`
- Skip PDFs modified within last 60s (Google Drive sync safety)
- Skip scanned PDFs (<100 chars extracted)

## Config

`config.yaml` at project root. Taxonomy folders are nested YAML mappings (not lists):

```yaml
folders:
  deep_learning:
    computer_vision:
      classification:
      segmentation:
```

Leaf values are `null`. The hierarchy provides LLM context but doesn't affect file paths.

## Git Workflow

Make atomic commits after each logical change using conventional commit style, then push.

Format: `<type>(<scope>): <description>`

Types: `feat`, `fix`, `refactor`, `docs`, `chore`, `test`, `build`

Scope is the module name when applicable (e.g., `config`, `cli`, `classify`).
