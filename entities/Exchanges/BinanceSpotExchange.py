import asyncio
from multiprocessing.pool import ThreadPool

from create_logger_module import create_logger
from entities.Exchanges.BitfinexSpotExchange import BitfinexSpotExchange
import ccxt
import toml
import ccxt.async_support

from entities.Exchanges.SpotExchange import SpotExchange


class BinanceSpotExchange(SpotExchange):
    IS_SUPPORT_HIDDEN: bool = False
    MAX_ORDER_LIMIT = 50

    def __init__(self, api_key, api_secret, name, proxy, nonce_multiplier):
        super().__init__(api_key, api_secret, name)
        self.proxy = proxy
        self.logger = create_logger()
        self.client = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'proxies': proxy
        })
        config = toml.load('settings/config.toml')
        self.client.set_sandbox_mode(config['Testnet'])
        self.client.options['warnOnFetchOpenOrdersWithoutSymbol'] = False

    def create_order(self, symbol, side, price, qty, ord_type='GTC', **kwargs):
        _type = kwargs['type'] if 'type' in kwargs else 'limit'
        params = {'timeInForce': ord_type}
        if _type == 'market':
            params={}
        response = self.client.create_order(symbol=symbol, side=side, price=price, amount=qty, type=_type, params=params)
        return response

    def market_order(self, symbol, side, qty):
        response = self.client.create_market_order(symbol=symbol, side=side, amount=qty)
        return response

    def multi_market_orders(self, symbol, side, list_volume, _type='limit', **kwargs):
        result = dict()
        pool = ThreadPool(len(list_volume))
        i = 0
        for level in list_volume:
            result[i] = pool.apply_async(self.create_order,
                                               (symbol, side, level[0], level[1]), kwargs)
            i+=1
        result = {k: v.get() for k, v in result.items()}
        return result

    def cancel_all(self):
        orders = self.client.fetch_open_orders()
        order_ids = [(o['id'], o['symbol']) for o in orders]
        cancel_result = [self.client.cancel_order(id=o[0], symbol=o[1]) for o in order_ids]
        return cancel_result




