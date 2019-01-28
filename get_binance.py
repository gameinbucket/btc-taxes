import sys
import signal
import time
import json
import os.path
import binance
from datetime import datetime
from datetime import timedelta


def interrupts(signal, frame):
    print()
    print("signal interrupt")
    global run
    run = False


print("----------------------------------------")
print("|        binance candle history        |")
print("----------------------------------------")

run = True
signal.signal(signal.SIGINT, interrupts)
signal.signal(signal.SIGTERM, interrupts)

products = [("XLM", "BTC"), ("NANO", "BTC")]

time_granularity = "1m"
time_granularity_seconds = 60.0
time_interval = time_granularity_seconds * 500.0
time_format = "%Y-%m-%d %I:%M:%S %p"

for product in products:

    base = product[0]
    quote = product[1]
    symbol = base + quote

    start = datetime(2018, 1, 1)
    end = datetime(2019, 1, 1)
    candles = dict()

    while run:
        current_time = start + timedelta(seconds=time_interval)
        print("{} - {}".format(start.strftime(time_format), current_time.strftime(time_format)))
        start_ms = int(start.timestamp()) * 1000
        end_ms = int(current_time.timestamp()) * 1000
        new_candles, status = binance.get_candles(symbol, time_granularity, start_ms, end_ms)
        if status != 200:
            print("something went wrong", status)
        for candle in new_candles:
            candles[candle.time] = candle
        time.sleep(1.0)
        start = current_time
        if start >= end:
            break

    if len(candles) > 0:
        print("writing {} to file".format(base + "-" + quote))
        file_out = "binance/" + base + "-" + quote + ".txt"
        with open(file_out, "w+") as f:
            for _, candle in sorted(candles.items()):
                line = "{} ".format(candle.time)
                line += "{} ".format(candle.open)
                line += "{} ".format(candle.high)
                line += "{} ".format(candle.low)
                line += "{} ".format(candle.closing)
                line += "{} ".format(candle.volume)
                line += "{} ".format(candle.close_time)
                line += "{} ".format(candle.quote_asset_volume)
                line += "{} ".format(candle.number_of_trades)
                line += "{} ".format(candle.taker_buy_base_asset_volume)
                line += "{}\n".format(candle.taker_buy_quote_asset_volume)
                f.write(line)