from django.shortcuts import render, HttpResponse
from upstox_api.api import *
import pandas as pd
from pandas.tseries.offsets import BDay
import math
import csv
from upstox_api.api import *
import dotenv
import os
import time
from datetime import datetime
# Create your views here.


def indexfunc(request):
    if request.method == "GET":
        return render(request, 'backtest/index2.html')

    elif request.method == 'POST':
        exchange = request.POST['exchange']
        contract = request.POST['contract']
        timeframe = request.POST['timeframe']
        Date = request.POST['filter'].split()
        bricksize = request.POST['bricksize']
        brickreversal = int(request.POST['brickreversal']) + 1
        pivotprice = request.POST['pivotprice']
        bricksizepercentage = request.POST['bricksizepercentage']

        if pivotprice:
            if bricksize and not bricksizepercentage:
                API_KEY = os.getenv('API_KEY')
                TOKEN = dotenv.get_key(dotenv.find_dotenv(), 'ACCESS_TOKEN')
                # 'startDate': '02/07/2012',
                # 'endDate': '02/07/2018',
                config = {
                    'startDate': Date[0],
                    'endDate': Date[1],
                    'apiKey': API_KEY,
                    'accessToken': TOKEN
                }
                u = Upstox(config['apiKey'], config['accessToken'])
                u.get_master_contract(exchange)
                u.get_instrument_by_symbol(exchange, contract)

                if timeframe == '1DAY' or timeframe == '1WEEK' or timeframe == '1MONTH':
                    data = u.get_ohlc(u.get_instrument_by_symbol(exchange, contract), timeframe,
                                      datetime.strptime(config['startDate'], '%d-%m-%Y').date(),
                                      datetime.strptime(config['endDate'], '%d-%m-%Y').date())
                    df = pd.DataFrame(data)
                else:
                    x = datetime.strptime(config['startDate'], '%d-%m-%Y')
                    df = pd.DataFrame()
                    while x <= datetime.strptime(config['endDate'], '%d-%m-%Y'):
                        data = u.get_ohlc(u.get_instrument_by_symbol(exchange, contract), timeframe,
                                          datetime.strptime(str(x).split(' ')[0], '%Y-%m-%d').date(),
                                          datetime.strptime(str(x + BDay(4)).split(' ')[0], '%Y-%m-%d').date())
                        temp = pd.DataFrame(data)
                        df = pd.concat([df, temp])
                        df = df.reset_index(drop=True)
                        x += BDay(4)

                # First Pause of 15 seconds
                time.sleep(20)
                box_size = int(bricksize)
                n_multiplies_box_size = brickreversal  # n_multiplies_box_size
                trend = ""
                trade = ""
                pivot_Price = 0
                for i in range(len(df)):
                    df['timestamp'].iloc[i] = datetime.fromtimestamp(int(df['timestamp'].iloc[i]) / 1000)

                df = df.rename(columns={"timestamp": "DateTime"})
                for i in range(len(df)):
                    if i == 0:
                        pivot_Price = float(pivotprice)
                        continue

                    if trend == "":
                        if (float(df["close"].iloc[i]) >= box_size + pivot_Price):
                            trend = "Upward"
                            df.at[i, "Trend"] = trend
                            df.at[i, "Brick"] = "GreenBrick"
                            pivot_Price = float(df["close"].iloc[i]) - ((float(df["close"].iloc[i]) - pivot_Price) % box_size)
                            df.at[i, "PivotPrice"] = pivot_Price
                            continue

                        if (float(df["close"].iloc[i]) <= pivot_Price - box_size):
                            trend = "Downward"
                            df.at[i, "Trend"] = trend
                            df.at[i, "Brick"] = "RedBrick"
                            pivot_Price = float(df["close"].iloc[i]) + (
                                    (pivot_Price - float(df["close"].iloc[i])) % (box_size))
                            df.at[i, "PivotPrice"] = pivot_Price
                            continue

                    if trend == "Upward":
                        if (pivot_Price - float(df["close"].iloc[i]) >= box_size * n_multiplies_box_size):
                            trade = "ReverseOfUpward"
                            trend = "Downward"
                            pivot_Price = float(df["close"].iloc[i]) + (
                                    (pivot_Price - float(df["close"].iloc[i])) % (box_size))
                            df.at[i, "PivotPrice"] = pivot_Price
                            df.at[i, "TRADE"] = trade
                            df.at[i, "Trend"] = trend
                            df.at[i, "Brick"] = "RedBrick"
                            continue

                        if (float(df["close"].iloc[i]) >= box_size + pivot_Price):
                            trend = "Upward"
                            df.at[i, "Trend"] = trend
                            df.at[i, "Brick"] = "GreenBrick"
                            pivot_Price = float(df["close"].iloc[i]) - (
                                    (float(df["close"].iloc[i]) - pivot_Price) % box_size)
                            df.at[i, "PivotPrice"] = pivot_Price

                    if trend == "Downward":
                        if (float(df["close"].iloc[i]) - pivot_Price >= box_size * n_multiplies_box_size):
                            trade = "ReverseOfDownward"
                            trend = "Upward"
                            pivot_Price = float(df["close"].iloc[i]) - (
                                    (float(df["close"].iloc[i]) - pivot_Price) % box_size)
                            df.at[i, "PivotPrice"] = pivot_Price
                            df.at[i, "TRADE"] = trade
                            df.at[i, "Trend"] = trend
                            df.at[i, "Brick"] = "GreenBrick"
                            continue

                        if (float(df["close"].iloc[i]) <= pivot_Price - box_size):
                            trend = "Downward"
                            df.at[i, "Trend"] = trend
                            df.at[i, "Brick"] = "RedBrick"
                            pivot_Price = float(df["close"].iloc[i]) + (
                                    (pivot_Price - float(df["close"].iloc[i])) % (box_size))
                            df.at[i, "PivotPrice"] = pivot_Price

                df.to_csv("C://upstox_oauth//media//Backtest//" + contract + "signal.csv", index=False)
                time.sleep(20)

                # Second Pause of 10 seconds
                df1 = pd.read_csv("C://upstox_oauth//media//Backtest//" + contract + "signal.csv")
                EntryPrice = 0
                ExitPrice = 0
                tradehappen = 0
                tradetype = ''
                PNL = 0
                PNLPercent = 0

                for i in range(len(df1)):
                    if df1["Brick"].iloc[i] == "GreenBrick" and df1["Trend"].iloc[i] == "Upward" and tradehappen == 0:
                        df1.at[i, 'BuySignal'] = 'BUY'
                        EntryPrice = float(df["close"].iloc[i])
                        df1.at[i, 'BuyEntryPrice'] = EntryPrice
                        tradehappen = 1
                        tradetype = 'LONG'
                        continue

                    if df1["Brick"].iloc[i] == "RedBrick" and df1["Trend"].iloc[i] == "Downward" and tradehappen == 0:
                        df1.at[i, 'SellSignal'] = 'SELL'
                        EntryPrice = float(df["close"].iloc[i])
                        df1.at[i, 'SellEntryPrice'] = EntryPrice
                        tradehappen = 1
                        tradetype = 'SHORT'
                        continue
                    if tradetype == 'LONG' and df1["TRADE"].iloc[i] == 'ReverseOfUpward' and df1['Brick'].iloc[
                        i] == 'RedBrick':
                        ExitPrice = float(df["close"].iloc[i])
                        PNL = ExitPrice - EntryPrice
                        PNLPercent = (PNL / EntryPrice) * 100
                        df1.at[i, 'BuySignal'] = 'LongExit'
                        df1.at[i, 'BuyExitPrice'] = ExitPrice
                        df1.at[i, 'BuyPNL'] = PNL
                        df1.at[i, 'BuyPNLPercent'] = PNLPercent

                        EntryPrice = 0
                        ExitPrice = 0
                        tradehappen = 0
                        tradetype = ''
                        PNL = 0
                        PNLPercent = 0

                        df1.at[i, 'SellSignal'] = 'SELL'
                        EntryPrice = float(df["close"].iloc[i])
                        df1.at[i, 'SellEntryPrice'] = EntryPrice
                        tradehappen = 1
                        tradetype = 'SHORT'

                        continue
                    if tradetype == 'SHORT' and df1["TRADE"].iloc[i] == 'ReverseOfDownward' and df1['Brick'].iloc[i] == 'GreenBrick':
                        ExitPrice = float(df["close"].iloc[i])
                        PNL = EntryPrice - ExitPrice
                        PNLPercent = (PNL / EntryPrice) * 100
                        df1.at[i, 'SellSignal'] = 'ShortExit'
                        df1.at[i, 'SellExitPrice'] = ExitPrice
                        df1.at[i, 'SellPNL'] = PNL
                        df1.at[i, 'SellPNLPercent'] = PNLPercent

                        EntryPrice = 0
                        ExitPrice = 0
                        tradehappen = 0
                        tradetype = ''
                        PNL = 0
                        PNLPercent = 0

                        df1.at[i, 'BuySignal'] = 'BUY'
                        EntryPrice = float(df["close"].iloc[i])
                        df1.at[i, 'BuyEntryPrice'] = EntryPrice
                        tradehappen = 1
                        tradetype = 'LONG'
                        continue

                df1.to_csv('C://upstox_oauth//media//Backtest//Result//result' + contract + '.csv')

                time.sleep(15)
                df_data = pd.read_csv('C://upstox_oauth//media//Backtest//Result//result' + contract + '.csv')

                # df_data=df_data.loc[:15000]

                df_data = df_data.reset_index(drop=True)

                database = pd.DataFrame()

                for i in range(len(df_data)):

                    if (df_data['SellSignal'].iloc[i] == 'SELL' and len(database) == 0):
                        df_bar = pd.DataFrame(
                            [[df_data['SellSignal'].iloc[i], df_data['DateTime'].iloc[i],
                              df_data['SellEntryPrice'].iloc[i]]], \
                            columns=["Signal", "EntryDateTime", "EntryPrice"])
                        database = pd.concat([database, df_bar])
                        continue

                    if (df_data['SellSignal'].iloc[i] == 'ShortExit'):
                        database = database.reset_index(drop=True)

                        j = len(database) - 1
                        database.at[j, 'ExitType'] = 'SELLEXIT'
                        database.at[j, 'ExitDateTime'] = df_data['DateTime'].iloc[i]
                        database.at[j, 'ExitPrice'] = df_data['SellExitPrice'].iloc[i]
                        database.at[j, 'PandL'] = df_data['SellPNL'].iloc[i]
                        database.at[j, 'PandL_Percentage'] = df_data['SellPNLPercent'].iloc[i]

                        database.at[j + 1, 'Signal'] = df_data['BuySignal'].iloc[i]
                        database.at[j + 1, 'EntryDateTime'] = df_data['DateTime'].iloc[i]
                        database.at[j + 1, 'EntryPrice'] = df_data['BuyEntryPrice'].iloc[i]

                    if (df_data['SellSignal'].iloc[i] == 'SELL'):
                        database = database.reset_index(drop=True)

                        j = len(database) - 1
                        database.at[j, 'ExitType'] = 'BUYEXIT'
                        database.at[j, 'ExitDateTime'] = df_data['DateTime'].iloc[i]
                        database.at[j, 'ExitPrice'] = df_data['BuyExitPrice'].iloc[i]
                        database.at[j, 'PandL'] = df_data['BuyPNL'].iloc[i]
                        database.at[j, 'PandL_Percentage'] = df_data['BuyPNLPercent'].iloc[i]

                        database.at[j + 1, 'Signal'] = df_data['SellSignal'].iloc[i]
                        database.at[j + 1, 'EntryDateTime'] = df_data['DateTime'].iloc[i]
                        database.at[j + 1, 'EntryPrice'] = df_data['SellEntryPrice'].iloc[i]

                database.to_csv(
                    'C://upstox_oauth//media//Backtest//TradeSheet//Tradesheet' + contract + timeframe + '.csv',
                    index=False)

                sent = 'Backtesting Completed Successfully'
                context = {'sent': sent}
                return render(request, 'backtest/index2.html', context=context)

            if not bricksize and bricksizepercentage:
                API_KEY = os.getenv('API_KEY')
                TOKEN = dotenv.get_key(dotenv.find_dotenv(), 'ACCESS_TOKEN')
                # 'startDate': '02/07/2012',
                # 'endDate': '02/07/2018',
                config = {
                    'startDate': Date[0],
                    'endDate': Date[1],
                    'apiKey': API_KEY,
                    'accessToken': TOKEN
                }
                u = Upstox(config['apiKey'], config['accessToken'])
                u.get_master_contract(exchange)
                u.get_instrument_by_symbol(exchange, contract)

                if timeframe == '1DAY' or timeframe == '1WEEK' or timeframe == '1MONTH':
                    data = u.get_ohlc(u.get_instrument_by_symbol(exchange, contract), timeframe,
                                      datetime.strptime(config['startDate'], '%d-%m-%Y').date(),
                                      datetime.strptime(config['endDate'], '%d-%m-%Y').date())
                    df = pd.DataFrame(data)
                else:
                    x = datetime.strptime(config['startDate'], '%d-%m-%Y')
                    df = pd.DataFrame()
                    while x <= datetime.strptime(config['endDate'], '%d-%m-%Y'):
                        data = u.get_ohlc(u.get_instrument_by_symbol(exchange, contract), timeframe,
                                          datetime.strptime(str(x).split(' ')[0], '%Y-%m-%d').date(),
                                          datetime.strptime(str(x + BDay(4)).split(' ')[0], '%Y-%m-%d').date())
                        temp = pd.DataFrame(data)
                        df = pd.concat([df, temp])
                        df = df.reset_index(drop=True)
                        x += BDay(4)

                # First Pause of 15 seconds
                time.sleep(20)
                box_size = float(bricksizepercentage) / 100
                n_multiplies_box_size = brickreversal  # n_multiplies_box_size
                trend = ""
                trade = ""
                pivot_Price = 0
                for i in range(len(df)):
                    df['timestamp'].iloc[i] = datetime.fromtimestamp(int(df['timestamp'].iloc[i]) / 1000)

                df = df.rename(columns={"timestamp": "DateTime"})
                for i in range(len(df)):
                    if i == 0:
                        pivot_Price = float(pivotprice)
                        continue

                    if trend == "":
                        if (float(df["close"].iloc[i]) >= (1 + box_size) * pivot_Price):
                            trend = "Upward"
                            df.at[i, "Trend"] = trend
                            df.at[i, "Brick"] = "GreenBrick"
                            pivot_Price = float(df["close"].iloc[i]) - (
                                        (float(df["close"].iloc[i]) - pivot_Price) % (box_size * pivot_Price))
                            df.at[i, "PivotPrice"] = pivot_Price
                            continue

                        if (float(df["close"].iloc[i]) <= (1 - box_size) * pivot_Price):
                            trend = "Downward"
                            df.at[i, "Trend"] = trend
                            df.at[i, "Brick"] = "RedBrick"
                            pivot_Price = float(df["close"].iloc[i]) + (
                                        (pivot_Price - float(df["close"].iloc[i])) % (box_size * pivot_Price))
                            df.at[i, "PivotPrice"] = pivot_Price
                            continue

                    if trend == "Upward":
                        if (pivot_Price - float(df["close"].iloc[i]) >= (
                                box_size * pivot_Price) * n_multiplies_box_size):
                            trade = "ReverseOfUpward"
                            trend = "Downward"
                            pivot_Price = float(df["close"].iloc[i]) + (
                                        (pivot_Price - float(df["close"].iloc[i])) % (box_size * pivot_Price))
                            df.at[i, "PivotPrice"] = pivot_Price
                            df.at[i, "TRADE"] = trade
                            df.at[i, "Trend"] = trend
                            df.at[i, "Brick"] = "RedBrick"
                            continue

                        if (float(df["close"].iloc[i]) >= (1 + box_size) * pivot_Price):
                            trend = "Upward"
                            df.at[i, "Trend"] = trend
                            df.at[i, "Brick"] = "GreenBrick"
                            pivot_Price = float(df["close"].iloc[i]) - (
                                        (float(df["close"].iloc[i]) - pivot_Price) % (box_size * pivot_Price))
                            df.at[i, "PivotPrice"] = pivot_Price

                    if trend == "Downward":
                        if (float(df["close"].iloc[i]) - pivot_Price >= (
                                box_size * pivot_Price) * n_multiplies_box_size):
                            trade = "ReverseOfDownward"
                            trend = "Upward"
                            pivot_Price = float(df["close"].iloc[i]) - (
                                        (float(df["close"].iloc[i]) - pivot_Price) % (box_size * pivot_Price))
                            df.at[i, "PivotPrice"] = pivot_Price
                            df.at[i, "TRADE"] = trade
                            df.at[i, "Trend"] = trend
                            df.at[i, "Brick"] = "GreenBrick"
                            continue

                        if (float(df["close"].iloc[i]) <= (1 - box_size) * pivot_Price):
                            trend = "Downward"
                            df.at[i, "Trend"] = trend
                            df.at[i, "Brick"] = "RedBrick"
                            pivot_Price = float(df["close"].iloc[i]) + (
                                        (pivot_Price - float(df["close"].iloc[i])) % (box_size * pivot_Price))
                            df.at[i, "PivotPrice"] = pivot_Price

                df.to_csv("C://upstox_oauth//media//Backtest//" + contract + "signalPercent.csv", index=False)
                time.sleep(20)

                # Second Pause of 10 seconds
                df1 = pd.read_csv("C://upstox_oauth//media//Backtest//" + contract + "signalPercent.csv")
                EntryPrice = 0
                ExitPrice = 0
                tradehappen = 0
                tradetype = ''
                PNL = 0
                PNLPercent = 0

                for i in range(len(df1)):
                    if df1["Brick"].iloc[i] == "GreenBrick" and df1["Trend"].iloc[i] == "Upward" and tradehappen == 0:
                        df1.at[i, 'BuySignal'] = 'BUY'
                        EntryPrice = float(df["close"].iloc[i])
                        df1.at[i, 'BuyEntryPrice'] = EntryPrice
                        tradehappen = 1
                        tradetype = 'LONG'
                        continue

                    if df1["Brick"].iloc[i] == "RedBrick" and df1["Trend"].iloc[i] == "Downward" and tradehappen == 0:
                        df1.at[i, 'SellSignal'] = 'SELL'
                        EntryPrice = float(df["close"].iloc[i])
                        df1.at[i, 'SellEntryPrice'] = EntryPrice
                        tradehappen = 1
                        tradetype = 'SHORT'
                        continue
                    if tradetype == 'LONG' and df1["TRADE"].iloc[i] == 'ReverseOfUpward' and df1['Brick'].iloc[
                        i] == 'RedBrick':
                        ExitPrice = float(df["close"].iloc[i])
                        PNL = ExitPrice - EntryPrice
                        PNLPercent = (PNL / EntryPrice) * 100
                        df1.at[i, 'BuySignal'] = 'LongExit'
                        df1.at[i, 'BuyExitPrice'] = ExitPrice
                        df1.at[i, 'BuyPNL'] = PNL
                        df1.at[i, 'BuyPNLPercent'] = PNLPercent

                        EntryPrice = 0
                        ExitPrice = 0
                        tradehappen = 0
                        tradetype = ''
                        PNL = 0
                        PNLPercent = 0

                        df1.at[i, 'SellSignal'] = 'SELL'
                        EntryPrice = float(df["close"].iloc[i])
                        df1.at[i, 'SellEntryPrice'] = EntryPrice
                        tradehappen = 1
                        tradetype = 'SHORT'

                        continue
                    if tradetype == 'SHORT' and df1["TRADE"].iloc[i] == 'ReverseOfDownward' and df1['Brick'].iloc[
                        i] == 'GreenBrick':
                        ExitPrice = float(df["close"].iloc[i])
                        PNL = EntryPrice - ExitPrice
                        PNLPercent = (PNL / EntryPrice) * 100
                        df1.at[i, 'SellSignal'] = 'ShortExit'
                        df1.at[i, 'SellExitPrice'] = ExitPrice
                        df1.at[i, 'SellPNL'] = PNL
                        df1.at[i, 'SellPNLPercent'] = PNLPercent

                        EntryPrice = 0
                        ExitPrice = 0
                        tradehappen = 0
                        tradetype = ''
                        PNL = 0
                        PNLPercent = 0

                        df1.at[i, 'BuySignal'] = 'BUY'
                        EntryPrice = float(df["close"].iloc[i])
                        df1.at[i, 'BuyEntryPrice'] = EntryPrice
                        tradehappen = 1
                        tradetype = 'LONG'
                        continue

                df1.to_csv('C://upstox_oauth//media//Backtest//Result//resultPercent' + contract + '.csv')

                time.sleep(15)
                df_data = pd.read_csv('C://upstox_oauth//media//Backtest//Result//resultPercent' + contract + '.csv')

                # df_data=df_data.loc[:15000]

                df_data = df_data.reset_index(drop=True)

                database = pd.DataFrame()

                for i in range(len(df_data)):

                    if (df_data['SellSignal'].iloc[i] == 'SELL' and len(database) == 0):
                        df_bar = pd.DataFrame(
                            [[df_data['SellSignal'].iloc[i], df_data['DateTime'].iloc[i],
                              df_data['SellEntryPrice'].iloc[i]]], \
                            columns=["Signal", "EntryDateTime", "EntryPrice"])
                        database = pd.concat([database, df_bar])
                        continue

                    if (df_data['SellSignal'].iloc[i] == 'ShortExit'):
                        database = database.reset_index(drop=True)

                        j = len(database) - 1
                        database.at[j, 'ExitType'] = 'SELLEXIT'
                        database.at[j, 'ExitDateTime'] = df_data['DateTime'].iloc[i]
                        database.at[j, 'ExitPrice'] = df_data['SellExitPrice'].iloc[i]
                        database.at[j, 'PandL'] = df_data['SellPNL'].iloc[i]
                        database.at[j, 'PandL_Percentage'] = df_data['SellPNLPercent'].iloc[i]

                        database.at[j + 1, 'Signal'] = df_data['BuySignal'].iloc[i]
                        database.at[j + 1, 'EntryDateTime'] = df_data['DateTime'].iloc[i]
                        database.at[j + 1, 'EntryPrice'] = df_data['BuyEntryPrice'].iloc[i]

                    if (df_data['SellSignal'].iloc[i] == 'SELL'):
                        database = database.reset_index(drop=True)

                        j = len(database) - 1
                        database.at[j, 'ExitType'] = 'BUYEXIT'
                        database.at[j, 'ExitDateTime'] = df_data['DateTime'].iloc[i]
                        database.at[j, 'ExitPrice'] = df_data['BuyExitPrice'].iloc[i]
                        database.at[j, 'PandL'] = df_data['BuyPNL'].iloc[i]
                        database.at[j, 'PandL_Percentage'] = df_data['BuyPNLPercent'].iloc[i]

                        database.at[j + 1, 'Signal'] = df_data['SellSignal'].iloc[i]
                        database.at[j + 1, 'EntryDateTime'] = df_data['DateTime'].iloc[i]
                        database.at[j + 1, 'EntryPrice'] = df_data['SellEntryPrice'].iloc[i]

                database.to_csv(
                    'C://upstox_oauth//media//Backtest//TradeSheet//TradesheetPercent' + contract + timeframe + '.csv',
                    index=False)

                sent = 'Backtesting Completed Successfully For Percentage'
                context = {'sent': sent}
                return render(request, 'backtest/index2.html', context=context)

        if not pivotprice:
            if bricksize and not bricksizepercentage:
                API_KEY = os.getenv('API_KEY')
                TOKEN = dotenv.get_key(dotenv.find_dotenv(), 'ACCESS_TOKEN')
                # 'startDate': '02/07/2012',
                # 'endDate': '02/07/2018',
                config = {
                    'startDate': Date[0],
                    'endDate': Date[1],
                    'apiKey': API_KEY,
                    'accessToken': TOKEN
                }
                u = Upstox(config['apiKey'], config['accessToken'])
                u.get_master_contract(exchange)
                u.get_instrument_by_symbol(exchange, contract)

                if timeframe == '1DAY' or timeframe == '1WEEK' or timeframe == '1MONTH':
                    data = u.get_ohlc(u.get_instrument_by_symbol(exchange, contract), timeframe,
                                      datetime.strptime(config['startDate'], '%d-%m-%Y').date(),
                                      datetime.strptime(config['endDate'], '%d-%m-%Y').date())
                    df = pd.DataFrame(data)
                else:
                    x = datetime.strptime(config['startDate'], '%d-%m-%Y')
                    df = pd.DataFrame()
                    while x <= datetime.strptime(config['endDate'], '%d-%m-%Y'):
                        data = u.get_ohlc(u.get_instrument_by_symbol(exchange, contract), timeframe,
                                          datetime.strptime(str(x).split(' ')[0], '%Y-%m-%d').date(),
                                          datetime.strptime(str(x + BDay(4)).split(' ')[0], '%Y-%m-%d').date())
                        temp = pd.DataFrame(data)
                        df = pd.concat([df, temp])
                        df = df.reset_index(drop=True)
                        x += BDay(4)

                # First Pause of 15 seconds
                time.sleep(20)
                box_size = int(bricksize)
                n_multiplies_box_size = brickreversal  # n_multiplies_box_size
                trend = ""
                trade = ""
                pivot_Price = 0
                for i in range(len(df)):
                    df['timestamp'].iloc[i] = datetime.fromtimestamp(int(df['timestamp'].iloc[i]) / 1000)

                df = df.rename(columns={"timestamp": "DateTime"})
                for i in range(len(df)):
                    if df["Close"] % box_size != 0:
                        pivot_Price = df['Close'] + box_size - (df['Close'] % box_size)
                    elif df["Close"] % box_size == 0:
                        pivot_Price = df['Close']

                    continue

                    if trend == "":
                        if (float(df["close"].iloc[i]) >= box_size + pivot_Price):
                            trend = "Upward"
                            df.at[i, "Trend"] = trend
                            df.at[i, "Brick"] = "GreenBrick"
                            pivot_Price = float(df["close"].iloc[i]) - (
                                    (float(df["close"].iloc[i]) - pivot_Price) % box_size)
                            df.at[i, "PivotPrice"] = pivot_Price
                            continue

                        if (float(df["close"].iloc[i]) <= pivot_Price - box_size):
                            trend = "Downward"
                            df.at[i, "Trend"] = trend
                            df.at[i, "Brick"] = "RedBrick"
                            pivot_Price = float(df["close"].iloc[i]) + (
                                    (pivot_Price - float(df["close"].iloc[i])) % (box_size))
                            df.at[i, "PivotPrice"] = pivot_Price
                            continue

                    if trend == "Upward":
                        if (pivot_Price - float(df["close"].iloc[i]) >= box_size * n_multiplies_box_size):
                            trade = "ReverseOfUpward"
                            trend = "Downward"
                            pivot_Price = float(df["close"].iloc[i]) + (
                                    (pivot_Price - float(df["close"].iloc[i])) % (box_size))
                            df.at[i, "PivotPrice"] = pivot_Price
                            df.at[i, "TRADE"] = trade
                            df.at[i, "Trend"] = trend
                            df.at[i, "Brick"] = "RedBrick"
                            continue

                        if (float(df["close"].iloc[i]) >= box_size + pivot_Price):
                            trend = "Upward"
                            df.at[i, "Trend"] = trend
                            df.at[i, "Brick"] = "GreenBrick"
                            pivot_Price = float(df["close"].iloc[i]) - (
                                    (float(df["close"].iloc[i]) - pivot_Price) % box_size)
                            df.at[i, "PivotPrice"] = pivot_Price

                    if trend == "Downward":
                        if (float(df["close"].iloc[i]) - pivot_Price >= box_size * n_multiplies_box_size):
                            trade = "ReverseOfDownward"
                            trend = "Upward"
                            pivot_Price = float(df["close"].iloc[i]) - (
                                    (float(df["close"].iloc[i]) - pivot_Price) % box_size)
                            df.at[i, "PivotPrice"] = pivot_Price
                            df.at[i, "TRADE"] = trade
                            df.at[i, "Trend"] = trend
                            df.at[i, "Brick"] = "GreenBrick"
                            continue

                        if (float(df["close"].iloc[i]) <= pivot_Price - box_size):
                            trend = "Downward"
                            df.at[i, "Trend"] = trend
                            df.at[i, "Brick"] = "RedBrick"
                            pivot_Price = float(df["close"].iloc[i]) + (
                                    (pivot_Price - float(df["close"].iloc[i])) % (box_size))
                            df.at[i, "PivotPrice"] = pivot_Price

                df.to_csv("C://upstox_oauth//media//Backtest//" + contract + "signal.csv", index=False)
                time.sleep(20)

                # Second Pause of 10 seconds
                df1 = pd.read_csv("C://upstox_oauth//media//Backtest//" + contract + "signal.csv")
                EntryPrice = 0
                ExitPrice = 0
                tradehappen = 0
                tradetype = ''
                PNL = 0
                PNLPercent = 0

                for i in range(len(df1)):
                    if df1["Brick"].iloc[i] == "GreenBrick" and df1["Trend"].iloc[i] == "Upward" and tradehappen == 0:
                        df1.at[i, 'BuySignal'] = 'BUY'
                        EntryPrice = float(df["close"].iloc[i])
                        df1.at[i, 'BuyEntryPrice'] = EntryPrice
                        tradehappen = 1
                        tradetype = 'LONG'
                        continue

                    if df1["Brick"].iloc[i] == "RedBrick" and df1["Trend"].iloc[i] == "Downward" and tradehappen == 0:
                        df1.at[i, 'SellSignal'] = 'SELL'
                        EntryPrice = float(df["close"].iloc[i])
                        df1.at[i, 'SellEntryPrice'] = EntryPrice
                        tradehappen = 1
                        tradetype = 'SHORT'
                        continue
                    if tradetype == 'LONG' and df1["TRADE"].iloc[i] == 'ReverseOfUpward' and df1['Brick'].iloc[
                        i] == 'RedBrick':
                        ExitPrice = float(df["close"].iloc[i])
                        PNL = ExitPrice - EntryPrice
                        PNLPercent = (PNL / EntryPrice) * 100
                        df1.at[i, 'BuySignal'] = 'LongExit'
                        df1.at[i, 'BuyExitPrice'] = ExitPrice
                        df1.at[i, 'BuyPNL'] = PNL
                        df1.at[i, 'BuyPNLPercent'] = PNLPercent

                        EntryPrice = 0
                        ExitPrice = 0
                        tradehappen = 0
                        tradetype = ''
                        PNL = 0
                        PNLPercent = 0

                        df1.at[i, 'SellSignal'] = 'SELL'
                        EntryPrice = float(df["close"].iloc[i])
                        df1.at[i, 'SellEntryPrice'] = EntryPrice
                        tradehappen = 1
                        tradetype = 'SHORT'

                        continue
                    if tradetype == 'SHORT' and df1["TRADE"].iloc[i] == 'ReverseOfDownward' and df1['Brick'].iloc[
                        i] == 'GreenBrick':
                        ExitPrice = float(df["close"].iloc[i])
                        PNL = EntryPrice - ExitPrice
                        PNLPercent = (PNL / EntryPrice) * 100
                        df1.at[i, 'SellSignal'] = 'ShortExit'
                        df1.at[i, 'SellExitPrice'] = ExitPrice
                        df1.at[i, 'SellPNL'] = PNL
                        df1.at[i, 'SellPNLPercent'] = PNLPercent

                        EntryPrice = 0
                        ExitPrice = 0
                        tradehappen = 0
                        tradetype = ''
                        PNL = 0
                        PNLPercent = 0

                        df1.at[i, 'BuySignal'] = 'BUY'
                        EntryPrice = float(df["close"].iloc[i])
                        df1.at[i, 'BuyEntryPrice'] = EntryPrice
                        tradehappen = 1
                        tradetype = 'LONG'
                        continue

                df1.to_csv('C://upstox_oauth//media//Backtest//Result//result' + contract + '.csv')

                time.sleep(15)
                df_data = pd.read_csv('C://upstox_oauth//media//Backtest//Result//result' + contract + '.csv')

                # df_data=df_data.loc[:15000]

                df_data = df_data.reset_index(drop=True)

                database = pd.DataFrame()

                for i in range(len(df_data)):

                    if (df_data['SellSignal'].iloc[i] == 'SELL' and len(database) == 0):
                        df_bar = pd.DataFrame(
                            [[df_data['SellSignal'].iloc[i], df_data['DateTime'].iloc[i],
                              df_data['SellEntryPrice'].iloc[i]]], \
                            columns=["Signal", "EntryDateTime", "EntryPrice"])
                        database = pd.concat([database, df_bar])
                        continue

                    if (df_data['SellSignal'].iloc[i] == 'ShortExit'):
                        database = database.reset_index(drop=True)

                        j = len(database) - 1
                        database.at[j, 'ExitType'] = 'SELLEXIT'
                        database.at[j, 'ExitDateTime'] = df_data['DateTime'].iloc[i]
                        database.at[j, 'ExitPrice'] = df_data['SellExitPrice'].iloc[i]
                        database.at[j, 'PandL'] = df_data['SellPNL'].iloc[i]
                        database.at[j, 'PandL_Percentage'] = df_data['SellPNLPercent'].iloc[i]

                        database.at[j + 1, 'Signal'] = df_data['BuySignal'].iloc[i]
                        database.at[j + 1, 'EntryDateTime'] = df_data['DateTime'].iloc[i]
                        database.at[j + 1, 'EntryPrice'] = df_data['BuyEntryPrice'].iloc[i]

                    if (df_data['SellSignal'].iloc[i] == 'SELL'):
                        database = database.reset_index(drop=True)

                        j = len(database) - 1
                        database.at[j, 'ExitType'] = 'BUYEXIT'
                        database.at[j, 'ExitDateTime'] = df_data['DateTime'].iloc[i]
                        database.at[j, 'ExitPrice'] = df_data['BuyExitPrice'].iloc[i]
                        database.at[j, 'PandL'] = df_data['BuyPNL'].iloc[i]
                        database.at[j, 'PandL_Percentage'] = df_data['BuyPNLPercent'].iloc[i]

                        database.at[j + 1, 'Signal'] = df_data['SellSignal'].iloc[i]
                        database.at[j + 1, 'EntryDateTime'] = df_data['DateTime'].iloc[i]
                        database.at[j + 1, 'EntryPrice'] = df_data['SellEntryPrice'].iloc[i]

                database.to_csv(
                    'C://upstox_oauth//media//Backtest//TradeSheet//Tradesheet' + contract + timeframe + '.csv',
                    index=False)

                sent = 'Backtesting Completed Successfully'
                context = {'sent': sent}
                return render(request, 'backtest/index2.html', context=context)

            if not bricksize and bricksizepercentage:
                API_KEY = os.getenv('API_KEY')
                TOKEN = dotenv.get_key(dotenv.find_dotenv(), 'ACCESS_TOKEN')
                # 'startDate': '02/07/2012',
                # 'endDate': '02/07/2018',
                config = {
                    'startDate': Date[0],
                    'endDate': Date[1],
                    'apiKey': API_KEY,
                    'accessToken': TOKEN
                }
                u = Upstox(config['apiKey'], config['accessToken'])
                u.get_master_contract(exchange)
                u.get_instrument_by_symbol(exchange, contract)

                if timeframe == '1DAY' or timeframe == '1WEEK' or timeframe == '1MONTH':
                    data = u.get_ohlc(u.get_instrument_by_symbol(exchange, contract), timeframe,
                                      datetime.strptime(config['startDate'], '%d-%m-%Y').date(),
                                      datetime.strptime(config['endDate'], '%d-%m-%Y').date())
                    df = pd.DataFrame(data)
                else:
                    x = datetime.strptime(config['startDate'], '%d-%m-%Y')
                    df = pd.DataFrame()
                    while x <= datetime.strptime(config['endDate'], '%d-%m-%Y'):
                        data = u.get_ohlc(u.get_instrument_by_symbol(exchange, contract), timeframe,
                                          datetime.strptime(str(x).split(' ')[0], '%Y-%m-%d').date(),
                                          datetime.strptime(str(x + BDay(4)).split(' ')[0], '%Y-%m-%d').date())
                        temp = pd.DataFrame(data)
                        df = pd.concat([df, temp])
                        df = df.reset_index(drop=True)
                        x += BDay(4)

                # First Pause of 15 seconds
                time.sleep(20)
                box_size = float(bricksizepercentage) / 100
                n_multiplies_box_size = brickreversal  # n_multiplies_box_size
                trend = ""
                trade = ""
                pivot_Price = 0
                for i in range(len(df)):
                    df['timestamp'].iloc[i] = datetime.fromtimestamp(int(df['timestamp'].iloc[i]) / 1000)

                df = df.rename(columns={"timestamp": "DateTime"})
                for i in range(len(df)):
                    if df["Close"] % (df["Close"]*box_size) != 0:
                        pivot_Price = df['Close'] + (df["Close"]*box_size) - (df['Close'] % (df["Close"]*box_size))
                    elif df["Close"] % (df["Close"]*box_size) == 0:
                        pivot_Price = df['Close']
                    continue

                    if trend == "":
                        if (float(df["close"].iloc[i]) >= (1 + box_size) * pivot_Price):
                            trend = "Upward"
                            df.at[i, "Trend"] = trend
                            df.at[i, "Brick"] = "GreenBrick"
                            pivot_Price = float(df["close"].iloc[i]) - (
                                        (float(df["close"].iloc[i]) - pivot_Price) % (box_size * pivot_Price))
                            df.at[i, "PivotPrice"] = pivot_Price
                            continue

                        if (float(df["close"].iloc[i]) <= (1 - box_size) * pivot_Price):
                            trend = "Downward"
                            df.at[i, "Trend"] = trend
                            df.at[i, "Brick"] = "RedBrick"
                            pivot_Price = float(df["close"].iloc[i]) + (
                                        (pivot_Price - float(df["close"].iloc[i])) % (box_size * pivot_Price))
                            df.at[i, "PivotPrice"] = pivot_Price
                            continue

                    if trend == "Upward":
                        if (pivot_Price - float(df["close"].iloc[i]) >= (
                                box_size * pivot_Price) * n_multiplies_box_size):
                            trade = "ReverseOfUpward"
                            trend = "Downward"
                            pivot_Price = float(df["close"].iloc[i]) + (
                                        (pivot_Price - float(df["close"].iloc[i])) % (box_size * pivot_Price))
                            df.at[i, "PivotPrice"] = pivot_Price
                            df.at[i, "TRADE"] = trade
                            df.at[i, "Trend"] = trend
                            df.at[i, "Brick"] = "RedBrick"
                            continue

                        if (float(df["close"].iloc[i]) >= (1 + box_size) * pivot_Price):
                            trend = "Upward"
                            df.at[i, "Trend"] = trend
                            df.at[i, "Brick"] = "GreenBrick"
                            pivot_Price = float(df["close"].iloc[i]) - (
                                        (float(df["close"].iloc[i]) - pivot_Price) % (box_size * pivot_Price))
                            df.at[i, "PivotPrice"] = pivot_Price

                    if trend == "Downward":
                        if (float(df["close"].iloc[i]) - pivot_Price >= (
                                box_size * pivot_Price) * n_multiplies_box_size):
                            trade = "ReverseOfDownward"
                            trend = "Upward"
                            pivot_Price = float(df["close"].iloc[i]) - (
                                        (float(df["close"].iloc[i]) - pivot_Price) % (box_size * pivot_Price))
                            df.at[i, "PivotPrice"] = pivot_Price
                            df.at[i, "TRADE"] = trade
                            df.at[i, "Trend"] = trend
                            df.at[i, "Brick"] = "GreenBrick"
                            continue

                        if (float(df["close"].iloc[i]) <= (1 - box_size) * pivot_Price):
                            trend = "Downward"
                            df.at[i, "Trend"] = trend
                            df.at[i, "Brick"] = "RedBrick"
                            pivot_Price = float(df["close"].iloc[i]) + (
                                        (pivot_Price - float(df["close"].iloc[i])) % (box_size * pivot_Price))
                            df.at[i, "PivotPrice"] = pivot_Price

                df.to_csv("C://upstox_oauth//media//Backtest//" + contract + "signalPercent.csv", index=False)
                time.sleep(20)

                # Second Pause of 10 seconds
                df1 = pd.read_csv("C://upstox_oauth//media//Backtest//" + contract + "signalPercent.csv")
                EntryPrice = 0
                ExitPrice = 0
                tradehappen = 0
                tradetype = ''
                PNL = 0
                PNLPercent = 0

                for i in range(len(df1)):
                    if df1["Brick"].iloc[i] == "GreenBrick" and df1["Trend"].iloc[i] == "Upward" and tradehappen == 0:
                        df1.at[i, 'BuySignal'] = 'BUY'
                        EntryPrice = float(df["close"].iloc[i])
                        df1.at[i, 'BuyEntryPrice'] = EntryPrice
                        tradehappen = 1
                        tradetype = 'LONG'
                        continue

                    if df1["Brick"].iloc[i] == "RedBrick" and df1["Trend"].iloc[i] == "Downward" and tradehappen == 0:
                        df1.at[i, 'SellSignal'] = 'SELL'
                        EntryPrice = float(df["close"].iloc[i])
                        df1.at[i, 'SellEntryPrice'] = EntryPrice
                        tradehappen = 1
                        tradetype = 'SHORT'
                        continue
                    if tradetype == 'LONG' and df1["TRADE"].iloc[i] == 'ReverseOfUpward' and df1['Brick'].iloc[
                        i] == 'RedBrick':
                        ExitPrice = float(df["close"].iloc[i])
                        PNL = ExitPrice - EntryPrice
                        PNLPercent = (PNL / EntryPrice) * 100
                        df1.at[i, 'BuySignal'] = 'LongExit'
                        df1.at[i, 'BuyExitPrice'] = ExitPrice
                        df1.at[i, 'BuyPNL'] = PNL
                        df1.at[i, 'BuyPNLPercent'] = PNLPercent

                        EntryPrice = 0
                        ExitPrice = 0
                        tradehappen = 0
                        tradetype = ''
                        PNL = 0
                        PNLPercent = 0

                        df1.at[i, 'SellSignal'] = 'SELL'
                        EntryPrice = float(df["close"].iloc[i])
                        df1.at[i, 'SellEntryPrice'] = EntryPrice
                        tradehappen = 1
                        tradetype = 'SHORT'

                        continue
                    if tradetype == 'SHORT' and df1["TRADE"].iloc[i] == 'ReverseOfDownward' and df1['Brick'].iloc[
                        i] == 'GreenBrick':
                        ExitPrice = float(df["close"].iloc[i])
                        PNL = EntryPrice - ExitPrice
                        PNLPercent = (PNL / EntryPrice) * 100
                        df1.at[i, 'SellSignal'] = 'ShortExit'
                        df1.at[i, 'SellExitPrice'] = ExitPrice
                        df1.at[i, 'SellPNL'] = PNL
                        df1.at[i, 'SellPNLPercent'] = PNLPercent

                        EntryPrice = 0
                        ExitPrice = 0
                        tradehappen = 0
                        tradetype = ''
                        PNL = 0
                        PNLPercent = 0

                        df1.at[i, 'BuySignal'] = 'BUY'
                        EntryPrice = float(df["close"].iloc[i])
                        df1.at[i, 'BuyEntryPrice'] = EntryPrice
                        tradehappen = 1
                        tradetype = 'LONG'
                        continue

                df1.to_csv('C://upstox_oauth//media//Backtest//Result//resultPercent' + contract + '.csv')

                time.sleep(15)
                df_data = pd.read_csv('C://upstox_oauth//media//Backtest//Result//resultPercent' + contract + '.csv')

                # df_data=df_data.loc[:15000]

                df_data = df_data.reset_index(drop=True)

                database = pd.DataFrame()

                for i in range(len(df_data)):

                    if (df_data['SellSignal'].iloc[i] == 'SELL' and len(database) == 0):
                        df_bar = pd.DataFrame(
                            [[df_data['SellSignal'].iloc[i], df_data['DateTime'].iloc[i],
                              df_data['SellEntryPrice'].iloc[i]]], \
                            columns=["Signal", "EntryDateTime", "EntryPrice"])
                        database = pd.concat([database, df_bar])
                        continue

                    if (df_data['SellSignal'].iloc[i] == 'ShortExit'):
                        database = database.reset_index(drop=True)

                        j = len(database) - 1
                        database.at[j, 'ExitType'] = 'SELLEXIT'
                        database.at[j, 'ExitDateTime'] = df_data['DateTime'].iloc[i]
                        database.at[j, 'ExitPrice'] = df_data['SellExitPrice'].iloc[i]
                        database.at[j, 'PandL'] = df_data['SellPNL'].iloc[i]
                        database.at[j, 'PandL_Percentage'] = df_data['SellPNLPercent'].iloc[i]

                        database.at[j + 1, 'Signal'] = df_data['BuySignal'].iloc[i]
                        database.at[j + 1, 'EntryDateTime'] = df_data['DateTime'].iloc[i]
                        database.at[j + 1, 'EntryPrice'] = df_data['BuyEntryPrice'].iloc[i]

                    if (df_data['SellSignal'].iloc[i] == 'SELL'):
                        database = database.reset_index(drop=True)

                        j = len(database) - 1
                        database.at[j, 'ExitType'] = 'BUYEXIT'
                        database.at[j, 'ExitDateTime'] = df_data['DateTime'].iloc[i]
                        database.at[j, 'ExitPrice'] = df_data['BuyExitPrice'].iloc[i]
                        database.at[j, 'PandL'] = df_data['BuyPNL'].iloc[i]
                        database.at[j, 'PandL_Percentage'] = df_data['BuyPNLPercent'].iloc[i]

                        database.at[j + 1, 'Signal'] = df_data['SellSignal'].iloc[i]
                        database.at[j + 1, 'EntryDateTime'] = df_data['DateTime'].iloc[i]
                        database.at[j + 1, 'EntryPrice'] = df_data['SellEntryPrice'].iloc[i]

                database.to_csv(
                    'C://upstox_oauth//media//Backtest//TradeSheet//TradesheetPercent' + contract + timeframe + '.csv',
                    index=False)

                sent = 'Backtesting Completed Successfully For Percentage'
                context = {'sent': sent}
                return render(request, 'backtest/index2.html', context=context)





