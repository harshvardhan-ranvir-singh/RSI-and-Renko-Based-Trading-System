# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 00:54:39 2019

@author: Harsh
"""
from datetime import datetime
from upstox_api.api import *
import pytz # $ pip install pytz
import pandas as pd

tz='Asia/Kolkata'




contracts = []
u = Upstox('T57lEJhTxJ2cdoWETCTVf5WvKTpfVh0f5QltvUBh', '69066ddd8e22cb9b64138af219bf897731310b8b')
d = u.get_master_contract('NSE_EQ') # get contracts for MCX FO




df = pd.DataFrame({
                    'Contracts': pd.Series(contracts)
                   })
    
OptionExchange = "NSE_FO"
OptionContract = "BANKNIFTY19SEP29500PE"
val = u.get_instrument_by_symbol(OptionExchange, OptionContract)






def event_handler_quote_update(message):
    print("Quote Update: %s" % str(message))




def event_handler_socket_disconnect():
	print("SOCKET DISCONNECTED" + str(datetime.now()))
	

# =============================================================================
# def event_handler_order_update(message):
# 	print ("event_handler_order_update : " + str(datetime.now()))
# 	print (message)
# 	
# 
# 
# def event_handler_trade_update(message):
# 	print ("event_handler_trade_update : " + str(datetime.now()))
# 	print (message)
# 	
# 
# 
# def event_handler_error(err):
# 	print ("event_handler_error : " + str(datetime.now()))
# 	print (err)
# 	
# 
# 
# def event_handler_socket_disconnect():
# 	print ("event_handler_socket_disconnect : " + str(datetime.now()))
# 	
# =============================================================================
    

def socket_connect():
       print ("Initiating the Socket Listeners")
       u.set_on_quote_update(event_handler_quote_update)
       u.set_on_disconnect(event_handler_socket_disconnect)
       print ("Subscription for the: " + val[4])
    
       #print (val)
       #upstoxAPI.unsubscribe(var, LiveFeedType.LTP)
       u.subscribe(val, LiveFeedType.LTP)
       #print(u.get_live_feed(val, LiveFeedType.LTP))
        
        
        
       print("connection with socket")
       u.start_websocket(False)
       
       
    
  # this will create a websocket for me . All ltp and real-time data will come over this socket
    
  
    
socket_connect()














































# =============================================================================
# print (u.get_balance()) # get balance / margin limits
# print()
# print()
# print()
# print (u.get_profile()) # get profile
# print()
# print()
# print()
# print (u.get_holdings()) # get holdings
# print()
# print()
# print (u.get_positions()) # get positions
# 
# =============================================================================

'''
u.get_master_contract('NSE_EQ')


FutureExchange = "NSE_EQ"
FutureContract = "RELIANCE"
val = u.get_instrument_by_symbol(FutureExchange, FutureContract)

df =pd.DataFrame(columns = ['Time', 'Open', 'High', 'Low', 'Close'])
df.to_csv("C://Users//Harsh//Desktop//RBTALGO//Upstox API//twoOHLC.csv")
stock_data=pd.read_csv("C://Users//Harsh//Desktop//RBTALGO//Upstox API//twoOHLC.csv")

bar_open = 0
bar_high = 0
bar_low = 0
bar_close = 0
LTprice = 0
bar_written = 0
time = None
def event_handler_quote_update(message):
    global bar_open, bar_high, bar_low, bar_close, LTprice, bar_written, stock_data, time
    time=datetime.now(pytz.timezone(tz)).strftime("%H:%M:%S") 
    LTprice = message['ltp']
    print(LTprice)
    if (time >= '09:15:00' and time <= '15:30:00'):
        if(time >='09:16:00'):
            if bar_open == 0:
                bar_open = LTprice
            if bar_high == 0 or LTprice > bar_high:
                bar_high = LTprice
            if bar_low == 0 or LTprice < bar_low:
                bar_low = LTprice
            
            if(int(time.split(':')[1]) % int(2) == 0 and bar_written == 0):

                bar_close = LTprice
                print('Time = ' + time)
                print('Open = {}'.format(bar_open))
                print('High = {}'.format(bar_high))
                print('Low = {}'.format(bar_low))
                print('Close = {}'.format(bar_close))
                idx = len(stock_data)
                stock_data.set_value(idx, 'Time', time)
                stock_data.set_value(idx, 'Open', bar_open)
                stock_data.set_value(idx, 'High', bar_high)
                stock_data.set_value(idx, 'Low', bar_low)
                stock_data.set_value(idx, 'Close', bar_close)
                stock_data.to_csv("C://Users//Harsh//Desktop//RBTALGO//Upstox API//twoOHLC.csv", index=False)
                
                bar_written = 1
                bar_open = 0
                bar_high = 0
                bar_low = 0
                bar_close = 0
            if(int(time.split(':')[1]) % int(2) != 0 and bar_written == 1):
                bar_written = 0
                

        
        
            
                
        
    
    


# =============================================================================
# def event_handler_order_update(message):
# 	print ("event_handler_order_update : " + str(datetime.now()))
# 	print (message)
# 	
# 
# 
# def event_handler_trade_update(message):
# 	print ("event_handler_trade_update : " + str(datetime.now()))
# 	print (message)
# 	
# 
# 
# def event_handler_error(err):
# 	print ("event_handler_error : " + str(datetime.now()))
# 	print (err)
# 	
# 
# 
# def event_handler_socket_disconnect():
# 	print ("event_handler_socket_disconnect : " + str(datetime.now()))
# 	
# =============================================================================
    
def socket_connect():
       print ("Initiating the Socket Listeners")
       u.set_on_quote_update(event_handler_quote_update)
       print ("Subscription for the: " + val[4])
    
       #print (val)
        #upstoxAPI.unsubscribe(SCRIP, LiveFeedType.LTP)
       u.subscribe(val, LiveFeedType.LTP)
       #print(u.get_live_feed(val, LiveFeedType.LTP))
        
        
        
       print("connection with socket")
       u.start_websocket(False)
       
       
    
  # this will create a websocket for me . All ltp and real-time data will come over this socket
    
  
    
socket_connect()

'''
