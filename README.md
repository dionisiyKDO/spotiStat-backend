# SpotiStat Backend

Flask server for processing Spotify streaming history and handling Spotify API integration.

## Features

- Spotify OAuth authentication
- Extended streaming history parsing
- Spotify API data integration
- REST API endpoints for music statistics

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
```

4. Run the server:
```bash
flask run --debug
```

## Requirements

- Python 3.8+
- Spotify account
- Extended streaming history export
