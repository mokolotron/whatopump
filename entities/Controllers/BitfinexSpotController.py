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

    def __init__(self, winners: ExchangeContainer, losers: ExchangeContainer,
                 data_getter: DataGetter, logger: Logger):
        super().__init__(winners, losers, data_getter, logger)

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
