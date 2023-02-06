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

    def multi_market_orders(self, symbol, side, list_volume, _type="EXCHANGE IOC", **kwargs):
        raise NotImplementedError



