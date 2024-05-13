from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.common import *

import pandas as pd
import numpy as np
import datetime
import time

class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.order_id = 3010  
        self.avg_days = 1
        self.historical_data = []
        self.moving_average = []
        self.x = []
        self.have = False
        self.profit = 10 
        self.old = 0
        print('App Initialized...')

    def createContract(self):
        contract = Contract()
        contract.symbol = "TSLA"
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        return contract

    def calculateMovingAverage(self, historical_data):
        print("Historical Data: ", historical_data)
        self.moving_average = pd.Series(historical_data).rolling(self.avg_days).mean()
        return np.gradient(self.moving_average)[-1]

    def nextValidId(self, orderId: int):
        self.reqMktData(self.generate_order_id(), self.createContract(), "", False, False, [])
        print('Data Imported...')

    def generate_order_id(self):
        self.order_id += 1
        return self.order_id

    def tickPrice(self, reqId, tickType, price, attrib):
        if datetime.datetime.now().minute != self.old and tickType == 4:
            self.old = datetime.datetime.now().minute
            self.historical_data.append(price)
            print("price",price)
            if len(self.historical_data) >= self.avg_days:
                self.sma = self.calculateMovingAverage(self.historical_data)

                order = Order()
                order.orderType = "LMT"
                order.lmtPrice = price
                if self.sma > 0 and not self.have:
                    order.totalQuantity = self.profit // price
                    order.action = "BUY"
                    order.lmtPrice += 0.001
                    self.placeOrder(self.generate_order_id(), self.createContract(), order)
                    print(f"Bought {order.totalQuantity} stocks at ${price} for ${price * order.totalQuantity}")
                    self.totalQuantity = order.totalQuantity
                    self.old_price = price
                    self.profit -= price * order.totalQuantity
                    self.have = True
                elif self.sma < 0 and self.have:
                    order.totalQuantity = self.totalQuantity
                    order.action = "SELL"
                    order.lmtPrice -= 0.001 
                    self.placeOrder(self.generate_order_id(), self.createContract(), order)
                    print(f"Sold at ${price} and made profit of ${(price - self.old_price) * self.totalQuantity}")
                    self.have = False
                    self.profit += price * self.totalQuantity

            
            if datetime.datetime.now().second % 20 == 0:
                if self.have:
                    order.totalQuantity = self.totalQuantity
                    order.action = "SELL"
                    self.placeOrder(self.generate_order_id(), self.createContract(), order)
                    print(f"Sold at ${price} and made profit of ${(price - self.old_price) * self.totalQuantity}")
                    self.have = False
                    self.profit += price * self.totalQuantity

                print("\nProfit Made Today: ", self.profit)

            # Disconnect if it's 2:06 AM
            if datetime.datetime.now().hour == 2 and datetime.datetime.now().minute == 6:
                if self.have:
                    order.totalQuantity = self.totalQuantity
                    order.action = "SELL"
                    self.placeOrder(self.generate_order_id(), self.createContract(), order)
                    print(f"Sold at ${price} and made profit of ${(price - self.old_price) * self.totalQuantity}")
                    self.have = False
                    self.profit += price * self.totalQuantity
                print("\nProfit Made Today: ", self.profit)
                self.disconnect()

app = IBapi()
app.connect('127.0.0.1', 7497, 1)  
app.run()  
