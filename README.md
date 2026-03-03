# vivendi-stock

Vivendi Group stock tracker built with Dash.

## Requirements

- Python 3.12+
- A valid Alpha Vantage API key

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

	```bash
	pip install -r requirements.txt
	```

3. Copy environment template and configure values:

	```bash
	cp .env.example .env
	```

4. Set your API key (either in shell env or `.env`):

	```bash
	export ALPHAVANTAGE_API_KEY="your_api_key"
	```

## Run locally

Use the package entrypoint:

```bash
python -m vivendi_stock
```

## Test CLI (data update + terminal output)

Run the CLI entrypoint to update/load data and print a console summary:

```bash
python -m vivendi_stock.cli
```

After installing the package (`pip install -e .`), you can also run:

```bash
vivendi-stock-cli
```

Useful flags:

- `--force-update` to force API refresh immediately

Optional environment overrides:

- `DASH_HOST` (default: `0.0.0.0`)
- `DASH_PORT` (default: `8051`)
- `DASH_DEBUG` (default: `false`)
- `ALPHAVANTAGE_CACHE` (default: `true`; set to `false` to force fresh API fetches)

Boolean env vars accept: `1/0`, `true/false`, `yes/no`, `on/off` (case-insensitive).

## Deployment (WSGI)

WSGI app is exposed as `application` in `wsgi.py`.

Example with Gunicorn:

```bash
gunicorn wsgi:application --bind 0.0.0.0:8051
```

Optional installed script form:

```bash
vivendi-stock-web
```

Useful flags:

- `--host 0.0.0.0`
- `--port 8052`
- `--debug`

Example:

```bash
vivendi-stock-web --host 127.0.0.1 --port 8052
```

If scripts are not found in shell, ensure your environment `bin` directory is in `PATH`.
For pyenv, run `pyenv rehash` after install.

## Project structure

- `vivendi_stock/` — application package
  - `dash_app.py` — Dash app layout and callbacks
  - `vivendi_data.py` — portfolio calculations and cache update flow
  - `web_api.py` — external API integration and caching
  - `models.py` — Pydantic validation models
  - `config.py` — centralized settings
  - `logger.py` — structured logging setup
- `data/` — cached API responses and computed cache file
- `static/` — stylesheets

## Notes

- Cached market data is stored under `data/`.
- Logging output is written to `logs/`.
