"""
NIRVANA Data Pipeline — Run Entry Point

Usage:
  python -m data_pipeline.run                # Full pipeline
  python -m data_pipeline.run --synthetic    # Synthetic data only
  python -m data_pipeline.run --dry-run      # Validate without loading
  python -m data_pipeline.run --source govdata  # Real gov data only
"""
import sys
import os
import logging
import argparse
from datetime import datetime

# Ensure project root is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"data_pipeline/logs/run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
    ],
)

console = Console()


def main():
    parser = argparse.ArgumentParser(description="NIRVANA Data Pipeline")
    parser.add_argument("--synthetic", action="store_true", help="Load synthetic data only (for development)")
    parser.add_argument("--govdata", action="store_true", help="Load government open data only")
    parser.add_argument("--dry-run", action="store_true", help="Validate without loading to DB")
    parser.add_argument("--n-synthetic", type=int, default=500, help="Number of synthetic records")
    args = parser.parse_args()

    console.print(Panel.fit(
        "[bold cyan]NIRVANA Data Pipeline[/bold cyan]\n"
        "National Infrastructure Reality & Verification Network using AI\n"
        "[yellow]⚠️  Synthetic data is clearly marked as SYNTHETIC in the database[/yellow]",
        border_style="blue",
    ))

    results = []

    # Initialize DB
    if not args.dry_run:
        console.print("\n[bold]Initializing database...[/bold]")
        from backend.database.init_db import main as init_db
        init_db()
        from backend.database.session import SyncSessionLocal
        db = SyncSessionLocal()
    else:
        db = None
        console.print("[yellow]DRY RUN — no database changes[/yellow]\n")

    try:
        # Real government data (GODL)
        if not args.synthetic:
            console.print("\n[bold green]→ Fetching GODL-licensed government data...[/bold green]")
            from data_pipeline.sources.data_gov_in import DataGovInSource

            for dataset_key in ["17th_lok_sabha_works"]:
                try:
                    source = DataGovInSource(dataset_key)
                    if args.dry_run:
                        raw = source.fetch()
                        validated = source.validate(raw)
                        valid_count = sum(1 for r in validated if r.is_valid)
                        console.print(f"  [green]✓[/green] {source.source_name}: {len(raw)} fetched, {valid_count} valid (dry run)")
                    else:
                        result = source.run(db)
                        results.append(result)
                except Exception as e:
                    console.print(f"  [red]✗[/red] {dataset_key} failed: {e}")
                    logging.error(f"Source {dataset_key} failed: {e}")

        # Synthetic data (always loaded in dev unless --govdata)
        if not args.govdata:
            console.print("\n[bold yellow]→ Generating SYNTHETIC data (development only)...[/bold yellow]")
            console.print("  [yellow]⚠️  These records are NOT government data[/yellow]")

            from data_pipeline.sources.synthetic import SyntheticDataSource
            synth_source = SyntheticDataSource(n_projects=args.n_synthetic, include_anomalies=True)

            if args.dry_run:
                raw = synth_source.fetch()
                console.print(f"  [green]✓[/green] Would generate {len(raw)} synthetic records (dry run)")
            else:
                result = synth_source.run(db)
                results.append(result)

    finally:
        if db:
            db.close()

    # Print summary
    if results:
        console.print("\n")
        table = Table(title="Pipeline Run Summary", border_style="blue")
        table.add_column("Source", style="cyan")
        table.add_column("Fetched", justify="right")
        table.add_column("Valid", justify="right")
        table.add_column("Loaded", justify="right")
        table.add_column("Success Rate", justify="right")
        table.add_column("Status", justify="center")
        table.add_column("Duration")

        for r in results:
            duration = (r.end_time - r.start_time).total_seconds()
            status = "[green]✓[/green]" if not r.errors else "[yellow]⚠[/yellow]"
            table.add_row(
                r.source_name[:40],
                str(r.total_fetched),
                str(r.total_valid),
                str(r.total_loaded),
                f"{r.success_rate:.1%}",
                status,
                f"{duration:.1f}s",
            )

        console.print(table)

        for r in results:
            if r.errors:
                console.print(f"\n[yellow]Errors for {r.source_name}:[/yellow]")
                for err in r.errors[:5]:
                    console.print(f"  - {err}")

    console.print("\n[bold green]Pipeline completed.[/bold green]")
    console.print("Next step: [cyan]python -m ml.train.cost_anomaly[/cyan]")


if __name__ == "__main__":
    main()
