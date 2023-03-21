from typing import List, Dict

import ccxt

from entities.DataGetters.DataGetter import DataGetter


class BitfinexDataGetter(DataGetter):
    SIDE_BUY = "BUY"
    SIDE_SELL = "SELL"

    def __init__(self, api_key, api_secret, proxy):
        super().__init__(api_key, api_secret)
        self.client = ccxt.bitfinex2({
            'apiKey': api_key,
            'secret': api_secret,
            'proxies': proxy
        })
        self.tickers = dict()

    def fetch(self):
        self.client.load_markets()
        symbols = list(self.client.fetch_tickers().keys())
        self.client.symbols = symbols
        pass

    def fetch_price(self, symbol, refresh=False):
        if refresh or (symbol not in self.tickers):
            self.tickers[symbol] = self.client.fetch_ticker(symbol)
        return self.tickers[symbol]

    def get_price(self, symbol) -> float:
        self.fetch_price(symbol)
        return self.tickers[symbol]['ask']

    def get_prices(self, symbols: List[str]) -> Dict[str, float]:
        tickers = self.client.fetch_tickers(symbols)
        prices = {symbol: tickers[symbol]['ask'] for symbol in symbols}
        return prices

    def amount_to_precision(self, symbol, amount) -> float:
        return float(self.client.amount_to_precision(symbol, amount))

    def fetch_order_book(self, symbol, **kwargs):
        assert kwargs['precision'] is not None, 'Missing attribute: precision='
        book = self.client.fetch_order_book(symbol, '100', {'precision': kwargs['precision']})
        return book

    def accurate_eval(self, symbol, to_price: float):
        # request book from smallest P0
        book = self.get_calculated_book(symbol, to_price)
        asks = book['asks']
        # else calculate sum
        last_elem = next((i for i in reversed(asks) if i[0] < float(to_price)),
                         None)  # return the last position which price lower than to_price or None if error
        assert last_elem is not None, "Cant find the last elem which lower than to_price"
        result_sum = last_elem[4]
        return result_sum

    def _fetch_book_in_best_precision(self, symbol, to_price: float):
        book = None
        for i in range(4):
            precision = 'P' + str(i)
            book = self.fetch_order_book(symbol, precision=precision)
            asks = book['asks']
            # if end of book price < to_price :
            if float(asks[-1][0]) >= float(to_price):
                break
        return book

    def get_calculated_book(self, symbol, to_price) -> dict:
        book = self._fetch_book_in_best_precision(symbol, to_price)
        calc_book = book
        calc_book['asks'] = self.calculate_book(book['asks'])
        calc_book['bids'] = self.calculate_book(book['bids'])
        return calc_book

    def convert(self, symbol, side: str, available_qty) -> float:
        self.client.load_markets()
        side = side.upper()
        price = self.get_price(symbol)
        if side == "BUY":
            new_qty = float(available_qty) / price
        elif side == "SELL":
            new_qty = float(available_qty) * price
        else:
            raise AttributeError(f"Unknown side: {side}")
        return new_qty

    def get_max_order(self, symbol):
        self.fetch()
        result = float(self.client.markets[symbol]['limits']['amount']['max'])
        return result

    def all_symbols_by_asset(self, asset):
        self.fetch()
        filtered_symbols = [symbol for symbol in self.client.symbols if asset in symbol.split('/')]
        # list(tuple(symbol.split(':')[0] for symbol in self.client.symbols if asset in symbol))
        return filtered_symbols

    def get_quotes(self) -> List[str]:
        symbols_all = self.client.symbols
        quotes = []
        for symbol in symbols_all:
            quote = symbol.split('/')[1]
            if (quote not in quotes) and ('F0' not in quote) and 'TEST' not in quote:
                if quote == "AAA" or quote == "BBB":
                    continue
                quotes.append(quote)
        return quotes

    def is_symbol_exist(self, symbol) -> bool:
        return symbol in self.client.symbols


        # absolute_main_quote = 'BTC'
        # # quotes = self.client.quote_currencies.get()
        #
        # result = []
        # quotes = ['EOS']
        # for quote in quotes:
        #     quote_price = self.convert(quote + '/' + absolute_main_quote, self.SIDE_SELL, 1)
        #     create_logger().debug(quote_price)
        #     quote_result = self.eval_many_by_quote(quote, x_pump)
        #     create_logger().debug(quote_result)
        #     quote_mod_result = [[q_res[0], q_res[1] * quote_price, q_res[2]] for q_res in quote_result]
        #     result.extend(quote_mod_result)
        #
        # return result




