from abc import abstractmethod, ABC, abstractproperty
from logging import Logger
from typing import List

from entities.Exchanges.ExchangeContainer import ExchangeContainer
from entities.Exchanges.Exchange import Exchange
from entities.DataGetters.DataGetter import DataGetter
from entities.Controllers.Controller import Controller


class AbstractFactory(ABC):

    @staticmethod
    @property
    @abstractmethod
    def name():
        return "AbstractFactory"

    @abstractmethod
    def create_exchange(self, config) -> Exchange:
        ...

    @abstractmethod
    def create_data_getter(self, config) -> DataGetter:
        ...

    @abstractmethod
    def create_controller(self, winners: ExchangeContainer, losers: ExchangeContainer,
                          data_getter: DataGetter, logger: Logger) -> Controller:
        ...

    def create_exchange_container(self, exchanges: List[Exchange]) -> ExchangeContainer:
        return ExchangeContainer(exchanges)
