# -*- coding: utf-8 -*-
"""
10 1 reversal 1min
Created on Mon Aug  5 13:08:50 2019

@author: Harsh
"""

import pandas as pd
import numpy as np
from tqdm import tqdm
import talib
from datetime import datetime
from upstox_api.api import *
import pytz # $ pip install pytz

tz='Asia/Kolkata'


u = Upstox('aocg0mAF6R2uotb5Mae4Q1PyBBlznq6i7EakN5Dc', '4751b15cca51fe9f32e266ce7dbc579ca49cb6b7')
u.get_master_contract('NSE_FO') # get contracts for MCX FO

OptionExchange = "NSE_FO"
OptionContract = "TATAMOTORS19AUGFUT"
val = u.get_instrument_by_symbol(OptionExchange, OptionContract)




df =pd.DataFrame(columns = ['Time', 'Close', 'Trend', 'Trade', 'Brick', 'PivotPrice', 'BUYSELL'])
df.to_csv("C://Users//Harsh//upstox_oauth//media//OneMinuteOHLC.csv")
stock_data=pd.read_csv("C://Users//Harsh//upstox_oauth//media//OneMinuteOHLC.csv")

oneLot = 1
twoLot = 2
lotSize = 0
LTprice = 0
bar_written = 0
time = None
flag = 0
pivot_Price = 0
Close = 0
trend = ""
box_size = 2
brick = ""
n_multiplies_box_size = 1
trade = ""
def event_handler_quote_update(message):
    global LTprice, val, lotSize, oneLot, twoLot, bar_written, stock_data, time, flag, pivot_Price, Close, trend, trade, box_size, brick, n_multiplies_box_size 
    time=datetime.now(pytz.timezone(tz)).strftime("%H:%M:%S") 
    LTprice = message['ltp']
    lotSize = message['instrument'][9]
    print("LTprice = {}".format(LTprice))
    print("Flag = {}".format(flag))
    if (time >= '09:15:00' and time <= '15:30:00'):
        if(time >='09:16:00'):
            
            if(int(time.split(':')[1]) % int(1) == 0 and int(time.split(':')[2]) == 0 and bar_written == 0):
                
                if not flag:
                    pivot_Price = LTprice
                    print("First pivot_Price = {}".format(pivot_Price))
                    
                
                Close = LTprice
                
                print("Close = {}".format(Close))
                
                if trend == "":
                    if (Close >= box_size + pivot_Price):
                        trend = "Upward"
                        brick = "GreenBrick"
                        print("Time = " + time)
                        print("Trend = " + trend)
                        print("Brick = " + brick)
                        pivot_Price = Close - ((Close - pivot_Price) % box_size)
                        print("PivotPrice = {}".format(pivot_Price))
                        idx = len(stock_data)
                        stock_data.set_value(idx, 'Time', time)
                        stock_data.set_value(idx, 'Close', Close)
                        stock_data.set_value(idx, 'Trend', trend)
                        stock_data.set_value(idx, 'Brick', brick)                        
                        stock_data.set_value(idx, 'PivotPrice', pivot_Price)
                        stock_data.set_value(idx, 'BUYSELL', 'BUY')
                        u.place_order(TransactionType.Buy, val, lotSize*oneLot, OrderType.Limit, ProductType.Delivery, Close, None, 0, DurationType.DAY, None, None, None)
                        #OrderPlacement(TransactionType.Buy, Close, lotSize*oneLot, val)
                        #stock_data.to_csv("C://Users//Harsh//upstox_oauth//media//OneMinuteOHLC.csv", index=False)
                                                                          
                    elif (Close <= pivot_Price - box_size):
                        trend = "Downward"
                        brick = "RedBrick"
                        print("Time = " + time)
                        print("Trend = " + trend)
                        print("Brick = " + brick)
                        pivot_Price = Close + ((pivot_Price - Close) % (box_size)) 
                        print("PivotPrice = {}".format(pivot_Price))
                        idx = len(stock_data)
                        stock_data.set_value(idx, 'Time', time)
                        stock_data.set_value(idx, 'Close', Close)
                        stock_data.set_value(idx, 'Trend', trend)                        
                        stock_data.set_value(idx, 'Brick', brick)                        
                        stock_data.set_value(idx, 'PivotPrice', pivot_Price)
                        stock_data.set_value(idx, 'BUYSELL', 'SELL')
                        u.place_order(TransactionType.Sell, val, lotSize*oneLot, OrderType.Limit, ProductType.Delivery, Close, None, 0, DurationType.DAY, None, None, None)
                        #OrderPlacement(TransactionType.Sell, Close, lotSize*oneLot, val)
                        #stock_data.to_csv("C://Users//Harsh//upstox_oauth//media//OneMinuteOHLC.csv", index=False)
                       
                                          
                if trend == "Upward":
                    if (pivot_Price - Close >= box_size * n_multiplies_box_size):
                        trade = "ReverseOfUpward" 
                        trend = "Downward"
                        brick = "RedBrick"
                        pivot_Price = Close + ((pivot_Price - Close) % (box_size))
                        print("Time = " + time)
                        print("PivotPrice = {}".format(pivot_Price))
                        print("Trade = " + trade)
                        print("Trend = " + trend)
                        print("Brick = " + brick)
                        idx = len(stock_data)
                        stock_data.set_value(idx, 'Time', time)
                        stock_data.set_value(idx, 'Trend', trend)
                        stock_data.set_value(idx, 'Trade', trade)
                        stock_data.set_value(idx, 'Brick', brick)
                        stock_data.set_value(idx, 'Close', Close)
                        stock_data.set_value(idx, 'PivotPrice', pivot_Price)
                        stock_data.set_value(idx, 'BUYSELL', 'SELL')
                        u.place_order(TransactionType.Sell, val, lotSize*twoLot, OrderType.Limit, ProductType.Delivery, Close, None, 0, DurationType.DAY, None, None, None)
                        #OrderPlacement(TransactionType.Sell, Close, lotSize*twoLot, val)
                        #stock_data.to_csv("C://Users//Harsh//upstox_oauth//media//OneMinuteOHLC.csv", index=False)
                                        
                    elif (Close >= box_size + pivot_Price ):
                        trend = "Upward"
                        brick = "GreenBrick"
                        print("Time = " + time)
                        print("Trend = " + trend)
                        print("Brick = " + brick) 
                        pivot_Price = Close - ((Close - pivot_Price) % box_size)
                        print("PivotPrice = {}".format(pivot_Price))
                        idx = len(stock_data)
                        stock_data.set_value(idx, 'Time', time)
                        stock_data.set_value(idx, 'Close', Close)
                        stock_data.set_value(idx, 'Trend', trend)
                        stock_data.set_value(idx, 'Brick', brick)                        
                        stock_data.set_value(idx, 'PivotPrice', pivot_Price)
                        #stock_data.to_csv("C://Users//Harsh//upstox_oauth//media//OneMinuteOHLC.csv", index=False)
                        
                        
                if trend == "Downward":
                    if(Close - pivot_Price >= box_size * n_multiplies_box_size):
                        trade = "ReverseOfDownward"
                        trend = "Upward"
                        brick = "GreenBrick"
                        pivot_Price = Close - ((Close - pivot_Price) % box_size)
                        print("Time = " + time)
                        print("PivotPrice = {}".format(pivot_Price))
                        print("Trade = " + trade)
                        print("Trend = " + trend)
                        print("Brick = " + brick)
                        idx = len(stock_data)
                        stock_data.set_value(idx, 'Time', time)
                        stock_data.set_value(idx, 'Trend', trend)
                        stock_data.set_value(idx, 'Trade', trade)
                        stock_data.set_value(idx, 'Brick', brick)
                        stock_data.set_value(idx, 'Close', Close)
                        stock_data.set_value(idx, 'PivotPrice', pivot_Price)
                        stock_data.set_value(idx, 'BUYSELL', 'BUY')
                        u.place_order(TransactionType.Buy, val, lotSize*twoLot, OrderType.Limit, ProductType.Delivery, Close, None, 0, DurationType.DAY, None, None, None)
                        #OrderPlacement(TransactionType.Buy, Close, lotSize*twoLot, val)
                        #stock_data.to_csv("C://Users//Harsh//upstox_oauth//media//OneMinuteOHLC.csv", index=False)
                        
                    elif (Close <= pivot_Price - box_size):
                        trend = "Downward"
                        brick = "RedBrick"
                        print("Time = " + time)
                        print("Trend = " + trend)
                        print("Brick = " + brick)
                        pivot_Price = Close + ((pivot_Price - Close) % (box_size))
                        print("PivotPrice = {}".format(pivot_Price))
                        idx = len(stock_data)
                        stock_data.set_value(idx, 'Time', time)
                        stock_data.set_value(idx, 'Close', Close)
                        stock_data.set_value(idx, 'Trend', trend)
                        stock_data.set_value(idx, 'Brick', brick)                        
                        stock_data.set_value(idx, 'PivotPrice', pivot_Price)
                        #stock_data.to_csv("C://Users//Harsh//upstox_oauth//media//OneMinuteOHLC.csv", index=False)
                            
                        
        
              
                bar_written = 1                
                Close = 0
            stock_data.to_csv("C://Users//Harsh//upstox_oauth//media//OneMinuteOHLC.csv", index=False)    
            #if(int(time.split(':')[1]) % int(2) != 0 and bar_written == 1):    
            if(int(time.split(':')[2]) != 0 and bar_written == 1):
                bar_written = 0
                

        
        
    flag = 1        
                
        




def event_handler_order_update(message):
	print ("event_handler_order_update : " + str(datetime.now()))
	print (message)
# =============================================================================
# def event_handler_socket_disconnect(err):
#    print("Socket Disconnected", err)
#    u.start_websocket(False)
# =============================================================================
# =============================================================================
# def OrderPlacement(side, price, qty, scrip):
# 	u.place_order(
#         side,  # transaction_type
# 		scrip,  # instrument
# 		qty,  # quantity
# 		OrderType.Market,  # order_type
# 		ProductType.Delivery,  # product_type
# 		price ,  # price
# 		None,  # trigger_price
# 		0,  # disclosed_quantity
# 		DurationType.DAY,  # duration
# 		None,  # stop_loss
# 		None,  # square_off
# 		None  # trailing_ticks
# 	)
# =============================================================================
    
def socket_connect():
       print ("Initiating the Socket Listeners")
       
       u.set_on_quote_update(event_handler_quote_update)
       u.set_on_order_update(event_handler_order_update)
       #u.set_on_disconnect(event_handler_socket_disconnect)
       print ("Subscription for the: " + val[4])
    
       
       u.unsubscribe(val, LiveFeedType.LTP)
       u.subscribe(val, LiveFeedType.LTP)
       #print(u.get_live_feed(val, LiveFeedType.LTP))
                        
       print("connection with socket")
       u.start_websocket(False)
       
       
    
  # this will create a websocket for me . All ltp and real-time data will come over this socket
    
  
    
socket_connect()



'''
df = pd.read_csv("C://Users//Harsh//Desktop//RBTALGO//Renko Trading Strategy//NIFTY-I.NFO_30.csv")
box_size = 10
n_multiplies_box_size = 3  # n_multiplies_box_size
pivot_Price = 0

trend = ""
trade = ""


for i in range(len(df)):
    if i == 0:
        pivot_Price = df["Close"].iloc[i]
        continue

    
    if trend == "":
        if (df["Close"].iloc[i] >= box_size + pivot_Price ):
            trend = "Upward"
            df.set_value(i, "Trend", trend)
            df.set_value(i, "Brick", "GreenBrick")
            pivot_Price = df["Close"].iloc[i] - ((df["Close"].iloc[i] - pivot_Price) % box_size)
            df.set_value(i, "PivotPrice", pivot_Price)
            continue
                  
        if (df["Close"].iloc[i] <= pivot_Price - box_size):
            trend = "Downward"
            df.set_value(i, "Trend", trend)
            df.set_value(i, "Brick", "RedBrick")
            pivot_Price = df["Close"].iloc[i] + ((pivot_Price - df["Close"].iloc[i]) % (box_size)) 
            df.set_value(i, "PivotPrice", pivot_Price)
            continue
            
              
    if trend == "Upward":
        if (pivot_Price - df["Close"].iloc[i] >= box_size * n_multiplies_box_size):
            trade = "ReverseOfUpward" 
            trend = "Downward"
            pivot_Price = df["Close"].iloc[i] + ((pivot_Price - df["Close"].iloc[i]) % (box_size))
            df.set_value(i, "PivotPrice", pivot_Price)
            df.set_value(i, "TRADE", trade)
            df.set_value(i, "Trend", trend)
            df.set_value(i, "Brick", "RedBrick")            
            continue
       
        if (df["Close"].iloc[i] >= box_size + pivot_Price ):
            trend = "Upward"
            df.set_value(i, "Trend", trend)
            df.set_value(i, "Brick", "GreenBrick")
            pivot_Price = df["Close"].iloc[i] - ((df["Close"].iloc[i] - pivot_Price) % box_size)
            df.set_value(i, "PivotPrice", pivot_Price)
            
            
    if trend == "Downward":
        if(df["Close"].iloc[i] - pivot_Price >= box_size * n_multiplies_box_size):
            trade = "ReverseOfDownward"
            trend = "Upward"
            pivot_Price = df["Close"].iloc[i] - ((df["Close"].iloc[i] - pivot_Price) % box_size)
            df.set_value(i, "PivotPrice", pivot_Price)
            df.set_value(i, "TRADE", trade)
            df.set_value(i, "Trend", trend)
            df.set_value(i, "Brick", "GreenBrick")
            continue
        
        if (df["Close"].iloc[i] <= pivot_Price - box_size):
            trend = "Downward"
            df.set_value(i, "Trend", trend)   
            df.set_value(i, "Brick", "RedBrick")
            pivot_Price = df["Close"].iloc[i] + ((pivot_Price - df["Close"].iloc[i]) % (box_size))
            df.set_value(i, "PivotPrice", pivot_Price)
            
df.to_csv("C://Users//Harsh//Desktop//RBTALGO//Renko Trading Strategy//NIFTY-I.NFO_30_signal.csv",index = False)
'''        


'''
def event_handler_quote_update(message):
    print(message['instrument'][9])
    print(type(message['instrument'][9]))
    

def socket_connect():
       print ("Initiating the Socket Listeners")
       u.set_on_quote_update(event_handler_quote_update)
       #u.set_on_disconnect(event_handler_socket_disconnect)
       print ("Subscription for the: " + val[4])
    
       
       u.unsubscribe(val, LiveFeedType.LTP)
       u.subscribe(val, LiveFeedType.LTP)
       #print(u.get_live_feed(val, LiveFeedType.LTP))
                        
       print("connection with socket")
       u.start_websocket(False)
       
       
    
  # this will create a websocket for me . All ltp and real-time data will come over this socket
    
  
    
socket_connect()
'''