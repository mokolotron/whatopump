import logging
from pprint import pprint

import click
import toml

from core import define_factory, Core
from evaluatecmd import add_options, symbol_option, price_option, name_option, side_option, quantity_option, \
    x_pump_option, all_flag_option, ratio_option


@click.group()
def pump():
    """
    module for pump
    """
    pass


@pump.command('make_pump')
@add_options(name_option)
@add_options(symbol_option)
@add_options(price_option)
@add_options(x_pump_option)
@click.option('--qty', '-q', 'quote_qty', default=None, type=float, help='max amount for making pump in quote asset')
@click.confirmation_option(prompt='You going to make a pump. It can loose all your money from account. Are you sure?', default=False)
def make_pump(name, symbol, to_price, x_pump, quote_qty):
    """
    MAKING PUMP
    """
    if not to_price and not x_pump:
        print('Please, input -p or -x')
        return

    if len(name) > 1  or len(name)==0:
        print('Only 1 exchange for pump support for now')
        return

    name = name[0]

    losers_names = [ex.name for ex in core.controller.losers.exchanges]
    if name not in losers_names:
        print(f'Please, input correct name, one from {losers_names}')
        return

    if not to_price and x_pump:
        to_price = core.controller.data_getter.get_price(symbol) * x_pump

    if quote_qty:
        order_res = core.single_loser_pump(name, symbol, float(to_price), float(quote_qty))
    else:
        order_res = core.single_loser_max_pump(name, symbol, float(to_price))
    pprint(order_res)


@pump.command('order')
@add_options(name_option)
@add_options(symbol_option)
@add_options(price_option)
@add_options(side_option)
@add_options(quantity_option)
@click.option('--winners', is_flag=True, default=False, help='make for all winners')
@click.option('--losers', is_flag=True, default=False, help='make for all losers')
@click.option('-hi', '--hidden', 'hidden', is_flag=True, default=False, help='make hidden order if exchange support')
def order(name, symbol, side, to_price, qty, winners, losers, hidden):
    """Place a limit order with given symbol"""
    
    # check input
    if not symbol:
        print('Please, input symbol')
        return
    
    if not to_price:
        print('Please, input to_price')
        return

    if not qty:
        print('Please, input qty')
        return
    
    if name:
        for n in name:
            core.create_order(n, symbol, side, to_price, qty, hidden=hidden)
    elif winners:
        core.controller.winners.create_order(symbol, side, to_price, qty, hidden=hidden)
    elif losers:
        core.controller.losers.create_order(symbol, side, to_price, qty, hidden=hidden)
    else:
        print('Please, input name or winners or losers')
        return
    print(f'Order was created')


@pump.command()
@add_options(name_option)
@add_options(symbol_option)
@add_options(side_option)
@add_options(ratio_option)
@add_options(quantity_option)
def convert(name, symbol: str, side, ratio, qty):
    """Place all quote/base amount by market order on buy/sell"""
    
    # check input
    if not symbol:
        print('Please, input symbol')
        return
    
    if not name:
        print('Please, input name')
        return

    core.convert(name, symbol, side, ratio, qty)


@pump.command('cancel_all')
@click.option('--winners', is_flag=True, default=False, help='make for all winners')
@click.option('--losers', is_flag=True, default=False, help='make for all losers')
@add_options(name_option)
@add_options(all_flag_option)
def cancel_all(winners, losers, name, is_all):
    """Cancel all orders"""
    if is_all:
        names = list(set(ex.name for ex in core.controller.winners + core.controller.losers))  # all names
        [core.cancel_all_by_name(n) for n in names]
        print('Canceled')
        return
    if winners:
        core.controller.cancel_all_in_selected(core.controller.winners)
    if losers:
        core.controller.cancel_all_in_selected(core.controller.losers)
    if len(name) > 0:
        [core.cancel_all_by_name(n) for n in name]
    elif name:
        core.cancel_all_by_name(name)
    print('Canceled')


@pump.command('grid_winners')
@add_options(symbol_option)
@add_options(price_option)
@click.option('-fp', '--from_price', 'from_price', type=float, required=False, help='price with lowest level in grid', default=0)
@click.option('-x', '--x', 'x', type=float, default=None, help='to_price=current_price*x. example of x: 1.25 pump on 25% from current')
@click.option('-hi', '--hidden', 'hidden', is_flag=True, default=False, help='use hidden orders if possible')
@click.option('-r', '--ratio', 'ratio', type=float, required=False, help='% of your free quote balance using in total grid value')
@click.option('-l', '--levels', 'levels', type=int, required=True, help='Count of levels in grid')
def grid_winners(symbol, to_price, x, hidden, ratio, levels, from_price):
    """place orders in the grid for winners"""
    # if from_price is None:
    #     from_price = 0
    result = core.create_win_grid(symbol, to_price, x, hidden, ratio, levels, from_price)
    pprint(result)

@pump.command('show_orders')
@add_options(name_option)
@add_options(all_flag_option)
def show_orders(name, is_all):

    if not (is_all or name):
        print('You must use --all or --name')
        return

    orders = core.get_orders(name)
    pprint(orders)



if __name__ == "__main__":
    config = toml.load('settings/config.toml')
    factory = define_factory(config['exchange_name'])
    core = Core(
        define_factory(config['exchange_name']),
        config
    )
    pump()
