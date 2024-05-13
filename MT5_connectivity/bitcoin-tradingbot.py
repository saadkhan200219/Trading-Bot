import MetaTrader5 as mt5
from datetime import datetime
from itertools import count
from sklearn.preprocessing import MinMaxScaler
import time
from tensorflow.keras.models import load_model

import tensorflow as tf
from tensorflow.keras.layers import Layer, Input, LSTM, Dropout, Dense
from tensorflow.keras.models import Model
import numpy as np


mt5.initialize("C:/Program Files/MetaTrader 5/terminal64.exe")

CRYPTO = 'BTCUSD'


PRICE_THRESHOLD = 0.001

STOP_LOSS = 5

TAKE_PROFIT = 0.5

BUY = mt5.ORDER_TYPE_BUY
SELL = mt5.ORDER_TYPE_SELL
ORDER_TYPE = BUY



class Swish(Layer):
    def call(self, inputs):
        return inputs * tf.nn.sigmoid(inputs)

def define_model(window_size):
    input1 = Input(shape=(window_size, 1))
    x = LSTM(units=64, return_sequences=True)(input1)
    x = Dropout(0.2)(x)
    x = LSTM(units=64, return_sequences=True)(x)
    x = Dropout(0.2)(x)
    x = LSTM(units=64)(x)
    x = Dropout(0.2)(x)
    x = Dense(128, activation=Swish())(x)
    dnn_output = Dense(1, activation=Swish())(x)

    model = Model(inputs=input1, outputs=[dnn_output])
    model.compile(loss='mean_squared_error', optimizer='Adam')
    model.summary()

    return model


window_size = 60 
model = define_model(window_size)

model_weights_path = 'model.h5'
model.load_weights(model_weights_path)



def preprocess_data(candles):

    scaler = MinMaxScaler()
    prices_array = np.array(candles)

    prices_reshaped = prices_array.reshape(-1, 1)
    scaled_data = scaler.fit_transform(prices_reshaped)
    last_60_days = scaled_data[-60:]
 
    X = np.reshape(last_60_days, (1, 60, 1))
    return X,scaler

def predict_next_day_price(candles):

    X ,scaler= preprocess_data(candles)

    predicted_price = model.predict(X)
    predicted_price = scaler.inverse_transform(predicted_price)

    return predicted_price


account_number = 2121939877
authorized = mt5.login(account_number,"@1IcZgUo", "XBTFX-MetaTrader5")

if authorized:
    print(f'connected to account #{account_number}')
else:
    print(f'failed to connect at account #{account_number}, error code: {mt5.last_error()}')


account_info = mt5.account_info()
if account_info is None:
    raise RuntimeError('Could not load the account equity level.')
else:
    equity = float(account_info[10])

def get_dates():
    today = datetime.today()
    utc_from = datetime(year=today.year, month=today.month, day=today.day - 1)
    return utc_from, datetime.now()

def get_data():
    utc_from, utc_to = get_dates()
    return mt5.copy_rates_range(CRYPTO, mt5.TIMEFRAME_M10, utc_from, utc_to)

def get_current_prices():
    current_buy_price = mt5.symbol_info_tick(CRYPTO)[2]
    current_sell_price = mt5.symbol_info_tick(CRYPTO)[1]
    return current_buy_price, current_sell_price

def trade():
    utc_from, utc_to = get_dates()
    candles = get_data()
    current_buy_price, current_sell_price = get_current_prices()

    difference = (candles['close'][-1] - candles['close'][-2]) / candles['close'][-2] * 100

    positions = mt5.positions_get(symbol=CRYPTO)
    orders = mt5.orders_get(symbol=CRYPTO)
    symbol_info = mt5.symbol_info(CRYPTO)
    candles1 = mt5.copy_rates_range(CRYPTO, mt5.TIMEFRAME_M10, utc_from, utc_to)
    print("openprice: ",candles1["close"][-1])
   
   
    if difference > PRICE_THRESHOLD:
        print(f'dif 1: {CRYPTO}, {difference}')
        time.sleep(8)
        candles = mt5.copy_rates_range(CRYPTO, mt5.TIMEFRAME_M10, utc_from, utc_to)
        print("openprice: ",candles["open"][-1])
        difference = (candles['close'][-1] - candles['close'][-2]) / candles['close'][-2] * 100
        if difference > PRICE_THRESHOLD:
            print(f'dif 2: {CRYPTO}, {difference}')
       
            predicted_price = predict_next_day_price(candles['open'])[0][0]
            if predicted_price > current_buy_price:
               
                if not mt5.initialize():
                    raise RuntimeError(f'MT5 initialize() failed with error code {mt5.last_error()}')

                if len(positions) == 0 and len(orders) < 1:
                    if symbol_info is None:
                        print(f'{CRYPTO} not found, can not call order_check()')
                        mt5.shutdown()
                    if not symbol_info.visible:
                        print(f'{CRYPTO} is not visible, trying to switch on')
                        if not mt5.symbol_select(CRYPTO, True):
                            print('symbol_select({}}) failed, exit', CRYPTO)

                    lot = float(round(((equity / 20) / current_buy_price), 2))
                    
                    if ORDER_TYPE == BUY:
                        sl = current_buy_price - (current_buy_price * STOP_LOSS) / 100
                        tp = current_buy_price + (current_buy_price * TAKE_PROFIT) / 100
                    else:
                        sl = current_buy_price + (current_buy_price * STOP_LOSS) / 100
                        tp = current_buy_price - (current_buy_price * TAKE_PROFIT) / 100
                        
                    request = {
                        'action': mt5.TRADE_ACTION_DEAL,
                        'symbol': CRYPTO,
                        'volume': lot,
                        'type': ORDER_TYPE,
                        'price': current_buy_price,
                        'sl': sl,
                        'tp': tp,
                        'magic': 66,
                        'comment': 'python-buy',
                        'type_time': mt5.ORDER_TIME_GTC,
                        'type_filling': mt5.ORDER_FILLING_IOC,
                    }

                    result = mt5.order_send(request)

                    print(f'1. order_send(): by {CRYPTO} {lot} lots at {current_buy_price}')

                    if result.retcode != mt5.TRADE_RETCODE_DONE:
                        print(f'2. order_send failed, retcode={result.retcode}')

                    print(f'2. order_send done, {result}')
                    print(f'   opened position with POSITION_TICKET={result.order}')

                else:
                    print(f'BUY signal detected, but {CRYPTO} has {len(positions)} active trade')

            else:
                pass

        else:
            pass

    else:
        if orders or positions:
            print('Buying signal detected but there is already an active trade')
        else:
            print(f'difference is only: {str(difference)}% trying again...')

if __name__ == '__main__':
    print('Press Ctrl-C to stop.')
    for i in count():
        trade()
        print(f'Iteration {i}')
        time.sleep(5)
