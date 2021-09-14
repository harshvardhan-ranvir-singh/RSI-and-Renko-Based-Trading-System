from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.http import JsonResponse
from upstox_api.api import *
from django.http import Http404
import dotenv
# import numpy as np
import pandas as pd
import os
from datetime import datetime
import pytz
import winsound
import shutil
tz = 'Asia/Kolkata'

#*****************************Global VAriable For Event Handler*******************
dict_out={}
dict_out_backup={}


stocklist_marketwatch = pd.read_csv("C://upstox_oauth//media//UpstoxList_marketwatch.csv")
stocklist = pd.read_csv("C://upstox_oauth//media//Upstox_stocklist.csv")

try:
    df_signal=pd.read_csv('C://upstox_oauth//media//Upstox_Tradesheet//'+datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y")+'_signal_Upstox.csv')
except:
    df_signal=pd.DataFrame()
    
bar_open=dict.fromkeys(stocklist['ContractSymbol'],0)
bar_high=dict.fromkeys(stocklist['ContractSymbol'],0)
bar_low=dict.fromkeys(stocklist['ContractSymbol'],0)
bar_close=dict.fromkeys(stocklist['ContractSymbol'],0)
bar_written=dict.fromkeys(stocklist['ContractSymbol'],0)


trade_happen=dict.fromkeys(stocklist['ContractSymbol'],0)

dfdatabase = pd.read_csv("C://upstox_oauth//media//Signal_DataBase.csv")

#*****************************Global VAriable For Event Handler*******************


# Create your views here.


def home(request):
    API_KEY = os.getenv('API_KEY')
    API_SECRET = os.getenv('API_SECRET')
    alert_text = "Please set up the environment. "
    alert_flag = False
    if not API_KEY:
        alert_flag = True
        alert_text = alert_text + "Could not find API KEY. "
    if not API_SECRET:
        alert_flag = True
        alert_text = alert_text + "Could not find API SECRET."
    context = {"alert_flag": alert_flag, "alert_text": alert_text}

    return render(request, 'upstox_auth/index.html', context=context)


def login(request):
    API_KEY = os.getenv('API_KEY')
    API_SECRET = os.getenv('API_SECRET')
    s = Session(API_KEY)
    s.set_api_secret(API_SECRET)
    url = request.build_absolute_uri(reverse('redirect'))
    s.set_redirect_uri(url)
    return HttpResponseRedirect(s.get_login_url())


def redirect(request):
    code = request.GET.get('code')
    if not code:
        raise Http404("Did not receive ACCESS_TOKEN")
    API_KEY = os.getenv('API_KEY')
    API_SECRET = os.getenv('API_SECRET')
    s = Session(API_KEY)
    s.set_api_secret(API_SECRET)
    url = request.build_absolute_uri(reverse('redirect'))
    s.set_redirect_uri(url)
    s.set_code(code)
    access_token = s.retrieve_access_token()
    print(access_token)
    dotenv.set_key(dotenv.find_dotenv(), 'ACCESS_TOKEN', access_token)
    return HttpResponseRedirect(reverse('readaccesstoken'))

    
def readaccesstoken(request):
    if request.method == 'GET':        
        df = pd.read_csv("C://upstox_oauth//media//Upstox_stocklist.csv")
        lst = os.listdir("C://upstox_oauth//media//market_watchlist")
        fullmarketwatchlist=[]
        for watchlist in lst:
            fullmarketwatchlist.append(watchlist.split('.')[0])                
        
        code = dotenv.get_key(dotenv.find_dotenv(), 'ACCESS_TOKEN')        
        contract = df['ContractSymbol'].tolist()
        
        contract2 = fullmarketwatchlist
        context = {'accesstoken': code, 'contract': contract, 'contract2': contract2 }
        return render(request, 'upstox_auth/tokendisplay.html', context=context)
    
    if request.method == 'POST':
        code = dotenv.get_key(dotenv.find_dotenv(), 'ACCESS_TOKEN')
        context = {'accesstoken': code}
        return render(request, 'upstox_auth/tokendisplay.html', context=context)


def get_started(request):
    tz = 'Asia/Kolkata'
    
    stocklist_marketwatch = pd.read_csv("C://upstox_oauth//media//UpstoxList_marketwatch.csv")
    stocklist = pd.read_csv("C://upstox_oauth//media//Upstox_stocklist.csv")
    try:
        df_signal=pd.read_csv('C://upstox_oauth//media//Upstox_Tradesheet//'+datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y")+'_signal_Upstox.csv')
    except:
        df_signal=pd.DataFrame()
        
        
    bar_open=dict.fromkeys(stocklist['ContractSymbol'],0)
    bar_high=dict.fromkeys(stocklist['ContractSymbol'],0)
    bar_low=dict.fromkeys(stocklist['ContractSymbol'],0)
    bar_close=dict.fromkeys(stocklist['ContractSymbol'],0)
    bar_written=dict.fromkeys(stocklist['ContractSymbol'],0)


    trade_happen=dict.fromkeys(stocklist['ContractSymbol'],0)

    dfdatabase = pd.read_csv("C://upstox_oauth//media//Signal_DataBase.csv")
    
    url = request.get_full_path
    url = str(url)
    print(url)
    
    if url.find('_s') != -1:
        os._exit(0)

        
    
    API_KEY = os.getenv('API_KEY')
    access_code = dotenv.get_key(dotenv.find_dotenv(), 'ACCESS_TOKEN')

    u = Upstox(API_KEY, access_code)
    
    for i in range(len(stocklist)):
        try:
            u.get_master_contract(stocklist['ExchangeSymbol'].iloc[i])
        except:
            pass

    def event_handler_socket_disconnect(err):
        print("Socket Disconnected", err)
        u.start_websocket(False)
        
    def event_handler_quote_update(message):
        global dict_out,dict_out_backup,stocklist_marketwatch,stocklist,df_signal,  bar_open,bar_high,bar_low,bar_close,bar_written,trade_happen,dfdatabase

        time=datetime.now(pytz.timezone(tz)).strftime("%H:%M:%S")
        
        if time >= "09:15:00" and time < "23:00:00":
            
            print(str(message['symbol'])+"->"+str(message['ltp']))
            dict_out.update({message['symbol'] : message['ltp']})

            # For 2,3,4,5 ........57,58,59 min
            if(int(str(time).split(':')[1])% int(stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']),'Timeframe'].iloc[0])!=0 and bar_written[message['symbol']]==1):
                bar_written[message['symbol']]=0

            # For 1 min
            if (int(str(time).split(':')[2]) != 59 and int(str(time).split(':')[2]) != 1 and int(str(time).split(':')[2]) != 2 and int(str(time).split(':')[2]) != 3 and bar_written[message['symbol']] == 1):
                bar_written[message['symbol']] = 0


            # For 1 Hour
            if (int(str(time).split(':')[1])  != 0 and time != "15:30:00" and bar_written[message['symbol']] == 1):
                bar_written[message['symbol']] = 0


            # For 2 Hour
            if (time != "11:00:00"and time != "13:00:00"and time != "15:00:00"and time != "15:30:00" and bar_written[message['symbol']] == 1):
                bar_written[message['symbol']] = 0

            # For 3 Hour
            if (time != "12:00:00"and time != "15:00:00" and time != "15:30:00" and bar_written[message['symbol']] == 1):
                bar_written[message['symbol']] = 0

            # For 4 Hour
            if (time != "13:00:00" and time != "15:30:00" and bar_written[message['symbol']] == 1):
                bar_written[message['symbol']] = 0

            # For 1 Day
            if (time != "15:20:00" and bar_written[message['symbol']] == 1):
                bar_written[message['symbol']] = 0


            if(trade_happen[message['symbol']]==0 and (str(message['symbol']) in str(dfdatabase['Symbol']))):
                trade_happen[message['symbol']]=1
                
            if bar_open[message['symbol']]==0:
                bar_open[message['symbol']]=message['ltp']
            if bar_high[message['symbol']]==0 or message['ltp'] > bar_high[message['symbol']]:
                bar_high[message['symbol']]=message['ltp']
            if bar_low[message['symbol']]==0 or message['ltp'] < bar_low[message['symbol']]:
               bar_low[message['symbol']]=message['ltp']

            if stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Timeframe'].iloc[0] == '1':
                if int(str(time).split(':')[2]) == 59 and int(str(time).split(':')[2]) == 1 and int(str(time).split(':')[2]) == 2 and int(str(time).split(':')[2]) == 3 and bar_written[message['symbol']] == 0 and time > "09:16:00":
                    stock_data = pd.read_csv('C:\\upstox_oauth\\media\\Stock_Data\\' + message['symbol'] + '.csv')
                    bar_close[message['symbol']] = message['ltp']
                    print('******************************************************')

                    idx = len(stock_data)
                    stock_data.set_value(idx, 'Date', datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"))
                    stock_data.set_value(idx, 'Open', bar_open[message['symbol']])
                    stock_data.set_value(idx, 'High', bar_high[message['symbol']])
                    stock_data.set_value(idx, 'Low', bar_low[message['symbol']])
                    stock_data.set_value(idx, 'Close', bar_close[message['symbol']])

                    stock_data.to_csv('C:\\upstox_oauth\\media\\Stock_Data\\' + message['symbol'] + '.csv', index=False)

                    bar_open[message['symbol']] = 0
                    bar_high[message['symbol']] = 0
                    bar_low[message['symbol']] = 0
                    bar_close[message['symbol']] = 0
                    bar_written[message['symbol']] = 1

                    pivot_price = float(
                        stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Pivot_Price'].iloc[0])
                    brick_size = int(
                        stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'BrickSize'].iloc[0])
                    brick_reversal = int(
                        stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'BrickReversal'].iloc[
                            0]) + 1

                    if (message['ltp'] - pivot_price >= brick_size and trade_happen[message['symbol']] == 0 and not (
                            str(message['symbol']) in str(dfdatabase['Symbol']))):
                        nu_of_lot = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'no_of_lot'].iloc[0])
                        Quantity = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Quantity'].iloc[0])

                        df1 = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "LONG", message['ltp'], nu_of_lot, Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        trade_happen[message['symbol']] = 1

                        df_signal = pd.concat([df_signal, df1])
                        df_signal.to_csv(
                            'C://upstox_oauth//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = pd.concat([dfdatabase, df1])
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv", index=False)

                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                message['ltp'] - ((message['ltp'] - pivot_price) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also
                        winsound.Beep(2500, 1000)

                    elif (pivot_price - message['ltp'] >= brick_size and trade_happen[message['symbol']] == 0 and not (
                            str(message['symbol']) in str(dfdatabase['Symbol']))):
                        nu_of_lot = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'no_of_lot'].iloc[0])
                        Quantity = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Quantity'].iloc[0])

                        df1 = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "SHORT", message['ltp'], nu_of_lot, Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        trade_happen[message['symbol']] = 1

                        df_signal = pd.concat([df_signal, df1])
                        df_signal.to_csv(
                            'C://upstox_oauth//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = pd.concat([dfdatabase, df1])
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv", index=False)

                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                message['ltp'] + ((pivot_price - message['ltp']) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also
                        winsound.Beep(2500, 1000)

                    elif (pivot_price - message['ltp'] >= (brick_size * brick_reversal) and trade_happen[
                        message['symbol']] == 1 and str(
                        dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']), 'Signal'].iloc[
                            0]) == "LONG"):
                        nu_of_lot = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'no_of_lot'].iloc[0])
                        Quantity = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Quantity'].iloc[0])

                        df1 = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "SHORT", message['ltp'], 2 * nu_of_lot, 2 * Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        trade_happen[message['symbol']] = 1

                        df_signal = pd.concat([df_signal, df1])
                        df_signal.to_csv(
                            'C://upstox_oauth//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        df1_database = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "SHORT", message['ltp'], nu_of_lot, Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = dfdatabase[
                            dfdatabase.Symbol != str(message['symbol'])]  # delete the exit position symbol
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = pd.concat([dfdatabase, df1_database])
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv", index=False)

                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                message['ltp'] + ((pivot_price - message['ltp']) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also
                        winsound.Beep(2500, 1000)

                    elif (message['ltp'] - pivot_price >= (brick_size * brick_reversal) and trade_happen[
                        message['symbol']] == 1 and str(
                        dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']), 'Signal'].iloc[
                            0]) == "SHORT"):
                        nu_of_lot = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'no_of_lot'].iloc[0])
                        Quantity = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Quantity'].iloc[0])

                        df1 = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "LONG", message['ltp'], 2 * nu_of_lot, 2 * Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        trade_happen[message['symbol']] = 1

                        df_signal = pd.concat([df_signal, df1])
                        df_signal.to_csv(
                            'C://upstox_oauth//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        df1_database = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "LONG", message['ltp'], nu_of_lot, Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = dfdatabase[
                            dfdatabase.Symbol != str(message['symbol'])]  # delete the exit position symbol
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = pd.concat([dfdatabase, df1_database])
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv", index=False)

                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                message['ltp'] - ((message['ltp'] - pivot_price) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also
                        winsound.Beep(2500, 1000)

                    elif (message['ltp'] - pivot_price >= brick_size and trade_happen[message['symbol']] == 1 and str(
                            dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']), 'Signal'].iloc[
                                0]) == "LONG"):
                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                message['ltp'] - ((message['ltp'] - pivot_price) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also


                    elif (pivot_price - message['ltp'] >= brick_size and trade_happen[message['symbol']] == 1 and str(
                            dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']), 'Signal'].iloc[
                                0]) == "SHORT"):
                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                message['ltp'] + ((pivot_price - message['ltp']) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also

            if stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Timeframe'].iloc[0] == '1D':
                if (time == "15:20:00" and bar_written[message['symbol']] == 0 ):

                    stock_data = pd.read_csv('C:\\upstox_oauth\\media\\Stock_Data\\' + message['symbol'] + '.csv')
                    bar_close[message['symbol']] = message['ltp']
                    print('******************************************************')

                    idx = len(stock_data)
                    stock_data.set_value(idx, 'Date', datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"))
                    stock_data.set_value(idx, 'Open', bar_open[message['symbol']])
                    stock_data.set_value(idx, 'High', bar_high[message['symbol']])
                    stock_data.set_value(idx, 'Low', bar_low[message['symbol']])
                    stock_data.set_value(idx, 'Close', bar_close[message['symbol']])

                    stock_data.to_csv('C:\\upstox_oauth\\media\\Stock_Data\\' + message['symbol'] + '.csv', index=False)

                    bar_open[message['symbol']] = 0
                    bar_high[message['symbol']] = 0
                    bar_low[message['symbol']] = 0
                    bar_close[message['symbol']] = 0
                    bar_written[message['symbol']] = 1

                    pivot_price = float(
                        stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Pivot_Price'].iloc[0])
                    brick_size = int(
                        stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'BrickSize'].iloc[0])
                    brick_reversal = int(
                        stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'BrickReversal'].iloc[
                            0]) + 1

                    if (message['ltp'] - pivot_price >= brick_size and trade_happen[message['symbol']] == 0 and not (
                            str(message['symbol']) in str(dfdatabase['Symbol']))):
                        nu_of_lot = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'no_of_lot'].iloc[0])
                        Quantity = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Quantity'].iloc[0])

                        df1 = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "LONG", message['ltp'], nu_of_lot, Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        trade_happen[message['symbol']] = 1

                        df_signal = pd.concat([df_signal, df1])
                        df_signal.to_csv(
                            'C://upstox_oauth//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = pd.concat([dfdatabase, df1])
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv", index=False)

                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] - ((message['ltp'] - pivot_price) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also
                        winsound.Beep(2500, 1000)

                    elif (pivot_price - message['ltp'] >= brick_size and trade_happen[message['symbol']] == 0 and not (
                            str(message['symbol']) in str(dfdatabase['Symbol']))):
                        nu_of_lot = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'no_of_lot'].iloc[0])
                        Quantity = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Quantity'].iloc[0])

                        df1 = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "SHORT", message['ltp'], nu_of_lot, Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        trade_happen[message['symbol']] = 1

                        df_signal = pd.concat([df_signal, df1])
                        df_signal.to_csv(
                            'C://upstox_oauth//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = pd.concat([dfdatabase, df1])
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv", index=False)

                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] + ((pivot_price - message['ltp']) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also
                        winsound.Beep(2500, 1000)

                    elif (pivot_price - message['ltp'] >= (brick_size * brick_reversal) and trade_happen[
                        message['symbol']] == 1 and str(
                            dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']), 'Signal'].iloc[
                                0]) == "LONG"):
                        nu_of_lot = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'no_of_lot'].iloc[0])
                        Quantity = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Quantity'].iloc[0])

                        df1 = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "SHORT", message['ltp'], 2 * nu_of_lot, 2 * Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        trade_happen[message['symbol']] = 1

                        df_signal = pd.concat([df_signal, df1])
                        df_signal.to_csv(
                            'C://upstox_oauth//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        df1_database = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "SHORT", message['ltp'], nu_of_lot, Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = dfdatabase[
                            dfdatabase.Symbol != str(message['symbol'])]  # delete the exit position symbol
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = pd.concat([dfdatabase, df1_database])
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv", index=False)

                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] + ((pivot_price - message['ltp']) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also
                        winsound.Beep(2500, 1000)

                    elif (message['ltp'] - pivot_price >= (brick_size * brick_reversal) and trade_happen[
                        message['symbol']] == 1 and str(
                            dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']), 'Signal'].iloc[
                                0]) == "SHORT"):
                        nu_of_lot = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'no_of_lot'].iloc[0])
                        Quantity = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Quantity'].iloc[0])

                        df1 = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "LONG", message['ltp'], 2 * nu_of_lot, 2 * Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        trade_happen[message['symbol']] = 1

                        df_signal = pd.concat([df_signal, df1])
                        df_signal.to_csv(
                            'C://upstox_oauth//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        df1_database = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "LONG", message['ltp'], nu_of_lot, Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = dfdatabase[
                            dfdatabase.Symbol != str(message['symbol'])]  # delete the exit position symbol
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = pd.concat([dfdatabase, df1_database])
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv", index=False)

                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] - ((message['ltp'] - pivot_price) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also
                        winsound.Beep(2500, 1000)

                    elif (message['ltp'] - pivot_price >= brick_size and trade_happen[message['symbol']] == 1 and str(
                            dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']), 'Signal'].iloc[
                                0]) == "LONG"):
                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] - ((message['ltp'] - pivot_price) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also


                    elif (pivot_price - message['ltp'] >= brick_size and trade_happen[message['symbol']] == 1 and str(
                            dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']), 'Signal'].iloc[
                                0]) == "SHORT"):
                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] + ((pivot_price - message['ltp']) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also


            if stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Timeframe'].iloc[0] == '1H':
                if (int(str(time).split(':')[1])  == 0 and time == "15:30:00" and bar_written[message['symbol']] == 0 and time > "09:16:00"):

                    stock_data = pd.read_csv('C:\\upstox_oauth\\media\\Stock_Data\\' + message['symbol'] + '.csv')
                    bar_close[message['symbol']] = message['ltp']
                    print('******************************************************')

                    idx = len(stock_data)
                    stock_data.set_value(idx, 'Date', datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"))
                    stock_data.set_value(idx, 'Open', bar_open[message['symbol']])
                    stock_data.set_value(idx, 'High', bar_high[message['symbol']])
                    stock_data.set_value(idx, 'Low', bar_low[message['symbol']])
                    stock_data.set_value(idx, 'Close', bar_close[message['symbol']])

                    stock_data.to_csv('C:\\upstox_oauth\\media\\Stock_Data\\' + message['symbol'] + '.csv', index=False)

                    bar_open[message['symbol']] = 0
                    bar_high[message['symbol']] = 0
                    bar_low[message['symbol']] = 0
                    bar_close[message['symbol']] = 0
                    bar_written[message['symbol']] = 1

                    pivot_price = float(
                        stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Pivot_Price'].iloc[0])
                    brick_size = int(
                        stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'BrickSize'].iloc[0])
                    brick_reversal = int(
                        stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'BrickReversal'].iloc[
                            0]) + 1

                    if (message['ltp'] - pivot_price >= brick_size and trade_happen[message['symbol']] == 0 and not (
                            str(message['symbol']) in str(dfdatabase['Symbol']))):
                        nu_of_lot = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'no_of_lot'].iloc[0])
                        Quantity = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Quantity'].iloc[0])

                        df1 = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "LONG", message['ltp'], nu_of_lot, Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        trade_happen[message['symbol']] = 1

                        df_signal = pd.concat([df_signal, df1])
                        df_signal.to_csv(
                            'C://upstox_oauth//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = pd.concat([dfdatabase, df1])
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv", index=False)

                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] - ((message['ltp'] - pivot_price) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also
                        winsound.Beep(2500, 1000)

                    elif (pivot_price - message['ltp'] >= brick_size and trade_happen[message['symbol']] == 0 and not (
                            str(message['symbol']) in str(dfdatabase['Symbol']))):
                        nu_of_lot = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'no_of_lot'].iloc[0])
                        Quantity = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Quantity'].iloc[0])

                        df1 = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "SHORT", message['ltp'], nu_of_lot, Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        trade_happen[message['symbol']] = 1

                        df_signal = pd.concat([df_signal, df1])
                        df_signal.to_csv(
                            'C://upstox_oauth//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = pd.concat([dfdatabase, df1])
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv", index=False)

                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] + ((pivot_price - message['ltp']) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also
                        winsound.Beep(2500, 1000)

                    elif (pivot_price - message['ltp'] >= (brick_size * brick_reversal) and trade_happen[
                        message['symbol']] == 1 and str(
                            dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']), 'Signal'].iloc[
                                0]) == "LONG"):
                        nu_of_lot = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'no_of_lot'].iloc[0])
                        Quantity = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Quantity'].iloc[0])

                        df1 = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "SHORT", message['ltp'], 2 * nu_of_lot, 2 * Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        trade_happen[message['symbol']] = 1

                        df_signal = pd.concat([df_signal, df1])
                        df_signal.to_csv(
                            'C://upstox_oauth//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        df1_database = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "SHORT", message['ltp'], nu_of_lot, Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = dfdatabase[
                            dfdatabase.Symbol != str(message['symbol'])]  # delete the exit position symbol
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = pd.concat([dfdatabase, df1_database])
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv", index=False)

                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] + ((pivot_price - message['ltp']) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also
                        winsound.Beep(2500, 1000)

                    elif (message['ltp'] - pivot_price >= (brick_size * brick_reversal) and trade_happen[
                        message['symbol']] == 1 and str(
                            dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']), 'Signal'].iloc[
                                0]) == "SHORT"):
                        nu_of_lot = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'no_of_lot'].iloc[0])
                        Quantity = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Quantity'].iloc[0])

                        df1 = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "LONG", message['ltp'], 2 * nu_of_lot, 2 * Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        trade_happen[message['symbol']] = 1

                        df_signal = pd.concat([df_signal, df1])
                        df_signal.to_csv(
                            'C://upstox_oauth//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        df1_database = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "LONG", message['ltp'], nu_of_lot, Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = dfdatabase[
                            dfdatabase.Symbol != str(message['symbol'])]  # delete the exit position symbol
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = pd.concat([dfdatabase, df1_database])
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv", index=False)

                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] - ((message['ltp'] - pivot_price) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also
                        winsound.Beep(2500, 1000)

                    elif (message['ltp'] - pivot_price >= brick_size and trade_happen[message['symbol']] == 1 and str(
                            dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']), 'Signal'].iloc[
                                0]) == "LONG"):
                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] - ((message['ltp'] - pivot_price) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also


                    elif (pivot_price - message['ltp'] >= brick_size and trade_happen[message['symbol']] == 1 and str(
                            dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']), 'Signal'].iloc[
                                0]) == "SHORT"):
                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] + ((pivot_price - message['ltp']) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also

            if stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']),'Timeframe'].iloc[0] == '2H':
                if (time == "11:00:00"and time == "13:00:00"and time == "15:00:00"and time == "15:30:00" and bar_written[message['symbol']] == 0 and time > "09:16:00"):

                    stock_data = pd.read_csv('C:\\upstox_oauth\\media\\Stock_Data\\' + message['symbol'] + '.csv')
                    bar_close[message['symbol']] = message['ltp']
                    print('******************************************************')

                    idx = len(stock_data)
                    stock_data.set_value(idx, 'Date', datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"))
                    stock_data.set_value(idx, 'Open', bar_open[message['symbol']])
                    stock_data.set_value(idx, 'High', bar_high[message['symbol']])
                    stock_data.set_value(idx, 'Low', bar_low[message['symbol']])
                    stock_data.set_value(idx, 'Close', bar_close[message['symbol']])

                    stock_data.to_csv('C:\\upstox_oauth\\media\\Stock_Data\\' + message['symbol'] + '.csv', index=False)

                    bar_open[message['symbol']] = 0
                    bar_high[message['symbol']] = 0
                    bar_low[message['symbol']] = 0
                    bar_close[message['symbol']] = 0
                    bar_written[message['symbol']] = 1

                    pivot_price = float(
                        stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Pivot_Price'].iloc[0])
                    brick_size = int(
                        stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'BrickSize'].iloc[0])
                    brick_reversal = int(
                        stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'BrickReversal'].iloc[
                            0]) + 1

                    if (message['ltp'] - pivot_price >= brick_size and trade_happen[message['symbol']] == 0 and not (
                            str(message['symbol']) in str(dfdatabase['Symbol']))):
                        nu_of_lot = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'no_of_lot'].iloc[0])
                        Quantity = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Quantity'].iloc[0])

                        df1 = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "LONG", message['ltp'], nu_of_lot, Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        trade_happen[message['symbol']] = 1

                        df_signal = pd.concat([df_signal, df1])
                        df_signal.to_csv(
                            'C://upstox_oauth//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = pd.concat([dfdatabase, df1])
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv", index=False)

                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] - ((message['ltp'] - pivot_price) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also
                        winsound.Beep(2500, 1000)

                    elif (pivot_price - message['ltp'] >= brick_size and trade_happen[message['symbol']] == 0 and not (
                            str(message['symbol']) in str(dfdatabase['Symbol']))):
                        nu_of_lot = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'no_of_lot'].iloc[0])
                        Quantity = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Quantity'].iloc[0])

                        df1 = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "SHORT", message['ltp'], nu_of_lot, Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        trade_happen[message['symbol']] = 1

                        df_signal = pd.concat([df_signal, df1])
                        df_signal.to_csv(
                            'C://upstox_oauth//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = pd.concat([dfdatabase, df1])
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv", index=False)

                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] + ((pivot_price - message['ltp']) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also
                        winsound.Beep(2500, 1000)

                    elif (pivot_price - message['ltp'] >= (brick_size * brick_reversal) and trade_happen[
                        message['symbol']] == 1 and str(
                            dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']), 'Signal'].iloc[
                                0]) == "LONG"):
                        nu_of_lot = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'no_of_lot'].iloc[0])
                        Quantity = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Quantity'].iloc[0])

                        df1 = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "SHORT", message['ltp'], 2 * nu_of_lot, 2 * Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        trade_happen[message['symbol']] = 1

                        df_signal = pd.concat([df_signal, df1])
                        df_signal.to_csv(
                            'C://upstox_oauth//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        df1_database = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "SHORT", message['ltp'], nu_of_lot, Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = dfdatabase[
                            dfdatabase.Symbol != str(message['symbol'])]  # delete the exit position symbol
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = pd.concat([dfdatabase, df1_database])
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv", index=False)

                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] + ((pivot_price - message['ltp']) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also
                        winsound.Beep(2500, 1000)

                    elif (message['ltp'] - pivot_price >= (brick_size * brick_reversal) and trade_happen[
                        message['symbol']] == 1 and str(
                            dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']), 'Signal'].iloc[
                                0]) == "SHORT"):
                        nu_of_lot = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'no_of_lot'].iloc[0])
                        Quantity = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Quantity'].iloc[0])

                        df1 = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "LONG", message['ltp'], 2 * nu_of_lot, 2 * Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        trade_happen[message['symbol']] = 1

                        df_signal = pd.concat([df_signal, df1])
                        df_signal.to_csv(
                            'C://upstox_oauth//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        df1_database = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "LONG", message['ltp'], nu_of_lot, Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = dfdatabase[
                            dfdatabase.Symbol != str(message['symbol'])]  # delete the exit position symbol
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = pd.concat([dfdatabase, df1_database])
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv", index=False)

                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] - ((message['ltp'] - pivot_price) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also
                        winsound.Beep(2500, 1000)

                    elif (message['ltp'] - pivot_price >= brick_size and trade_happen[message['symbol']] == 1 and str(
                            dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']), 'Signal'].iloc[
                                0]) == "LONG"):
                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] - ((message['ltp'] - pivot_price) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also


                    elif (pivot_price - message['ltp'] >= brick_size and trade_happen[message['symbol']] == 1 and str(
                            dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']), 'Signal'].iloc[
                                0]) == "SHORT"):
                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] + ((pivot_price - message['ltp']) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also



            if stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']),'Timeframe'].iloc[0] == '3H':
                if (time == "12:00:00"and time == "15:00:00" and time == "15:30:00" and bar_written[message['symbol']] == 0 and time > "09:16:00"):

                    stock_data = pd.read_csv('C:\\upstox_oauth\\media\\Stock_Data\\' + message['symbol'] + '.csv')
                    bar_close[message['symbol']] = message['ltp']
                    print('******************************************************')

                    idx = len(stock_data)
                    stock_data.set_value(idx, 'Date', datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"))
                    stock_data.set_value(idx, 'Open', bar_open[message['symbol']])
                    stock_data.set_value(idx, 'High', bar_high[message['symbol']])
                    stock_data.set_value(idx, 'Low', bar_low[message['symbol']])
                    stock_data.set_value(idx, 'Close', bar_close[message['symbol']])

                    stock_data.to_csv('C:\\upstox_oauth\\media\\Stock_Data\\' + message['symbol'] + '.csv', index=False)

                    bar_open[message['symbol']] = 0
                    bar_high[message['symbol']] = 0
                    bar_low[message['symbol']] = 0
                    bar_close[message['symbol']] = 0
                    bar_written[message['symbol']] = 1

                    pivot_price = float(
                        stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Pivot_Price'].iloc[0])
                    brick_size = int(
                        stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'BrickSize'].iloc[0])
                    brick_reversal = int(
                        stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'BrickReversal'].iloc[
                            0]) + 1

                    if (message['ltp'] - pivot_price >= brick_size and trade_happen[message['symbol']] == 0 and not (
                            str(message['symbol']) in str(dfdatabase['Symbol']))):
                        nu_of_lot = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'no_of_lot'].iloc[0])
                        Quantity = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Quantity'].iloc[0])

                        df1 = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "LONG", message['ltp'], nu_of_lot, Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        trade_happen[message['symbol']] = 1

                        df_signal = pd.concat([df_signal, df1])
                        df_signal.to_csv(
                            'C://upstox_oauth//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = pd.concat([dfdatabase, df1])
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv", index=False)

                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] - ((message['ltp'] - pivot_price) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also
                        winsound.Beep(2500, 1000)

                    elif (pivot_price - message['ltp'] >= brick_size and trade_happen[message['symbol']] == 0 and not (
                            str(message['symbol']) in str(dfdatabase['Symbol']))):
                        nu_of_lot = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'no_of_lot'].iloc[0])
                        Quantity = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Quantity'].iloc[0])

                        df1 = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "SHORT", message['ltp'], nu_of_lot, Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        trade_happen[message['symbol']] = 1

                        df_signal = pd.concat([df_signal, df1])
                        df_signal.to_csv(
                            'C://upstox_oauth//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = pd.concat([dfdatabase, df1])
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv", index=False)

                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] + ((pivot_price - message['ltp']) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also
                        winsound.Beep(2500, 1000)

                    elif (pivot_price - message['ltp'] >= (brick_size * brick_reversal) and trade_happen[
                        message['symbol']] == 1 and str(
                            dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']), 'Signal'].iloc[
                                0]) == "LONG"):
                        nu_of_lot = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'no_of_lot'].iloc[0])
                        Quantity = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Quantity'].iloc[0])

                        df1 = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "SHORT", message['ltp'], 2 * nu_of_lot, 2 * Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        trade_happen[message['symbol']] = 1

                        df_signal = pd.concat([df_signal, df1])
                        df_signal.to_csv(
                            'C://upstox_oauth//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        df1_database = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "SHORT", message['ltp'], nu_of_lot, Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = dfdatabase[
                            dfdatabase.Symbol != str(message['symbol'])]  # delete the exit position symbol
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = pd.concat([dfdatabase, df1_database])
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv", index=False)

                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] + ((pivot_price - message['ltp']) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also
                        winsound.Beep(2500, 1000)

                    elif (message['ltp'] - pivot_price >= (brick_size * brick_reversal) and trade_happen[
                        message['symbol']] == 1 and str(
                            dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']), 'Signal'].iloc[
                                0]) == "SHORT"):
                        nu_of_lot = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'no_of_lot'].iloc[0])
                        Quantity = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Quantity'].iloc[0])

                        df1 = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "LONG", message['ltp'], 2 * nu_of_lot, 2 * Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        trade_happen[message['symbol']] = 1

                        df_signal = pd.concat([df_signal, df1])
                        df_signal.to_csv(
                            'C://upstox_oauth//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        df1_database = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "LONG", message['ltp'], nu_of_lot, Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = dfdatabase[
                            dfdatabase.Symbol != str(message['symbol'])]  # delete the exit position symbol
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = pd.concat([dfdatabase, df1_database])
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv", index=False)

                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] - ((message['ltp'] - pivot_price) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also
                        winsound.Beep(2500, 1000)

                    elif (message['ltp'] - pivot_price >= brick_size and trade_happen[message['symbol']] == 1 and str(
                            dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']), 'Signal'].iloc[
                                0]) == "LONG"):
                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] - ((message['ltp'] - pivot_price) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also


                    elif (pivot_price - message['ltp'] >= brick_size and trade_happen[message['symbol']] == 1 and str(
                            dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']), 'Signal'].iloc[
                                0]) == "SHORT"):
                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] + ((pivot_price - message['ltp']) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also




            if stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']),'Timeframe'].iloc[0] == '4H':
                if (time == "13:00:00" and time == "15:30:00" and bar_written[message['symbol']] == 0 and time > "09:16:00"):

                    stock_data = pd.read_csv('C:\\upstox_oauth\\media\\Stock_Data\\' + message['symbol'] + '.csv')
                    bar_close[message['symbol']] = message['ltp']
                    print('******************************************************')

                    idx = len(stock_data)
                    stock_data.set_value(idx, 'Date', datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"))
                    stock_data.set_value(idx, 'Open', bar_open[message['symbol']])
                    stock_data.set_value(idx, 'High', bar_high[message['symbol']])
                    stock_data.set_value(idx, 'Low', bar_low[message['symbol']])
                    stock_data.set_value(idx, 'Close', bar_close[message['symbol']])

                    stock_data.to_csv('C:\\upstox_oauth\\media\\Stock_Data\\' + message['symbol'] + '.csv', index=False)

                    bar_open[message['symbol']] = 0
                    bar_high[message['symbol']] = 0
                    bar_low[message['symbol']] = 0
                    bar_close[message['symbol']] = 0
                    bar_written[message['symbol']] = 1

                    pivot_price = float(
                        stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Pivot_Price'].iloc[0])
                    brick_size = int(
                        stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'BrickSize'].iloc[0])
                    brick_reversal = int(
                        stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'BrickReversal'].iloc[
                            0]) + 1

                    if (message['ltp'] - pivot_price >= brick_size and trade_happen[message['symbol']] == 0 and not (
                            str(message['symbol']) in str(dfdatabase['Symbol']))):
                        nu_of_lot = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'no_of_lot'].iloc[0])
                        Quantity = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Quantity'].iloc[0])

                        df1 = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "LONG", message['ltp'], nu_of_lot, Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        trade_happen[message['symbol']] = 1

                        df_signal = pd.concat([df_signal, df1])
                        df_signal.to_csv(
                            'C://upstox_oauth//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = pd.concat([dfdatabase, df1])
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv", index=False)

                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] - ((message['ltp'] - pivot_price) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also
                        winsound.Beep(2500, 1000)

                    elif (pivot_price - message['ltp'] >= brick_size and trade_happen[message['symbol']] == 0 and not (
                            str(message['symbol']) in str(dfdatabase['Symbol']))):
                        nu_of_lot = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'no_of_lot'].iloc[0])
                        Quantity = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Quantity'].iloc[0])

                        df1 = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "SHORT", message['ltp'], nu_of_lot, Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        trade_happen[message['symbol']] = 1

                        df_signal = pd.concat([df_signal, df1])
                        df_signal.to_csv(
                            'C://upstox_oauth//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = pd.concat([dfdatabase, df1])
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv", index=False)

                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] + ((pivot_price - message['ltp']) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also
                        winsound.Beep(2500, 1000)

                    elif (pivot_price - message['ltp'] >= (brick_size * brick_reversal) and trade_happen[
                        message['symbol']] == 1 and str(
                            dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']), 'Signal'].iloc[
                                0]) == "LONG"):
                        nu_of_lot = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'no_of_lot'].iloc[0])
                        Quantity = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Quantity'].iloc[0])

                        df1 = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "SHORT", message['ltp'], 2 * nu_of_lot, 2 * Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        trade_happen[message['symbol']] = 1

                        df_signal = pd.concat([df_signal, df1])
                        df_signal.to_csv(
                            'C://upstox_oauth//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        df1_database = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "SHORT", message['ltp'], nu_of_lot, Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = dfdatabase[
                            dfdatabase.Symbol != str(message['symbol'])]  # delete the exit position symbol
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = pd.concat([dfdatabase, df1_database])
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv", index=False)

                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] + ((pivot_price - message['ltp']) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also
                        winsound.Beep(2500, 1000)

                    elif (message['ltp'] - pivot_price >= (brick_size * brick_reversal) and trade_happen[
                        message['symbol']] == 1 and str(
                            dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']), 'Signal'].iloc[
                                0]) == "SHORT"):
                        nu_of_lot = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'no_of_lot'].iloc[0])
                        Quantity = int(
                            stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']), 'Quantity'].iloc[0])

                        df1 = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "LONG", message['ltp'], 2 * nu_of_lot, 2 * Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        trade_happen[message['symbol']] = 1

                        df_signal = pd.concat([df_signal, df1])
                        df_signal.to_csv(
                            'C://upstox_oauth//media//Upstox_Tradesheet//' + datetime.now(pytz.timezone(tz)).strftime(
                                "%d-%m-%y") + '_signal_Upstox.csv', index=False)

                        df1_database = pd.DataFrame(
                            [[message['symbol'], datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"), \
                              "LONG", message['ltp'], nu_of_lot, Quantity]], \
                            columns=["Symbol", "Date", "Signal", "Price", "Lots", "Qty"])

                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = dfdatabase[
                            dfdatabase.Symbol != str(message['symbol'])]  # delete the exit position symbol
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase = pd.concat([dfdatabase, df1_database])
                        dfdatabase = dfdatabase.drop_duplicates()
                        dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv", index=False)

                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] - ((message['ltp'] - pivot_price) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also
                        winsound.Beep(2500, 1000)

                    elif (message['ltp'] - pivot_price >= brick_size and trade_happen[message['symbol']] == 1 and str(
                            dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']), 'Signal'].iloc[
                                0]) == "LONG"):
                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] - ((message['ltp'] - pivot_price) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also


                    elif (pivot_price - message['ltp'] >= brick_size and trade_happen[message['symbol']] == 1 and str(
                            dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']), 'Signal'].iloc[
                                0]) == "SHORT"):
                        df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                        stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (
                                    message['ltp'] + ((pivot_price - message['ltp']) % brick_size))
                        stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",
                                         index=False)  # update the pivot price in csv also




            if(int(str(time).split(':')[1]) % int(stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']),'Timeframe'].iloc[0])==0 and \
              bar_written[message['symbol']]==0 and time > "09:16:00"):

                stock_data=pd.read_csv('C:\\upstox_oauth\\media\\Stock_Data\\'+message['symbol']+'.csv')
                bar_close[message['symbol']]=message['ltp']
                print('******************************************************')

                idx = len(stock_data)
                stock_data.set_value(idx, 'Date', datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"))
                stock_data.set_value(idx, 'Open',bar_open[message['symbol']])
                stock_data.set_value(idx, 'High',bar_high[message['symbol']])
                stock_data.set_value(idx, 'Low',bar_low[message['symbol']])
                stock_data.set_value(idx, 'Close',bar_close[message['symbol']])

                stock_data.to_csv('C:\\upstox_oauth\\media\\Stock_Data\\'+message['symbol']+'.csv',index=False)

                bar_open[message['symbol']]=0
                bar_high[message['symbol']]=0
                bar_low[message['symbol']]=0
                bar_close[message['symbol']]=0
                bar_written[message['symbol']]=1

                pivot_price = float(stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']),'Pivot_Price'].iloc[0])
                brick_size = int(stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']),'BrickSize'].iloc[0])
                brick_reversal = int(stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']),'BrickReversal'].iloc[0]) + 1

                if(message['ltp'] - pivot_price >= brick_size and trade_happen[message['symbol']]==0 and  not(str(message['symbol']) in str(dfdatabase['Symbol']))):
                    nu_of_lot = int(stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']),'no_of_lot'].iloc[0])
                    Quantity = int(stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']),'Quantity'].iloc[0])

                    df1 = pd.DataFrame([[message['symbol'],datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"),\
                                                 "LONG",message['ltp'],nu_of_lot,Quantity]],\
                            columns = ["Symbol","Date","Signal","Price","Lots","Qty"])

                    trade_happen[message['symbol']]=1

                    df_signal = pd.concat([df_signal, df1])
                    df_signal.to_csv('C://upstox_oauth//media//Upstox_Tradesheet//'+datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y")+'_signal_Upstox.csv',index=False)

                    dfdatabase = dfdatabase.drop_duplicates()
                    dfdatabase = pd.concat([dfdatabase, df1])
                    dfdatabase=dfdatabase.drop_duplicates()
                    dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv",index=False)

                    df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                    stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (message['ltp'] - ((message['ltp']-pivot_price)%brick_size))
                    stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",index=False)#update the pivot price in csv also
                    winsound.Beep(2500, 1000)

                elif(pivot_price - message['ltp'] >= brick_size and trade_happen[message['symbol']]==0 and  not(str(message['symbol']) in str(dfdatabase['Symbol']))):
                    nu_of_lot = int(stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']),'no_of_lot'].iloc[0])
                    Quantity = int(stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']),'Quantity'].iloc[0])

                    df1 = pd.DataFrame([[message['symbol'],datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"),\
                                                 "SHORT",message['ltp'],nu_of_lot,Quantity]],\
                            columns = ["Symbol","Date","Signal","Price","Lots","Qty"])

                    trade_happen[message['symbol']]=1

                    df_signal = pd.concat([df_signal, df1])
                    df_signal.to_csv('C://upstox_oauth//media//Upstox_Tradesheet//'+datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y")+'_signal_Upstox.csv',index=False)

                    dfdatabase=dfdatabase.drop_duplicates()
                    dfdatabase = pd.concat([dfdatabase, df1])
                    dfdatabase=dfdatabase.drop_duplicates()
                    dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv",index=False)

                    df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                    stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (message['ltp'] + ((pivot_price - message['ltp'])%brick_size))
                    stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",index=False)#update the pivot price in csv also
                    winsound.Beep(2500, 1000)

                elif(pivot_price - message['ltp'] >= (brick_size * brick_reversal) and trade_happen[message['symbol']]==1  and str(dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']),'Signal'].iloc[0])=="LONG"):
                    nu_of_lot = int(stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']),'no_of_lot'].iloc[0])
                    Quantity = int(stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']),'Quantity'].iloc[0])

                    df1 = pd.DataFrame([[message['symbol'],datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"),\
                                                 "SHORT",message['ltp'],2 * nu_of_lot,2 * Quantity]],\
                            columns = ["Symbol","Date","Signal","Price","Lots","Qty"])


                    trade_happen[message['symbol']]=1

                    df_signal = pd.concat([df_signal, df1])
                    df_signal.to_csv('C://upstox_oauth//media//Upstox_Tradesheet//'+datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y")+'_signal_Upstox.csv',index=False)

                    df1_database = pd.DataFrame([[message['symbol'],datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"),\
                                                 "SHORT",message['ltp'],nu_of_lot,Quantity]],\
                            columns = ["Symbol","Date","Signal","Price","Lots","Qty"])

                    dfdatabase=dfdatabase.drop_duplicates()
                    dfdatabase = dfdatabase[dfdatabase.Symbol != str(message['symbol'])] # delete the exit position symbol
                    dfdatabase=dfdatabase.drop_duplicates()
                    dfdatabase = pd.concat([dfdatabase, df1_database])
                    dfdatabase=dfdatabase.drop_duplicates()
                    dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv",index=False)

                    df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                    stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (message['ltp'] + ((pivot_price - message['ltp'])%brick_size))
                    stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",index=False)#update the pivot price in csv also
                    winsound.Beep(2500, 1000)

                elif (message['ltp'] - pivot_price >= (brick_size * brick_reversal) and trade_happen[message['symbol']]==1  and str(dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']),'Signal'].iloc[0])=="SHORT"):
                    nu_of_lot = int(stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']),'no_of_lot'].iloc[0])
                    Quantity = int(stocklist.loc[stocklist['ContractSymbol'] == str(message['symbol']),'Quantity'].iloc[0])

                    df1 = pd.DataFrame([[message['symbol'],datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"),\
                                                 "LONG",message['ltp'],2 * nu_of_lot,2 * Quantity]],\
                            columns = ["Symbol","Date","Signal","Price","Lots","Qty"])


                    trade_happen[message['symbol']]=1

                    df_signal = pd.concat([df_signal, df1])
                    df_signal.to_csv('C://upstox_oauth//media//Upstox_Tradesheet//'+datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y")+'_signal_Upstox.csv',index=False)

                    df1_database = pd.DataFrame([[message['symbol'],datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y %H:%M:%S"),\
                                                 "LONG",message['ltp'],nu_of_lot,Quantity]],\
                            columns = ["Symbol","Date","Signal","Price","Lots","Qty"])

                    dfdatabase=dfdatabase.drop_duplicates()
                    dfdatabase = dfdatabase[dfdatabase.Symbol != str(message['symbol'])] # delete the exit position symbol
                    dfdatabase=dfdatabase.drop_duplicates()
                    dfdatabase = pd.concat([dfdatabase, df1_database])
                    dfdatabase=dfdatabase.drop_duplicates()
                    dfdatabase.to_csv("C://upstox_oauth//media//Signal_DataBase.csv",index=False)

                    df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                    stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (message['ltp'] - ((message['ltp']-pivot_price)%brick_size))
                    stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",index=False)#update the pivot price in csv also
                    winsound.Beep(2500, 1000)

                elif (message['ltp'] - pivot_price >= brick_size and trade_happen[message['symbol']]==1  and str(dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']),'Signal'].iloc[0])=="LONG"):
                    df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                    stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (message['ltp'] - ((message['ltp']-pivot_price)%brick_size))
                    stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",index=False)#update the pivot price in csv also


                elif (pivot_price - message['ltp'] >= brick_size and trade_happen[message['symbol']]==1  and str(dfdatabase.loc[dfdatabase['Symbol'] == str(message['symbol']),'Signal'].iloc[0])=="SHORT"):
                    df_stock_index = stocklist.index[stocklist['ContractSymbol'] == str(message['symbol'])].tolist()
                    stocklist['Pivot_Price'].iloc[df_stock_index[0]] = (message['ltp'] + ((pivot_price - message['ltp'])%brick_size))
                    stocklist.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",index=False)#update the pivot price in csv also
    
    u.set_on_quote_update(event_handler_quote_update)    
    u.set_on_disconnect(event_handler_socket_disconnect)
    
    
    for i in range(len(stocklist)):
        try:
            u.unsubscribe(u.get_instrument_by_symbol(stocklist['ExchangeSymbol'].iloc[i], stocklist['ContractSymbol'].iloc[i]), LiveFeedType.LTP)        
        except:
            pass
    for stock in stocklist_marketwatch['ContractSymbol']:
        try:
            u.subscribe(u.get_instrument_by_symbol(stocklist.loc[stocklist['ContractSymbol'] == str(stock),'ExchangeSymbol'].iloc[0], stock), LiveFeedType.LTP)
        except:
            pass
    print("connection with socket")
    u.start_websocket(False)
     
    return HttpResponse("Algo started")

           
def get_log(request):
  
    results1=""
    
    df_new = pd.DataFrame(list(dict_out.items()), columns=['Symbol', 'Price'])
    
    df_old = dict_out_backup
    df_old = pd.DataFrame(list(df_old.items()), columns=['Symbol', 'Price'])
  
    the_table = """<table border="1" class="dataframe" style = " margin-left: 100px;">
    <thead>
    <tr style="text-align: right;">
      <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Symbol</th>
      <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Price</th>
    </tr>
    </thead>
    <tbody>"""
    if(len(df_new)==0):
        df_start_price_symbol=pd.read_csv('C:\\upstox_oauth\\media\\UpstoxList_marketwatch.csv')
        
        for k in range(0,len(df_start_price_symbol)):
            
            try: 
               value1=df_start_price_symbol['ContractSymbol'].iloc[k] 
               
               value2="--"

               the_table+="""<tr>
                                <td>%(value1)s</td>
                                <td><centre>%(value2)s</centre></td>
                            </tr>"""% {'value1': value1, 
                                       'value2': value2,
                                       } 
            except:
                 pass
        
    else:
        for k in range(0,len(df_new)):
            
            try: 
               value1=df_new['Symbol'].iloc[k]
               value2=df_new['Price'].iloc[k]
               value3=df_old['Price'].iloc[k]
               
               the_table+="""<tr>
                                <td>%(value1)s</td>
                                <td style="background-color: %(color1)s;"><font color="white">%(value2)s</font></td>
                            </tr>"""% {'value1': value1, 
                                       'value2': round(value2,2),
                                       'value3': round(value3,2),
                                       'color1': get_color_for_ticker(value2,value3)
                                       } 
            except:
                 pass
    
    the_table+="""</tbody>
                </table>"""
    
    results1+=the_table

    dict_out_backup.update(dict_out)

    try:
        stocks_signal = pd.read_csv('C://upstox_oauth//media//Upstox_Tradesheet//'+datetime.now(pytz.timezone(tz)).strftime("%d-%m-%y")+'_signal_Upstox.csv')
        stocks_signal = stocks_signal.to_html(index = False).replace('<th>','<th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">')
        results1 += stocks_signal
    except:
        stocks_signal = pd.DataFrame(columns = ["Symbol","Date","Signal","Price","Lots","Qty"])
        stocks_signal = stocks_signal.to_html(index = False).replace('<th>','<th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">')
        results1 += stocks_signal
    #P and L calculation computed here
    try:
        stocks_pos=pd.read_csv("C://upstox_oauth//media//Signal_DataBase.csv")
        stocklist_for_reversal = pd.read_csv("C://upstox_oauth//media//Upstox_stocklist.csv")
        
        if(len(stocks_pos)==0):
            stocks_pos = stocks_pos.to_html(index = False).replace('<th>','<th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">')
            results1 += stocks_pos
        else:
            df_pos=pd.DataFrame()
            for i in range(len(stocks_pos)):
                pivotPriceForReversal = float(stocklist_for_reversal.loc[stocklist_for_reversal['ContractSymbol'] == str(stocks_pos['Symbol'].iloc[i]),'Pivot_Price'].iloc[0])
                brickSizeForReversal = int(stocklist_for_reversal.loc[stocklist_for_reversal['ContractSymbol'] == str(stocks_pos['Symbol'].iloc[i]),'BrickSize'].iloc[0])
                brickReversalForReversal = int(stocklist_for_reversal.loc[stocklist_for_reversal['ContractSymbol'] == str(stocks_pos['Symbol'].iloc[i]),'BrickReversal'].iloc[0]) + 1

                try:
                    if(len(df_new)!=0 and  (str(stocks_pos['Symbol'].iloc[i]) in str(df_new['Symbol']))):
                        if(str(stocks_pos['Signal'].iloc[i])=="LONG"):
                            df_bar = pd.DataFrame([[stocks_pos['Symbol'].iloc[i],stocks_pos['Date'].iloc[i],stocks_pos['Signal'].iloc[i],\
                                                   stocks_pos['Price'].iloc[i],stocks_pos['Lots'].iloc[i],stocks_pos['Qty'].iloc[i],round(pivotPriceForReversal - (brickSizeForReversal * brickReversalForReversal),2),\
                                                   round(((df_new.loc[df_new['Symbol']== str(stocks_pos['Symbol'].iloc[i]),'Price'].iloc[0])*stocks_pos['Qty'].iloc[i])\
                                                    -(stocks_pos['Price'].iloc[i]*stocks_pos['Qty'].iloc[i]),2)]],\
                                                columns = ["Symbol","Date","Signal","Price","Lots","Qty","Reversal Value","P&L"])
                        else:
                            df_bar = pd.DataFrame([[stocks_pos['Symbol'].iloc[i],stocks_pos['Date'].iloc[i],stocks_pos['Signal'].iloc[i],\
                                                   stocks_pos['Price'].iloc[i],stocks_pos['Lots'].iloc[i],stocks_pos['Qty'].iloc[i],round(pivotPriceForReversal + (brickSizeForReversal * brickReversalForReversal),2),\
                                                   round((stocks_pos['Price'].iloc[i]*stocks_pos['Qty'].iloc[i])\
                                                   -((df_new.loc[df_new['Symbol']== str(stocks_pos['Symbol'].iloc[i]),'Price'].iloc[0])*stocks_pos['Qty'].iloc[i]),2)]],\
                                                columns = ["Symbol","Date","Signal","Price","Lots","Qty","Reversal Value","P&L"])
                    else:
                        if(str(stocks_pos['Signal'].iloc[i])=="LONG"):
                            df_bar = pd.DataFrame([[stocks_pos['Symbol'].iloc[i],stocks_pos['Date'].iloc[i],stocks_pos['Signal'].iloc[i],\
                                                       stocks_pos['Price'].iloc[i],stocks_pos['Lots'].iloc[i],stocks_pos['Qty'].iloc[i],round(pivotPriceForReversal - (brickSizeForReversal * brickReversalForReversal),2),\
                                                        "--"]],\
                                                    columns = ["Symbol","Date","Signal","Price","Lots","Qty","Reversal Value","P&L"])
                        else:   
                            df_bar = pd.DataFrame([[stocks_pos['Symbol'].iloc[i],stocks_pos['Date'].iloc[i],stocks_pos['Signal'].iloc[i],\
                                                       stocks_pos['Price'].iloc[i],stocks_pos['Lots'].iloc[i],stocks_pos['Qty'].iloc[i],round(pivotPriceForReversal + (brickSizeForReversal * brickReversalForReversal),2),\
                                                       "--"]],\
                                                    columns = ["Symbol","Date","Signal","Price","Lots","Qty","Reversal Value","P&L"])
                            
                except:
                    continue
                df_pos = pd.concat([df_pos, df_bar]) 
                

            
            the_table_pos = """<table border="1" class="dataframe">
            <thead>
            <tr style="text-align: right;">
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Symbol</th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Date</th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Signal</th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Price</th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Lots</th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Qty</th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Reversal Value</th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">P&L</th>
            </tr>
            </thead>
            <tbody>"""
            
            for k in range(0,len(df_pos)):
                
                try: 
                   value1=df_pos['Symbol'].iloc[k]
                   value2=df_pos['Date'].iloc[k]
                   value3=df_pos['Signal'].iloc[k]
                   value4=df_pos['Price'].iloc[k]
                   value5=df_pos['Lots'].iloc[k]
                   value6=df_pos['Qty'].iloc[k]
                   value7=df_pos['Reversal Value'].iloc[k]
                   value8=df_pos['P&L'].iloc[k]
                   the_table_pos+="""<tr>
                                    <td>%(value1)s</td>
                                    <td>%(value2)s</td>
                                    <td>%(value3)s</td>
                                    <td>%(value4)s</td>
                                    <td>%(value5)s</td>
                                    <td>%(value6)s</td>
                                    <td>%(value7)s</td>
                                    <td>%(value8)s</td>
                                    
                                </tr>"""% {'value1': value1, 
                                           'value2': value2,
                                           'value3': value3,
                                           'value4': value4,
                                           'value5': value5,
                                           'value6': value6,
                                           'value7': value7,
                                           'value8': value8
                                           } 
                except:
                     pass
            
            the_table_pos+="""</tbody>
                        </table>"""
            
            results1+=the_table_pos

    except:
        stocks_pos = pd.DataFrame(columns = ["Symbol","Date","Signal","Price","Lots","Qty","Reversal Value","P&L"])
        stocks_pos = stocks_pos.to_html(index = False).replace('<th>','<th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">')
        results1 += stocks_pos

        
    return HttpResponse(results1)    

def get_color_for_ticker(value2,value3):
    #print(value2+"*********"+value3)
    if(value2>value3):
        return "green"
    elif(value2<value3):
        return "Red" 
    else:
        return "#4d4d4d"     
            
            
def updatemarketwatchstrike(request):
    url = request.get_full_path
    print(url)
    params = str(url)[:-3].split('?')[1]
    params = str(params).split('*%*')

    df1=pd.read_csv("C://upstox_oauth//media//Upstox_stocklist.csv")

    idx = len(df1)

    df1.set_value(idx, 'S_no', int(idx))
    df1.set_value(idx, 'ContractSymbol', str(params[0]))
    df1.set_value(idx, 'ExchangeSymbol', str(params[1]))
    df1.set_value(idx, 'BrickSize', params[2])
    df1.set_value(idx, 'BrickReversal', params[3])
    df1.set_value(idx, 'Timeframe', params[4])
    df1.set_value(idx, 'no_of_lot', params[5])
    df1.set_value(idx, 'Quantity', params[6])
    df1.set_value(idx, 'Pivot_Price', params[7])
    
    df1.drop_duplicates(subset ="ContractSymbol", keep = "first", inplace = True) 
    
    df1.to_csv("C://upstox_oauth//media//Upstox_stocklist.csv",index=False)
    error=""
    return JsonResponse({"error": error})           
            
def get_stocklistmkt(request):
    url = request.get_full_path
    print(url)
    params = str(url)[:-3].split('?')[1]
    nameofmktwatch=params.split('***')[1]
    params = params.split('***')[0]
    #stocklist123=pd.DataFrame()
    #for i in range(len(params)):
    df1 = pd.DataFrame([[params]],columns = ["ContractSymbol"]) 
    df1.to_csv("C://upstox_oauth//media//market_watchlist//"+nameofmktwatch+".csv",index=False)
    error=""
    return JsonResponse({"error": error}) 

def scrip_master_updation(request):
    shutil.rmtree('C:\\upstox_oauth\\media\\Stock_Data\\')
    os.mkdir("C:\\upstox_oauth\\media\\Stock_Data")
    
    url = request.get_full_path
    print(url)
    params = str(url)[:-3].split('?')[1]
    stocklist123=pd.read_csv("C://upstox_oauth//media//market_watchlist//"+params.split('*&*')[0]+".csv")
    stocks_name = []
    df_stocks = pd.DataFrame()
    stocks_name=str(stocklist123["ContractSymbol"].iloc[0]).split(',')
    for i in range(len(stocks_name)):
        new_stock_data = pd.DataFrame(columns = ['Date', 'Open', 'High', 'Low', 'Close'])
        new_stock_data.to_csv('C://upstox_oauth//media//Stock_Data//' + str(stocks_name[i]) + '.csv', index = False)
        df1 = pd.DataFrame([[str(stocks_name[i]),str(params.split('*&*')[0])]],columns = ["ContractSymbol","name_of_marketwatch"])    
        df_stocks = pd.concat([df_stocks, df1])
        
    df_stocks.to_csv("C://upstox_oauth//media//UpstoxList_marketwatch.csv",index=False)
    error=""
    return JsonResponse({"error": error})

def MarketWatch(request):
    return render(request, "upstox_auth/marketwatchpage.html", {})

def screener_only(request):
    results1screener=""    
    try:
        print("************************************************************")
        df_marketwatch=pd.read_csv('C://upstox_oauth//media//UpstoxList_marketwatch.csv')
        df_pos=pd.read_csv('C://upstox_oauth//media//Upstox_stocklist.csv')
        df_pos = df_pos.drop_duplicates()
        df_marketwatch = df_marketwatch.drop_duplicates()
    
        if(len(df_marketwatch)==0):
            results1screener += "No Stock"
        else:
            the_table_pos = """<table border="1" class="table table-striped">
            <thead>
            <tr style="text-align: right;">
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">S No.</th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Contract Symbol</th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Exchange Symbol</th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Brick Size</th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Brick Reversal</th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Timeframe</th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">No. of Lots</th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Quantity</th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;">Pivot Price</th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;"></th>
              <th style = "background-color : DodgerBlue; padding-top: 12px; padding-bottom: 12px; text-align: left; color: white; font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;"></th>
            </tr>
            </thead>
            <tbody>"""
            
            for k in range(0,len(df_marketwatch)):
                
                try: 
                   value1 = k+1
                   value2 = df_marketwatch['ContractSymbol'].iloc[k]
                   value3 = df_pos.loc[df_pos["ContractSymbol"] == str(df_marketwatch['ContractSymbol'].iloc[k]),'ExchangeSymbol'].iloc[0]
                   value4 = int(df_pos.loc[df_pos["ContractSymbol"] == str(df_marketwatch['ContractSymbol'].iloc[k]),'BrickSize'].iloc[0])
                   value5 = int(df_pos.loc[df_pos["ContractSymbol"] == str(df_marketwatch['ContractSymbol'].iloc[k]),'BrickReversal'].iloc[0])
                   value6 = int(df_pos.loc[df_pos["ContractSymbol"] == str(df_marketwatch['ContractSymbol'].iloc[k]),'Timeframe'].iloc[0])
                   value7 = int(df_pos.loc[df_pos["ContractSymbol"] == str(df_marketwatch['ContractSymbol'].iloc[k]),'no_of_lot'].iloc[0])
                   value8 = int(df_pos.loc[df_pos["ContractSymbol"] == str(df_marketwatch['ContractSymbol'].iloc[k]),'Quantity'].iloc[0])
                   value9 = round(df_pos.loc[df_pos["ContractSymbol"] == str(df_marketwatch['ContractSymbol'].iloc[k]),'Pivot_Price'].iloc[0], 2)
                   value10 = df_marketwatch['ContractSymbol'].iloc[k]
                   value11 = df_marketwatch['ContractSymbol'].iloc[k]
    
                   
                   the_table_pos+="""<tr>
                                    <td>%(value1)s</td>
                                    <td>%(value2)s</td>
                                    <td>%(value3)s</td>
                                    <td>%(value4)s</td>
                                    <td>%(value5)s</td>
                                    <td>%(value6)s</td>
                                    <td>%(value7)s</td>
                                    <td>%(value8)s</td>
                                    <td>%(value9)s</td>
                                    <td id=%(value10)s onclick="mainDataBase(this.id)"><a href= "javascript:void(0)">Remove</a></td>
                                    <td id=%(value11)s onclick="updateDataBase(this.id)"><a href= "javascript:void(0)">UpdateParameter</a></td>
                                    
                                </tr>"""% {'value1': value1, 
                                           'value2': value2,
                                           'value3': value3,
                                           'value4': value4,
                                           'value5': value5,
                                           'value6': value6,
                                           'value7': value7,
                                           'value8': value8,
                                           'value9': value9,
                                           'value10': value10,
                                           'value11': value11,
                                           } 
                except:
                     pass
            
            the_table_pos+="""</tbody>
                        </table>"""
            
            results1screener+=the_table_pos
    
    except:   
        results1screener += "No Stock"
    return HttpResponse(results1screener)

def removeStock_maindatabase(request):
    url = request.get_full_path
    print(url)
    params = str(url)[:-3].split('?')[1]
    params = str(params).split('$$')[0]
    
    print(params)
    
    try:
       df_marketwatch=pd.read_csv('C://upstox_oauth//media//UpstoxList_marketwatch.csv')
       df_frommarket = pd.read_csv("C://upstox_oauth//media//market_watchlist//"+str(df_marketwatch['name_of_marketwatch'].iloc[0])+".csv")
       
       df_marketwatch=df_marketwatch.drop_duplicates()
       df_marketwatch=df_marketwatch.loc[df_marketwatch['ContractSymbol'] != str(params)]
       df_marketwatch=df_marketwatch.drop_duplicates()
       df_marketwatch.to_csv('C://upstox_oauth//media//UpstoxList_marketwatch.csv',index=False)
       
       string_params=params + ','
       
       if (string_params in df_frommarket['ContractSymbol'].iloc[0]):
           df_frommarket['ContractSymbol'].iloc[0]=df_frommarket['ContractSymbol'].iloc[0].replace(string_params,'')
       else:
           string_params = ',' + params
           df_frommarket['ContractSymbol'].iloc[0]=df_frommarket['ContractSymbol'].iloc[0].replace(string_params,'')
           
       df_frommarket.to_csv("C://upstox_oauth//media//market_watchlist//"+str(df_marketwatch['name_of_marketwatch'].iloc[0])+".csv",index=False)
       
    except:
        print("error in Removal")

    error=""
    return JsonResponse({"error": error})

def update_maindatabase(request):

    url = request.get_full_path
    print(url)
    params = str(url)[:-3].split('?')[1]
    params = str(params).split('$$')[0]
   
    print(params)
    
    try:
       df_StockDetail=pd.read_csv('C://upstox_oauth//media//Upstox_stocklist.csv')
       
       df_stock_index = df_StockDetail.index[df_StockDetail['ContractSymbol'] == str(params).split('*')[0]].tolist()
       
       df_StockDetail['BrickSize'].iloc[df_stock_index[0]] = str(params).split('*')[1]
       df_StockDetail['BrickReversal'].iloc[df_stock_index[0]] = str(params).split('*')[2]
       df_StockDetail['Timeframe'].iloc[df_stock_index[0]] = str(params).split('*')[3]
       df_StockDetail['no_of_lot'].iloc[df_stock_index[0]] = str(params).split('*')[4]
       df_StockDetail['Quantity'].iloc[df_stock_index[0]] = str(params).split('*')[5]
       df_StockDetail['Pivot_Price'].iloc[df_stock_index[0]] = str(params).split('*')[6]

       df_StockDetail=df_StockDetail.drop_duplicates()
       df_StockDetail.to_csv('C://upstox_oauth//media//Upstox_stocklist.csv',index=False)
       
    except:
        print("error in updating")

    error=""
    return JsonResponse({"error": error})
 
            
            
    