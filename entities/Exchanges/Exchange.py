from abc import ABC, abstractmethod
import ccxt


class Exchange(ABC):
    SIDE_BUY: str = "BUY"
    SIDE_SELL: str = "SELL"
    IS_SUPPORT_HIDDEN: bool
    MAX_ORDER_LIMIT: int


    def __init__(self, api_key, api_secret, name):
        self.api_key: str = api_key
        self.api_secret: str = api_secret
        self.name: str = name
        self.client: ccxt.Exchange = ccxt.Exchange()

    def get_balance(self):
        balance = self.client.fetch_balance({'type': 'spot'})
        return balance

    def get_quote_balance_by_symbol(self, symbol):
        balances = self.get_balance()
        quote = symbol.split('/')[1]
        quote_balance = balances[quote]['free']
        return float(quote_balance)

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

    def fetch(self):
        pass

    def get_orders(self):
        return self.client.fetch_open_orders()

    def order_history(self, symbol):
        orders = self.client.fetch_orders(symbol=symbol)
        for order in orders:
            order['info']={}

