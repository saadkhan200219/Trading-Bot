
import time
import random
import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime, timedelta

tickers = ['BTCUSD', 'ETHUSD', 'XRPUSD', 'LTCUSD', 'SOLUSD', 'BNBUSD', 'DOTUSD', 'DOGUSD', 'TETUSD']

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
    ACC_ID = 2121941196
    ACC_KEY = "*5YhChYk"
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
                'volume': float(ticks_frame["volume"]),
                'last': float(ticks_frame["last"]),
                'open': float(rates_frame["open"]),
                'close': float(rates_frame["close"]),
                'high': float(rates_frame["high"]),
                'low': float(rates_frame["low"]),
                'tick_volume': float(rates_frame["tick_volume"]),
                'spread': float(rates_frame["spread"])
            }
            tickerQuotes.append(tickerQuote)
    return tickerQuotes

def requestHistoryDeals():
    from_date = pd.Timestamp.now() - pd.Timedelta(days=30)
    to_date = pd.Timestamp.now()
    historyDeals = mt5.history_deals_get(from_date, to_date)
    arrHistoryDeals = []
    if historyDeals is not None:
        for deal in historyDeals:
            historyDeal = {
            'symbol': deal[15],
            'ticket': int(deal[0]),
            'time': datetime.fromtimestamp(deal[2]).strftime('%Y-%m-%d %H:%M:%S'),
            'type': deal[4],
            'volume': float(deal[9]),
            'price': float(deal[10]),
            'commission': float(deal[11]),
            'swap': float(deal[12]),
            'profit': float(deal[13]),
            'comment': deal[16],
            'reason': int(deal[8]),
            }
            arrHistoryDeals.append(historyDeal)
        return arrHistoryDeals

def requestActiveTrades():
    positions = mt5.positions_get()
    tradesData = []
    if positions is not None:
        for trade in positions:
            tradeData = {
            'symbol': trade[16],
            'ticket': trade[0],
            'time': datetime.fromtimestamp(trade[1]).strftime('%Y-%m-%d %H:%M:%S'),
            'type': trade[5],
            'volume': float(trade[9]),
            'tradePrice': float(trade[10]),
            'stopLoss': float(trade[11]),
            'takeProfit': float(trade[12]),
            'price': float(trade[13]),
            'profit': float(trade[15]),
            'change': float((trade[13]-trade[10])/trade[13]*100),
            'identity': trade[17],
            }
            tradesData.append(tradeData)
        return tradesData

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

@cross_origin()
def handle_trades_data_updates(data):
    emit('On_Trades_Data_Update', data)

@cross_origin()
def handle_history_data(data):
    emit('On_History_Data_Update', data)

def get_market_data_updates():
    conflation_intv = random.uniform(1,2)
    while True:
        tickerQuotes = requestTickerQuote(tickers)
        for tickerQuote in tickerQuotes:
            socketio.emit('On_Market_Data_Update', tickerQuote)
        time.sleep(conflation_intv)

def get_trades_data_updates():
    conflation_intv = random.uniform(1, 2)
    while True:
        tradesData = requestActiveTrades()
        for trade in tradesData:
            socketio.emit('On_Trades_Data_Update', trade)
        time.sleep(conflation_intv)

def get_history_data():
    conflation_intv = random.uniform(2, 4)
    while True:
        historyData = requestHistoryDeals()
        for deal in historyData:
            socketio.emit('On_History_Data_Update', deal)
        time.sleep(conflation_intv)


if __name__ == '__main__':
    print('[INFO] => Starting Market Data')
    initializeMt5()
    loginMt5()

    thrMktDataUpdates = threading.Thread(target=get_market_data_updates)
    thrMktDataUpdates.start()

    thrTradesDataUpdates = threading.Thread(target=get_trades_data_updates)
    thrTradesDataUpdates.start()

    thrHistoryData = threading.Thread(target=get_history_data)
    thrHistoryData.start()
    
    print('[INFO] => Starting Provider API')
    socketio.run(app, port=8080)
