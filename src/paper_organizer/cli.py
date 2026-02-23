"""Typer CLI entry point for paper-organizer."""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer

from paper_organizer.classify import classify, estimate_cost
from paper_organizer.config import flatten_folders, load_config
from paper_organizer.extract import extract_text
from paper_organizer.notes import generate_note, sanitize_filename, write_note
from paper_organizer.state import content_hash, is_processed, mark_processed

app = typer.Typer(help="AI-powered research paper classification for Obsidian.")

STABILITY_SECONDS = 60
MIN_TEXT_CHARS = 100


@app.command()
def run(
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without calling LLM or writing files."),
    reprocess: Optional[str] = typer.Option(None, "--reprocess", help="Force reclassify a specific paper."),
    cost_estimate: bool = typer.Option(False, "--cost-estimate", help="Estimate API cost before processing."),
) -> None:
    """Process all new (unprocessed) papers."""
    config = load_config()
    state_path = config.obsidian_vault / ".processed_papers.json"

    pdfs = sorted(config.paperpile_dir.glob("*.pdf"))
    if not pdfs:
        typer.echo("No PDFs found in paperpile_dir.")
        return

    if reprocess:
        pdfs = [p for p in pdfs if p.name == reprocess]
        if not pdfs:
            typer.echo(f"PDF not found: {reprocess}")
            raise typer.Exit(1)

    # Stability check: skip files modified within last 60s
    now = time.time()
    stable_pdfs = []
    for pdf in pdfs:
        if now - pdf.stat().st_mtime < STABILITY_SECONDS:
            typer.echo(f"  Skipping (recently modified): {pdf.name}")
            continue
        stable_pdfs.append(pdf)
    pdfs = stable_pdfs

    # Dedup: skip already-processed unless --reprocess
    candidates: list[tuple[Path, str]] = []
    for pdf in pdfs:
        h = content_hash(pdf)
        if not reprocess and is_processed(h, state_path):
            continue
        candidates.append((pdf, h))

    if not candidates:
        typer.echo("All papers already processed.")
        return

    typer.echo(f"Found {len(candidates)} paper(s) to process.")

    # --dry-run: list files and exit
    if dry_run:
        for pdf, _ in candidates:
            typer.echo(f"  {pdf.name}")
        return

    # --cost-estimate: extract all texts, estimate, exit
    if cost_estimate:
        texts = []
        for pdf, _ in candidates:
            try:
                texts.append(extract_text(pdf))
            except Exception as exc:
                typer.echo(f"  Error extracting {pdf.name}: {exc}")
        cost = estimate_cost(texts, config)
        typer.echo(f"Estimated cost: ${cost:.4f} for {len(texts)} paper(s)")
        return

    known_categories = set(flatten_folders(config.taxonomy.folders))
    date_added = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for pdf, h in candidates:
        try:
            typer.echo(f"Processing: {pdf.name}")

            text = extract_text(pdf)
            if len(text) < MIN_TEXT_CHARS:
                typer.echo(f"  Skipping (scanned/low text): {pdf.name}")
                continue

            result = classify(text, config)
            note_content = generate_note(result, pdf.name, date_added)
            note_filename = sanitize_filename(result.title) + ".md"
            note_dest = config.obsidian_vault / note_filename

            if reprocess and note_dest.exists():
                note_dest.unlink()

            write_note(note_content, note_dest)
            mark_processed(h, pdf.name, state_path, note_file=note_filename)
            typer.echo(f"  Created: {note_filename}")

            if result.folder not in known_categories:
                typer.echo(f"  Warning: new category '{result.folder}' not in taxonomy")

        except Exception as exc:
            typer.echo(f"  Error processing {pdf.name}: {exc}")


@app.command()
def status() -> None:
    """Health check: paths, processed counts, model access."""
    config = load_config()

    # Check paths
    issues = []
    if config.paperpile_dir.exists():
        typer.echo(f"Paperpile dir: {config.paperpile_dir} [OK]")
    else:
        typer.echo(f"Paperpile dir: {config.paperpile_dir} [MISSING]")
        issues.append(f"Create directory or fix paperpile_dir in config.yaml")

    if config.obsidian_vault.exists():
        typer.echo(f"Obsidian vault: {config.obsidian_vault} [OK]")
    else:
        typer.echo(f"Obsidian vault: {config.obsidian_vault} [MISSING]")
        issues.append(f"Create directory or fix obsidian_vault in config.yaml")

    # Count PDFs and processed
    pdf_count = len(list(config.paperpile_dir.glob("*.pdf"))) if config.paperpile_dir.exists() else 0
    state_path = config.obsidian_vault / ".processed_papers.json"
    processed_count = 0
    if state_path.exists():
        import json
        processed_count = len(json.loads(state_path.read_text()))

    typer.echo(f"PDFs found: {pdf_count}")
    typer.echo(f"Already processed: {processed_count}")
    typer.echo(f"Unprocessed: {pdf_count - processed_count}")

    # Check API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        typer.echo("ANTHROPIC_API_KEY: set [OK]")
    else:
        typer.echo("ANTHROPIC_API_KEY: not set [MISSING]")
        issues.append("Set ANTHROPIC_API_KEY environment variable")

    # Quick model ping
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic()
            client.messages.create(
                model=config.model.name,
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}],
            )
            typer.echo(f"Model access ({config.model.name}): [OK]")
        except Exception as exc:
            typer.echo(f"Model access ({config.model.name}): [FAILED] {exc}")
            issues.append(f"Check model name and API key")

    if issues:
        typer.echo("\nIssues:")
        for issue in issues:
            typer.echo(f"  - {issue}")
    else:
        typer.echo("\nAll checks passed.")
