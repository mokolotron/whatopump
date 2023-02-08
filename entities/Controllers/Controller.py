from logging import Logger
from typing import List

import toml

from entities.DataGetters.DataGetter import DataGetter
from entities.Exchanges.ExchangeContainer import ExchangeContainer
from abc import abstractmethod, ABC
CONFIG_PATH = 'settings/config.toml'


class Controller(ABC):
    config = toml.load(CONFIG_PATH)
    LOW_INSURANCE_K = 1 - config['INSURANCE']/100
    MAX_ORDER_MULT = config['MAX_ORDER_MULT']/100

    @abstractmethod
    def __init__(self, winners: ExchangeContainer, losers: ExchangeContainer,
                 data_getter: DataGetter, logger: Logger):
        self.winners = winners
        self.losers = losers
        self.data_getter = data_getter
        self.logger = logger

    @abstractmethod
    def request_data(self):
        raise NotImplementedError

    @abstractmethod
    def balances(self, names):
        raise NotImplementedError

    @abstractmethod
    def single_loser_max_pump(self, name, symbol, to_price):
        raise NotImplementedError

    # @abstractmethod
    # def accurate_eval(self, symbol, to_price):
    #     raise NotImplementedError

    def single_loser_pump(self, name, symbol, to_price, quote_qty):
        raise NotImplementedError

    @abstractmethod
    def convert(self, name, symbol: str, side):
        raise NotImplementedError

    @staticmethod
    def cancel_all_in_selected(selected: ExchangeContainer):
        for exchange in selected:
            exchange.fetch()
            exchange.cancel_all()

    @abstractmethod
    def create_full_order(self, container: ExchangeContainer, symbol, side, price):
        raise NotImplementedError

    def calc_eval_asset(self):
        raise NotImplementedError

    def calc_separately(self):
        raise NotImplementedError

    def eval_all(self, x_pump):
        raise NotImplementedError

    def eval_many_by_quote(self, quote, x_pump):
        raise NotImplementedError

    def add_split_volume(self, original_list: List, price_volume: List, max_quote_ord_in_base) -> List:
        raise NotImplementedError

    def create_win_grid(self, symbol, to_price, x, ratio, hidden, levels, from_price=0):
        raise NotImplementedError


