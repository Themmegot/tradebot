import json
from time import sleep
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import FUTURE_ORDER_TYPE_LIMIT, FUTURE_ORDER_TYPE_TAKE_PROFIT
from binance.exceptions import BinanceAPIException
import config

app = Flask(__name__)

client = Client(config.API_KEY, config.API_SECRET, tld='com')

MIN_NOTIONAL = 100  # Minimum notional value required by Binance

@app.route('/')
def welcome():
    return render_template('index.html')

def validate_request_data(data):
    required_fields = ['passphrase', 'ticker', 'leverage', 'percent_of_equity', 'roi_target']
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
    return None

def get_adjusted_price(ticker, price):
    info = client.get_symbol_info(ticker)
    tick_size = next(filter['tickSize'] for filter in info['filters'] if filter['filterType'] == 'PRICE_FILTER')
    return round(float(price) / float(tick_size)) * float(tick_size)

def get_available_margin():
    account_info = client.futures_account()
    for asset in account_info['assets']:
        if asset['asset'] == "USDT":
            return float(asset['availableBalance'])
    return 0

def create_order(ticker, action, order_type, quantity, price=None, stop_price=None):
    server_time = client.get_server_time()
    time_stamp = int(server_time['serverTime'])
    order_params = {
        "symbol": ticker,
        "side": action,
        "type": order_type,
        "quantity": quantity,
        "timestamp": time_stamp
    }
    if price:
        order_params["price"] = price
        order_params["timeInForce"] = "GTC"
    if stop_price:
        order_params["stopPrice"] = stop_price
        order_params["type"] = FUTURE_ORDER_TYPE_TAKE_PROFIT
    order_response = client.futures_create_order(**order_params)
    print(f"Order executed: {order_response}")
    return order_response

def check_order_status(symbol, order_id):
    order = client.futures_get_order(symbol=symbol, orderId=order_id)
    return order['status']

@app.route('/webhook', methods=['POST'])
def webhook():
    data = json.loads(request.data)
    validation_error = validate_request_data(data)
    if validation_error:
        return validation_error

    order_id = data['strategy']['order_id']
    order_action = data['strategy']['order_action'].upper()
    ticker = data['ticker']
    order_price = data['bar']['order_price']
    adjusted_price = get_adjusted_price(ticker, order_price)
    leverage = data['leverage']
    percent_of_equity = data['percent_of_equity']
    roi_target = data['roi_target'] / 100  # Convert percentage to decimal

    print(f"Received request: {data}")
    print(f"Adjusted price: {adjusted_price}")
    print(f"Leverage: {leverage}")
    print(f"Percent of equity: {percent_of_equity}")
    print(f"ROI target: {roi_target}")

    if order_id in ["Enter Long", "Enter Short"]:
        available_margin = get_available_margin()
        print(f"Available margin: {available_margin}")
        if available_margin <= 0:
            return {
                "code": "error",
                "message": "Insufficient margin available"
            }, 400

        # Adjust leverage
        client.futures_change_leverage(symbol=ticker, leverage=leverage)

        quantity = round(available_margin * leverage * percent_of_equity / adjusted_price, 3)
        print(f"Calculated quantity: {quantity}")

        # Check if the order's notional value meets the minimum requirement
        notional_value = quantity * adjusted_price
        print(f"Notional value: {notional_value}")
        if notional_value < MIN_NOTIONAL:
            return {
                "code": "error",
                "message": f"Order's notional value ({notional_value}) is below the minimum required value ({MIN_NOTIONAL})"
            }, 400

        # Check if the margin is sufficient
        initial_margin_required = notional_value / leverage
        print(f"Initial margin required: {initial_margin_required}")
        if initial_margin_required > available_margin:
            return {
                "code": "error",
                "message": f"Insufficient margin. Required: {initial_margin_required}, Available: {available_margin}"
            }, 400

        if order_action not in ["BUY", "SELL"]:
            return {
                "code": "error",
                "message": "Invalid order action"
            }, 400

        print(f"{order_id} - {order_action} {quantity} {ticker} @ {adjusted_price}")
        try:
            main_order = create_order(ticker, order_action, FUTURE_ORDER_TYPE_LIMIT, quantity, adjusted_price)
        except BinanceAPIException as e:
            print(f"Error creating main order: {str(e)}")
            return {
                "code": "error",
                "message": str(e)
            }, 400

        # Check the status of the main order
        while True:
            status = check_order_status(ticker, main_order['orderId'])
            print(f"Order status: {status}")
            if status == 'FILLED':
                # Calculate take profit price based on the margin used for the initial investment
                initial_margin = (adjusted_price * quantity) / leverage
                target_profit = initial_margin * roi_target
                if order_action == "BUY":
                    take_profit_price = adjusted_price + (target_profit / quantity)
                else:
                    take_profit_price = adjusted_price - (target_profit / quantity)
                take_profit_price = get_adjusted_price(ticker, take_profit_price)  # Adjust take profit price by tick size

                print(f"Take profit price: {take_profit_price}")
                try:
                    create_order(ticker, "SELL" if order_action == "BUY" else "BUY", FUTURE_ORDER_TYPE_LIMIT, quantity, take_profit_price)
                except BinanceAPIException as e:
                    print(f"Error creating take profit order: {str(e)}")
                    return {
                        "code": "error",
                        "message": str(e)
                    }, 400
                break
            elif status in ['CANCELED', 'REJECTED', 'EXPIRED']:
                print(f"Order {main_order['orderId']} status: {status}")
                break
            sleep(1)  # Wait for 1 second before checking again

        return {
            "code": "success",
            "message": "Enter trade order executed"
        }, 200

    elif order_id in ["Exit Long", "Exit Short"]:
        positions = client.futures_account()
        position = next((pos for pos in positions['positions'] if pos['symbol'] == ticker), None)
        if not position or float(position['positionAmt']) == 0:
            return {
                "code": "error",
                "message": "Empty balance"
            }, 400

        quantity = abs(float(position['positionAmt']))

        # Check if the order's notional value meets the minimum requirement
        notional_value = quantity * adjusted_price
        if notional_value < MIN_NOTIONAL:
            return {
                "code": "error",
                "message": f"Order's notional value ({notional_value}) is below the minimum required value ({MIN_NOTIONAL})"
            }, 400

        if order_action not in ["BUY", "SELL"]:
            return {
                "code": "error",
                "message": "Invalid order action"
            }, 400

        print(f"{order_id} - {order_action} {quantity} {ticker}")
        try:
            create_order(ticker, order_action, FUTURE_ORDER_TYPE_LIMIT, quantity, adjusted_price)
        except BinanceAPIException as e:
            print(f"Error creating exit order: {str(e)}")
            return {
                "code": "error",
                "message": str(e)
            }, 400

        return {
            "code": "success",
            "message": "Exit trade order executed"
        }, 200

    else:
        return {
            "code": "error",
            "message": "Invalid order action"
        }, 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
