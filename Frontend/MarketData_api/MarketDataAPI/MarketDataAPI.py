import time
import random
import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime, timedelta

def getTimeSinceEpoch(seconds):
    epoch = datetime(1970, 1, 1)
    seconds = int(seconds)
    delta = timedelta(seconds=seconds)
    result = epoch + delta
    return result

def initializeMt5():
    print('[INFO] => Initializing MT5')
    if not mt5.initialize("C:/Program Files/MetaTrader 5/terminal64.exe"):
        print("[ERROR] => Initialization Failed.")
        mt5.shutdown()
        quit()
    else:
        print("[INFO] => Initialization Successful.")

def loginMt5():
    print('[INFO] => Logging into MT5')
    ACC_ID = 2121939877
    ACC_KEY = "@1IcZgUo"
    ACC_ORG = "XBTFX-MetaTrader5"
    if mt5.login(ACC_ID, ACC_KEY, ACC_ORG):
        print(f'[INFO] => Connected to ACC_ID: {ACC_ID} on ACC_ORG: {ACC_ORG}')
    else:
        print(f'[ERROR] => Failed to connect to ACC_ID: {ACC_ID} on ACC_ORG: {ACC_ORG} ERROR_CODE: {mt5.last_error()}')

def requestTickerQuote(tickers):
    tickerQuotes = []
    for ticker in tickers:
        ticks = mt5.copy_ticks_from(ticker, datetime.now(), 1, mt5.COPY_TICKS_ALL)
        rates = mt5.copy_rates_from(ticker, mt5.TIMEFRAME_M1, datetime.now(), 1)
        if ticks is not None and len(ticks) > 0 and rates is not None and len(rates) > 0:
            ticks_frame = ticks[0]
            rates_frame = rates[0]
            tickerQuote = {
                'ticker': ticker,
                'time': getTimeSinceEpoch(ticks_frame["time"]).strftime('%Y-%m-%d %H:%M:%S'),  # Convert to string
                'bid': float(ticks_frame["bid"]),
                'ask': float(ticks_frame["ask"]),
                'volume': int(ticks_frame["volume"]),
                'last': float(ticks_frame["last"]),
                'open': float(rates_frame["open"]),
                'close': float(rates_frame["close"]),
                'high': float(rates_frame["high"]),
                'low': float(rates_frame["low"]),
                'tick_volume': int(rates_frame["tick_volume"]),
                'spread': float(rates_frame["spread"])
            }
            tickerQuotes.append(tickerQuote)
    return tickerQuotes

from flask import Flask
from flask_socketio import SocketIO, emit
from flask_cors import CORS, cross_origin
import threading

app = Flask(__name__)
CORS(app) 
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('On_Market_Data_Update')
@cross_origin()
def handle_market_data_update(data):
    emit('On_Market_Data_Update', data)

def get_market_data_updates():
    initializeMt5()
    loginMt5()
    sleep_time = random.uniform(0, 1)
    tickers = ['BTCUSD', 'ETHUSD', 'XRPUSD', 'LTCUSD', 'SOLUSD', 'BNBUSD', 'DOTUSD', 'DOGUSD', 'TETUSD']
    while True:
        tickerQuotes = requestTickerQuote(tickers)
        for tickerQuote in tickerQuotes:
            time.sleep(sleep_time)
            socketio.emit('On_Market_Data_Update', tickerQuote)
        time.sleep(sleep_time)

if __name__ == '__main__':
    print('[INFO] => Starting Market Data')
    t = threading.Thread(target=get_market_data_updates)
    t.start()
    print('[INFO] => Starting Provider API')
    socketio.run(app, port=8080)
