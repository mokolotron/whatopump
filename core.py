from typing import List

from ccxt import BadSymbol

from entities.Exchanges.Exchange import Exchange
from entities.Exchanges.ExchangeContainer import ExchangeContainer
from entities.Factories.AbstractFactory import AbstractFactory
from create_logger_module import create_logger, LOG_NAME

from entities.Factories.BitfinexSpotFactory import BitfinexSpotFactory
from entities.Factories.BinanceSpotFactory import BinanceSpotFactory
from entities.Helpers.Helpers import Pump, OHLC


def define_factory(ex_name) -> AbstractFactory:
    exchange_name = ex_name
    necessary_class = globals()[exchange_name]
    return necessary_class()


def create_exchanges(factory: AbstractFactory, config_list) -> List[Exchange]:
    ex_list: List = list()
    for ex_conf in config_list:
        if ex_conf['key'] == "" and ex_conf['secret'] == "":
            continue
        ex_list.append(factory.create_exchange(ex_conf))
    return ex_list


def exchange_from_name(name, config, factory) -> Exchange:
    exchange = None
    for ex_conf in config['winners'] + config['losers']:
        if ex_conf['name'] == name:
            exchange = factory.create_exchange(ex_conf)
    if exchange is None:
        raise AttributeError("name is not exist")
    return exchange


class Core:
    """
    Singleton
    """

    def __init__(self, factory: AbstractFactory, config):
        self.factory = factory
        self.config = config
        data_getter = self.factory.create_data_getter(self.config['data_getter'])
        winners = create_exchanges(self.factory, self.config['winners'])
        losers = create_exchanges(self.factory, self.config['losers'])
        self.controller = self.factory.create_controller(
            self.factory.create_exchange_container(winners),
            self.factory.create_exchange_container(losers),
            data_getter,
            logger=create_logger()
        )

    def evaluate_symbol(self, symbol, to_price):
        return self.controller.data_getter.accurate_eval(symbol, to_price)

    def create_order(self, name, symbol, side, price, qty, **kwargs):
        ex = (self.controller.losers + self.controller.winners).get_by_name(name)
        return ex.create_order(symbol, side, price, qty, **kwargs)

    def balances(self, names: List[str]):
        if not bool(names):
            names = list(set(ex.name for ex in self.controller.winners + self.controller.losers))    # all names
        return self.controller.balances(names)

    def single_loser_max_pump(self, name, symbol, to_price):
        self.controller.single_loser_max_pump(name, symbol, to_price)

    def single_loser_pump(self, name, symbol, to_price, quote_qty):
        orders_res = self.controller.single_loser_pump(name, symbol, to_price, quote_qty)
        return orders_res

    def show_book(self, symbol, to_price) -> (dict, float):
        """
        :param symbol:
        :param to_price:
        :return: book[asks[price, qty, price*qty], bids['same as asks']],
                 (sum of (price*qty) need for pump to_price of asks)
        """
        try:
            book = self.controller.data_getter.get_calculated_book(symbol, to_price)
        except BadSymbol as e:
            self.controller.logger.error(f"Symbol {symbol} does not exist: {e.args}")
            return None, None
        result_sum = self.controller.data_getter.accurate_eval(symbol, to_price)
        return book, result_sum

    def convert(self, names, symbol: str, side, ratio=None, quantity=None):
        balance = self.controller.get_ex_by_name(names[0]).get_balance()['free']
        base, quote = symbol.split('/')
        if quantity:
            balance[base] = quantity
            balance[quote] = quantity
        if side == "BUY":
            base_qty = self.controller.data_getter.convert(symbol, side, balance[quote])
        else:       # sell
            base_qty = balance[base]
        if ratio:
            base_qty *= ratio / 100
        for name in names:
            self.controller.convert(name, symbol, side, amount=base_qty)

    def cancel_all(self):
        self.controller.cancel_all_in_selected(self.controller.losers + self.controller.winners)

    def cancel_all_by_name(self, name):
        ex: Exchange = (self.controller.losers + self.controller.winners).get_by_name(name)
        ex.cancel_all()

    def get_symbols_by_asset(self, quote):
        symbols = self.controller.data_getter.all_symbols_by_asset(quote)
        return symbols

    def eval_many_by_quote(self, quote, x_pump: float):
        return self.controller.eval_many_by_quote(quote, x_pump)

    def eval_all(self, x_pump: float):
        return self.controller.eval_all(x_pump)

    def calc_eval_asset(self):
        return self.controller.calc_eval_asset()

    def calc_separately(self):
        return self.controller.calc_separately()

    def create_win_grid(self, symbol, to_price, x, hidden, ratio, levels, from_price=0):
        if levels > 100:
            raise AttributeError("levels must be less than 100")

        if not ratio:
            ratio = 100

        return self.controller.create_win_grid(symbol, to_price, x, ratio, hidden, levels=levels, from_price=from_price)

    def get_orders(self, names):
        if not bool(names):
            names = list(set(ex.name for ex in self.controller.winners + self.controller.losers))  # all names
        orders_dict ={}
        for name in names:
            ex = (self.controller.losers + self.controller.winners).get_by_name(name)
            orders = ex.get_orders()
            for o in orders:
                o['info'] = {}
            orders_dict[name] = orders
        return orders_dict

    def order_history(self, names, symbol):
        if not bool(names):
            names = list(set(ex.name for ex in self.controller.winners + self.controller.losers))  # all names

        orders_dict = {}
        for name in names:
            ex = (self.controller.losers + self.controller.winners).get_by_name(name)
            orders = ex.order_history(symbol)
            orders_dict[name] = orders
        return orders_dict

    def get_pumps_history(self, min_x=3) -> List[Pump]:
        self.controller.data_getter.fetch()
        pumps : List[Pump] = []
        for symbol in self.controller.data_getter.get_symbols():
            try:
                ohlc_l: List[OHLC] = self.controller.data_getter.get_ohlc(symbol, '1d', None, 365)
                for ohlc in ohlc_l:
                    if ohlc.high > ohlc.open * min_x:
                        pump = Pump()
                        pump.symbol = symbol
                        pump.x = ohlc.high / ohlc.open
                        pump.dump_x = ohlc.low / ohlc.open
                        pump.date = ohlc.date
                        pump.volume = ohlc.volume
                        pump.ohlc = ohlc
                        pumps.append(pump)
                        self.controller.logger.info(f"Pump found: {pump.__repr__()}")
            except Exception as e:
                self.controller.logger.error(f"Error in symbol {symbol}. Skip this symbol. Reason {list(e.args)}")
                continue
        return pumps








