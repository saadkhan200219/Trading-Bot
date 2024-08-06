import requests
import threading
import numpy as np
import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from tensorflow.keras.models import load_model
from sklearn.preprocessing import StandardScaler, LabelEncoder

def initialize_mt5():
    print("Initializing MetaTrader 5...")
    if not mt5.initialize():
        print(f"initialize() failed, error code: {mt5.last_error()}")
        quit()
    print("MetaTrader 5 initialized successfully.")

def get_account_info():
    account_info = mt5.account_info()
    if account_info is None:
        print(f"account_info() failed, error code: {mt5.last_error()}")
        return None
    return account_info

def get_positions():
    positions = mt5.positions_get()
    if positions is None:
        print(f"positions_get() failed, error code: {mt5.last_error()}")
        return None
    return positions

def get_symbol_info(symbol):
    print(f"Getting symbol info for {symbol}...")
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"symbol_info() failed, error code: {mt5.last_error()}")
        return None
    print(f"Symbol info for {symbol} retrieved successfully.")
    return symbol_info

def calculate_sl_tp(price, order_type, stop_loss_percent, take_profit_percent):
    print(f"Calculating SL/TP for price: {price}, order_type: {order_type}...")
    if order_type == mt5.ORDER_TYPE_BUY:
        sl = price - (price * stop_loss_percent) / 100
        tp = price + (price * take_profit_percent) / 100
    else:
        sl = price + (price * stop_loss_percent) / 100
        tp = price - (price * take_profit_percent) / 100
    print(f"SL: {sl}, TP: {tp}")
    return sl, tp

def calculate_volume(current_price):
    open_positions = get_positions()
    if open_positions is not None and len(open_positions) >= 10:
        print(f"High volume at risk, Holding equity..")
        return None

    account_info = get_account_info()
    if account_info is None:
        return None
    
    equity = account_info.equity
    return float(round(((equity / 20) / current_price), 2))

def send_buy_order(symbol, volume, price, sl, tp):
    print(f"Sending buy order for {symbol} at price: {price}, volume: {volume}...")
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": mt5.ORDER_TYPE_BUY,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 10,
        "magic": 123456,
        "comment": "py-bot-buy",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Buy order failed, retcode={result.retcode}")
    else:
        print("Buy order placed successfully.")
    return result

def send_sell_order(symbol, volume, price, sl, tp):
    print(f"Sending sell order for {symbol} at price: {price}, volume: {volume}...")
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": mt5.ORDER_TYPE_SELL,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 10,
        "magic": 123456,
        "comment": "py-bot-sell",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Sell order failed, retcode={result.retcode}")
    else:
        print("Sell order placed successfully.")
    return result

def preprocess_new_data(tick_frame):
    tick_frame['tickDirection'] = LabelEncoder().fit_transform(tick_frame['tickDirection'])
    numerical_cols = ['bid', 'ask', 'volume', 'open', 'high', 'low', 'tick_volume']
    tick_frame[numerical_cols] = StandardScaler().fit_transform(tick_frame[numerical_cols])
    return tick_frame

def predict_next_price(model, tick_frame):
    tick_frame = preprocess_new_data(tick_frame)
    tick_sequence = np.array([tick_frame.values for _ in range(10)])
    tick_sequence = np.array(tick_sequence).reshape((1, 10, 8))
    print(tick_sequence.shape)
    predicted_price = model.predict(tick_sequence)
    return predicted_price[0][0]


def analyze_and_trade(symbol, stop_loss_percent, take_profit_percent, model):
    print(f"Analysing account equity and deciding to trade for {symbol}...")
    account_info = get_account_info()
    if account_info is None:
        return

    equity = account_info.equity
    positions = get_positions()
    if positions is None:
        return

    active_position = next((pos for pos in positions if pos.symbol == symbol), None)
    if active_position:
        profit = active_position.profit
        if profit < 0:
            print(f"Active position for {symbol} is in loss. Skipping trade.")
            return
        else:
            print(f"Active position for {symbol} is in profit. Proceeding with analysis.")

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print(f"symbol_info_tick() failed, error code: {mt5.last_error()}")
        return

    print(f"Current ask price for {symbol}: {tick.ask}, bid price: {tick.bid}")
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 1)
    if rates is None or len(rates) == 0:
        print(f"copy_rates_from_pos() failed, error code: {mt5.last_error()}")
        return

    rates_frame = pd.DataFrame(rates)
    tick_frame = pd.DataFrame([{
        'bid': tick.bid,
        'ask': tick.ask,
        'volume': tick.volume,
        'open': rates_frame['open'].iloc[0],
        'high': rates_frame['high'].iloc[0],
        'low': rates_frame['low'].iloc[0],
        'tick_volume': rates_frame['tick_volume'].iloc[0],
        'tickDirection': 'ZeroPlusTick'
    }])

    predicted_price = predict_next_price(model, tick_frame)
    print(f"Predicted next price for {symbol}: {predicted_price}")
    if equity < account_info.balance * 0.3:
        print("Equity is less than 30% of the balance. Cannot trade.")
        return

    if predicted_price > tick.ask:
        print(f"Predicted price {predicted_price} is higher than ask price {tick.ask}. Considering buy order...")
        sl, tp = calculate_sl_tp(tick.ask, mt5.ORDER_TYPE_BUY, stop_loss_percent, take_profit_percent)
        volume = calculate_volume(tick.ask)
        if volume is not None:
            send_buy_order(symbol, volume, tick.ask, sl, tp)
    elif predicted_price < tick.bid:
        print(f"Predicted price {predicted_price} is lower than bid price {tick.bid}. Considering sell order...")
        sl, tp = calculate_sl_tp(tick.bid, mt5.ORDER_TYPE_SELL, stop_loss_percent, take_profit_percent)
        volume = calculate_volume(tick.bid)
        if volume is not None:
            send_sell_order(symbol, volume, tick.bid, sl, tp)

RUNNING = False
BOTTHREAD = None

def main():
    initialize_mt5()
    model = load_model('crypto_price_predictor_model_2024-05-16_23-03-21.h5')
    symbols = ['BTCUSD', 'ETHUSD', 'SOLUSD']
    stop_loss_percent = 2.0
    take_profit_percent = 1.0

    while RUNNING:
        for symbol in symbols:
            if not RUNNING:
                break
            analyze_and_trade(symbol, stop_loss_percent, take_profit_percent, model)









app = Flask(__name__)
CORS(app)
@app.route('/start-bot', methods=['GET'])
def start_bot():
    global RUNNING
    global BOTTHREAD

    if not RUNNING:
        RUNNING = True
        BOTTHREAD = threading.Thread(target=main)
        BOTTHREAD.start()
        return jsonify(
            {
                "Message": "Bot started.",
                "Status": 1
            })
    else:
        return jsonify(
            {
                "Message": "Bot is already running.",
                "Status": 1
            })

@app.route('/stop-bot', methods=['GET'])
def stop_bot():
    global RUNNING
    global BOTTHREAD

    if RUNNING:
        RUNNING = False
        BOTTHREAD.join()
        return jsonify(
            {
                "Message": "Bot stopped.",
                "Status": 0
            })
    else:
        return jsonify(
            {
                "Message": "Bot is not running.",
                "Status": -2
            })

@app.route('/fetch-news', methods=['GET'])
@cross_origin()
def fetch_news():
    from_date = datetime.today()
    to_date = from_date - timedelta(days=2)
    from_date_str = from_date.strftime('%Y-%m-%d')
    to_date_str = to_date.strftime('%Y-%m-%d')

    print("Fetching news from", to_date_str, "to", from_date_str)
    
    api_key = 'eec815cd8dbf484b9ad21f9426612a87'
    api_url = f'https://newsapi.org/v2/everything?q=crypto&from={from_date}&to={to_date}&language=en&sortBy=relevancy&apiKey={api_key}&pageSize=20'
    print(api_url)
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        response = jsonify(data['articles'])
        print(response)      
        return response
    except requests.exceptions.RequestException as error:
        print('There was a problem with the fetch operation:', error)

if __name__ == '__main__':
    app.run(port=8081)