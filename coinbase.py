import time
import http.client
import time
import json

SITE = "api.gdax.com"


def prepare_request(method, site, path, body):
    con = http.client.HTTPSConnection(site, 443)
    if body:
        con.putrequest(method, path, body)
    else:
        con.putrequest(method, path)
    con.putheader("Accept", "application/json")
    con.putheader("Content-Type", "application/json")
    con.putheader("User-Agent", "napa")
    return con


def request(method, site, path, body):
    con = prepare_request(method, site, path, body)
    con.endheaders()
    response = con.getresponse()
    raw_js = response.read()
    status = response.status
    con.close()
    time.sleep(0.5)
    try:
        return json.loads(raw_js.decode()), status
    except Exception:
        return raw_js, status


class Candle:
    def __init__(self, candle_data):
        self.time = int(candle_data[0])
        self.low = float(candle_data[1])
        self.high = float(candle_data[2])
        self.open = float(candle_data[3])
        self.closing = float(candle_data[4])
        self.volume = float(candle_data[5])

    def typical_price(self):
        return (self.high + self.low + self.closing) / 3


def get_candles(product, start, end, granularity):
    read, status = request("GET", SITE, "/products/" + product + "/candles?start=" + start + "&end=" + end + "&granularity=" + granularity, "")
    if status != 200 or not isinstance(read, list):
        return read, status
    candles = []
    for read_candle in read:
        candles.append(Candle(read_candle))
    candles.sort(key=lambda c: c.time, reverse=False)
    return candles, status