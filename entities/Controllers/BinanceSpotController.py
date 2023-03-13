import math
import pprint
from typing import List

from entities.Controllers.Controller import Controller
from entities.Exchanges.Exchange import Exchange


class BinanceSpotController(Controller):
   allow_repeat_pump = True

   def convert(self, name, symbol: str, side: str, amount=None):
      max_quote_order_in_base = self.data_getter.get_max_order(symbol) * self.MAX_ORDER_MULT
      price = self.data_getter.get_price(symbol)
      max_price_change = price * self.config['MAX_LOSS_CONVERT'] / 100
      exchange = self.get_ex_by_name(name)
      price = price - max_price_change if side == exchange.SIDE_SELL else price + max_price_change
      # balance = exchange.get_balance()
      # base, quote = symbol.split('/')

      list_grid = [[price, amount]]
      calculated_list_grid = self.data_getter.calculate_book(list_grid)
      list_flat_grid = []
      for line in calculated_list_grid:
         list_flat_grid = self.add_split_volume(list_flat_grid, line, max_quote_order_in_base)

      list_flat_grid = [[level[0], self.data_getter.amount_to_precision(symbol, level[1])] + level[2:] for level in
                          list_flat_grid]
      self.logger.info("Sending orders to convert:")
      self.logger.info(pprint.pformat(list_flat_grid))
      if len(list_flat_grid)>=50:
         self.logger.info(f"Too many orders {len(list_flat_grid)}, current limit is {exchange.MAX_ORDER_LIMIT}. "
                          f"Try to increase MAX_ORDER_MULT in config.toml or use smaller amount of order")
         return
      response = exchange.multi_market_orders(symbol, side, list_flat_grid, ord_type='IOC', type='limit')
      return response

   def single_loser_pump(self, name, symbol, to_price: float, quote_qty: float):
      result_loser = self.losers.get_by_name(name)
      list_flat_levels = list()
      book = self.data_getter.get_calculated_book(symbol, to_price)
      max_order = self.data_getter.get_max_order(symbol) * self.MAX_ORDER_MULT
      current_price = self.data_getter.get_price(symbol)
      base_qty = quote_qty / current_price
      # level = [price, qty]
      levels = list()
      temp = 0
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
      list_flat_levels = [[level[0], self.data_getter.amount_to_precision(symbol, level[1])] + level[2:] for level in
                          list_flat_levels]
      resp = result_loser.multi_market_orders(symbol, "BUY", list_flat_levels, ord_type="IOC")
      self.logger.debug(f"Multiple Orders created: {resp}")
      self.__check_if_all_orders_executed(list_flat_levels, quote_qty, result_loser, symbol) # repeat pump if not all orders executed
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

   def __check_if_all_orders_executed(self, list_flat_levels, prev_quote_qty, result_loser: Exchange, symbol: str):
      spend_sum_quote = list_flat_levels[-1][4]
      new_balance = result_loser.get_balance()
      quote_name = symbol.split('/')[1]
      new_qute_qty=new_balance[quote_name]['free']
      expected_new_quote_qty = prev_quote_qty - spend_sum_quote
      if expected_new_quote_qty >= new_qute_qty:
         self.logger.info("Good, all orders executed")
         return
      self.logger.info(f"Not all order executed: expected quote qty: {expected_new_quote_qty}, real qute qty: {new_qute_qty}")
      not_executed_qty = new_qute_qty - expected_new_quote_qty
      self.logger.info(f"auto sending pump again on {not_executed_qty} {quote_name} ...")
      if self.allow_repeat_pump:
         self.allow_repeat_pump = False
         self.single_loser_pump(result_loser.name, symbol, to_price=list_flat_levels[-1][0], quote_qty=not_executed_qty)



