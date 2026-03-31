# from flask import Flask, request
# from threading import Thread
# import time
# import datetime
# import json
# import requests
# import os
# import pandas as pd
# import ta

# STATE_FILE = "state.json"

# # ---------------------------
# # Config
# # ---------------------------
# TOKEN = "8689386667:AAFhazRA-tWJK4_h5q7mlTNp5Z0J_gviGYk"
# CHAT_ID = "8006267074"
# SYMBOL = "BTC-USDT"
# RANGE = 300  # Range threshold

# alerts_list = []
# last_price = 0.0
# last_time = ""

# # ---------------------------
# # Load & Save state
# # ---------------------------
# def save_state():
#     global last_price, last_time, alerts_list
#     try:
#         with open(STATE_FILE, "w") as f:
#             json.dump({
#                 "last_price": last_price,
#                 "last_time": last_time,
#                 "alerts_list": alerts_list
#             }, f)
#     except Exception as e:
#         print("State save error:", e)

# def load_state():
#     global last_price, last_time, alerts_list
#     try:
#         with open(STATE_FILE, "r") as f:
#             data = json.load(f)
#             last_price = data.get("last_price", 0.0)
#             last_time = data.get("last_time", "")
#             alerts_list = data.get("alerts_list", [])
#     except:
#         print("No previous state found.")

# load_state()

# # ---------------------------
# # Telegram
# # ---------------------------
# def send_telegram(message):
#     url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
#     try:
#         requests.post(url, data={"chat_id": CHAT_ID, "text": message}, timeout=10)
#     except Exception as e:
#         print("Telegram error:", e)

# # ---------------------------
# # Flask App
# # ---------------------------
# app = Flask(__name__)

# @app.route("/")
# def home():
#     alerts_html = "<br>".join(alerts_list[-10:][::-1])
#     return f"""
#     <h2>Crypto Bot Dashboard</h2>
#     <p><b>Symbol:</b> {SYMBOL}</p>
#     <p><b>Current Price:</b> {last_price}</p>
#     <p><b>Last Updated:</b> {last_time}</p>
#     <h3>Last Alerts:</h3>
#     <p>{alerts_html}</p>
#     """

# # ---------------------------
# # TradingView Webhook
# # ---------------------------
# @app.route("/tv-webhook", methods=["POST"])
# def tradingview_webhook():
#     global last_price, last_time, alerts_list

#     data = request.json
#     if not data:
#         return "No data received", 400

#     action = data.get("action")
#     price = data.get("price", 0.0)
#     symbol = data.get("symbol", SYMBOL)

#     last_price = price
#     last_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#     if action == "BUY":
#         msg = f"📈 TRADINGVIEW UP | {symbol} | {price}"
#     elif action == "SELL":
#         msg = f"📉 TRADINGVIEW DOWN | {symbol} | {price}"
#     else:
#         msg = f"⏸ TRADINGVIEW NO SIGNAL | {symbol} | {price}"

#     print(msg)
#     send_telegram(msg)

#     alerts_list.append(msg)
#     if len(alerts_list) > 50:
#         alerts_list = alerts_list[-50:]
#     save_state()

#     return "ok", 200

# # ---------------------------
# # Range Logic
# # ---------------------------
# def get_ohlc():
#     try:
#         url = f"https://api.kucoin.com/api/v1/market/candles?type=15min&symbol={SYMBOL}"
#         response = requests.get(url, timeout=10)
#         if response.status_code != 200:
#             print("KuCoin error:", response.text)
#             return None

#         data = response.json()
#         if "data" not in data:
#             print("Invalid response:", data)
#             return None

#         candles = data["data"]
#         df = pd.DataFrame(candles, columns=["time","open","close","high","low","volume","turnover"])

#         for col in ["open","close","high","low"]:
#             df[col] = df[col].astype(float)

#         df = df.iloc[::-1].reset_index(drop=True)
#         return df

#     except Exception as e:
#         print("Fetch OHLC error:", e)
#         return None


# def check_range_alert():
#     global last_price

#     df = get_ohlc()
#     if df is None or len(df) < 20:
#         return "NONE", last_price

#     # ✅ APPLY OFFSET TO PRICE (FIX)
#     price_now = df["close"].iloc[-1] - 200
#     price_60min_ago = df["close"].iloc[-5] - 200

#     slope = (price_now - price_60min_ago) / 4

#     atr = ta.volatility.AverageTrueRange(
#         high=df["high"],
#         low=df["low"],
#         close=df["close"],
#         window=14
#     ).average_true_range().iloc[-1]

#     vol_factor = atr * 0.5

#     ema20 = ta.trend.EMAIndicator(df["close"], 20).ema_indicator()
#     direction = 1 if ema20.iloc[-1] > ema20.iloc[-5] else -1

#     predicted = price_now + slope + direction * vol_factor

#     if predicted >= price_now + RANGE:
#         return "BET-UP", df["close"].iloc[-1]  # return real price
#     elif predicted <= price_now - RANGE:
#         return "BET-DOWN", df["close"].iloc[-1]
#     else:
#         return "NONE", df["close"].iloc[-1]


# def run_range_bot():
#     global last_price, last_time, alerts_list

#     last_status = None

#     while True:
#         try:
#             status, price = check_range_alert()

#             last_price = price
#             last_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#             if status != last_status:
#                 if status == "BET-UP":
#                     msg = f"📈 RANGE UP | {SYMBOL} | {price}"
#                 elif status == "BET-DOWN":
#                     msg = f"📉 RANGE DOWN | {SYMBOL} | {price}"
#                 else:
#                     msg = f"⏸ RANGE NO SIGNAL | {SYMBOL} | {price}"

#                 print(msg)
#                 send_telegram(msg)

#                 alerts_list.append(msg)
#                 if len(alerts_list) > 50:
#                     alerts_list = alerts_list[-50:]

#                 save_state()
#                 last_status = status

#             time.sleep(30)

#         except Exception as e:
#             print("Range bot error:", e)
#             time.sleep(60)


# # ---------------------------
# # Run Services
# # ---------------------------
# if __name__ == "__main__":
#     Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))).start()
#     Thread(target=run_range_bot).start()

from flask import Flask, request
from threading import Thread
import time
import datetime
import json
import requests
import os
import pandas as pd
import ta

STATE_FILE = "state.json"

# ---------------------------
# Config
# ---------------------------
TOKEN = "8689386667:AAFhazRA-tWJK4_h5q7mlTNp5Z0J_gviGYk"
CHAT_ID = "8006267074"
SYMBOL = "BTC-USDT"
RANGE = 300

alerts_list = []
prediction_history = []

last_price = 0.0
last_time = ""

# ---------------------------
# Load & Save state
# ---------------------------
def save_state():
    global last_price, last_time, alerts_list, prediction_history
    try:
        with open(STATE_FILE, "w") as f:
            json.dump({
                "last_price": last_price,
                "last_time": last_time,
                "alerts_list": alerts_list,
                "prediction_history": prediction_history
            }, f, default=str)
    except Exception as e:
        print("State save error:", e)


def load_state():
    global last_price, last_time, alerts_list, prediction_history
    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
            last_price = data.get("last_price", 0.0)
            last_time = data.get("last_time", "")
            alerts_list = data.get("alerts_list", [])
            prediction_history = data.get("prediction_history", [])
    except:
        print("No previous state found.")


load_state()

# ---------------------------
# Telegram
# ---------------------------
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message}, timeout=10)
    except Exception as e:
        print("Telegram error:", e)

# ---------------------------
# Flask App
# ---------------------------
app = Flask(__name__)

@app.route("/")
def home():
    alerts_html = "<br>".join(alerts_list[-10:][::-1])
    accuracy = calculate_accuracy()

    return f"""
    <h2>Crypto Bot Dashboard</h2>
    <p><b>Symbol:</b> {SYMBOL}</p>
    <p><b>Current Price:</b> {last_price}</p>
    <p><b>Last Updated:</b> {last_time}</p>
    <p><b>Accuracy:</b> {accuracy:.2f}%</p>
    <h3>Last Alerts:</h3>
    <p>{alerts_html}</p>
    """

# ---------------------------
# TradingView Webhook
# ---------------------------
@app.route("/tv-webhook", methods=["POST"])
def tradingview_webhook():
    global last_price, last_time, alerts_list

    data = request.json
    if not data:
        return "No data received", 400

    action = data.get("action")
    price = data.get("price", 0.0)
    symbol = data.get("symbol", SYMBOL)

    last_price = price
    last_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if action == "BUY":
        msg = f"📈 TRADINGVIEW UP | {symbol} | {price}"
    elif action == "SELL":
        msg = f"📉 TRADINGVIEW DOWN | {symbol} | {price}"
    else:
        msg = f"⏸ TRADINGVIEW NO SIGNAL | {symbol} | {price}"

    print(msg)
    send_telegram(msg)

    alerts_list.append(msg)
    if len(alerts_list) > 50:
        alerts_list = alerts_list[-50:]

    save_state()
    return "ok", 200

# ---------------------------
# Fetch OHLC
# ---------------------------
def get_ohlc():
    try:
        url = f"https://api.kucoin.com/api/v1/market/candles?type=15min&symbol={SYMBOL}"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return None

        data = response.json()
        candles = data["data"]

        df = pd.DataFrame(candles, columns=[
            "time", "open", "close", "high", "low", "volume", "turnover"
        ])

        for col in ["open", "close", "high", "low"]:
            df[col] = df[col].astype(float)

        df = df.iloc[::-1].reset_index(drop=True)
        return df

    except:
        return None

# ---------------------------
# Prediction Logic
# ---------------------------
def check_range_alert():
    df = get_ohlc()
    if df is None or len(df) < 20:
        return "NONE", last_price

    price_now = df["close"].iloc[-1]
    price_30min_ago = df["close"].iloc[-2]

    slope_per_candle = (price_now - price_30min_ago) / 2
    slope = slope_per_candle * 5  # 75 mins

    atr = ta.volatility.AverageTrueRange(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        window=14
    ).average_true_range().iloc[-1]

    vol_factor = atr * 0.5

    ema20 = ta.trend.EMAIndicator(df["close"], 20).ema_indicator()
    direction = 1 if ema20.iloc[-1] > ema20.iloc[-2] else -1

    predicted = price_now + slope + direction * vol_factor

    if predicted >= price_now + RANGE:
        return "BET-UP", price_now
    elif predicted <= price_now - RANGE:
        return "BET-DOWN", price_now
    else:
        return "NONE", price_now

# ---------------------------
# Accuracy Check
# ---------------------------
def check_prediction_accuracy():
    global prediction_history

    df = get_ohlc()
    if df is None:
        return

    current_price = df["close"].iloc[-1]

    for p in prediction_history:
        if p.get("checked"):
            continue

        time_diff = (datetime.datetime.now() - datetime.datetime.fromisoformat(p["time"])).total_seconds()

        if time_diff >= 4500:  # 75 mins
            entry = p["price"]

            if p["prediction"] == "BET-UP":
                result = "WIN" if current_price > entry else "LOSS"
            elif p["prediction"] == "BET-DOWN":
                result = "WIN" if current_price < entry else "LOSS"
            else:
                result = "SKIP"

            msg = f"📊 RESULT | {p['prediction']} | Entry: {entry} | Now: {current_price} | {result}"
            print(msg)
            send_telegram(msg)

            p["checked"] = True
            p["result"] = result

# ---------------------------
# Accuracy %
# ---------------------------
def calculate_accuracy():
    wins = 0
    total = 0

    for p in prediction_history:
        if p.get("checked") and p.get("result") in ["WIN", "LOSS"]:
            total += 1
            if p["result"] == "WIN":
                wins += 1

    return (wins / total * 100) if total > 0 else 0

# ---------------------------
# Bot Loop
# ---------------------------
def run_range_bot():
    global last_price, last_time, alerts_list, prediction_history

    last_status = None

    while True:
        try:
            status, price = check_range_alert()

            last_price = price
            last_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if status != last_status:
                if status == "BET-UP":
                    msg = f"📈 RANGE UP | {SYMBOL} | {price}"
                elif status == "BET-DOWN":
                    msg = f"📉 RANGE DOWN | {SYMBOL} | {price}"
                else:
                    msg = f"⏸ RANGE NO SIGNAL | {SYMBOL} | {price}"

                print(msg)
                send_telegram(msg)

                alerts_list.append(msg)

                if status in ["BET-UP", "BET-DOWN"]:
                    prediction_history.append({
                        "time": datetime.datetime.now().isoformat(),
                        "price": price,
                        "prediction": status,
                        "checked": False
                    })

                if len(alerts_list) > 50:
                    alerts_list = alerts_list[-50:]

                save_state()
                last_status = status

            # ✅ CHECK RESULTS
            check_prediction_accuracy()

            time.sleep(30)

        except Exception as e:
            print("Bot error:", e)
            time.sleep(60)

# ---------------------------
# Run
# ---------------------------
if __name__ == "__main__":
    Thread(target=lambda: app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080))
    )).start()

    Thread(target=run_range_bot).start()
