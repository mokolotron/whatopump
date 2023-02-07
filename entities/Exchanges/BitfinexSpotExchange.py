from create_logger_module import create_logger, LOG_NAME
from multiprocessing.pool import ThreadPool
from bitfinex import ClientV2
from bitfinex.utils import Operation as Op
import ccxt

from entities.Exchanges.SpotExchange import SpotExchange


class BitfinexSpotExchange(SpotExchange):
    SIDE_BUY: str = "BUY"
    SIDE_SELL: str = "SELL"
    IS_SUPPORT_HIDDEN = True

    def __init__(self, api_key, api_secret, name, proxy, nonce_multiplier):
        super().__init__(api_key, api_secret, name)
        # ccxt.bitfinex
        self.proxy = proxy
        self.logger = create_logger()
        self.client = ccxt.bitfinex2({
            'apiKey': api_key,
            'secret': api_secret,
            'proxies': proxy
        })
        self.nonce_multiplier = nonce_multiplier
        self.client.nonce_multiplier = self.nonce_multiplier

    def fetch(self):
        pass

    def create_order(self, symbol, side, price, qty, ord_type='GTC', **kwargs):
        is_hidden = kwargs.get('hidden', False)
        response = self.client.create_order(symbol, 'limit', side.lower(),
                                            qty, price,
                                            {'timeInForce': ord_type, 'hidden': int(is_hidden)})
        return response

    def get_balance(self):
        balance = self.client.fetch_balance({'type': 'spot'})
        return balance

    def get_quote_balance_by_symbol(self, symbol):
        balances = self.get_balance()
        quote = symbol.split('/')[1]
        quote_balance = balances[quote]['free']
        return float(quote_balance)

    def multi_market_orders(self, symbol, side, list_volume, _type="EXCHANGE IOC",  **kwargs):
        client = ClientV2(self.api_key, self.api_secret, proxy=self.proxy,
                          nonce_multiplier=1000.0                         # ccxt miliseconds
                                                 * self.nonce_multiplier  # custom api nonce
                          )

        ops = []
        hidden = kwargs.get('hidden', False)
        _flags = 64 if hidden else 0
        if side == 'sell':
            # in all list_volume[1] change the sign to negative
            list_volume = [[x[0], -x[1]] for x in list_volume]
        self.client.load_markets()
        market_symbol = self.client.market(symbol)['id']
        for level in list_volume:
            order_operation = client.get_order_op(
                op=Op.NEW,
                type=_type,
                symbol=market_symbol,
                price=str(level[0]).replace(',', '.'),
                amount=str(level[1]).replace(',', '.'),
                flags=_flags)
            ops.append(order_operation)
        ex_resp = client.order_multi_op(ops)
        resp = {'status': ex_resp[7], 'price': ex_resp[4][0][16] if ex_resp[4][0] else ex_resp[4][16],
                            'amount': ex_resp[4][0][6] if ex_resp[4][0] else ex_resp[4][6]}
        return resp

    def market_order(self, symbol, side, qty):
        self.client.create_order(symbol, 'EXCHANGE MARKET', str(side).lower(), qty)

    def cancel_all(self):
        self.client.load_markets()
        self.client.cancel_all_orders()




