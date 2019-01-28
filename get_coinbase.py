import sys
import signal
import time
import json
import coinbase
import os.path
from datetime import datetime
from datetime import timedelta


def interrupts(signal, frame):
    print()
    print("signal interrupt")
    global run
    run = False


print("----------------------------------------")
print("|       coinbase candle history        |")
print("----------------------------------------")

run = True
signal.signal(signal.SIGINT, interrupts)
signal.signal(signal.SIGTERM, interrupts)

products = ["BTC-USD", "ETH-USD"]

time_granularity = "60"
time_interval = float(time_granularity) * 200.0
time_format = "%Y-%m-%d %I:%M:%S %p"

for product in products:
    start = datetime(2018, 1, 1)
    end = datetime(2019, 1, 1)
    candles = dict()

    while run:
        current_time = start + timedelta(seconds=time_interval)
        print("{} - {}".format(start.strftime(time_format), current_time.strftime(time_format)))
        new_candles, status = coinbase.get_candles(product, start.isoformat(), current_time.isoformat(), time_granularity)
        if status != 200:
            print("something went wrong", status)
        for candle in new_candles:
            candles[candle.time] = candle
        time.sleep(1.0)
        start = current_time
        if start >= end:
            break

    print("writing", product, "to file")
    file_out = "coinbase/" + product + ".txt"
    with open(file_out, "w+") as f:
        for key, candle in sorted(candles.items()):
            f.write("{} {:.2f} {:.2f} {:.2f} {:.2f} {:.2f}\n".format(candle.time, candle.low, candle.high, candle.open, candle.closing, candle.volume))
