from flask import Flask, render_template, request, jsonify
from binance.client import Client
import pandas as pd
import threading
import time

app = Flask(__name__)

# Load API Keys from environment variables
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
client = Client(API_KEY, API_SECRET)

# Bot State
bot_running = False
trade_logs = []

def get_price(symbol="BTCUSDT"):
    """Fetch live price of a crypto asset."""
    ticker = client.get_symbol_ticker(symbol=symbol)
    return float(ticker["price"])

def get_historical_prices(symbol="BTCUSDT", interval="1h", limit=50):
    """Fetch historical price data."""
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=["time", "open", "high", "low", "close", "volume", "_", "_", "_", "_", "_", "_"])
    df["close"] = df["close"].astype(float)
    return df

def calculate_sma(df, short_window=5, long_window=20):
    """Calculate moving averages."""
    df["SMA_Short"] = df["close"].rolling(window=short_window).mean()
    df["SMA_Long"] = df["close"].rolling(window=long_window).mean()
    return df

def trading_bot(symbol="BTCUSDT"):
    """Trading strategy with moving average crossover."""
    global bot_running

    while bot_running:
        data = get_historical_prices(symbol)
        data = calculate_sma(data)
        last_row = data.iloc[-1]

        if last_row["SMA_Short"] > last_row["SMA_Long"]:
            action = "BUY"
        elif last_row["SMA_Short"] < last_row["SMA_Long"]:
            action = "SELL"
        else:
            action = "HOLD"

        trade_logs.append(f"{symbol}: {action} at ${get_price()}")

        time.sleep(3600)  # Run every hour

@app.route("/")
def index():
    """Render the homepage."""
    price = get_price()
    return render_template("index.html", price=price, logs=trade_logs)

@app.route("/start", methods=["POST"])
def start_bot():
    """Start the trading bot."""
    global bot_running
    if not bot_running:
        bot_running = True
        thread = threading.Thread(target=trading_bot)
        thread.start()
    return jsonify({"status": "Bot started!"})

@app.route("/stop", methods=["POST"])
def stop_bot():
    """Stop the trading bot."""
    global bot_running
    bot_running = False
    return jsonify({"status": "Bot stopped!"})

if __name__ == "__main__":
    app.run(debug=True)
