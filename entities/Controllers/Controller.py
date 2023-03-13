import json
import os
from logging import Logger
from operator import itemgetter
from typing import List

import toml

from entities.DataGetters.DataGetter import DataGetter
from entities.Exchanges.Exchange import Exchange
from entities.Exchanges.ExchangeContainer import ExchangeContainer
from abc import abstractmethod, ABC
CONFIG_PATH = 'settings/config.toml'


class Controller(ABC):
    config = toml.load(CONFIG_PATH)
    LOW_INSURANCE_K = 1 - config['INSURANCE']/100
    MAX_ORDER_MULT = config['MAX_ORDER_MULT']/100

    def __init__(self, winners: ExchangeContainer, losers: ExchangeContainer,
                 data_getter: DataGetter, logger: Logger):
        self.winners = winners
        self.losers = losers
        self.data_getter = data_getter
        self.logger = logger

    def request_data(self):
        pass
        raise NotImplementedError

    def get_ex_by_name(self, name) -> Exchange:
        return (self.winners + self.losers).get_by_name(name)

    def balances(self, names: List[str]):
        ex_cont = self.winners + self.losers
        filtered_exs = [ex for ex in ex_cont.exchanges if ex.name in names]
        filtered_ex_cont = ExchangeContainer(filtered_exs)
        bals = filtered_ex_cont.balances()

        for b, vb in bals.items():
            vb.pop('info', None)
        return bals

    def single_loser_max_pump(self, name, symbol, to_price: float):
        result_loser = self.losers.get_by_name(name)
        if result_loser is None:
            raise AttributeError(f"loser {name} not exist")

        result_loser: Exchange
        base, quote = symbol.split('/')
        quote_balance = result_loser.get_balance()
        quote_balance_f = quote_balance[quote]['free']
        result = self.single_loser_pump(name, symbol, to_price, quote_balance_f)
        return result

    def single_loser_pump(self, name, symbol, to_price, quote_qty):
        raise NotImplementedError

    def convert(self, name, symbol: str, side, amount=None):
        exchange = self.get_ex_by_name(name)
        balance = exchange.get_balance()
        base, quote = symbol.split('/')
        if side == "BUY":
            qty = self.data_getter.convert(symbol, side, balance[quote]['free']) * self.LOW_INSURANCE_K
        else:
            qty = balance[base]['free'] * self.LOW_INSURANCE_K
        resp = exchange.market_order(symbol, side, qty)
        return resp

    @staticmethod
    def cancel_all_in_selected(selected: ExchangeContainer):
        for exchange in selected:
            exchange.fetch()
            exchange.cancel_all()

    def calc_eval_asset(self):
        result = self.calc_separately()

        base_dict = {}
        for v in result:
            base, quote = v[0].split('/')
            base_dict[base] = [_v for _v in result if _v[0].split('/')[0] == base]

        base_arr = []
        for k, v in base_dict.items():
            total = sum([_v[1] for _v in v])
            base_arr.append([k, total, v])

        base_sorted_arr = sorted(base_arr, key=itemgetter(1))
        with open('calculated_data.json', 'w') as f:
            json.dump(base_sorted_arr, f)

        return base_sorted_arr


    def calc_separately(self):
        self.data_getter.fetch()
        if not os.path.isfile('data.json'):
            self.logger.error("File data.json not found. Run evaluate_all first")
            return None
        with open('data.json', 'r') as f:
            data = json.load(f)
            quote_s = list(data.keys())
            convert_prices = dict()
            for q in quote_s:
                usdt_symbol = q + '/USDT'
                if q == 'USD' or q == 'USDT':
                    convert_prices[q] = 1
                    continue
                convert_prices[q] = self.data_getter.get_price(usdt_symbol) if self.data_getter.is_symbol_exist(usdt_symbol) else 0
                # if price not found try to reverse symbol to get it price
                if convert_prices[q] == 0:
                    reversed_symbol = 'USDT/' + q
                    convert_prices[q] = self.data_getter.get_price(reversed_symbol) if self.data_getter.is_symbol_exist(reversed_symbol) else 0
            # filter convert_prices with zero price
            convert_prices = {k: v for k, v in convert_prices.items() if v != 0}
            result = []
            for quote_name, values in data.items():
                if quote_name not in convert_prices:
                    self.logger.warning(f"No price for convert {quote_name} to USD. skip")
                    continue
                convert_price = convert_prices[quote_name]
                values_mod = [[v[0], v[1] * convert_price, v[2]] for v in values]
                result.extend(values_mod)

        base_sorted_arr = sorted(result, key=itemgetter(1))
        return base_sorted_arr

    def eval_all(self, x_pump: float):

        self.data_getter.fetch()
        quotes = self.data_getter.get_quotes()

        result = {}
        for quote in quotes:
            quote_result = self.eval_many_by_quote(quote, x_pump)
            self.logger.debug(json.dumps(quote_result))
            result[quote] = quote_result

        with open('data.json', 'w') as f:
            json.dump(result, f)
        return result

    def eval_many_by_quote(self, quote, x_pump: float):
        results = []
        symbols = self.data_getter.all_symbols_by_asset(quote)
        for symbol in symbols:
            try:
                if not quote == symbol.split('/')[1]:
                    continue
                to_price = self.data_getter.get_price(symbol) * float(x_pump)
                pump_cost = self.data_getter.accurate_eval(symbol, to_price)
                results.append([symbol, pump_cost, to_price])
            except Exception as e:
                self.logger.error(f"Error in symbol {symbol}. Reason :{e}")
                continue
        results = sorted(results, key=itemgetter(1))
        return results

    def add_split_volume(self, original_list: List, price_volume: List, max_quote_ord_in_base) -> List:
        raise NotImplementedError

    def create_win_grid(self, symbol, to_price, x, ratio, hidden, levels, from_price=0):
        if not to_price and not x:
            self.logger.error("one of to_price or x args must be taken")
            return
        if to_price is None and x is not None:
            to_price = self.data_getter.get_price(symbol) * x
        if not self.winners.exchanges[0].IS_SUPPORT_HIDDEN:
            hidden = False
        ratio = ratio/100
        current_price = self.data_getter.get_price(symbol)
        if from_price > 0:
            current_price = from_price
        side = 'sell'
        # balances = self.winners.get_quote_balances_by_symbol(symbol)
        baseAsset = symbol.split('/')[0]
        balances = {ex: balance[baseAsset]['free'] for ex, balance in self.winners.balances().items()}
        calc_quote_balances = {name: quote_bal * ratio for name, quote_bal in balances.items()}
        max_quote_order_in_base = self.data_getter.get_max_order(symbol) * self.MAX_ORDER_MULT
        # create orders grid with i lines
        list_grid = list()
        for name, balance in calc_quote_balances.items():
            # calculate COUNT_LINES, price between current_price and to_price
            for i in range(1, levels + 1):
                price = current_price + (to_price - current_price) / levels * i
                amount = balance / levels
                rounded_amount = ((amount * 10**7)//1)/10**7  # 7 digits after point
                list_grid.append([price, rounded_amount])
            list_flat_grid = list()
        for line in list_grid:
            list_flat_grid = self.add_split_volume(list_flat_grid, line, max_quote_order_in_base)

        resp = self.winners.multi_orders(symbol, side, list_flat_grid, _type="EXCHANGE LIMIT", hidden=hidden)
        # create report for orders result
        return resp


