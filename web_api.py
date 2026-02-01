import os
import json
import requests
import pandas
import time


APP_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)))
DATA_STORAGE = os.path.join(APP_ROOT, 'data')


def get_api_key() -> str:
    api_key = os.getenv('ALPHAVANTAGE_API_KEY')
    if api_key:
        return api_key
    # try to load from file
    try:
        with open(os.path.join(APP_ROOT, 'api.key'), encoding='utf8') as f:
            api_key = f.readline()
        return api_key.strip()
    except Exception as e:
        print(f'error: {e}')
    return None


def load_json_data(file_name: str) -> dict:
    data_file = os.path.join(DATA_STORAGE, file_name)
    try:
        if os.path.isfile(data_file):
            with open(data_file, encoding='utf8') as f:
                return json.load(f)
    except Exception as e:
        print(f'error: {e}')
    return {}


def load_cached_data(file_name: str) -> pandas.DataFrame:
    data_file = os.path.join(DATA_STORAGE, file_name)
    try:
        if os.path.isfile(data_file):
            with open(data_file, encoding='utf8') as f:
                data_frame = pandas.read_json(f)
                data_frame.index = pandas.to_datetime(data_frame.index).normalize()
                return data_frame
    except Exception as e:
        print(f'error: {e}')
    return pandas.DataFrame()


def save_json_data(data: dict, file_name: str) -> None:
    data_file = os.path.join(DATA_STORAGE, file_name)
    try:
        if not os.path.isdir(os.path.dirname(data_file)):
            os.makedirs(os.path.dirname(data_file))
        with open(data_file, mode='wt', encoding='utf8') as f:
            json.dump(data, f, sort_keys=True, indent=4, separators=(',', ' : '))
    except Exception as e:
        print(f'error: {e}')


def save_cached_data(data: pandas.DataFrame, file_name: str) -> None:
    try:
        jsons = data.to_json(date_format='iso')
        save_json_data(json.loads(jsons), file_name)
    except Exception as e:
        print(f'error: {e}')


last_api_call = 0


def __execute_api_request(url: str) -> dict:
    global last_api_call
    elapsed = time.time() - last_api_call
    if elapsed < 3.0:
        time.sleep(3.0 - elapsed)
    last_api_call = time.time()
    print(f'> {url}')
    response = requests.get(url)
    return response.json()


def __download_query(api_key: str, function: str, query_id: str) -> dict:
    url = f'https://www.alphavantage.co/query?function={function}&outputsize=compact&datatype=json&apikey={api_key}'

    data = load_json_data(f'{query_id}.json') if os.getenv('ALPHAVANTAGE_CACHE') else {}
    if data:
        print(f'using cached data for {query_id}')
    else:
        data = __execute_api_request(url)

    save_json_data(data, f'{query_id}.json')
    return data


def __download_stock_symbol(api_key: str, symbol: str) -> dict:
    return __download_query(api_key, f'TIME_SERIES_DAILY&symbol={symbol}', symbol)


def __download_exchange_pair(api_key: str, exchange_pair: str) -> dict:
    from_symbol, to_symbol = exchange_pair.split('.')
    return __download_query(api_key, f'FX_DAILY&from_symbol={from_symbol}&to_symbol={to_symbol}', exchange_pair)


def download_stock_data(stock_symbols, currency_pairs) -> pandas.DataFrame:
    def get_daily_close_price(series: str, data: dict) -> dict:
        def get_day_close_price(day_data: dict) -> float:
            for key in day_data:
                if 'close' in key.lower():
                    return float(day_data[key])
            return 0.0

        try:
            time_series = data[series]
            return {day: get_day_close_price(time_series[day]) for day in time_series}
        except:
            return {}

    try:
        api_key = get_api_key()
        # download stock data
        stock_data = {symbol: get_daily_close_price('Time Series (Daily)', __download_stock_symbol(api_key, symbol))
                      for symbol in stock_symbols}
        exchange_data = {currency: get_daily_close_price('Time Series FX (Daily)', __download_exchange_pair(api_key, currency))
                         for currency in currency_pairs}
        stock_data.update(exchange_data)
        # ensure that all stock data has the same dates
        dates = [set(stock_data[symbol].keys()) for symbol in stock_data]
        dates = set.intersection(*dates)
        stock_data = {symbol: {date: stock_data[symbol][date] for date in dates} for symbol in stock_data}
        # convert to DataFrame
        data_frame = pandas.DataFrame().from_dict(stock_data, orient='columns')
        data_frame.index = pandas.to_datetime(data_frame.index).normalize()
        return data_frame
    except Exception as e:
        print(f'error: {e}')
        return pandas.DataFrame()


def download_exchange_rate(currency: str, date: pandas.Timestamp = None) -> float:
    base, target = currency.lower().split('.')
    if date is None:
        date = 'latest'
    elif isinstance(date, pandas.Timestamp):
        date = date.strftime('%Y-%m-%d')
    urls = [
        f'https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{date}/v1/currencies/{base}.json',
        f'https://{date}.currency-api.pages.dev/v1/currencies/{base}.json'
    ]
    for url in urls:
        try:
            parsed_response = __execute_api_request(url)
            return parsed_response[base][target]
        except:
            pass
    return 0.0
