# -*- coding: utf-8 -*-
"""
Created on Tue Feb 19 09:49:41 2019

@author: Algo
"""

import numpy as np
import pandas as pd
#import pandas.io.data as web
import matplotlib.pylab as plt
import csv
from datetime import datetime, timedelta
from dateutil.parser import parse
import os
from operator import itemgetter, attrgetter
#from pandas.lib import Timestamp
from multiprocessing import Pool
from collections import OrderedDict
#from progressbar import ProgressBar
from tqdm import tqdm
import sys
#from swifter import swiftapply
import math
import pickle
import multiprocessing
from joblib import Parallel, delayed
import multiprocessing.dummy as mp
import threading
import time
from pandas.tseries.offsets import BDay

# =============================================================================
# print("Loading Pickel...")
# Reliance= open(os.path.expanduser('~/Desktop/FNO/Pickles/New folder (2)/' + "NIFTY" + '.pkl'), 'rb')
# Reliance_Pickle= pickle.load(Reliance)
# print("Pickel loaded")
# =============================================================================


print("Loading Pickel...")
Reliance123= open(os.path.expanduser('~/Desktop/FNO/Pickles/' + "NIFTY123CASH" + '.pkl'), 'rb')
Reliance_Pickle123= pickle.load(Reliance123)
print("Pickel loaded")

Reliance_Pickle=Reliance_Pickle123

Reliance_Pickle=Reliance_Pickle.loc[Reliance_Pickle.Contract_Duration=="Current",]
Reliance_Pickle = Reliance_Pickle.loc[(Reliance_Pickle['Type']=="PE")]

df=Reliance_Pickle



Reliance_Pickle123 = Reliance_Pickle123.loc[(Reliance_Pickle123['Type']=="PE")]

df123=Reliance_Pickle123

Reliance_Pickle = Reliance_Pickle.loc[Reliance_Pickle['Time'].isin(['09:44:59','10:44:59','11:44:59',\
                    '12:44:59','13:44:59','14:44:59','10:14:59','11:14:59','12:14:59',\
                    '13:14:59','14:14:59','15:14:59','15:30:59'])]

Reliance_Pickle = Reliance_Pickle.loc[(Reliance_Pickle['Moneyness_index']==0)]

Reliance_Pickle = Reliance_Pickle.sort_values(['Date_x','Time'], ascending=[True, True])

#Reliance_Pickle=Reliance_Pickle.tail(2000)

df_drop_datframe=Reliance_Pickle
df_drop_datframe=df_drop_datframe.drop_duplicates(subset=['Date_x', 'Time'], keep="first")

df_drop_datframe=df_drop_datframe.reset_index(drop=True)

box_size_entry=input("Enter box size value :-")
box_reversal=input("Enter nu of box reversal:-")  

box_size=0
    
trend_direction=""
no_of_brick=0
left_price=0
entry_price=0
entry_price_future=0
entry_position=""
PandL=0
bracket_low=0
bracket_high=0
entry_price_expiry_month=""
exit_price_actual=0


for i in range(len(df_drop_datframe)):
        
    print(df_drop_datframe['Date_x'].iloc[i])
    try:
        if (i==0):
            continue
   
        if(trend_direction==""):
      
            if(i==1 or ((df_drop_datframe['Close_FUT'].iloc[i] >= df_drop_datframe['Close_FUT'].iloc[i-1]) and \
                        ((df_drop_datframe['Close_FUT'].iloc[i] - (bracket_low)) >=(int(box_size_entry)*int(box_reversal))))):  
                
                box_size=int(box_size_entry)
                
                bracket_low=int(df_drop_datframe['Close_FUT'].iloc[i]-(df_drop_datframe['Close_FUT'].iloc[i]%10))
                bracket_high=bracket_low - (int(box_size)*int(box_reversal))
                
                no_of_brick=int((df_drop_datframe['Close_FUT'].iloc[i] - bracket_low)/int(box_size))
                left_price = ((df_drop_datframe['Close_FUT'].iloc[i] - bracket_low)%int(box_size))
                
                if(bracket_low%100 >= 50):
                    ticker_strike=(bracket_low-(bracket_low%100)+100)
                else:
                    ticker_strike=(bracket_low-(bracket_low%100))
                    
                if(df_drop_datframe['Date_x'].iloc[i] >= df_drop_datframe['Date_y'].iloc[i]-BDay(5)):
                    filtdata_for_strk = df123.loc[(df123['Strike']==ticker_strike)]
                    filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Date_y']>df_drop_datframe['Date_y'].iloc[i])]
# =============================================================================
#                     if(int(str(str(filtdata_for_strk['Date_y'].iloc[0]).split(' ')[0]).split('-')[2]) <= 10):
#                         garbage_date=filtdata_for_strk['Date_y'].iloc[0]
#                         filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Date_y']>garbage_date)]
#          
# =============================================================================
                    filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Date_x']==df_drop_datframe['Date_x'].iloc[i])]
                    filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Time']==df_drop_datframe['Time'].iloc[i])]
                else:
                    filtdata_for_strk = df.loc[(df['Strike']==ticker_strike)]
                    filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Date_y']>=df_drop_datframe['Date_y'].iloc[i])]
# =============================================================================
#                     if(int(str(str(filtdata_for_strk['Date_y'].iloc[0]).split(' ')[0]).split('-')[2]) <= 10):
#                         garbage_date=filtdata_for_strk['Date_y'].iloc[0]
#                         filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Date_y']>garbage_date)]
#          
# =============================================================================
                    filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Date_x']==df_drop_datframe['Date_x'].iloc[i])]
                    filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Time']==df_drop_datframe['Time'].iloc[i])]
                    
                trend_direction="upward"
                entry_price=filtdata_for_strk['Close_OPT'].iloc[0]
                entry_price_future=df_drop_datframe['Close_FUT'].iloc[i]
                entry_price_expiry_month=filtdata_for_strk['Date_y'].iloc[0]
                entry_position="Long"
        
                df_drop_datframe.set_value(i, 'Bracket_Range', (str(bracket_low)+"******"+str(bracket_high)))
                df_drop_datframe.set_value(i, 'Brick', (str(no_of_brick)+"up"))
                df_drop_datframe.set_value(i, 'pr_val_left_aftrbox', left_price)
                df_drop_datframe.set_value(i, 'Ticker', filtdata_for_strk['Strike'].iloc[0])
                df_drop_datframe.set_value(i, 'Ticker_expiry', entry_price_expiry_month)
                df_drop_datframe.set_value(i, 'OptionDate', filtdata_for_strk['Date_x'].iloc[0])
                df_drop_datframe.set_value(i, 'OptionTime', filtdata_for_strk['Time'].iloc[0])
                df_drop_datframe.set_value(i, 'Position', "Long")
                df_drop_datframe.set_value(i, 'entry_price', entry_price)
            
            else:
                if((df_drop_datframe['Close_FUT'].iloc[i] < df_drop_datframe['Close_FUT'].iloc[i-1]) and\
                   df_drop_datframe['Close_FUT'].iloc[i]<exit_price_actual):
                    
                    bracket_low=int(df_drop_datframe['Close_FUT'].iloc[i]-(df_drop_datframe['Close_FUT'].iloc[i]%10))
                    bracket_high=bracket_low - (int(box_size)*int(box_reversal))
                
                no_of_brick=int((df_drop_datframe['Close_FUT'].iloc[i] - bracket_low)/int(box_size))
                left_price = ((df_drop_datframe['Close_FUT'].iloc[i] - bracket_low)%int(box_size))
                
                if(bracket_low%100 >= 50):
                    ticker_strike=(bracket_low-(bracket_low%100)+100)
                else:
                    ticker_strike=(bracket_low-(bracket_low%100))
                
                df_drop_datframe.set_value(i, 'Bracket_Range', (str(bracket_low)+"******"+str(bracket_high)))
                df_drop_datframe.set_value(i, 'pr_val_left_aftrbox', left_price)
        
        elif(trend_direction=="upward" and df_drop_datframe['Close_FUT'].iloc[i] != df_drop_datframe['Close_FUT'].iloc[i-1]):
            
            if(df_drop_datframe['Date_y'].iloc[i] != entry_price_expiry_month):
                entry_price_expiry_month=df_drop_datframe['Date_y'].iloc[i]
                
            if(df_drop_datframe['Date_x'].iloc[i] == df_drop_datframe['Date_y'].iloc[i]-BDay(5)\
               and df_drop_datframe['Time'].iloc[i]=='15:14:59'):
                
                    print("***************************monthlyrolling**************************")
                    filtdata_for_strk = df123.loc[(df123['Strike']==ticker_strike)]
                    filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Date_y']==entry_price_expiry_month)]
                    filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Date_x']==df_drop_datframe['Date_x'].iloc[i])]
                    filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Time']==df_drop_datframe['Time'].iloc[i])]
              
                    PandL=entry_price-filtdata_for_strk['Close_OPT'].iloc[0]
                    exit_price=filtdata_for_strk['Close_OPT'].iloc[0]
                    trend_direction=""
                    entry_price=0
                    entry_price_future=0
                    entry_price_expiry_month=""
                    entry_position=""
                
                    df_drop_datframe.set_value(i, 'Bracket_Range', (str(bracket_low)+"******"+str(bracket_high)))
                    if(no_of_brick > 1):
                        df_drop_datframe.set_value(i, 'Brick', (str(no_of_brick)+"dn"))
                    df_drop_datframe.set_value(i, 'pr_val_left_aftrbox', left_price)
                    df_drop_datframe.set_value(i, 'Ticker', filtdata_for_strk['Strike'].iloc[0])
                    df_drop_datframe.set_value(i, 'OptionDate', filtdata_for_strk['Date_x'].iloc[0])
                    df_drop_datframe.set_value(i, 'OptionTime', filtdata_for_strk['Time'].iloc[0])
                    df_drop_datframe.set_value(i, 'exit_type', "month_rolling")
                    df_drop_datframe.set_value(i, 'exit_price', filtdata_for_strk['Close_OPT'].iloc[0])
                    df_drop_datframe.set_value(i, 'PandL', PandL)
      
                        #*****************************rebuy**************#
                    
                    box_size=int(box_size_entry)
                    
                    bracket_low=int(df_drop_datframe['Close_FUT'].iloc[i+1]-(df_drop_datframe['Close_FUT'].iloc[i+1]%10))
                    bracket_high=bracket_low - (int(box_size)*int(box_reversal))
                    
                    no_of_brick=int((df_drop_datframe['Close_FUT'].iloc[i] - bracket_low)/int(box_size))
                    left_price = ((df_drop_datframe['Close_FUT'].iloc[i] - bracket_low)%int(box_size))
                    
                    if(bracket_low%100 >= 50):
                        ticker_strike=(bracket_low-(bracket_low%100)+100)
                    else:
                        ticker_strike=(bracket_low-(bracket_low%100))
                        
                    if(df_drop_datframe['Date_x'].iloc[i] >= df_drop_datframe['Date_y'].iloc[i]-BDay(5)):
                        filtdata_for_strk = df123.loc[(df123['Strike']==ticker_strike)]
                        filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Date_y']>df_drop_datframe['Date_y'].iloc[i])]
# =============================================================================
#                         if(int(str(str(filtdata_for_strk['Date_y'].iloc[0]).split(' ')[0]).split('-')[2]) <= 10):
#                            garbage_date=filtdata_for_strk['Date_y'].iloc[0]
#                            filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Date_y']>garbage_date)]
#          
# =============================================================================
                        filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Date_x']==df_drop_datframe['Date_x'].iloc[i])]
                        filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Time']==df_drop_datframe['Time'].iloc[i])]
                    else:
                        filtdata_for_strk = df.loc[(df['Strike']==ticker_strike)]
                        filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Date_y']>=df_drop_datframe['Date_y'].iloc[i])]
# =============================================================================
#                         if(int(str(str(filtdata_for_strk['Date_y'].iloc[0]).split(' ')[0]).split('-')[2]) <= 10):
#                             garbage_date=filtdata_for_strk['Date_y'].iloc[0]
#                             filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Date_y']>garbage_date)]
#          
# =============================================================================
                        filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Date_x']==df_drop_datframe['Date_x'].iloc[i])]
                        filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Time']==df_drop_datframe['Time'].iloc[i])]
                        
                    trend_direction="upward"
                    entry_price=filtdata_for_strk['Close_OPT'].iloc[0]
                    entry_price_future=df_drop_datframe['Close_FUT'].iloc[i]
                    entry_price_expiry_month=filtdata_for_strk['Date_y'].iloc[0]
                    entry_position="Long"
            
                    df_drop_datframe.set_value(i+1, 'Bracket_Range', (str(bracket_low)+"******"+str(bracket_high)))
                    df_drop_datframe.set_value(i+1, 'Brick', (str(no_of_brick)+"up"))
                    df_drop_datframe.set_value(i+1, 'pr_val_left_aftrbox', left_price)
                    df_drop_datframe.set_value(i+1, 'Ticker', filtdata_for_strk['Strike'].iloc[0])
                    df_drop_datframe.set_value(i+1, 'Ticker_expiry', entry_price_expiry_month)
                    df_drop_datframe.set_value(i+1, 'OptionDate', filtdata_for_strk['Date_x'].iloc[0])
                    df_drop_datframe.set_value(i+1, 'OptionTime', filtdata_for_strk['Time'].iloc[0])
                    df_drop_datframe.set_value(i+1, 'Position', "Long")
                    df_drop_datframe.set_value(i+1, 'entry_price', entry_price)
                   
        
                    i=i+1 
                
            elif(((bracket_low) - df_drop_datframe['Close_FUT'].iloc[i]) >= int(box_size)*int(box_reversal)):
                    
                bracket_low=int(df_drop_datframe['Close_FUT'].iloc[i]-(df_drop_datframe['Close_FUT'].iloc[i]%10))
                bracket_high=bracket_low - (int(box_size)*int(box_reversal))
            
                no_of_brick=int((bracket_low - df_drop_datframe['Close_FUT'].iloc[i])/int(box_size))
                left_price = ((bracket_low - df_drop_datframe['Close_FUT'].iloc[i])%int(box_size))

                filtdata_for_strk = df.loc[(df['Strike']==ticker_strike)]
                filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Date_y']==entry_price_expiry_month)]
# =============================================================================
#                 if(int(str(str(filtdata_for_strk['Date_y'].iloc[0]).split(' ')[0]).split('-')[2]) <= 10):
#                                  garbage_date=filtdata_for_strk['Date_y'].iloc[0]
#                                  filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Date_y']>garbage_date)]
#          
# =============================================================================
                filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Date_x']==df_drop_datframe['Date_x'].iloc[i])]
                filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Time']==df_drop_datframe['Time'].iloc[i])]
              
                PandL=entry_price-filtdata_for_strk['Close_OPT'].iloc[0]
                exit_price=filtdata_for_strk['Close_OPT'].iloc[0]
                exit_price_actual=bracket_low
                trend_direction=""
                entry_price=0
                entry_price_future=0
                entry_price_expiry_month=""
                entry_position=""
                
                df_drop_datframe.set_value(i, 'Bracket_Range', (str(bracket_low)+"******"+str(bracket_high)))
                if(no_of_brick > 1):
                    df_drop_datframe.set_value(i, 'Brick', (str(no_of_brick)+"dn"))
                df_drop_datframe.set_value(i, 'pr_val_left_aftrbox', left_price)
                df_drop_datframe.set_value(i, 'Ticker', filtdata_for_strk['Strike'].iloc[0])
                df_drop_datframe.set_value(i, 'OptionDate', filtdata_for_strk['Date_x'].iloc[0])
                df_drop_datframe.set_value(i, 'OptionTime', filtdata_for_strk['Time'].iloc[0])
                df_drop_datframe.set_value(i, 'exit_type', str(box_reversal)+"bracketreversal")
                df_drop_datframe.set_value(i, 'exit_price', exit_price)
                df_drop_datframe.set_value(i, 'PandL', PandL)
          
            else:
                if(df_drop_datframe['Close_FUT'].iloc[i] > bracket_low):
                    
                    if(int((df_drop_datframe['Close_FUT'].iloc[i] - bracket_low)/int(box_size))>=1):
                        
                        no_of_brick=int((df_drop_datframe['Close_FUT'].iloc[i] - bracket_low)/int(box_size))
                        left_price = ((df_drop_datframe['Close_FUT'].iloc[i] - bracket_low)%int(box_size))
                        
                        if(df_drop_datframe['Close_FUT'].iloc[i]-entry_price_future>=\
                           entry_price_future/100):
         
                             filtdata_for_strk = df.loc[(df['Strike']==ticker_strike)]
                             filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Date_y']==entry_price_expiry_month)]
# =============================================================================
#                              if(int(str(str(filtdata_for_strk['Date_y'].iloc[0]).split(' ')[0]).split('-')[2]) <= 10):
#                                  garbage_date=filtdata_for_strk['Date_y'].iloc[0]
#                                  filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Date_y']>garbage_date)]
#          
# =============================================================================
                             filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Date_x']==df_drop_datframe['Date_x'].iloc[i])]
                             filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Time']==df_drop_datframe['Time'].iloc[i])]
              
                             PandL=entry_price-filtdata_for_strk['Close_OPT'].iloc[0]
                             exit_price=filtdata_for_strk['Close_OPT'].iloc[0]
                             exit_price_actual=bracket_low
                             trend_direction=""
                             entry_price=0
                             entry_price_future=0
                             entry_price_expiry_month=""
                             entry_position=""
                
                             ticker_strike+=100
                             
                             box_size=int(box_size_entry)
                           
                             filtdata_for_strk = df.loc[(df['Strike']==ticker_strike)]
                             filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Date_y']>=df_drop_datframe['Date_y'].iloc[i])]
# =============================================================================
#                              if(int(str(str(filtdata_for_strk['Date_y'].iloc[0]).split(' ')[0]).split('-')[2]) <= 10):
#                                  garbage_date=filtdata_for_strk['Date_y'].iloc[0]
#                                  filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Date_y']>garbage_date)]
#          
# =============================================================================
                             filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Date_x']==df_drop_datframe['Date_x'].iloc[i])]
                             filtdata_for_strk = filtdata_for_strk.loc[(filtdata_for_strk['Time']==df_drop_datframe['Time'].iloc[i])]
           
                             trend_direction="upward"
                             entry_price=filtdata_for_strk['Close_OPT'].iloc[0]
                             entry_price_future=df_drop_datframe['Close_FUT'].iloc[i]
                             entry_price_expiry_month=filtdata_for_strk['Date_y'].iloc[0]
                             entry_position="Long"
                
                             df_drop_datframe.set_value(i, 'Ticker', filtdata_for_strk['Strike'].iloc[0])
                             df_drop_datframe.set_value(i, 'Ticker_expiry', entry_price_expiry_month)
                             df_drop_datframe.set_value(i, 'OptionDate', filtdata_for_strk['Date_x'].iloc[0])
                             df_drop_datframe.set_value(i, 'OptionTime', filtdata_for_strk['Time'].iloc[0])
                             df_drop_datframe.set_value(i, 'Position', "Long")
                             df_drop_datframe.set_value(i, 'entry_price', entry_price)
                             df_drop_datframe.set_value(i, 'exit_type', "Trailing")
                             df_drop_datframe.set_value(i, 'exit_price',exit_price )
                             df_drop_datframe.set_value(i, 'PandL', PandL)
                        
                        trend_direction="upward"
                        
                        if(no_of_brick >= 1):
                            df_drop_datframe.set_value(i, 'Brick', (str(no_of_brick)+"up"))
                        df_drop_datframe.set_value(i, 'pr_val_left_aftrbox', left_price)
                      
                        bracket_low=int(df_drop_datframe['Close_FUT'].iloc[i]-(df_drop_datframe['Close_FUT'].iloc[i]%10))
                        bracket_high=bracket_low - (int(box_size)*int(box_reversal))
                    else:
                        no_of_brick=int((df_drop_datframe['Close_FUT'].iloc[i] - bracket_low)/int(box_size))
                        left_price = ((df_drop_datframe['Close_FUT'].iloc[i] - bracket_low)%int(box_size))
                        
                        trend_direction="upward"
                        
                        if(no_of_brick >= 1):
                            df_drop_datframe.set_value(i, 'Brick', (str(no_of_brick)+"up"))
                        df_drop_datframe.set_value(i, 'pr_val_left_aftrbox', left_price)
                    
                    df_drop_datframe.set_value(i, 'Bracket_Range', (str(bracket_low)+"******"+str(bracket_high)))
                            
                else:
                    no_of_brick=int((bracket_low - df_drop_datframe['Close_FUT'].iloc[i])/int(box_size))
                    left_price = ((bracket_low - df_drop_datframe['Close_FUT'].iloc[i])%int(box_size))
                    
                    df_drop_datframe.set_value(i, 'Bracket_Range', (str(bracket_low)+"******"+str(bracket_high)))
                    if(no_of_brick > 1 ):
                        df_drop_datframe.set_value(i, 'Brick', (str(no_of_brick)+"dn"))
                    df_drop_datframe.set_value(i, 'pr_val_left_aftrbox', left_price)
                    
        
        
    except:                
        df_drop_datframe.to_csv('C://Users//admin//Desktop//FNO//renkowithpickellongcash.csv')

   
df_drop_datframe.to_csv('C://Users//admin//Desktop//FNO//renkowithpickellongcash.csv')
   




