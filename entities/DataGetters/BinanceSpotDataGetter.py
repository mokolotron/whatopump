from typing import List

from entities.DataGetters.DataGetter import DataGetter
from entities.DataGetters.BitfinexDataGetter import BitfinexDataGetter
import ccxt

class BinanceSpotDataGetter(BitfinexDataGetter):
    def __init__(self, api_key, api_secret, proxy):
        super().__init__(api_key, api_secret, proxy)
        self.client = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'proxies': proxy
        })
        self.tickers = dict()

    def fetch_order_book(self, symbol, **kwargs):
        book = self.client.fetch_order_book(symbol, 5000)
        return book

    def _fetch_book_in_best_precision(self, symbol, to_price: float):
        return self.fetch_order_book(symbol)


