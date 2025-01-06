import yfinance
import pandas
import requests
from typing import Sequence


class VivendiStock:
    app_stock = {
        "VIV.PA": "Vivendi SE",
        "HAVAS.AS": "Havas N.V",
        "CAN.L": "Canal+ SA",
        "ALHG.PA": "Louis Hachette Group S.A.",
    }
    api_key = 'f8ce3957e9cf680f04bba1a3'

    def __init__(self):
        self.stock_data = yfinance.download([k for k in self.app_stock.keys()],
                                            interval="1d", start="2024-12-15", rounding=True)

        # url = f'https://v6.exchangerate-api.com/v6/{self.api_key}/pair/EUR/AUD'
        # response = requests.get(url)
        # print(response.json())
        # url = f'https://v6.exchangerate-api.com/v6/{self.api_key}/pair/GBP/AUD'
        # response = requests.get(url)
        # print(response.json())

    def keys(self) -> Sequence:
        return self.app_stock.keys()

    def name(self, id: str) -> str:
        try:
            return self.app_stock[id]
        except Exception:
            return '<unknown>'

    def index(self) -> pandas.DatetimeIndex:
        return self.stock_data.index

    def price(self, id: str) -> pandas.Series:
        try:
            return self.stock_data.Close[id]
        except Exception:
            return pandas.Series(index=self.stock_data.index)

    def price_change(self, id: str) -> float:
        try:
            last_price = self.previous_price(id)
            return round(((self.current_price(id) - last_price) / last_price) * 100, 2)
        except Exception:
            return 0

    def current_price(self, id: str) -> float:
        try:
            return float(self.stock_data.Close[id].values[-1])
        except Exception:
            return 0

    def previous_price(self, id: str) -> float:
        try:
            return float(self.stock_data.Close[id].values[-2])
        except Exception:
            return 0


if __name__ == '__main__':
    stock = VivendiStock()
    print(stock.stock_data)