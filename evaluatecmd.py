import json
from pprint import pprint
from tabulate import tabulate

import click
import toml

from core import define_factory, Core
from create_logger_module import create_logger

symbol_option = [click.option('--symbol', '-s', 'symbol', type=str, default=None, help='symbol name in format BTC/USDT')]
price_option = [click.option('--to_price', '-p', 'to_price', default=None, type=float, help='What price should be pump')]
x_pump_option = [click.option('--x_pump', '-x', 'x_pump', default=None, type=float, help='to_price = x_pump * price')]
all_flag_option = [click.option('--all', '-a', 'is_all', is_flag=True, default=False)]
quote_option = [click.option('--quote', '-q', 'quote', default='USDT', type=str, help='quote asset')]
name_option = [click.option('--name', '-n', 'name', default=None,  multiple=True, type=str, help='exchange name')]
side_option = [click.option('--side', '-si', 'side', default=None, type=click.Choice(['BUY', 'SELL'], case_sensitive=False), required=True, help='side of order')]
quantity_option = [click.option('--qty', '-q', 'qty', default=None, type=float, help='amount for making order')]
ratio_option = [click.option('-r', '--ratio', 'ratio', type=float, required=False, help='% of your free quote balance using in total grid value')]


def add_options(options):
    def _add_options(func):
        for option in options:
            func = option(func)
        return func
    return _add_options


@click.group()
def evaluate():
    """
    module for calculate required amount to make a pump
    """
    pass


@evaluate.command('show_options')
@add_options(name_option)
@add_options(symbol_option)
@add_options(price_option)
@add_options(x_pump_option)
@add_options(all_flag_option)
@add_options(quote_option)
@add_options(quantity_option)
def show_options(**kwargs):
    """Show all options"""
    pass


@evaluate.command()
@add_options(name_option)
@add_options(all_flag_option)
def balance(name, is_all):
    """Show balance by name"""
    if not (is_all or name):
        print('You must use --all or --name')
        return
    pprint(core.balances(name))


@evaluate.command('evaluate_all')
@add_options(x_pump_option)
def evaluate_all(x_pump):
    """This return a sum of quote asset need for pump given symbol to given price"""
    logger = core.controller.logger
    logger.info('Calculate all symbols, Its can took a lot of time')

    if not x_pump:
        logger.error('Please, input to_price or x_pump')
        return

    pprint(core.eval_all(x_pump))
    return True


@evaluate.command()
@add_options(symbol_option)
@add_options(price_option)
@add_options(x_pump_option)
def book(symbol, to_price, x_pump):
    """Show calculated order books"""
    logger = core.controller.logger
    is_price_entered = to_price or x_pump
    if not is_price_entered:
        logger.error('Please, input to_price or x_pump')
        return

    to_price = to_price if not x_pump else core.controller.data_getter.get_price(symbol) * float(x_pump)
    _book, cumulative_sum = core.show_book(symbol, to_price)
    if not (_book and cumulative_sum):
        return
    print('ASKS')
    print(tabulate(_book['asks'], floatfmt=".8f",
                   headers=['price', 'base_qty', 'quote_value', 'sum_base', 'sum_quote']))
    print('\nBIDS')
    print(tabulate(_book['bids'], floatfmt=".8f",
                   headers=['price', 'base_qty', 'quote_value', 'sum_base', 'sum_quote']))
    print('\n')
    pprint(f"{cumulative_sum} {symbol.split('/')[1]} need for pump {symbol} to price {to_price}: ")


@evaluate.command()
@add_options(quote_option)
def symbols(quote):
    """Show all symbols with given quote"""
    if not quote:
        print('Please, input quote')
        return

    result = core.get_symbols_by_asset(quote=quote)
    pprint(result)


@evaluate.command('evaluate_by_quote')
@add_options(quote_option)
@add_options(x_pump_option)
def evaluate_by_quote(quote, x_pump):
    """
    Evaluate all available symbols with given quote
    """
    if not quote:
        print('Please, input quote')
        return

    if not x_pump:
        print('Please, input to_price or x_pump')
        return

    result = core.eval_many_by_quote(quote=quote, x_pump=x_pump)
    pprint(result)



@evaluate.command("calculate_evaluated")
@click.option('--union', '-u', 'union', is_flag=True, default=False, help="Calculate and sort for base qty (for long permanent pump)")
def calculate_evaluated(union: bool):
    """Show result from last \'evaluate_all\' command in USD value"""
    if union:
        result = core.calc_eval_asset()
    else:
        result = core.calc_separately()


    pprint(result)


@evaluate.command()
@click.argument('file_name')
def rjson(file_name):
    """Show json file. App store data in data.json or calculated_data.json"""
    # check if file name exist
    # if not then print error
    try:
        with open(file_name, 'r') as f:
            pprint(json.load(f))
    except FileNotFoundError as e:
        create_logger().error(f'File{file_name} not exist now data.json will be available after first \'evaluate --all ...\' command. calculated_data.json will be available after first \'calculate_evaluated\' command')
        return False

@evaluate.command('order_history')
@add_options(name_option)
@add_options(all_flag_option)
@add_options(symbol_option)
def order_history(name, is_all, symbol):
    """Show last order history"""
    if not (is_all or name):
        print('You must use --all or --name')
        return
    orders = core.order_history(name, symbol)
    pprint(orders)


if __name__ == "__main__":
    config = toml.load('settings/config.toml')
    factory = define_factory(config['exchange_name'])
    core = Core(
        define_factory(config['exchange_name']),
        config
    )
    evaluate()
