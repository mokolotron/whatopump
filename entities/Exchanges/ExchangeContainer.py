from typing import List, Dict, Generator

from entities.Exchanges.Exchange import Exchange
from multiprocessing.pool import ThreadPool


class ExchangeContainer:
    """
    Response to delegate async tasks between included exchanges
    """

    def __init__(self, exchanges: List[Exchange]):
        self.exchanges: List[Exchange] = exchanges

    def add_exchange(self, exchange: Exchange):
        self.exchanges.append(exchange)

    def remove_exchange(self):
        raise NotImplementedError

    def get_by_name(self, name: str) -> Exchange:
        for ex in self.exchanges:
            if ex.name == name:
                return ex
        raise AttributeError(f"specified name {name} not exist")

    def __add__(self, other):
        if not hasattr(other, 'exchanges'):
            raise AttributeError("Second argument must be ExchangeContainer class")
        return self.__class__(self.exchanges + other.exchanges)

    def __iter__(self) -> Generator[Exchange, None, None]:
        return (e for e in self.exchanges)

    def balances(self) -> Dict[str, Dict]:
        result = dict()
        pool = ThreadPool(len(self.exchanges))
        for ex in self.exchanges:
            result[ex.name] = pool.apply_async(ex.get_balance, ())
        result = {k: v.get() for k, v in result.items()}
        return result

    def create_order(self, symbol, side, price, qty, **kwargs):
        result = dict()
        pool = ThreadPool(len(self.exchanges))

        for ex in self.exchanges:
            result[ex.name] = pool.apply_async(ex.create_order, (symbol, side, price, qty), kwargs)
        result = {k: v.get() for k, v in result.items()}
        return result

    def create_order_list(self, symbol, side, price, qty_s: dict):
        result = dict()
        pool = ThreadPool(len(self.exchanges))
        for ex in self.exchanges:
            result[ex.name] = pool.apply_async(ex.create_order, (symbol, side, price, qty_s[ex.name]))
        result = {k: v.get() for k, v in result.items()}
        return result

    def get_quote_balances_by_symbol(self, symbol):
        result = dict()
        pool = ThreadPool(len(self.exchanges))
        for ex in self.exchanges:
            result[ex.name] = pool.apply_async(ex.get_quote_balance_by_symbol, (symbol,))
        result = {k: v.get() for k, v in result.items()}
        return result

    def multi_orders(self, symbol, side, list_flat_grid, **kwargs):
        result = dict()
        pool = ThreadPool(len(self.exchanges))
        for ex in self.exchanges:
            result[ex.name] = pool.apply_async(ex.multi_market_orders,
                                               (symbol, side, list_flat_grid), kwargs)
        result = {k: v.get() for k, v in result.items()}
        return result
