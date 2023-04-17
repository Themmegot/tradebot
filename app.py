import json, config
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import *

app = Flask(__name__)

client = Client(config.API_KEY, config.API_SECRET, tld='com')

def place_order(order_type, order_action, quantity, ticker, timeStamp):
    try:
        print(f"sending order - {order_action} - {quantity}")
        order = client.futures_create_order(symbol=ticker, side=order_action, type=order_type, quantity=quantity, timestamp=timeStamp)
        print(f"{order_action} ORDER OK")
    except Exception as e:
        print("an exception occurred - {}".format(e))
        return False
    return True

def cancel_order(ticker, timeStamp):
    try:
        print(f"canceling order")
        cancel_order = client.futures_cancel_order(symbol=ticker, timestamp=timeStamp)
        print("CANCEL ORDER OK")
    except Exception as e:
        print("an exception occurred - {}".format(e))
        return False
    return True

def receive_order(order_type, order_action, quantity, ticker, order_id, timeStamp):
    if order_id in ["Enter Long", "Enter Short"]:
        # Place a new order
        return place_order(order_type, order_action, quantity, ticker, timeStamp)
    elif order_id in ["Exit Long", "Exit Short"]:
        # Cancel an existing order
        return cancel_order(ticker, timeStamp)
    else:
        print("Invalid order_id")
        return False

@app.route('/')
def welcome():
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    data = json.loads(request.data)

    # Validate the required fields in the JSON payload
    required_fields = ['passphrase', 'ticker', 'time']
    if not all(field in data for field in required_fields):
        return {
            "code": "error",
            "message": "Missing required fields"
        }, 400

    if data['passphrase'] != config.WEBHOOK_PASSPHRASE:
        return {
            "code": "error",
            "message": "Invalid passphrase"
        }, 401

    order_id = data['strategy']['order_id']

    # Open or close a position
    if order_id in ["Enter Long", "Enter Short"]:

        balances = client.futures_account_balance()
        leverage = 30 # As set in the binance trading platform
        percent_of_equity = 0.75

        for item in balances:
            asset = item['asset']
            balance = item['balance']
            if float(balance) > 0:
                print(f"Asset: {asset}, Balance: {balance}")
        # Invest 75% of available funds at 30 times leverage
        quantity = round((round(float(balance), 3) / round(float(data['strategy']['order_price']), 3)) * 30 * 0.75, 3)
        print(f"{quantity}")
        order_type = FUTURE_ORDER_TYPE_MARKET
        order_id = data['strategy']['order_id']
        order_action = data['strategy']['order_action']
        ticker = data['ticker']
        server_time = client.get_server_time()
        timeStamp = int(server_time['serverTime'])
        #timeStamp = data['bar']['time']
        if order_action not in ["buy", "sell"]:
            return {
                "code": "error",
                "message": "Invalid order action"
                }, 400
        order_action = "BUY" if order_action == "buy" else "SELL"

        receive_order(order_type, order_action, quantity, ticker, order_id, timeStamp)
        return {
            "code": "success",
            "message": "order executed"
        }
    elif order_id in ["Exit Long", "Exit Short"]:
        order_id = data['strategy']['order_id']
        order_action = data['strategy']['order_action']
        ticker = data['ticker']
        server_time = client.get_server_time()
        timeStamp = int(server_time['serverTime'])
        #timeStamp = data['bar']['time']
        if order_action not in ["buy", "sell"]:
            return {
                "code": "error",
                "message": "Invalid order action"
                }, 400
        order_action = "BUY" if order_action == "buy" else "SELL"

        receive_order('', order_action, '', ticker, order_id, timeStamp)
        return {
            "code": "success",
            "message": "cancel order executed"
        }
    else:
        return {
            "code": "error",
            "message": "Invalid order action"
        }, 400
