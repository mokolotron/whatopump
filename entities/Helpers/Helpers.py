import datetime

class Api:
    def __init__(self, key, secret):
        self.key = key
        self.secret = secret

class OHLC:
    open: float
    high: float
    low: float
    close: float
    volume: float
    date: datetime.datetime

    def __init__(self, ccxt_list):
        self.date = datetime.datetime.fromtimestamp(ccxt_list[0] / 1000)
        self.open = ccxt_list[1]
        self.high = ccxt_list[2]
        self.low = ccxt_list[3]
        self.close = ccxt_list[4]
        self.volume = ccxt_list[5]

    def __str__(self):
        return f"date: {self.date}, open: {self.open:.08f}, high {self.high:.08f}, low {self.low:.08f}, close {self.close:.08f}, volume {self.volume}"

    def __repr__(self):
        return self.__str__()

class Pump:
    date: datetime.datetime
    symbol: str
    volume: float
    x: float
    dump_x: float
    ohlc: OHLC

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"date: {self.date}, symbol {self.symbol}, x {self.x}  open {self.ohlc.open:.08f}, high {self.ohlc.high:.08f}, volume {self.volume}"

