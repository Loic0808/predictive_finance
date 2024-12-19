from alpaca.data.live import StockDataStream

api_key = "PKAG0XBVFXJPXPXBWPGW"
secret_key = "pjp69zCQBSUziTzXEjZ9DagW04sni7Jg99QKH6TH"

wss_client = StockDataStream(api_key, secret_key)

# async handler
async def quote_data_handler(data):
    # quote data will arrive here
    print(data)

wss_client.subscribe_quotes(quote_data_handler, "SPY")

# Doesn't work when market is closed
wss_client.run()