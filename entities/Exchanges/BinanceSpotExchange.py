import asyncio
from multiprocessing.pool import ThreadPool

from create_logger_module import create_logger
from entities.Exchanges.BitfinexSpotExchange import BitfinexSpotExchange
import ccxt
import toml
import ccxt.async_support


class BinanceSpotExchange(BitfinexSpotExchange):
    def __init__(self, api_key, api_secret, name, proxy, nonce_multiplier):
        super().__init__(api_key, api_secret, name, proxy, nonce_multiplier)
        # ccxt.bitfinex
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

        self.async_client = ccxt.async_support.binance({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'proxies': self.proxy
        })
        self.async_client.set_sandbox_mode(config['Testnet'])
        self.async_client.options['warnOnFetchOpenOrdersWithoutSymbol'] = False

    def create_order(self, symbol, side, price, qty, ord_type='GTC', **kwargs):
        response = self.client.create_order(symbol=symbol, side=side, price=price, amount=qty, type='limit')
        return response

    def market_order(self, symbol, side, qty):
        response = self.client.create_market_order(symbol=symbol, side=side, amount=qty)
        return response

    def multi_market_orders(self, symbol, side, list_volume, _type="EXCHANGE IOC", **kwargs):
        result = dict()
        pool = ThreadPool(len(list_volume))
        for level in list_volume:
            result[level[0]] = pool.apply_async(self.create_order,
                                               (symbol, side, level[0], level[1]), kwargs)
        result = {k: v.get() for k, v in result.items()}
        return result


    def cancel_all(self):
        orders = self.client.fetch_open_orders()
        order_ids = [(o['id'], o['symbol']) for o in orders]
        cancel_result = [self.client.cancel_order(id=o[0], symbol=o[1]) for o in order_ids]
        return cancel_result



