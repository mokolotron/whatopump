from create_logger_module import create_logger
from entities.Exchanges.BitfinexSpotExchange import BitfinexSpotExchange
import ccxt
import toml


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

    def create_order(self, symbol, side, price, qty, ord_type='GTC', **kwargs):
        response = self.client.create_order(symbol=symbol, side=side, price=price, amount=qty, type='limit')
        return response

    def multi_market_orders(self, symbol, side, list_volume, _type="EXCHANGE IOC", **kwargs):
        raise NotImplementedError

    def cancel_all(self):
        orders = self.client.fetch_open_orders()
        order_ids = [(o['id'], o['symbol']) for o in orders]
        cancel_result = [self.client.cancel_order(id=o[0], symbol=o[1]) for o in order_ids]
        return cancel_result



