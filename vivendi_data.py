import os
import datetime
import pandas

from typing import Tuple
from web_api import download_stock_data, download_exchange_rate
from web_api import get_api_key, load_cached_data, save_cached_data


DATA_STORAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
CURRENCIES = ('EUR.AUD', 'GBP.AUD')
STOCK = {
    'VIV.PA': {'currency': 'EUR', 'multiplier': 1,   'name': 'Vivendi SE'},
    'HAVAS.AS': {'currency': 'EUR', 'multiplier': 1,   'name': 'Havas N.V'},
    'CAN.L': {'currency': 'GBP', 'multiplier': 0.01, 'name': 'Canal+ SA'},
    'ALHG.PA': {'currency': 'EUR', 'multiplier': 1,   'name': 'Louis Hachette Group S.A.'}
}


def update_stock_data(current_data: pandas.DataFrame, new_data: pandas.DataFrame) -> pandas.DataFrame:
    def update_exchange_rate(data: pandas.DataFrame) -> pandas.DataFrame:
        for curr in CURRENCIES:
            for day in data.index:
                rate = data[curr][day]
                if rate == 0.0:
                    data.loc[day, curr] = download_exchange_rate(curr, day)
        return data

    def calc_day_value(row) -> float:
        value = 0
        for s in STOCK.keys():
            currency = STOCK[s]['currency']
            value += row[s] * STOCK[s]['multiplier'] * row[f'{currency}.AUD']
        return round(value, 3)

    if current_data is None:
        current_data = new_data.combine(pandas.DataFrame(0, index=new_data.index, columns=CURRENCIES),
                                        pandas.Series.combine_first)
    else:
        current_data = current_data.combine(new_data, pandas.Series.combine_first)

    # ensure that exchange rate values are present
    current_data = update_exchange_rate(current_data.fillna(0))

    # recalculate stock value
    kwargs = {'AUD.VALUE': lambda row: calc_day_value(row)}
    current_data = current_data.assign(**kwargs)

    return current_data


class VivendiStock:
    def __init__(self):
        self.api_key = get_api_key()
        if self.api_key is None:
            raise ValueError('API key is required')
        self.data = load_cached_data('cache.json')
        self.last_update = self.data.last_valid_index()
        self.update()

    def update(self):
        now = datetime.datetime.now()
        should_update = self.last_update is None
        should_update = should_update or self.last_update < now - datetime.timedelta(days=1)
        if should_update:
            self.last_update = now
            new_data = download_stock_data(self.api_key, STOCK.keys(), CURRENCIES)
            self.data = update_stock_data(self.data, new_data)
            save_cached_data(self.data, 'cache.json')

    def get_data(self, id: str) -> Tuple[pandas.Series, float, float]:
        try:
            series = self.data[id]
            prices = series.values
            curr_price = prices[-1]
            prev_price = prices[-2]
            price_change = round(((curr_price - prev_price) / prev_price) * 100, 2)
            return series, round(curr_price, 3), price_change
        except Exception:
            return pandas.Series(index=self.data.index), 0, 0


if __name__ == '__main__':
    stock = VivendiStock()
    print(stock.data)
    _, curr_price, change = stock.get_data('HAVAS.AS')
    print(curr_price, change)
