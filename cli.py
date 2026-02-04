"""Command-line interface for simple IBISWorld operations."""
from __future__ import annotations

import json
import os
from typing import List

import typer
from dotenv import load_dotenv

from ibisworld_client import IBISWorldClient

load_dotenv()
app = typer.Typer(help="IBISWorld helper CLI")


@app.command()
def list_reports(country: str = "US", language: str = "English", refresh: bool = False):
    """List available industry reports for a country."""
    client = IBISWorldClient()
    data = client.list_reports(country=country, language=language, use_cache=not refresh)
    typer.echo(json.dumps(data, indent=2))


@app.command()
def get_segment(code: str, sections: List[str] = typer.Option(...), country: str = "US", language: str = "English", out: str = "segment.json", refresh: bool = False):
    """Download selected sections of a Segment Benchmarking report."""
    client = IBISWorldClient()
    data = client.get_segment_sections(code=code, sections=sections, country=country, language=language, use_cache=not refresh)
    with open(out, "w") as f:
        json.dump(data, f, indent=2)
    typer.echo(f"Saved to {out}")


@app.command()
def updated_reports(start_date: str, end_date: str, country: str = "US", language: str = "English"):
    client = IBISWorldClient()
    data = client.get_updated_reports(start_date=start_date, end_date=end_date, country=country, language=language)
    typer.echo(json.dumps(data, indent=2))


@app.command()
def export_segments(
    codes_file: str = typer.Option(None, help="Path to file with NAICS codes, one per line"),
    codes: List[str] = typer.Option(None, "--code", help="One or more NAICS codes to export"),
    sections: List[str] = typer.Option(["keystatistics", "currentyearoverview", "keyratios"], help="Report sections to fetch"),
    out: str = "segments.csv",
    refresh: bool = False,
):
    """Export datapoints for multiple NAICS codes into a CSV file."""
    if not codes_file and not codes:
        typer.echo("Provide --codes-file or one or more --code")
        raise typer.Exit(code=2)

    if codes_file:
        with open(codes_file) as f:
            codes_list = [line.strip() for line in f if line.strip()]
    else:
        codes_list = codes

    client = IBISWorldClient()
    from ibisworld_client.bulk import export_segments as _export

    _export(client, codes_list, sections=sections, out=out, use_cache=not refresh)
    typer.echo(f"Saved to {out}")


if __name__ == "__main__":
    app()