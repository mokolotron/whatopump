from typing import List

from binance.streams import ThreadedWebsocketManager
from abc import ABC, abstractmethod


class DataGetter(ABC):

    @abstractmethod
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    tickers24: dict
    socket: ThreadedWebsocketManager
    conn: None
    tickers: dict
    # client: Client
    symbols_info: dict
    tickerSizes: dict
    SIDE_BUY: str
    SIDE_SELL: str

    @abstractmethod
    def fetch(self):
        raise NotImplementedError

    @abstractmethod
    def fetch_order_book(self, symbol, **kwargs) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_calculated_book(self, symbol, to_price) -> dict:
        raise NotImplementedError

    @abstractmethod
    def accurate_eval(self, symbol, to_price: float) -> float:
        raise NotImplementedError

    @abstractmethod
    def get_price(self, symbol) -> float:
        raise NotImplementedError

    def get_prices(self, symbols: List[str]):
        raise NotImplementedError

    @abstractmethod
    def amount_to_precision(self, symbol, volume) -> float:
        raise NotImplementedError

    @staticmethod
    def calculate_book(book_part: List[list]):
        m_book_part = list()
        sum_base = 0
        sum_quote = 0
        for el in book_part:
            m_book_part_el = [el[0], el[1]]
            quote_value = el[0] * el[1]
            m_book_part_el.append(el[0] * el[1])
            sum_base += el[1]
            sum_quote += quote_value
            m_book_part_el.append(sum_base)
            m_book_part_el.append(sum_quote)
            m_book_part.append(m_book_part_el)
        return m_book_part

    @abstractmethod
    def convert(self, symbol, side, available_qty) -> float:
        raise NotImplementedError

    @abstractmethod
    def get_max_order(self, symbol) -> float:
        raise NotImplementedError

    @abstractmethod
    def all_symbols_by_asset(self, asset):
        raise NotImplementedError

    @abstractmethod
    def get_quotes(self):
        raise NotImplementedError

    def is_symbol_exist(self, symbol):
        raise NotImplementedError
