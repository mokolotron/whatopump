from logging import Logger

from entities.Controllers.BinanceSpotController import BinanceSpotController
from entities.Controllers.Controller import Controller
from entities.DataGetters.DataGetter import DataGetter
from entities.Exchanges.BinanceSpotExchange import BinanceSpotExchange
from entities.Exchanges.Exchange import Exchange
from entities.Exchanges.ExchangeContainer import ExchangeContainer
from entities.Factories.AbstractFactory import AbstractFactory
from entities.DataGetters.BinanceSpotDataGetter import BinanceSpotDataGetter


class BinanceSpotFactory(AbstractFactory):
    @staticmethod
    def name():
        return "BinanceSpot"

    def create_exchange(self, config) -> Exchange:
        return BinanceSpotExchange(config['key'], config['secret'], config['name'], config['proxy'], nonce_multiplier=1)

    def create_data_getter(self, config) -> DataGetter:
        return BinanceSpotDataGetter(config['key'], config['secret'], config['proxy'])

    def create_controller(self, winners: ExchangeContainer, losers: ExchangeContainer, data_getter: DataGetter,
                          logger: Logger) -> Controller:
        return BinanceSpotController(winners, losers, data_getter, logger)

