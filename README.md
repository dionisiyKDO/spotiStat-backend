# SpotiStat Backend

FastAPI backend that turns a Spotify **Extended Streaming History** export into a
personal listening-stats dashboard.

`username` is just a key identifying whose archive a set of listens belongs to —
there's no auth or accounts. You can hold several people's histories side by side.

## How it works

- **Import** a user's archive (`Streaming_History_Audio_*.json`) into SQLite.
- On import, all dashboard stats are **precomputed once** and stored per-stat.
- The API serves one precomputed **dashboard bundle** (for the single-page view) plus
  **live** artist/track drill-downs queried on demand.

## Setup

```bash
uv sync
```

## Usage

Put a user's archive under `data/<username>/` (the `Streaming_History_Audio_*.json`
files from the Spotify export), then:

```bash
# import the archive and compute stats
uv run python -m spotistat.cli import <username>

# recompute stats later without re-importing
uv run python -m spotistat.cli recompute <username>

# run the API — interactive docs at http://127.0.0.1:8000/docs
uv run fastapi dev spotistat/main.py
```

## API

- `GET /stats/{username}/dashboard` — full precomputed bundle (the single-page dashboard)
- `GET /stats/{username}/artists` · `/artists/{name}` · `/artists/{name}/tracks`
- `GET /stats/{username}/tracks` · `/tracks/{id}`
- `GET /health`

## Config

Set via environment variables (prefix `SPOTISTAT_`) or a `.env` file:

| setting | default | purpose |
| --- | --- | --- |
| `SPOTISTAT_DATABASE_URL` | `sqlite:///./data/spotistat.db` | database location |
| `SPOTISTAT_DATA_DIR` | `data` | where `<username>/` archive folders live |
| `SPOTISTAT_TIMEZONE` | `Europe/Kyiv` | local tz for hour/weekday/date stats |

## Layout

```text
spotistat/
  main.py        app + route wiring
  config.py      settings
  constants.py
  db/            models + session
  services/      ingest · stats (precompute) · library (live queries)
  api/           HTTP routes
tests/
data/            archives + SQLite db (gitignored)
```

## Tests

```bash
uv run pytest
```
