from itertools import permutations
from typing import List

import ccxt
from binance.streams import ThreadedWebsocketManager
from abc import ABC, abstractmethod

from entities.Helpers.Helpers import OHLC
from entities.Helpers.PriceGraph import CurrencyGraph


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
    client: ccxt.Exchange
    graph: CurrencyGraph = None

    @abstractmethod
    def fetch(self):
        raise NotImplementedError

    def _load_graph(self):
        if self.graph is not None:
            return

        self.client.load_markets()
        symbols = self.client.symbols
        quote_s = [s.split('/')[1] for s in symbols if '/' in s]
        pairs = list(permutations(set(quote_s), 2))
        not_filtered_symbols = [f"{p[0]}/{p[1]}" for p in pairs]
        quote_symbols = [p for p in not_filtered_symbols if self.is_symbol_exist(p)]
        non_filtered_prices = self.get_prices(quote_symbols)
        prices = {k: p for k, p in non_filtered_prices.items() if p != 0}
        graph = CurrencyGraph()

        for key_s in prices:
            base, quote = key_s.split('/')
            graph.add_edge(base, quote, prices[key_s])

        self.graph = graph

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
    def calculate_book(book_part: List[List]):
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


    def not_direct_convert(self, asset_from, asset_to, count) -> float:
        self._load_graph()
        result = self.graph.convert_currency(asset_from, asset_to, count)
        return result

    @abstractmethod
    def get_max_order(self, symbol) -> float:
        raise NotImplementedError

    @abstractmethod
    def all_symbols_by_asset(self, asset):
        raise NotImplementedError

    @abstractmethod
    def get_quotes(self):
        raise NotImplementedError

    @abstractmethod
    def convert(self, symbol, side, available_qty) -> float:
        raise NotImplementedError

    def is_symbol_exist(self, symbol) -> bool:
        return symbol in self.client.symbols

    def get_ohlc(self, symbol, timeframe, science, limit) -> List[OHLC]:
        response = self.client.fetch_ohlcv(symbol, timeframe, science, limit)
        result:  List[OHLC] = []
        for row in response:
            result.append(OHLC(row))
        return result

    def get_symbols(self):
        return self.client.symbols
