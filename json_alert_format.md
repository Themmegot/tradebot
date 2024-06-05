# Explanation of the JSON fields:
passphrase: The webhook passphrase for validation.
strategy: Contains the order details.
order_id: Specifies the action, here "Enter Long" to enter a long position.
order_action: The order action, here "BUY" for a long position.
ticker: The symbol for the trading pair, here "BTCUSDT".
leverage: The leverage to be used for the trade.
percent_of_equity: The percentage of available equity to be used for the trade.
bar: Contains the price details.
order_price: The price at which to enter the long position, here 71050.
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
