from __future__ import annotations

import os
import json
import requests
import pandas
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from ..utils.config import config
from ..utils.logger import setup_logger
from .models import ExchangeRate
from ..utils.rate_limiter import RateLimiter


APP_ROOT = str(config.APP_ROOT)
DATA_STORAGE = str(config.DATA_DIR)
logger = setup_logger(__name__)
rate_limiter = RateLimiter(min_interval=config.API_RATE_LIMIT_SECONDS)


def _redact_url(url: str) -> str:
    """Return URL with sensitive query parameters redacted."""
    try:
        parsed = urlsplit(url)
        redacted_params = []
        for key, value in parse_qsl(parsed.query, keep_blank_values=True):
            if key.lower() in {'apikey', 'api_key', 'token', 'access_token'}:
                redacted_params.append((key, '***REDACTED***'))
            else:
                redacted_params.append((key, value))
        redacted_query = urlencode(redacted_params)
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, redacted_query, parsed.fragment))
    except Exception:
        return '[unparseable-url]'


def get_api_key() -> str | None:
    api_key = os.getenv('ALPHAVANTAGE_API_KEY')
    if api_key:
        return api_key
    try:
        with open(os.path.join(APP_ROOT, 'api.key'), encoding='utf8') as f:
            api_key = f.readline()
        return api_key.strip()
    except OSError as e:
        logger.warning('Unable to read api.key: %s', e)
    return None


def load_json_data(file_name: str) -> dict:
    data_file = os.path.join(DATA_STORAGE, file_name)
    try:
        if os.path.isfile(data_file):
            with open(data_file, encoding='utf8') as f:
                return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.error('Failed to load JSON data from %s: %s', data_file, e)
    return {}


def load_cached_data(file_name: str) -> pandas.DataFrame:
    data_file = os.path.join(DATA_STORAGE, file_name)
    try:
        if os.path.isfile(data_file):
            with open(data_file, encoding='utf8') as f:
                data_frame = pandas.read_json(f)
                data_frame.index = pandas.to_datetime(data_frame.index).normalize()
                return data_frame
    except (OSError, ValueError) as e:
        logger.error('Failed to load cached data from %s: %s', data_file, e)
    return pandas.DataFrame()


def save_json_data(data: dict, file_name: str) -> None:
    data_file = os.path.join(DATA_STORAGE, file_name)
    try:
        if not os.path.isdir(os.path.dirname(data_file)):
            os.makedirs(os.path.dirname(data_file), exist_ok=True)
        with open(data_file, mode='wt', encoding='utf8') as f:
            json.dump(data, f, sort_keys=True, indent=4, separators=(',', ' : '))
    except OSError as e:
        logger.error('Failed to save JSON data to %s: %s', data_file, e)


def save_cached_data(data: pandas.DataFrame, file_name: str) -> None:
    try:
        jsons = data.to_json(date_format='iso')
        save_json_data(json.loads(jsons), file_name)
    except (TypeError, ValueError) as e:
        logger.error('Failed to serialize cached dataframe to %s: %s', file_name, e)


def __execute_api_request(url: str) -> dict:
    rate_limiter.wait()
    logger.info('Requesting URL: %s', _redact_url(url))
    response = requests.get(url, timeout=config.API_TIMEOUT_SECONDS)
    response.raise_for_status()
    try:
        return response.json()
    except ValueError as e:
        logger.error('Invalid JSON response from %s: %s', _redact_url(url), e)
        return {}


def __download_query(api_key: str | None, function: str, query_id: str, use_cache: bool = True) -> dict:
    if not api_key:
        logger.error('Missing AlphaVantage API key, cannot download %s', query_id)
        return {}
    url = f'https://www.alphavantage.co/query?function={function}&outputsize=compact&datatype=json&apikey={api_key}'

    data = load_json_data(f'{query_id}.json') if (config.ALPHAVANTAGE_CACHE and use_cache) else {}
    cache_hit = bool(data)

    # Discard cached entries that are Alpha Vantage error/rate-limit responses,
    # identified by the presence of 'Information' or 'Note' top-level keys.
    if data and ('Information' in data or 'Note' in data):
        logger.warning('Cached data for %s contains an API error response — discarding and re-fetching', query_id)
        data = {}
        cache_hit = False

    if data:
        logger.info('Using cached data for %s', query_id)
    else:
        try:
            data = __execute_api_request(url)
        except requests.RequestException as e:
            logger.error('Request failed for %s: %s', query_id, e)
            return {}
        # Only persist valid time series responses — never cache error payloads.
        if 'Information' in data or 'Note' in data:
            logger.warning('API returned an error/rate-limit response for %s — not caching', query_id)
            return {}

    if data and not cache_hit:
        save_json_data(data, f'{query_id}.json')
    return data


def __download_stock_symbol(api_key: str | None, symbol: str, use_cache: bool = True) -> dict:
    return __download_query(api_key, f'TIME_SERIES_DAILY&symbol={symbol}', symbol, use_cache=use_cache)


def __download_exchange_pair(api_key: str | None, exchange_pair: str, use_cache: bool = True) -> dict:
    from_symbol, to_symbol = exchange_pair.split('.')
    return __download_query(
        api_key,
        f'FX_DAILY&from_symbol={from_symbol}&to_symbol={to_symbol}',
        exchange_pair,
        use_cache=use_cache
    )


def download_stock_data(
    stock_symbols: Iterable[str],
    currency_pairs: Iterable[str],
    use_cache: bool = True
) -> pandas.DataFrame:
    def get_daily_close_price(series: str, data: dict) -> dict:
        def get_day_close_price(day_data: dict) -> float:
            for key in day_data:
                if 'close' in key.lower():
                    return float(day_data[key])
            return 0.0

        try:
            time_series = data[series]
            return {day: get_day_close_price(time_series[day]) for day in time_series}
        except (KeyError, TypeError, ValueError):
            return {}

    api_key = get_api_key()
    if not api_key:
        logger.error('Missing AlphaVantage API key — skipping download. Set ALPHAVANTAGE_API_KEY or provide api.key.')
        return pandas.DataFrame()

    symbols = list(stock_symbols)
    pairs = list(currency_pairs)

    def fetch_symbol(sym: str) -> tuple[str, dict]:
        return sym, get_daily_close_price(
            'Time Series (Daily)',
            __download_stock_symbol(api_key, sym, use_cache=use_cache)
        )

    def fetch_pair(pair: str) -> tuple[str, dict]:
        return pair, get_daily_close_price(
            'Time Series FX (Daily)',
            __download_exchange_pair(api_key, pair, use_cache=use_cache)
        )

    stock_data: dict[str, dict] = {}
    max_workers = max(1, len(symbols) + len(pairs))
    with ThreadPoolExecutor(max_workers=min(max_workers, config.API_MAX_WORKERS)) as executor:
        futures = (
            {executor.submit(fetch_symbol, s): s for s in symbols}
            | {executor.submit(fetch_pair, p): p for p in pairs}
        )
        for future in as_completed(futures):
            query_id = futures[future]
            try:
                key, data = future.result()
                stock_data[key] = data
            except Exception as e:
                logger.error('Download task failed for %s: %s', query_id, e)
                stock_data[query_id] = {}

    valid_series = [set(series.keys()) for series in stock_data.values() if series]
    source = 'cache' if use_cache else 'API'
    if not valid_series:
        logger.warning('No stock or exchange data returned from %s', source)
        return pandas.DataFrame()

    dates = set.intersection(*valid_series)
    if not dates:
        logger.warning('No overlapping dates found across symbols returned from %s', source)
        return pandas.DataFrame()

    stock_data = {
        symbol: {date: stock_data[symbol][date] for date in dates if date in stock_data[symbol]}
        for symbol in stock_data
    }
    data_frame = pandas.DataFrame().from_dict(stock_data, orient='columns')
    data_frame.index = pandas.to_datetime(data_frame.index).normalize()
    return data_frame


def download_exchange_rate(currency: str, date: pandas.Timestamp | None = None) -> float:
    try:
        base, target = currency.lower().split('.')
    except ValueError:
        logger.error('Invalid currency format: %s', currency)
        return 0.0

    if date is None:
        date_str = 'latest'
    elif isinstance(date, pandas.Timestamp):
        date_str = date.strftime('%Y-%m-%d')
    else:
        date_str = str(date)

    urls = [url.format(date=date_str, base=base) for url in config.CURRENCY_API_URLS]
    for url in urls:
        try:
            parsed_response = __execute_api_request(url)
            rate = float(parsed_response[base][target])
            validated = ExchangeRate(date=date_str, currency_pair=currency, rate=rate)
            return validated.rate
        except (requests.RequestException, KeyError, TypeError, ValueError) as e:
            logger.warning('Failed fetching exchange rate from %s: %s', url, e)
    return 0.0
