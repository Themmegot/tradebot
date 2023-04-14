import json, config
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import *

app = Flask(__name__)

client = Client(config.API_KEY, config.API_SECRET, tld='com')

def adjust_leverage(symbol, client):
    client.futures_change_leverage(symbol=symbol, leverage=15)

def adjust_margintype(symbol, client):
    client.futures_change_margin_type(symbol=symbol, marginType='CROSSED')

def my_execute_order(order_type, side, quantity, symbol, order_id, timeStamp):
    if order_id == 'Open':
        # Place a new order
        try:
            print(f"sending order {order_type} - {side} {quantity} {symbol}")
            order = client.futures_create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
            print("BUY ORDER OK")
        except Exception as e:
            print("an exception occured - {}".format(e))
            return False
        return order
    elif order_id == 'Close':
        # Cancel an existing order
        try:
            print(f"canceling order {symbol} - {order_id}")
            cancel_order = client.futures_cancel_order(symbol=symbol, timestamp=timeStamp)
            print("CANCEL ORDER OK")
        except Exception as e:
            print("an exception occured - {}".format(e))
            return False
        return cancel_order

@app.route('/')
def welcome():
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    data = json.loads(request.data)

    # Validate the required fields in the JSON payload
    required_fields = ['passphrase', 'side', 'quantity', 'ticker', 'action', 'time']
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

    order_action = data['action']

    # Open or close a position
    if order_action in ["Open Short", "Open Long"]:
        order_type = FUTURE_ORDER_TYPE_MARKET
        side = data['side'].upper()
        quantity = data['quantity']
        ticker = data['ticker']
        timeStamp = data['time']
        order_id = data['order_id']
        my_execute_order(order_type, side, quantity, ticker, '', '')
        return {
            "code": "success",
            "message": "order executed"
        }
    elif order_action in ["Close Short", "Close Long"]:
        ticker = data['ticker']
        timeStamp = data['time']
        order_id = data['order_id']
        my_execute_order('', '', '', ticker, '', timeStamp)
        return {
            "code": "success",
            "message": "cancel order executed"
        }
    else:
        return {
            "code": "error",
            "message": "Invalid order action"
        }, 400
