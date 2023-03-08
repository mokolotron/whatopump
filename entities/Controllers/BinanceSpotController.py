import math
from logging import Logger
from typing import List

from entities.Controllers.BitfinexSpotController import BitfinexSpotController
from entities.Controllers.Controller import Controller
from entities.DataGetters.DataGetter import DataGetter
from entities.Exchanges.ExchangeContainer import ExchangeContainer


class BinanceSpotController(BitfinexSpotController):

   def single_loser_pump(self, name, symbol, to_price: float, quote_qty: float):
      result_loser = self.losers.get_by_name(name)
      list_flat_levels = list()
      book = self.data_getter.get_calculated_book(symbol, to_price)
      max_order = self.data_getter.get_max_order(symbol)
      current_price = self.data_getter.get_price(symbol)
      base_qty = quote_qty / current_price
      # level = [price, qty]
      levels = list()
      temp = 0
      finished = False
      prev_price = 0
      for el in book['asks']:
         temp += el[1]
         if temp >= max_order:
            level = [to_price, temp - el[1], el[2], el[3], el[4]] # get previous level sum
            levels.append(level)
            temp = el[1] # to 0 except this level
         if el[0] >= to_price or el[0] == book['asks'][-1][0]: # last elem
            level = [to_price, temp, el[2], el[3], el[4]]
            levels.append(level)
            break
         prev_price = el[0]

      # if not finished:
      #    level = [to_price, temp]
      #    level = self.data_getter.calculate_book([level])
      #    levels.append(level)

      for level in levels:
         list_flat_levels = self.add_split_volume(list_flat_levels, level, max_order)
      calc_list_flat_levels = list_flat_levels
      # calc_list_flat_levels = self.data_getter.calculate_book(list_flat_levels)
      if len(calc_list_flat_levels) == 0:
         raise AttributeError("Maybe to_price < ask. Check it")
      if calc_list_flat_levels[-1][4] > quote_qty:
         raise AttributeError(f"quote_qty {quote_qty} is not enough to pump, need {calc_list_flat_levels[-1][4]}")
      free_funds = base_qty - calc_list_flat_levels[-1][3]
      if free_funds > 0:
         list_flat_levels = self.add_split_volume(list_flat_levels, [to_price, free_funds], max_order)
      list_flat_levels = [[level[0], self.data_getter.amount_to_precision(symbol, level[1])] for level in
                          list_flat_levels]
      resp = result_loser.multi_market_orders(symbol, "BUY", list_flat_levels)
      self.logger.debug(f"Multiple Orders created: {resp}")
      self.logger.info("Finish pump")

   def add_split_volume(self, original_list: List, price_volume: List, max_quote_ord_in_base) -> List:
      new_original_list = original_list.copy()
      l, k = math.modf(price_volume[1] / max_quote_ord_in_base)
      list_volume = list()
      list_volume.extend([max_quote_ord_in_base] * int(k))
      list_volume.extend([l * max_quote_ord_in_base])
      new_list_part = [[price_volume[0], float(volume)] + price_volume[2:] for volume in list_volume]
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

