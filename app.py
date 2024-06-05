import json
import logging
from time import sleep
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import FUTURE_ORDER_TYPE_LIMIT, FUTURE_ORDER_TYPE_TAKE_PROFIT, FUTURE_ORDER_TYPE_TRAILING_STOP_MARKET
from binance.exceptions import BinanceAPIException
import config

app = Flask(__name__)

client = Client(config.API_KEY, config.API_SECRET, tld='com')

MIN_NOTIONAL = 100  # Minimum notional value required by Binance

# Configure logging
logging.basicConfig(filename='trades.log', level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

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
    try:
        info = client.get_symbol_info(ticker)
        tick_size = float(next(filter['tickSize'] for filter in info['filters'] if filter['filterType'] == 'PRICE_FILTER'))
        adjusted_price = round(price / tick_size) * tick_size
        logging.info(f"Original price: {price}, Adjusted price: {adjusted_price}, Tick size: {tick_size}")
        return adjusted_price
    except Exception as e:
        logging.error(f"Error adjusting price: {str(e)}")
        raise

def get_available_margin():
    try:
        account_info = client.futures_account()
        for asset in account_info['assets']:
            if asset['asset'] == "USDT":
                return float(asset['availableBalance'])
        return 0
    except BinanceAPIException as e:
        logging.error(f"Error fetching margin: {str(e)}")
        return 0

def create_order(ticker, action, order_type, quantity, price=None, stop_price=None, callback_rate=None):
    try:
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
        if callback_rate:
            order_params["callbackRate"] = callback_rate
        order_response = client.futures_create_order(**order_params)
        logging.info(f"Order executed: {order_response}")
        return order_response
    except BinanceAPIException as e:
        logging.error(f"Error creating order: {str(e)}")
        raise

def check_order_status(symbol, order_id):
    try:
        order = client.futures_get_order(symbol=symbol, orderId=order_id)
        return order['status']
    except BinanceAPIException as e:
        logging.error(f"Error checking order status: {str(e)}")
        raise

@app.route('/webhook', methods=['POST'])
def webhook():
    data = json.loads(request.data)
    validation_error = validate_request_data(data)
    if validation_error:
        return jsonify(validation_error)

    order_id = data['strategy']['order_id']
    order_action = data['strategy']['order_action'].upper()
    ticker = data['ticker']
    order_price = data['bar']['order_price']
    adjusted_price = get_adjusted_price(ticker, float(order_price))
    leverage = data['leverage']
    percent_of_equity = data['percent_of_equity']
    roi_target = data['roi_target'] / 100  # Convert percentage to decimal
    trailing_stop_percentage = data.get('trailing_stop_percentage')  # Get trailing stop percentage if provided

    logging.info(f"Received request: {data}")
    logging.info(f"Adjusted price: {adjusted_price}")
    logging.info(f"Leverage: {leverage}")
    logging.info(f"Percent of equity: {percent_of_equity}")
    logging.info(f"ROI target: {roi_target}")
    logging.info(f"Trailing stop percentage: {trailing_stop_percentage}")

    try:
        if order_id in ["Enter Long", "Enter Short"]:
            available_margin = get_available_margin()
            if available_margin <= 0:
                return jsonify({
                    "code": "error",
                    "message": "Insufficient margin available"
                }), 400

            client.futures_change_leverage(symbol=ticker, leverage=leverage)

            quantity = round(available_margin * leverage * percent_of_equity / adjusted_price, 3)
            notional_value = quantity * adjusted_price
            if notional_value < MIN_NOTIONAL:
                return jsonify({
                    "code": "error",
                    "message": f"Order's notional value ({notional_value}) is below the minimum required value ({MIN_NOTIONAL})"
                }), 400

            initial_margin_required = notional_value / leverage
            if initial_margin_required > available_margin:
                return jsonify({
                    "code": "error",
                    "message": f"Insufficient margin. Required: {initial_margin_required}, Available: {available_margin}"
                }), 400

            if order_action not in ["BUY", "SELL"]:
                return jsonify({
                    "code": "error",
                    "message": "Invalid order action"
                }), 400

            main_order = create_order(ticker, order_action, FUTURE_ORDER_TYPE_LIMIT, quantity, adjusted_price)

            while True:
                status = check_order_status(ticker, main_order['orderId'])
                if status == 'FILLED':
                    initial_margin = (adjusted_price * quantity) / leverage
                    initial_margin = get_adjusted_price(ticker, initial_margin)  # Ensure initial margin is adjusted
                    target_profit = initial_margin * roi_target
                    target_profit = get_adjusted_price(ticker, target_profit)  # Ensure target profit is adjusted
                    if order_action == "BUY":
                        take_profit_price = adjusted_price + (target_profit / quantity)
                    else:
                        take_profit_price = adjusted_price - (target_profit / quantity)
                    take_profit_price = get_adjusted_price(ticker, take_profit_price)

                    logging.info(f"Take profit price calculation: initial_margin={initial_margin}, target_profit={target_profit}, take_profit_price={take_profit_price}")

                    create_order(ticker, "SELL" if order_action == "BUY" else "BUY", FUTURE_ORDER_TYPE_LIMIT, quantity, take_profit_price)

                    if trailing_stop_percentage:
                        logging.info(f"Creating trailing stop order with callback rate: {trailing_stop_percentage}")
                        create_order(
                            ticker,
                            "SELL" if order_action == "BUY" else "BUY",
                            FUTURE_ORDER_TYPE_TRAILING_STOP_MARKET,
                            quantity,
                            callback_rate=trailing_stop_percentage
                        )

                    break
                elif status in ['CANCELED', 'REJECTED', 'EXPIRED']:
                    logging.info(f"Order {main_order['orderId']} status: {status}")
                    break
                sleep(1)  # Wait for 1 second before checking again

            return jsonify({
                "code": "success",
                "message": "Enter trade order executed"
            }), 200

        elif order_id in ["Exit Long", "Exit Short"]:
            positions = client.futures_account()
            position = next((pos for pos in positions['positions'] if pos['symbol'] == ticker), None)
            if not position or float(position['positionAmt']) == 0:
                return jsonify({
                    "code": "error",
                    "message": "Empty balance"
                }), 400

            quantity = abs(float(position['positionAmt']))
            notional_value = quantity * adjusted_price
            if notional_value < MIN_NOTIONAL:
                return jsonify({
                    "code": "error",
                    "message": f"Order's notional value ({notional_value}) is below the minimum required value ({MIN_NOTIONAL})"
                }), 400

            if order_action not in ["BUY", "SELL"]:
                return jsonify({
                    "code": "error",
                    "message": "Invalid order action"
                }), 400

            create_order(ticker, order_action, FUTURE_ORDER_TYPE_LIMIT, quantity, adjusted_price)

            return jsonify({
                "code": "success",
                "message": "Exit trade order executed"
            }), 200

        else:
            return jsonify({
                "code": "error",
                "message": "Invalid order action"
            }), 400

    except BinanceAPIException as e:
        logging.error(f"Error during order processing: {str(e)}")
        return jsonify({
            "code": "error",
            "message": str(e)
        }), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
