"""CLI entrypoint for testing data update and terminal display."""

import argparse
import sys
from datetime import datetime

import requests

from .vivendi_data import STOCK, VivendiStock
from .web_api import get_api_key


def _format_change(change: float) -> str:
    sign = '+' if change > 0 else ''
    return f'{sign}{change:.2f}%'


def _latest_date(series) -> str:
    non_null = series.dropna()
    if non_null.empty:
        return 'n/a'
    return non_null.index[-1].strftime('%Y-%m-%d')


def _test_setup() -> bool:
    """Verify configuration and live API key validity. Returns True if all checks pass."""
    print('Vivendi Stock — Setup Check')
    print('=' * 50)
    passed = True

    # 1. API key presence
    api_key = get_api_key()
    if api_key:
        masked = api_key[:4] + '*' * (len(api_key) - 4)
        print(f'  [OK] API key loaded: {masked}')
    else:
        print('  [FAIL] API key not found. Set ALPHAVANTAGE_API_KEY or provide api.key.')
        passed = False

    # 2. Live API reachability — GLOBAL_QUOTE is a lightweight single-call endpoint
    if api_key:
        test_symbol = next(iter(STOCK))
        url = (
            f'https://www.alphavantage.co/query'
            f'?function=GLOBAL_QUOTE&symbol={test_symbol}&apikey={api_key}'
        )
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            payload = response.json()
            def _redact_message(msg: str) -> str:
                """Strip any API key values embedded in Alpha Vantage error messages."""
                import re
                return re.sub(r'[A-Z0-9]{16}', '***REDACTED***', msg)

            quote = payload.get('Global Quote', {})
            price = quote.get('05. price')
            if price:
                print(f'  [OK] API key is valid. {test_symbol} last price: {float(price):.3f}')
            elif 'Information' in payload:
                msg = _redact_message(payload['Information'])
                # Alpha Vantage returns 'Information' for both invalid keys and rate limits.
                # Rate-limit messages mention 'rate limit' — key is valid but quota exhausted.
                if 'rate limit' in msg.lower():
                    print(f'  [WARN] API key valid but daily rate limit reached: {msg}')
                else:
                    print(f'  [FAIL] API key rejected: {msg}')
                    passed = False
            elif 'Note' in payload:
                print(f'  [WARN] API rate-limit note: {_redact_message(payload["Note"])}')
            else:
                print(f'  [WARN] Unexpected response shape: {list(payload.keys())}')
        except requests.RequestException as e:
            print(f'  [FAIL] Network error reaching Alpha Vantage: {e}')
            passed = False

    # 3. Data directory
    from .config import config
    if config.DATA_DIR.is_dir():
        print(f'  [OK] Data directory: {config.DATA_DIR}')
    else:
        print(f'  [FAIL] Data directory missing: {config.DATA_DIR}')
        passed = False

    # 4. Cache file
    cache_path = config.DATA_DIR / config.CACHE_FILE
    if cache_path.is_file():
        print(f'  [OK] Cache file present: {cache_path}')
    else:
        print(f'  [WARN] Cache file not found ({cache_path}) — will be created on first update.')

    print('=' * 50)
    print('Result:', 'PASS' if passed else 'FAIL')
    return passed


def _print_summary(stock_data: VivendiStock, series_ids: list[str]) -> None:
    print('\nVivendi Stock Data Snapshot')
    print(f'Generated at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('-' * 78)
    print(f'{"Series":<14} {"Name":<35} {"Price":>10} {"Change":>10} {"Date":>10}')
    print('-' * 78)

    for series_id in series_ids:
        series, current_price, change = stock_data.get_data(series_id)
        if series_id in STOCK:
            name = STOCK[series_id]['name']
        elif series_id == 'STOCK.VALUE':
            name = 'Estimated stock value in AUD'
        elif series_id == 'AUD.VALUE':
            name = 'Estimated unit value in AUD'
        else:
            name = series_id

        print(
            f'{series_id:<14} '
            f'{name[:35]:<35} '
            f'{current_price:>10.3f} '
            f'{_format_change(change):>10} '
            f'{_latest_date(series):>10}'
        )

    print('-' * 78)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog='vivendi-stock-cli',
        description='Run stock data update and print portfolio summary in terminal.'
    )
    parser.add_argument(
        '--test-setup',
        action='store_true',
        help='Verify configuration and test the API key against a live Alpha Vantage call.'
    )
    parser.add_argument(
        '--force-update',
        action='store_true',
        help='Force refresh data from APIs, bypassing local source cache and weekday/update interval checks.'
    )
    parser.add_argument(
        '--include-aud-value',
        action='store_true',
        help='Include AUD.VALUE series in output.'
    )
    args = parser.parse_args()

    if args.test_setup:
        ok = _test_setup()
        sys.exit(0 if ok else 1)

    stock_data = VivendiStock()
    if args.force_update:
        stock_data.update(force=True)

    series_ids = ['STOCK.VALUE', *STOCK.keys()]
    if args.include_aud_value:
        series_ids = ['AUD.VALUE', *series_ids]

    _print_summary(stock_data, series_ids)


if __name__ == '__main__':
    main()
