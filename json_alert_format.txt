Close Long
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

Close Short
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

Open Long
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


Open Short
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
