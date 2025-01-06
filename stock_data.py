import yfinance
import pandas

class StockData:
    def __init__(self, key: str, name: str, start_date: str = "2024-12-15"):
        self.key = key
        self.name = name
        self.data = yfinance.download(self.key, interval="1d", start=start_date, rounding=True)
        self.pdata = self.data.Close.to_json(date_format = 'iso')

    def index(self) -> pandas.DatetimeIndex:
        return self.data.index

    def price(self) -> pandas.Series:
        try:
            return self.data.Close
        except Exception:
            return pandas.Series(index=self.data.index)

    def price_change(self) -> float:
        try:
            last_price = self.previous_price()
            return round(((self.current_price() - last_price) / last_price) * 100, 2)
        except Exception:
            return 0

    def current_price(self) -> float:
        try:
            return float(self.data.Close.values[-1])
        except Exception:
            return 0

    def previous_price(self) -> float:
        try:
            return float(self.data.Close.values[-2])
        except Exception:
            return 0


if __name__ == '__main__':
    stock = StockData('VIV.PA', "Vivendi SE")
    print(stock.pdata)