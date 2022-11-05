import click
import toml

from core import define_factory, Core
from pumpcmd import pump
import pumpcmd
from evaluatecmd import evaluate
import evaluatecmd

wtp = click.CommandCollection(sources=[pump, evaluate], help="Welcome to WhatOPump. "
                                                             "This is a tool for making pump on crypto exchanges (pumpcmd.py --help). "
                                                             "It can also calculate how much money you need to make a pump (evaluate.py --help). "
                                                             "Also you can call all commands from wtp.py. "
                                                             "To see all options from scope - type \'wtp.py show_options --help\' "
                                                             "For more information, please, read README.md")

if __name__ == "__main__":
    config = toml.load('settings/config.toml')
    factory = define_factory(config['exchange_name'])
    core = Core(
        define_factory(config['exchange_name']),
        config
    )
    pumpcmd.core = core
    evaluatecmd.core = core
    wtp()
