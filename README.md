# tradebot
Using binance python api to create buy and sell futures orders

usage: 

export FLASK_ENV=developement
export FLASK_DEBUG=on

then

flask run --host=0.0.0.0 --port=5000

The bot is tailored to use the tradingview indicator "Machine Learning: Lorentzian Classification" by jdehorty and takes alerts from Open Long, Open Short, Close Long and Close Short. The bot also needs a alert json crafted to contain passphrase, quantity, side and ticker as well as the rest needed to perform a trade. Check the alert_json_format.txt file for specifics.


It is an iteration of:

TradingView Strategy Alert Webhook that buys and sells crypto with the Binance API

YouTube tutorial on how to use this code
https://www.youtube.com/watch?v=gMRee2srpe8
