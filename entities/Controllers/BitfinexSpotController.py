import json
import math
import os
from logging import Logger
from operator import itemgetter
from pprint import pformat
from typing import List

from entities.Controllers.Controller import Controller
from entities.DataGetters.DataGetter import DataGetter
from entities.Exchanges.ExchangeContainer import ExchangeContainer
from entities.Exchanges.Exchange import Exchange


class BitfinexSpotController(Controller):

    def request_data(self):
        pass

    def __init__(self, winners: ExchangeContainer, losers: ExchangeContainer,
                 data_getter: DataGetter, logger: Logger):
        super().__init__(winners, losers, data_getter, logger)

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

    def single_loser_pump(self, name, symbol, to_price: float, quote_qty: float):
        result_loser = self.losers.get_by_name(name)
        current_price = self.data_getter.get_price(symbol)
        max_quote_ord_in_base = self.data_getter.get_max_order(symbol) * self.MAX_ORDER_MULT
        base_qty = quote_qty / current_price

        book = self.data_getter.get_calculated_book(symbol, to_price)
        list_levels = list()

        for el in book['asks']:
            if el[0] >= to_price:
                break
            list_levels.append([el[0], el[1]])

        list_flat_levels = list()
        for level in list_levels:
            list_flat_levels = self.add_split_volume(list_flat_levels, level, max_quote_ord_in_base)
        calc_list_flat_levels = self.data_getter.calculate_book(list_flat_levels)
        if len(calc_list_flat_levels) == 0:
            raise AttributeError("Maybe to_price < ask. Check it")
        if calc_list_flat_levels[-1][4] > quote_qty:
            raise AttributeError(f"quote_qty {quote_qty} is not enough to pump, need {calc_list_flat_levels[-1][4]}")
        free_funds = base_qty - calc_list_flat_levels[-1][3]
        if free_funds > 0:
            list_flat_levels = self.add_split_volume(list_flat_levels, [to_price, free_funds], max_quote_ord_in_base)
        self.logger.debug(f'Orders:\n {pformat(list_flat_levels)}')
        list_flat_levels = [[level[0], self.data_getter.amount_to_precision(symbol, level[1])] for level in
                            list_flat_levels]
        resp = result_loser.multi_market_orders(symbol, "BUY", list_flat_levels)
        self.logger.debug(f"Multiple Orders created: {resp}")
        self.logger.info("Finish pump")
        # raise NotImplementedError  # in ioc order
        return resp

    def add_split_volume(self, original_list: List, price_volume: List, max_quote_ord_in_base) -> List:
        new_original_list = original_list.copy()
        l, k = math.modf(price_volume[1] / max_quote_ord_in_base)
        list_volume = list()
        list_volume.extend([max_quote_ord_in_base] * int(k))
        list_volume.extend([l * max_quote_ord_in_base])
        new_list_part = [[price_volume[0], float(volume)] for volume in list_volume]
        new_original_list.extend(new_list_part)
        return new_original_list

    def convert(self, name, symbol: str, side):
        exchange = self.get_ex_by_name(name)
        balance = exchange.get_balance()
        base, quote = symbol.split('/')
        if side == "BUY":
            qty = self.data_getter.convert(symbol, side, balance[quote]['free']) * self.LOW_INSURANCE_K
        else:
            qty = balance[base]['free'] * self.LOW_INSURANCE_K
        resp = exchange.market_order(symbol, side, qty)
        return resp

    def create_full_order(self, container: ExchangeContainer, symbol, side, price):
        base_name, quote_name = symbol.split('/')
        qty_s = container.balances()
        if side.upper() == "SELL":
            qty_s = {k: v[base_name]['free'] for k, v in qty_s.items()}
        elif side.upper() == "BUY":
            qty_s = {k: self.data_getter.convert(symbol, side, v[quote_name]['free']) for k, v in qty_s.items()}

        result = container.create_order_list(symbol, side, price, qty_s)
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

    def create_win_grid(self, symbol, to_price, x, ratio, hidden, levels):
        if not to_price and not x:
            self.logger.error("one of to_price or x args must be taken")
            return
        if to_price is None and x is not None:
            to_price = self.data_getter.get_price(symbol) * x
        if not self.winners.exchanges[0].IS_SUPPORT_HIDDEN:
            hidden = False
        ratio = ratio/100
        current_price = self.data_getter.get_price(symbol)
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
        report = dict()
        for ex_name, vals in resp.items():
            report[ex_name] = [{'status': ex_resp[7], 'price': ex_resp[4][0][16] if ex_resp[4][0] else ex_resp[4][16], 'amount': ex_resp[4][0][6] if ex_resp[4][0] else ex_resp[4][6]} for ex_resp in vals[4]]
        return report

