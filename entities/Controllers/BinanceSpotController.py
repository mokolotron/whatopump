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
      for el in book['asks']:
         temp += el[1]
         if temp >= max_order:
            level = [el[0], temp - el[1]] # get previous level sum
            levels.append(level)
            temp = el[1] # to 0 except this level
         if el[0] >= to_price:
            finished = True
            level = [to_price, temp]
            levels.append(level)
            break

      if not finished:
         level = [to_price, temp]
         levels.append(level)

      for level in levels:
         list_flat_levels = self.add_split_volume(list_flat_levels, level, max_order)
      calc_list_flat_levels = self.data_getter.calculate_book(list_flat_levels)
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
