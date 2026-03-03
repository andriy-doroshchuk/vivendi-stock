"""Centralized configuration for Vivendi Stock Tracker."""
from __future__ import annotations

import os
import warnings
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # Load .env file before reading any os.getenv() calls below


def _env_bool(name: str, default: bool) -> bool:
    """Parse a boolean environment variable using tolerant truthy/falsey values."""
    value = os.getenv(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {'1', 'true', 'yes', 'y', 'on'}:
        return True
    if normalized in {'0', 'false', 'no', 'n', 'off', ''}:
        return False
    return default


@dataclass
class Config:
    """Application configuration settings."""

    ALPHAVANTAGE_API_KEY: str = field(
        default_factory=lambda: os.getenv('ALPHAVANTAGE_API_KEY', ''),
        repr=False  # Prevent API key from appearing in repr/logs
    )
    ALPHAVANTAGE_CACHE: bool = _env_bool('ALPHAVANTAGE_CACHE', True)
    API_RATE_LIMIT_SECONDS: float = 3.0
    API_TIMEOUT_SECONDS: int = 30
    API_MAX_WORKERS: int = int(os.getenv('API_MAX_WORKERS', '6'))

    APP_ROOT: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)
    DATA_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / 'data')
    LOG_DIR: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / 'logs')
    WORKDATA_START_DATE: str = '2025-12-01'
    CACHE_FILE: str = 'cache.json'

    DASH_HOST: str = os.getenv('DASH_HOST', '0.0.0.0')
    DASH_PORT: int = int(os.getenv('DASH_PORT', '8051'))
    DASH_DEBUG: bool = _env_bool('DASH_DEBUG', False)

    CURRENCY_API_URLS: list[str] = field(default_factory=lambda: [
        'https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{date}/v1/currencies/{base}.json',
        'https://{date}.currency-api.pages.dev/v1/currencies/{base}.json'
    ])

    CURRENCIES: tuple[str, ...] = ('EUR.AUD', 'GBP.AUD')
    STOCK: dict[str, dict] = field(default_factory=lambda: {
        'VIV.PA': {
            'stock': 1565,
            'currency': 'EUR',
            'multiplier': 1,
            'name': 'Vivendi SE'
        },
        'HAVAS.AS': {
            'stock': 91,
            'currency': 'EUR',
            'multiplier': 1,
            'name': 'Havas N.V'
        },
        'CAN.L': {
            'stock': 891,
            'currency': 'GBP',
            'multiplier': 0.01,
            'name': 'Canal+ SA'
        },
        'ALHG.PA': {
            'stock': 922,
            'currency': 'EUR',
            'multiplier': 1,
            'name': 'Louis Hachette Group S.A.'
        }
    })

    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_MAX_BYTES: int = 10485760
    LOG_BACKUP_COUNT: int = 5

    def __post_init__(self) -> None:
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)
        # Only warn when neither the env var nor the api.key fallback file is present.
        api_key_file = self.APP_ROOT / 'api.key'
        if not self.ALPHAVANTAGE_API_KEY and not api_key_file.is_file():
            warnings.warn(
                'ALPHAVANTAGE_API_KEY is not set and no api.key file was found. '
                'API downloads will fail. '
                'Set it via environment variable or place the key in api.key.',
                RuntimeWarning,
                stacklevel=2
            )


config = Config()
