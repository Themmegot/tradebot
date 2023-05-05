import json, config
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import *

app = Flask(__name__)

client = Client(config.API_KEY, config.API_SECRET, tld='com')

@app.route('/')
def welcome():
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    data = json.loads(request.data)

    order_type = FUTURE_ORDER_TYPE_MARKET
    #order_type = FUTURE_ORDER_TYPE_LIMIT
    order_id = data['strategy']['order_id']
    order_action = data['strategy']['order_action']
    order_price= data['bar']['order_price']
    #order_price= data['strategy']['order_price']
 
    ticker = data['ticker']
    server_time = client.get_server_time()
    timeStamp = int(server_time['serverTime'])

    # Validate the required fields in the JSON payload
    required_fields = ['passphrase', 'ticker']
    if not all(field in data for field in required_fields):
        return {
            "code": "error",
            "message": "Missing required fields"
        }, 400

    # Validate the passphrase in the config.py file
    if data['passphrase'] != config.WEBHOOK_PASSPHRASE:
        return {
            "code": "error",
            "message": "Invalid passphrase"
        }, 401

    # Enter a long or short position
    if order_id in ["Enter Long", "Enter Short"]:
        print("----------------------")        
        print(f"   {order_id} TRADE")
        print("----------------------")

        # Fetch the balance from the futures account
        balances = client.futures_account_balance()
        leverage = 20 # As set in the binance trading platform
        #leverage = float(data['leverage'])
        #client.futures_change_leverage(symbol=symbol, leverage=leverage)
        percent_of_equity = 0.75 # Do not trade with 100%, you will get reckd!
        #percent_of_equity = float(data['percent_of_equity'])
        take_profit_percent = 1.05  # 5% take profit target
        #take_profit_percent = data['take_profit_percent']

        for item in balances:
            if item['asset'] == "BUSD":
                asset = item['asset']
                balance = item['balance']
                print(f"Asset: {asset}, Balance: {balance}" )
                if float(balance) > 0:
                    #quantity = round((round(float(balance), 3) / round(float(data['strategy']['order_price']), 3)) * leverage * percent_of_equity, 3)
                    quantity = round((round(float(balance), 3) / round(float(data['bar']['order_price']), 3)) * leverage * percent_of_equity, 3)
                else:
                    return {
                        "code": "error",
                        "message": "Empty balance"
                    }, 400

        # If the order action is neither buy or sell, fail the order
        if order_action not in ["buy", "sell"]:
            return {
                "code": "error",
                "message": "Invalid order action"
                }, 400
        # The alerts create the order action in small caps. This makes sure it is in large caps 
        order_action = "BUY" if order_action == "buy" else "SELL"

        # Execute the order
        print(f"{order_id} - {order_action} {quantity} {data['ticker']} @ {order_price}")
        client.futures_create_order(symbol=ticker, side=order_action, type=order_type, quantity=quantity, timestamp=timeStamp)
        #client.futures_create_order(symbol=ticker, side=order_action, type=order_type, timeInForce=TIME_IN_FORCE_GTC, quantity=quantity, timestamp=timeStamp, price=order_price)

        # Create the take-profit order
        # Calculate the take profit based on the position direction
        if order_id == "Enter Long":
            take_profit_price = round(float(order_price) * (1 + take_profit_percent / 100), 2)
            #client.futures_create_order(symbol=ticker, side="SELL" if order_action == "BUY" else "BUY", type=FUTURE_ORDER_TYPE_LIMIT, quantity=quantity, price=take_profit_price, timeInForce=TIME_IN_FORCE_GTC, reduceOnly=True)
            print(f"Profit Price {take_profit_price} / Order Price: {order_price}")
        elif order_id == "Enter Short":
            take_profit_price = round(float(order_price) * (1 - take_profit_percent / 100), 2)
            #client.futures_create_order(symbol=ticker, side="SELL" if order_action == "BUY" else "BUY", type=FUTURE_ORDER_TYPE_LIMIT, quantity=quantity, price=take_profit_price, timeInForce=TIME_IN_FORCE_GTC, reduceOnly=True)
            print(f"Profit Price {take_profit_price} / Order Price: {order_price}")
        else:
            return {
                "code": "error",
                "message": "Invalid position direction"
            }, 400

        return {
            "code": "success",
            "message": "Open order executed"
        }, 200
    
    # Exit a long or short position
    elif order_id in ["Exit Long", "Exit Short"]:
        print("----------------------")        
        print(f"   {order_id} TRADE")
        print("----------------------")

        # Fetch the balance from the futures account
 
        positions = client.futures_account()

        for position in positions['positions']: 
            if position['symbol'] == data['ticker']:
                balance = abs(float(position['positionAmt']))
                asset = position['symbol']
                print(f"Asset: {asset}, Balance: {balance}" )
                if float(balance) > 0:
                    quantity = balance
                else:
                    return {
                        "code": "error",
                        "message": "Empty balance"
                    }, 400

        # If the order action is neither buy or sell, fail the order        
        if order_action not in ["buy", "sell"]:
            return {
                "code": "error",
                "message": "Invalid order action"
            }, 400
        
        # The alerts create the order action in small caps. This makes sure it is in large caps
        order_action = "BUY" if order_action == "buy" else "SELL"
        # Execute the order
        print(f"{order_id} - {order_action} {quantity} {data['ticker']} @ {order_price}")
        #client.futures_create_order(symbol=ticker, side=order_action, type=order_type, quantity=quantity, timestamp=timeStamp)
        client.futures_create_order(symbol=ticker, side=order_action, type=order_type, timeInForce=TIME_IN_FORCE_GTC, quantity=quantity, timestamp=timeStamp, price=order_price)
        return {
            "code": "success",
            "message": "Exit order executed"
        }, 200
    else:
        return {
            "code": "error",
            "message": "Invalid order action"
        }, 400
      
  
