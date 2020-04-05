#!/usr/bin/python3

import sys
import csv
from operator import itemgetter
from datetime import datetime

debug = False
form_8949 = True
epoch = datetime(1970, 1, 1)


def epoch_to_basic(time):
    return datetime.fromtimestamp(time).isoformat()


def epoch_to_date(time):
    return datetime.fromtimestamp(time).strftime("%m/%d/%Y")


class Trade:
    def __init__(self, size, price, time):
        self.size = size
        self.price = price
        self.time = epoch_to_date(time)

    def __repr__(self):
        return "<Trade size:{:,.3f}, price:{:,.3f}, time:{}>".format(self.size, self.price, self.time)


def main():
    if len(sys.argv) <= 3:
        print("[strategy (LIFO|FIFO)] [coinbase path to csv] [binance path to csv]")
        return

    strategy = sys.argv[1]
    coinbase_path = sys.argv[2]
    binance_path = sys.argv[3]

    trades = []

    try:
        with open(coinbase_path, newline="") as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            header = next(reader, None)
            if debug:
                print(header)
            for row in reader:
                time = datetime.strptime(row[3], "%Y-%m-%dT%H:%M:%S.%fZ")
                time = int((time - epoch).total_seconds())
                del row[3]
                row.insert(0, time)
                row.insert(0, "COINBASE")
                trades.append(row)
    except FileNotFoundError:
        print(coinbase_path, "not found")
        return

    try:
        with open(binance_path, newline="") as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            header = next(reader, None)
            if debug:
                print(header)
            for row in reader:
                time = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                row[0] = int((time - epoch).total_seconds())
                row.insert(0, "BINANCE")
                trades.append(row)
    except FileNotFoundError:
        print(binance_path, "not found")
        return

    trades.sort(key=itemgetter(1))

    import usd
    coin_data = usd.CoinData("coinbase/BTC-USD.txt", "coinbase/ETH-USD.txt", "binance")

    delete = list()
    trade_count = len(trades)
    for index, row in enumerate(trades):
        if index + 1 == trade_count:
            break
        next_row = trades[index + 1]
        # exchange time
        if row[0] != next_row[0] or row[1] != next_row[1]:
            continue
        if row[0] == "COINBASE":
            # side coin price
            if row[4] != next_row[4] or row[6] != next_row[6] or row[7] != next_row[7]:
                continue
            row[5] = float(row[5]) + float(next_row[5])  # size
            if debug:
                print("merging", row, "and", next_row)
            delete.append(next_row)
        else:
            # market side coin
            if row[2] != next_row[2] or row[3] != next_row[3] or row[8] != next_row[8]:
                continue
            row[5] = float(row[5]) + float(next_row[5])  # size
            row[6] = float(row[6]) + float(next_row[6])  # total
            if debug:
                print("merging", row, "and", next_row)
            delete.append(next_row)

    for trade in delete:
        trades.remove(trade)
        if debug:
            print("deleted", trade)

    gains = 0.0
    history = dict()
    for row in trades:
        if debug:
            print(row)
        if row[0] == "COINBASE":
            time = row[1]
            side = row[4]
            size = float(row[5])
            coin = row[6]
            price = float(row[7])
            if side == "BUY":
                if coin not in history:
                    history[coin] = list()
                history[coin].append(Trade(size, price, time))
                if not form_8949:
                    print("{} bought {:,.2f} {} at $ {:,.2f}".format(epoch_to_basic(time), size, coin, price))
            else:
                delete = list()
                coin_history = history[coin]
                if strategy == "LIFO":
                    coin_history = coin_history[:]
                    coin_history.reverse()

                if len(coin_history) == 0:
                    raise Exception("something went wrong")

                for trade in coin_history:
                    if trade.size >= size:
                        trade.size -= size
                        cost = (size * trade.price)
                        proceeds = (size * price)
                        profit = proceeds - cost
                        gains += profit
                        if form_8949:
                            print("{:,.6f} {} for {} | {} | {} | $ {:,.2f} | $ {:,.2f} | $ {:,.2f}".format(size, coin, "USD", trade.time, epoch_to_date(time), proceeds, cost, profit))
                        else:
                            if profit >= 0.0:
                                print("{} sold {:,} {} at $ {:,.2f} bought at $ {:,.2f} on {} profit $ {:,.2f}".format(epoch_to_basic(time), size, coin, price, trade.price, trade.time, profit))
                            else:
                                print("{} sold {:,} {} at $ {:,.2f} bought at $ {:,.2f} on {} lost $ {:,.2f}".format(epoch_to_basic(time), size, coin, price, trade.price, trade.time, -profit))
                        if trade.size == 0.0:
                            delete.append(trade)
                        break
                    else:
                        cost = (trade.size * trade.price)
                        proceeds = (trade.size * price)
                        profit = proceeds - cost
                        gains += profit
                        if form_8949:
                            print("{:,.6f} {} for {} | {} | {} | $ {:,.2f} | $ {:,.2f} | $ {:,.2f}".format(trade.size, coin, "USD", trade.time, epoch_to_date(time), proceeds, cost, profit))
                        else:
                            if profit >= 0.0:
                                print("{} sold {:,} {} at $ {:,.2f} bought at $ {:,.2f} on {} profit $ {:,.2f}".format(epoch_to_basic(time), trade.size, coin, price, trade.price, trade.time, profit))
                            else:
                                print("{} sold {:,} {} at $ {:,.2f} bought at $ {:,.2f} on {} lost $ {:,.2f}".format(epoch_to_basic(time), trade.size, coin, price, trade.price, trade.time, -profit))
                        size -= trade.size
                        trade.size = 0
                        delete.append(trade)

                for trade in delete:
                    history[coin].remove(trade)

        elif row[0] == "BINANCE":
            time = row[1]
            market = row[2]
            side = row[3]
            size = float(row[5])
            total = float(row[6])
            fee_coin = row[8]

            buy_coin = fee_coin
            sold_coin = market.replace(fee_coin, "")

            if side == "BUY":
                sold_size = total
                buy_size = size
            else:
                sold_size = size
                buy_size = total

            buy_coin_usd = coin_data.get_usd_value(time, buy_coin)
            sold_coin_usd = coin_data.get_usd_value(time, sold_coin)

            delete = list()
            coin_history = history[sold_coin]
            if strategy == "LIFO":
                coin_history = coin_history[:]
                coin_history.reverse()

            if len(coin_history) == 0:
                raise Exception("something went wrong")

            print("--- " + side + " ---")

            for trade in coin_history:
                if trade.size >= sold_size:
                    trade.size -= sold_size
                    proceeds = (sold_size * sold_coin_usd)
                    cost = (sold_size * trade.price)
                    profit = proceeds - cost
                    gains += profit
                    if form_8949:
                        print("{:,.6f} {} for {} | {} | {} | $ {:,.2f} | $ {:,.2f} | $ {:,.2f}".format(sold_size, sold_coin, buy_coin, trade.time, epoch_to_date(time), proceeds, cost, profit))
                    else:
                        if profit >= 0.0:
                            print("{} sold {:,} {} at $ {:,.2f} bought at $ {:,.2f} on {} profit $ {:,.2f}".format(
                                epoch_to_basic(time), sold_size, sold_coin, sold_coin_usd, trade.price, trade.time, profit))
                        else:
                            print("{} sold {:,} {} at $ {:,.2f} bought at $ {:,.2f} on {} lost $ {:,.2f}".format(
                                epoch_to_basic(time), sold_size, sold_coin, sold_coin_usd, trade.price, trade.time, -profit))
                    if trade.size == 0.0:
                        delete.append(trade)
                    break
                else:
                    proceeds = (trade.size * sold_coin_usd)
                    cost = (trade.size * trade.price)
                    profit = proceeds - cost
                    gains += profit
                    if form_8949:
                        print("{:,.6f} {} for {} | {} | {} | $ {:,.2f} | $ {:,.2f} | $ {:,.2f}".format(trade.size, sold_coin, buy_coin, trade.time, epoch_to_date(time), proceeds, cost, profit))
                    else:
                        if profit >= 0.0:
                            print("{} sold {:,} {} at $ {:,.2f} bought at $ {:,.2f} on {} profit $ {:,.2f}".format(
                                epoch_to_basic(time), trade.size, sold_coin, sold_coin_usd, trade.price, trade.time, profit))
                        else:
                            print("{} sold {:,} {} at $ {:,.2f} bought at $ {:,.2f} on {} lost $ {:,.2f}".format(
                                epoch_to_basic(time), trade.size, sold_coin, sold_coin_usd, trade.price, trade.time, -profit))
                    sold_size -= trade.size
                    trade.size = 0
                    delete.append(trade)

            for trade in delete:
                history[sold_coin].remove(trade)

            if buy_coin not in history:
                history[buy_coin] = list()
            history[buy_coin].append(Trade(buy_size, buy_coin_usd, time))

            if not form_8949:
                print("{} bought {:,} {} ($ {:,.2f}) for {:,} {} ($ {:,.2f})".format(epoch_to_basic(time), sold_size, sold_coin, sold_coin_usd, buy_size, buy_coin, buy_coin_usd))

            print("===========")

    print()
    if gains > 0.0:
        rate = 0.25
        taxes = gains * rate
        print("capital gains $ {:,.3f}, taxes owed $ {:,.3f}".format(gains, taxes))
    else:
        print("capital losses $ {:,.3f}, no taxes owed".format(-gains))
    print('----------------------------------------')


print("----------------------------------------")
print("|              coin taxes              |")
print("----------------------------------------")
main()
