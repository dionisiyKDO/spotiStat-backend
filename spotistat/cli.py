"""Admin CLI: ``python -m spotistat.cli import <username>`` etc."""

from __future__ import annotations

import typer

from spotistat.config import get_settings
from spotistat.db.session import SessionLocal, init_db
from spotistat.services import stats as stats_service
from spotistat.services.ingest import import_archive

cli = typer.Typer(help="SpotiStat admin commands.", no_args_is_help=True)


@cli.command("import")
def import_cmd(
    username: str = typer.Argument(..., help="Key identifying whose history this is."),
    archive_dir: str | None = typer.Option(
        None, help="Folder of Streaming_History_Audio_*.json (default: <data_dir>/<username>)."
    ),
) -> None:
    """Import a user's archive, then recompute their dashboard stats."""
    init_db()
    target = archive_dir or f"{get_settings().data_dir}/{username}"
    with SessionLocal() as db:
        count = import_archive(db, target, username)
        stats_service.recompute(db, username)
    typer.echo(f"Imported {count} listens for {username!r} from {target} and recomputed stats.")


@cli.command("recompute")
def recompute_cmd(
    username: str = typer.Argument(..., help="User whose stats to recompute."),
) -> None:
    """Recompute precomputed dashboard stats for a user."""
    init_db()
    with SessionLocal() as db:
        computed_at = stats_service.recompute(db, username)
    typer.echo(f"Recomputed stats for {username!r} (computed_at={computed_at}).")


if __name__ == "__main__":
    cli()
