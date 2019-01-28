import os
import coinbase
import binance
from collections import OrderedDict


def get_coinbase_candles(path):
    candles = dict()
    with open(path, "r") as f:
        for line in f:
            candle = coinbase.Candle(line.split())
            candles[candle.time] = candle
    return candles


def get_binance_candles(path):
    candles = dict()
    for file_in in os.listdir(path):
        with open(os.path.join(path, file_in), "r") as f:
            symbol = file_in.split(".")[0]
            coin_pair = symbol.split("-")
            base = coin_pair[0]
            quote = coin_pair[1]
            symbol = base + quote
            for line in f:
                candle = binance.Candle(line.split())
                candle.time = int(candle.time / 1000)
                if not candle.time in candles:
                    candles[candle.time] = dict()
                candles[candle.time][symbol] = candle
    return OrderedDict(sorted(candles.items(), key=lambda t: t[0]))


class CoinData:
    def __init__(self, btc_path, eth_path, alt_path):
        self.btc_candles = get_coinbase_candles(btc_path)
        self.eth_candles = get_coinbase_candles(eth_path)
        self.alt_candles = get_binance_candles(alt_path)

    def get_most_recent_candle(self, time, dictionary):
        for t in dictionary:
            if t >= time:
                return dictionary[t]
        return None

    def get_usd_value(self, time, coin):
        if coin == "BTC":
            candle = self.get_most_recent_candle(time, self.btc_candles)
            if candle is None:
                raise Exception("BTC not found")
            return candle.closing

        if coin == "ETH":
            candle = self.get_most_recent_candle(time, self.eth_candles)
            if candle is None:
                raise Exception("ETH not found")
            return candle.closing

        if coin == "USDT":
            return 1.0

        alt_candles = self.get_most_recent_candle(time, self.alt_candles)
        if alt_candles is None:
            raise Exception(time + " not found")
        btc_candle = self.get_most_recent_candle(time, self.btc_candles)
        if btc_candle is None:
            raise Exception("BTC not found")
        symbol = coin + "BTC"
        if symbol not in alt_candles:
            raise Exception(symbol + " not found")
        alt_candle = alt_candles[symbol]
        usd = alt_candle.closing * btc_candle.closing

        return usd
