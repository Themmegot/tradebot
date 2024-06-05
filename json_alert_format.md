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

# Close Long
{
	"passphrase": "<your passphrase>",
	"ticker": "BTCBUSD",
	"leverage": 30,
	"percent_of_equity": 0.75,
	"roi_target": 1.05,
	"bar": {
		"order_price": "{{close}}"
	},
    "strategy": {
        "order_id": "Exit Long",
		"order_action": "sell"
    }
}

# Close Short
{
	"passphrase": "<your passphrase>",
	"ticker": "BTCBUSD",
	"leverage": 30,
	"percent_of_equity": 0.75,
	"roi_target": 1.05,
	"bar": {
		"order_price": "{{close}}"
	},
    "strategy": {
        "order_id": "Exit Short",
		"order_action": "buy"
    }
}

# Open Long
{
	"passphrase": "<your passphrase>",
	"ticker": "BTCBUSD",
	"leverage": 30,
	"percent_of_equity": 0.75,
	"roi_target": 1.05,
	"bar": {
		"order_price": "{{close}}"
	},
    "strategy": {
        "order_id": "Enter Long",
		"order_action": "buy"
    }
}


# Open Short
{
	"passphrase": "<your passphrase>",
	"ticker": "BTCBUSD",
	"leverage": 30,
	"percent_of_equity": 0.75,
	"roi_target": 1.05,
	"bar": {
		"order_price": "{{close}}"
	},
    "strategy": {
        "order_id": "Enter Short",
		"order_action": "sell"
    }
}
