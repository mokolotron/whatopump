
# whatopump


Command line tool for making pump and calculation how much need for pump. Currently working only on Bitfinex

This tool can:
- Calculate volume in ask order book by symbol
- Find symbols with the smallest order volume in ask order book
- Placing orders grid to catch a pump
- Making pump by placing orders to buy all levels in ask order book.

**Warning**: Soft in Beta


## Installation

1. Clone the repo
```bash
git clone https://github.com/mokolotron/whatopump
cd whatopump
```
2. Set up a virtual environment
```
python -m venv venv
source ./venv/bin/activate 
pip install -r requirements.txt
```
3. Configure
```
cp ./settings/config-sample.toml ./settings/config.toml
```
- open file `./settings/config.toml` with text editor. 
- input api keys to `data_getter` `losers` and `winners` sections


    
## Usage
`python wtp.py --help` to see help. Use ` --help` after command name to see all options for each command
<details> 
<summary>Help Output</summary>
<p>

```
python wtp.py --help
Usage: wtp.py [OPTIONS] COMMAND [ARGS]...

  Welcome to whatopump. This is a tool for making pump on crypto exchanges
  (pumpcmd.py --help). It can also calculate how much money you need to make
  a pump (evaluate.py --help). Also you can call all commands from wtp.py.
  To see all options from scope - type 'wtp.py show_options --help' For more
  information, please, read README.md

Options:
  --help  Show this message and exit.

Commands:
  balance              Show balance by name
  book                 Show calculated order books
  calculate_evaluated  Show result from last 'evaluate_all' command in USD...
  cancel_all           Cancel all orders
  convert              Place all quote/base amount by market order on...
  evaluate_all         This return a sum of quote asset need for pump given...
  evaluate_by_quote    Evaluate all available symbols with given quote
  grid_winners         place orders in the grid for winners
  make_pump            MAKING PUMP
  order                Place a limit order with given symbol
  rjson                Show json file.
  show_options         Show all options
  symbols              Show all symbols with given quote

```
</p>
</details>


`python wtp.py book -s EOS/USDT -x 5` see calculated volumes in order book of symbol `EOS/USDT` to price `5*current_eos_price`
<details><summary>Example book output</summary>
<p>

```
(venv) python wtp.py book -s EOS/USDT -x 5
ASKS
   price     base_qty    quote_value      sum_base     sum_quote
--------  -----------  -------------  ------------  ------------
 1.20000  62737.74707    75285.29648   62737.74707   75285.29648
 1.30000  30577.45202    39750.68763   93315.19909  115035.98411
 1.40000  16714.59865    23400.43811  110029.79774  138436.42222
 1.60000  27292.43080    43667.88927  149448.10411  200293.12485
 1.90000    280.67273      533.27818  150338.26092  201869.78501
 2.00000     29.12906       58.25812  150367.38998  201928.04312
...
 5.50000     24.87000      136.78500  155010.98712  218626.80346
 5.60000      5.19971       29.11836  155016.18683  218655.92182
 5.70000    300.00000     1710.00000  155316.18683  220365.92182
 6.00000    506.00000     3036.00000  155822.18683  223401.92182
...

BIDS
  price     base_qty    quote_value      sum_base     sum_quote
-------  -----------  -------------  ------------  ------------
1.10000  74571.91516    82029.10668   74571.91516   82029.10668
1.00000  21643.80678    21643.80678   96215.72194  103672.91345
0.97000   7663.15310     7433.25851  103878.87504  111106.17196
0.94000   8953.70748     8416.48503  112832.58252  119522.65700
0.93000      4.67301        4.34590  112837.25553  119527.00289
0.92000    250.00000      230.00000  113087.25553  119757.00289
0.91000      4.82723        4.39278  113092.08276  119761.39567
0.90000     14.98145       13.48331  113107.06421  119774.87898
...


'220344.77168726103 USDT need for pump EOS/USDT to price 5.805: '

```
</p>
</details>

Some other usages
```
python wtp.py evaluate_all -x 3     # calculate ask order book for all available symbols to pump on `3x` from its current price. Its can took a lot of time
python wtp.py order --winners -s EOS/USDT -p 5.8 -si SELL   # place order to `SELL` `EOS/USDT` at price `5.8` on all available `EOS` amount 
python wtp.py balance --all         # show all balances
```
To see all options from scope - type `python wtp.py show_options --help`
<details><summary>Example show_options output</summary>
<p>

```
python wtp.py show_options --help
Usage: wtp.py show_options [OPTIONS]

  Show all options

Options:
  -n, --name TEXT       exchange name
  -s, --symbol TEXT     symbol name in format BTC/USDT
  -p, --to_price FLOAT  What price should be pump
  -x, --x_pump TEXT     to_price = x_pump * price
  -a, --all
  -q, --quote TEXT      quote asset
  -q, --qty FLOAT       amount for making order
  --help                Show this message and exit.
```
</p>
</details>





### How to make a pump
1. `python wtp.py evaluate_all -x 3` - calculate ask order book for all available symbols to pump on `3x` from its current price. Its can took a lot of time
2. `python calculate_evaluated.py` - show result from last `evaluate_all` command in USD. You can see how much money you need to make a pump
3. Choose the symbol with the smallest amount in ask order book 
4. Buy and deposit asset to winner exchange account
5. `python wtp.py grid_winners -s your_symbol -x 3 -l 10 ` - place 10 orders in the grid for winners
6. `python wtp.py make_pump -s your_symbol -x 3` - make a pump on `your_symbol` to price `3x` from its current price
7. Profit

## Disclaimer
I'm not responsible for your actions. Use this tool at your own risk. This tool cause loses with 100% chance. I don't recommend make pump or dump at all, it's restricted by exchange rules!
This tool is for educational purposes only. Its tested only on testnet accounts. 

## License
GNU General Public License v3.0

## Support me

### Crypto
- ETH network: `0x3BDF272693be2ab0b953A5E88A97B78Ed534c18A`
- BSC network: `0x3BDF272693be2ab0b953A5E88A97B78Ed534c18A`
- TRON network: `THw2aZ6gr8d6sydPQpkYcNLWRQHEik3LSn`

### Buy me a coffee (USD)
https://www.buymeacoffee.com/mokolotron

**Or support by contributing to this project**. Feel free to open issues and pull requests. 

I can help with installation and configuration. Contact me in telegram: @mokolotron or email: mokolotron2000@gmail.com





