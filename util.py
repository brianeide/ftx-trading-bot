from datetime import datetime
import json
import requests
import time
import hmac


config = json.load(open("config.json", "r"))
HTTP_URI = "https://ftx.us/api"
WS_URI = "wss://ftx.us/ws"
MARKET = config["market"]
SUBACCOUNT = config["subaccount"]
API_KEY = config["api_key"]
API_SECRET = config["api_secret"]
WEBHOOK_URI = config["webhook"]


def log(message):
    print(f"[{datetime.now()}] {message}")


def send_privileged_post(uri, payload):
    s = requests.Session()
    ts = int(time.time() * 1000)
    request = requests.Request('POST', uri, json=payload)
    prepared = request.prepare()
    signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
    if prepared.body:
        signature_payload += prepared.body
    signature = hmac.new(API_SECRET.encode(), signature_payload, 'sha256').hexdigest()
    prepared.headers['FTXUS-KEY'] = API_KEY
    prepared.headers['FTXUS-SIGN'] = signature
    prepared.headers['FTXUS-TS'] = str(ts)
    prepared.headers['FTXUS-SUBACCOUNT'] = SUBACCOUNT
    return s.send(prepared).json()


def send_privileged_get(uri):
    s = requests.Session()
    ts = int(time.time() * 1000)
    request = requests.Request('GET', uri)
    prepared = request.prepare()
    signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
    signature = hmac.new(API_SECRET.encode(), signature_payload, 'sha256').hexdigest()
    prepared.headers['FTXUS-KEY'] = API_KEY
    prepared.headers['FTXUS-SIGN'] = signature
    prepared.headers['FTXUS-TS'] = str(ts)
    prepared.headers['FTXUS-SUBACCOUNT'] = SUBACCOUNT
    return s.send(prepared).json()


def get_order(order_id):
    data = send_privileged_get(HTTP_URI + f"/orders/{order_id}")
    if 'success' in data and data['success']:
        result = data["result"]
        return {
            "market": result["market"],
            "side": result["side"],
            "type": result["type"],
            "filled": result["filledSize"],
            "size": result["size"],
            "remaining_size": result["remainingSize"],
            "fill_price": result["avgFillPrice"],
            "price": result["price"]
        }
    return None


def gen_auth_payload():
    ts = int(time.time() * 1000)
    signature = hmac.new(API_SECRET.encode(), f"{ts}websocket_login".encode(), 'sha256').hexdigest()
    return {
        'op': 'login',
        'args': {
            'key': API_KEY,
            'sign': signature,
            'time': ts,
            'subaccount': SUBACCOUNT
        }
    }
