from abc import ABC, abstractmethod


class Exchange(ABC):
    SIDE_BUY: str
    SIDE_SELL: str
    IS_SUPPORT_HIDDEN: bool

    def __init__(self, api_key, api_secret, name):
        self.api_key: str = api_key
        self.api_secret: str = api_secret
        self.name: str = name

    def get_balance(self):
        raise NotImplementedError

    def create_order(self, symbol, side, price, qty, ord_type='', **kwargs):
        raise NotImplementedError

    @abstractmethod
    def multi_market_orders(self, symbol, side, list_volume, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def market_order(self, symbol, side, qty):
        raise NotImplementedError

    @abstractmethod
    def cancel_all(self):
        raise NotImplementedError

    @abstractmethod
    def fetch(self):
        pass

    def get_quote_balance_by_symbol(self, symbol):
        raise NotImplementedError

    @abstractmethod
    def create_grid(self, symbol, side, to_price, quote_bal, hidden):
        raise NotImplementedError


