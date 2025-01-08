import os
import json
import requests
import pandas
import yfinance
from typing import Sequence, Tuple

STOCK = {
    "VIV.PA"    : { "currency" : "EUR", "multiplier" : 1,   "name" : "Vivendi SE" },
    "HAVAS.AS"  : { "currency" : "EUR", "multiplier" : 1,   "name" : "Havas N.V" },
    "CAN.L"     : { "currency" : "GBP", "multiplier" : 0.01,"name" : "Canal+ SA" },
    "ALHG.PA"   : { "currency" : "EUR", "multiplier" : 1,   "name" : "Louis Hachette Group S.A." }
}

def get_exchange_rate(currency: str, date: pandas.Timestamp = None) -> float:
    base, target = currency.lower().split('.')
    date = date.strftime('%Y-%m-%d') if date is not None else 'latest'
    urls = [
        f'https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{date}/v1/currencies/{base}.json',
        f'https://{date}.currency-api.pages.dev/v1/currencies/{base}.json'
    ]
    for url in urls:
        try:
            response = requests.get(url)
            parsed_response = response.json()
            return parsed_response[base][target]
        except Exception:
            pass
    return 0.0

def calc_day_value(row):
    value = 0
    for s in STOCK.keys():
        currency = STOCK[s]['currency']
        value += row[s] * STOCK[s]['multiplier'] * row[f'{currency}.AUD']
    return value

class VivendiStock:
    def __init__(self):
        data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'storage.json')

        self.data = None
        # load the data from a file (if present)
        try:
            if os.path.isfile(data_file):
                with open(data_file, encoding = 'utf8') as f:
                    self.data = pandas.read_json(f)
        except Exception as e:
            print(f'error: {e}')
            self.data = None

        # update data from providers
        self.data = self._update_data(self.data)

        # convert and save
        json_data = json.loads(self.data.to_json(date_format = 'iso'))
        if not os.path.isdir(os.path.dirname(data_file)):
            os.makedirs(os.path.dirname(data_file))
        with open(data_file, mode='wt', encoding = 'utf8') as f:
            json.dump(json_data, f, sort_keys = True, indent = 4, separators=(',', ' : '))

    def keys(self) -> Sequence:
        return STOCK.keys()

    def name(self, id: str) -> str:
        try:
            return STOCK[id]['name']
        except Exception:
            return '<unknown>'

    def index(self) -> pandas.DatetimeIndex:
        return self.data.index

    def price(self, id: str) -> pandas.Series:
        try:
            return self.data[id]
        except Exception:
            return pandas.Series(index=self.data.index)

    def current_price(self, id: str) -> Tuple[float, float]:
        try:
            prices = self.data[id].values
            curr_price = prices[-1]
            prev_price = prices[-2]
            price_change = round(((curr_price - prev_price) / prev_price) * 100, 2)
            return curr_price, price_change
        except Exception:
            return 0, 0
        
    def _update_data(self, current_data: pandas.DataFrame = None) -> pandas.DataFrame:
        currencies = ('EUR.AUD', 'GBP.AUD')

        latest_data = yfinance.download([k for k in STOCK.keys()],
                                        interval="1d", start="2024-12-15", rounding=True).Close

        if current_data is None:
            zero_values = [0.0] * len(latest_data.index)
            kwargs = { k : zero_values for k in currencies }
        elif len(current_data.index) < len(latest_data.index):
            zero_values = [0.0] * (len(latest_data.index) - len(current_data.index))
            kwargs = { k : current_data[k].values + zero_values for k in currencies }
      
        kwargs = { k : pandas.Series(kwargs[k], index = latest_data.index) for k in kwargs }
        current_data = latest_data.assign(**kwargs)

        # initialize exchange data
        for curr in currencies:
            for d in current_data.index:
                rate = current_data[curr][d]
                if rate == 0.0:
                    current_data.loc[d, curr] = get_exchange_rate(curr, d)

        # recalculate stock value
        kwargs = { 'AUD.VALUE' : lambda row: calc_day_value(row) }
        current_data = current_data.assign(**kwargs)

        return current_data


if __name__ == '__main__':
    stock = VivendiStock()
    print(stock.data)