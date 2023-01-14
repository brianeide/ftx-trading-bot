import websockets
from websockets.exceptions import ConnectionClosedError
import json
import time
import requests
import traceback
from util import log, WS_URI, WEBHOOK_URI
import util
import asyncio


history = list()  # orders already logged


def send_webhook(market, side, order_type, size, fill_price):
    payload = {
        "content": "",
        "embeds": [
            {
                "type": "rich",
                "title": "Order filled!",
                "color": 0x11A9BC,
                "thumbnail": {
                    "url": "https://help.ftx.com/hc/article_attachments/4409987732500/mceclip4.png"
                },
                "fields": [
                    {
                        "name": "Market",
                        "value": market,
                        "inline": True
                    },
                    {
                        "name": "Side",
                        "value": side.capitalize(),
                        "inline": True
                    },
                    {
                        "name": "Type",
                        "value": order_type.capitalize(),
                        "inline": True
                    },
                    {
                        "name": "Filled Size",
                        "value": str(size),
                        "inline": True
                    },
                    {
                        "name": "Fill Price",
                        "value": str(fill_price),
                        "inline": True
                    }
                ]
            }
        ]
    }
    try:
        requests.post(WEBHOOK_URI, json=payload)
    except:
        log("Error sending webhook.")


def on_fill(obj):
    if 'type' in obj and obj['type'] == 'subscribed':
        log("Starting to monitor fills")
    if 'data' in obj:
        log(json.dumps(obj))
        data = obj['data']
        order_id = data['orderId']
        if order_id in history:
            return
        order = util.get_order(order_id)
        if order is not None:
            remaining = order["remaining_size"]
            if remaining == 0:
                history.append(order_id)
                send_webhook(order["market"], order["side"], order["type"], data["size"], order["fill_price"])


async def go():
    async with websockets.connect(WS_URI) as websocket:
        try:
            await websocket.send(json.dumps(util.gen_auth_payload()))
            fills_payload = {'op': 'subscribe', 'channel': 'fills'}
            await websocket.send(json.dumps(fills_payload))
            while True:
                receive = await websocket.recv()
                jobj = json.loads(receive)
                if jobj['channel'] == 'fills':
                    on_fill(jobj)
        except ConnectionClosedError:
            log("Connection closed. Reopening in 5 seconds...")
            time.sleep(5)
            await go()
        except:
            log("Uncaught error: Shutting down.")
            traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(go())
