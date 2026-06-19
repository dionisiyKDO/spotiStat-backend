"""Admin CLI: ``python -m spotistat.cli import <username>`` etc."""

from __future__ import annotations

import typer

from spotistat.config import get_settings
from spotistat.db.session import SessionLocal, init_db
from spotistat.services.ingest import import_archive

cli = typer.Typer(help="SpotiStat admin commands.", no_args_is_help=True)


@cli.command("import")
def import_cmd(
    username: str = typer.Argument(..., help="Key identifying whose history this is."),
    archive_dir: str | None = typer.Option(
        None, help="Folder of Streaming_History_Audio_*.json (default: <data_dir>/<username>)."
    ),
) -> None:
    """Import a user's streaming-history archive into the database."""
    settings = get_settings()
    init_db()
    target = archive_dir or f"{settings.data_dir}/{username}"
    with SessionLocal() as db:
        count = import_archive(db, target, username)
    typer.echo(f"Imported {count} listens for {username!r} from {target}")


@cli.command("recompute")
def recompute_cmd(username: str) -> None:
    """Recompute precomputed dashboard stats for a user. (Implemented next step.)"""
    typer.echo("Stats calculation is not wired up yet — coming in the next step.")


if __name__ == "__main__":
    cli()
