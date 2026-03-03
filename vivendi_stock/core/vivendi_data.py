from __future__ import annotations

import datetime
import pandas

from .web_api import download_stock_data, download_exchange_rate, load_cached_data, save_cached_data
from ..utils.config import config
from ..utils.logger import setup_logger


CURRENCIES = config.CURRENCIES
STOCK = config.STOCK
logger = setup_logger(__name__)


def update_stock_data(current_data: pandas.DataFrame | None, new_data: pandas.DataFrame) -> pandas.DataFrame:
    """Merge cached and new stock data and recompute portfolio values."""

    def update_exchange_rate(data: pandas.DataFrame) -> pandas.DataFrame:
        for curr in CURRENCIES:
            for day in data.index:
                rate = data[curr][day]
                try:
                    if rate == 0.0:
                        data.loc[day, curr] = download_exchange_rate(curr, day)
                except (KeyError, TypeError, ValueError) as e:
                    logger.warning('Failed to update exchange rate for %s on %s: %s', curr, day, e)
        return data

    def calc_day_value(row: pandas.Series, stock: bool) -> float:
        value = 0
        for symbol in STOCK.keys():
            currency = STOCK[symbol]['currency']
            stock_value = row[symbol] * STOCK[symbol]['multiplier'] * row[f'{currency}.AUD']
            if stock:
                stock_value *= STOCK[symbol]['stock']
            value += stock_value
        return round(value, 3)

    if current_data is None:
        current_data = new_data.combine(
            pandas.DataFrame(0, index=new_data.index, columns=CURRENCIES),
            pandas.Series.combine_first
        )
    else:
        current_data = current_data.combine(new_data, pandas.Series.combine_first)

    current_data = update_exchange_rate(current_data.fillna(0))

    kwargs = {
        'STOCK.VALUE': lambda row: calc_day_value(row, True)
    }
    current_data = current_data.assign(**kwargs)
    return current_data


class VivendiStock:
    """Vivendi portfolio service for loading, updating, and serving stock time-series."""

    def __init__(self) -> None:
        self.data = load_cached_data(config.CACHE_FILE)
        self.last_update = self.data.last_valid_index()
        self.update()

    def _refresh_workdata(self) -> None:
        self.workdata = self.data.loc[self.data.index >= config.WORKDATA_START_DATE]

    def update(self, force: bool = False) -> None:
        """Update cached stock data when the market day has advanced."""
        now = datetime.datetime.now()
        should_update = force or self.last_update is None
        if not should_update and now.weekday() in (0, 1, 2, 3, 4):
            should_update = should_update or self.last_update < now - datetime.timedelta(days=1)
        if should_update:
            self.last_update = now
            self.data = update_stock_data(
                self.data,
                download_stock_data(STOCK.keys(), CURRENCIES, use_cache=not force)
            )
            save_cached_data(self.data, config.CACHE_FILE)
        self._refresh_workdata()

    def get_data(self, series_id: str) -> tuple[pandas.Series, float, float]:
        """Return series, latest price, and day-over-day percentage change for a symbol."""
        workdata = self.workdata
        try:
            series = workdata[series_id]
            prices = series.values
            if len(prices) < 2:
                return series, 0, 0
            curr_price = prices[-1]
            prev_price = prices[-2]
            if prev_price == 0:
                return series, round(curr_price, 3), 0
            price_change = round(((curr_price - prev_price) / prev_price) * 100, 2)
            return series, round(curr_price, 3), price_change
        except (KeyError, IndexError, TypeError, ValueError):
            return pandas.Series(index=workdata.index, dtype=float), 0, 0
