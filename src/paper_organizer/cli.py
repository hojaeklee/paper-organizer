"""Typer CLI entry point for paper-organizer."""

from __future__ import annotations

from typing import Optional

import typer

app = typer.Typer(help="AI-powered research paper classification for Obsidian.")


@app.command()
def run(
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without calling LLM or writing files."),
    reprocess: Optional[str] = typer.Option(None, "--reprocess", help="Force reclassify a specific paper."),
    cost_estimate: bool = typer.Option(False, "--cost-estimate", help="Estimate API cost before processing."),
) -> None:
    """Process all new (unprocessed) papers."""
    typer.echo("[run] Not yet implemented.")


@app.command()
def status() -> None:
    """Health check: paths, processed counts, model access."""
    typer.echo("[status] Not yet implemented.")
