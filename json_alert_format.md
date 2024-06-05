# Explanation of the JSON fields:

passphrase: The webhook passphrase for validation. Replace "your passphrase" with your actual webhook passphrase defined in your config.py

strategy: Contains the order details.

order_id: Specifies the action
	Enter Long, Exit Long, Enter Short, Exit Short

order_action: The order action
	buy or sell

ticker: The symbol for the trading pair.

leverage: The leverage to be used for the trade.

percent_of_equity: The percentage of available equity to be used for the trade.

order_price: The price at which to enter the long position, received from the alert

take_profit_percent: Optional. The percentage of profit at which to take profit. 

stop_loss_percent: Optional. The percentage at which to set the stop loss. 

trailing_stop_percentage: Optional. The percentage for the trailing stop.

# Open Long - example
{
    "passphrase": "your_webhook_passphrase",
    "strategy": {
        "order_id": "Enter Long",
        "order_action": "BUY"
    },
    "ticker": "BTCUSDT",
    "leverage": 10,
    "percent_of_equity": 0.25,
    "bar": {
        "order_price": "{{close}}"
    },
    "take_profit_percent": 25,  
    "stop_loss_percent": 15,    
    "trailing_stop_percentage": 0.5  
}

# Close Long - example
{
    "passphrase": "your_webhook_passphrase",
    "strategy": {
        "order_id": "Exit Long",
        "order_action": "SELL"
    },
    "ticker": "BTCUSDT",
    "leverage": 10,
    "percent_of_equity": 0.25,
    "bar": {
        "order_price": "{{close}}"
    },
    "take_profit_percent": 25,  
    "stop_loss_percent": 15,    
    "trailing_stop_percentage": 0.5  
}

# Open Short - example
{
    "passphrase": "your_webhook_passphrase",
    "strategy": {
        "order_id": "Enter Short",
        "order_action": "SELL"
    },
    "ticker": "BTCUSDT",
    "leverage": 10,
    "percent_of_equity": 0.25,
    "bar": {
        "order_price": "{{close}}"
    },
    "take_profit_percent": 25,  
    "stop_loss_percent": 15,    
    "trailing_stop_percentage": 0.5  
}

# Close Short - example
{
    "passphrase": "your_webhook_passphrase",
    "strategy": {
        "order_id": "Exit Short",
        "order_action": "BUY"
    },
    "ticker": "BTCUSDT",
    "leverage": 10,
    "percent_of_equity": 0.25,
    "bar": {
        "order_price": "{{close}}"
    },
    "take_profit_percent": 25,  
    "stop_loss_percent": 15,    
    "trailing_stop_percentage": 0.5  
}

