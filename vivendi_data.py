import os
import yfinance
import pandas
import json
import requests
from typing import Sequence, Tuple


class VivendiStock:
    app_stock = {
        "VIV.PA": "Vivendi SE",
        "HAVAS.AS": "Havas N.V",
        "CAN.L": "Canal+ SA",
        "ALHG.PA": "Louis Hachette Group S.A.",
    }
    api_key = 'f8ce3957e9cf680f04bba1a3'

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
        return self.app_stock.keys()

    def name(self, id: str) -> str:
        try:
            return self.app_stock[id]
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
        latest_data = yfinance.download([k for k in self.app_stock.keys()],
                                        interval="1d", start="2024-12-15", rounding=True).Close
        
        if current_data is None:
            zero_values = [0.0] * len(latest_data.index)
            latest_data = latest_data.assign(EUR = pandas.Series(zero_values, index = latest_data.index))
            latest_data = latest_data.assign(GBP = pandas.Series(zero_values, index = latest_data.index))
            current_data = latest_data
        elif len(current_data.index) < len(latest_data.index):
            zero_values = [0.0] * (len(latest_data.index) - len(current_data.index))
            latest_data = latest_data.assign(EUR = pandas.Series(current_data['EUR'].values + zero_values, index = latest_data.index))
            latest_data = latest_data.assign(GBP = pandas.Series(current_data['GBP'].values + zero_values, index = latest_data.index))
            current_data = latest_data
        
        # initialize exchange data
        # https://stackoverflow.com/questions/3139879/how-do-i-get-currency-exchange-rates-via-an-api-such-as-google-finance
        for curr in ('EUR', 'GBP'):
            for d in current_data.index:
                rate = current_data[curr][d]
                if rate is None or rate == 0.0:
                    url = f'https://v6.exchangerate-api.com/v6/{self.api_key}/pair/{curr}/AUD'
                    response = requests.get(url)
                    parsed_response = response.json()
                    if 'conversion_rate' in parsed_response:
                        current_data.loc[d, curr] = parsed_response['conversion_rate']
                        break

        return current_data



if __name__ == '__main__':
    stock = VivendiStock()
    print(stock.data)