from entities.Controllers.BitfinexSpotController import BitfinexSpotController
from entities.Controllers.Controller import Controller
from entities.DataGetters.BitfinexDataGetter import BitfinexDataGetter
from entities.DataGetters.DataGetter import DataGetter
from entities.Exchanges.ExchangeContainer import ExchangeContainer
from entities.Exchanges.Exchange import Exchange
from entities.Factories.AbstractFactory import AbstractFactory
from entities.Exchanges.BitfinexSpotExchange import BitfinexSpotExchange


class BitfinexSpotFactory(AbstractFactory):
    @staticmethod
    def name():
        return "BitfinexSpot"

    def create_exchange(self, config) -> Exchange:
        if 'nonce_multiplier' not in config:
            config['nonce_multiplier'] = 1
        return BitfinexSpotExchange(config['key'], config['secret'], config['name'], config['proxy'],
                                    config['nonce_multiplier'])

    def create_data_getter(self, config) -> DataGetter:
        return BitfinexDataGetter(config['key'], config['secret'], config['proxy'])

    def create_controller(self, winners: ExchangeContainer, losers: ExchangeContainer,
                          data_getter: DataGetter, logger) -> Controller:
        return BitfinexSpotController(winners, losers, data_getter, logger)



