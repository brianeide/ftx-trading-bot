import time
import websockets
from websockets.exceptions import ConnectionClosedError
import json
import asyncio
import requests
import traceback
from util import log, HTTP_URI, WS_URI, MARKET
import util

last_price = -1
last_trade = 0
trigger = False
buy_ids = list()
last_sma = -1

TRADE_SIZING = 0.05


def update_sma():
    current_time = time.time()
    resolution = 15 * 60
    start_time = current_time - (resolution * 4)
    end_time = current_time
    req = requests.get(
        f"{HTTP_URI}/markets/{MARKET}/candles?resolution={resolution}&start_time={start_time}&end_time={end_time}")
    res = req.json()
    global last_sma
    if 'success' in res and res['success']:
        result = res['result']
        prices = list(map(lambda o: o['close'], result))
        prices.append(last_price)
        last_sma = sum(prices) / 5
    else:
        last_sma = -1


def get_sma():
    return last_sma


def get_balance():  # Get free USD balance
    data = util.send_privileged_get(HTTP_URI + "/wallet/balances")
    usd = 0
    if "success" in data and data["success"]:
        for coin in data["result"]:
            if coin["coin"] == "USD":
                usd = coin["free"]
                break
    return usd


def place_buy(size):
    payload = {
        'market': MARKET,
        'side': 'buy',
        'price': None,
        'type': 'market',
        'size': size
    }
    res = util.send_privileged_post(uri=HTTP_URI + "/orders", payload=payload)
    log(f"Buy order response: {json.dumps(res)}")
    if 'success' in res and res['success']:
        buy_ids.append(res['result']['id'])


def place_sell(price, size):
    payload = {
        'market': MARKET,
        'side': 'sell',
        'price': price,
        'type': 'limit',
        'size': size
    }
    res = util.send_privileged_post(uri=HTTP_URI + "/orders", payload=payload)
    log(f"Sell order response: {json.dumps(res)}")


def on_price_change():
    update_sma()
    sma = get_sma()
    if sma == -1:
        log("Error getting SMA!")
        return
    global trigger
    if last_price * 1.008 < sma:  # Trigger to buy
        if not trigger:
            log("Buy signal triggered.")
            trigger = True
        global last_trade
        if time.time() - last_trade > 15 * 60:  # If last trade happened > 15 minutes ago
            log(f"Price is {last_price}. SMA is {sma}. Buy!")
            size = get_balance() * TRADE_SIZING / last_price
            place_buy(size)
            last_trade = time.time()
    else:
        if trigger:
            log("Buy signal no longer triggered!")
            trigger = False


def on_trade(obj):
    if 'data' in obj:
        price_data = obj['data'][0]
        global last_price
        old_price = last_price
        last_price = price_data['price']
        if old_price != last_price:
            on_price_change()


def on_fill(obj):
    if 'type' in obj and obj['type'] == 'subscribed':
        log("Ready!")
    if 'data' in obj:
        log(json.dumps(obj))
        fill_data = obj['data']
        order_id = fill_data['orderId']
        if fill_data['side'] == 'buy' and order_id in buy_ids:
            order = util.get_order(order_id)
            if order is not None and order['remaining_size'] == 0:
                place_sell(price=get_sma(), size=order['size'])
                buy_ids.remove(order_id)


async def go():
    async with websockets.connect(WS_URI) as websocket:
        try:
            await websocket.send(json.dumps(util.gen_auth_payload()))
            trades_payload = {'op': 'subscribe', 'channel': 'trades', 'market': MARKET}
            await websocket.send(json.dumps(trades_payload))
            fills_payload = {'op': 'subscribe', 'channel': 'fills'}
            await websocket.send(json.dumps(fills_payload))
            while True:
                receive = await websocket.recv()
                jobj = json.loads(receive)
                if jobj['channel'] == 'trades':
                    on_trade(jobj)
                if jobj['channel'] == 'fills':
                    on_fill(jobj)
        except ConnectionClosedError:
            log("Error: Connection closed unexpectedly. Retrying in 5 seconds.")
            time.sleep(5)
            await go()
        except:
            log("Uncaught error: Shutting down.")
            traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(go())
