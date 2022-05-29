import pandas as pd
import numpy as np

#Reading stock csv file and storing it in pandas dataframe , parse_dates=True, index_col=0
df = pd.read_csv('BANKNIFTY_2018-19.csv')
df['Date'] = pd.to_datetime(df['Date'])
print(df.info())
print(df.head())

def RSI(DF, n):
    df = DF.copy()
    df['delta'] = df['Close']-df['Close'].shift(1)
    df['gain'] = np.where(df['delta']>=0, df['delta'],0)
    df['loss'] = np.where(df['delta'] <0, abs(df['delta']),0)
    avg_gain = []
    avg_loss = []
    gain = df['gain'].tolist()
    loss = df['loss'].tolist()
    for i in range(len(df)):
        if i < n:
            avg_gain.append(np.nan)
            avg_loss.append(np.nan)
        elif i == n:
            avg_gain.append(df['gain'].rolling(n).mean()[n])
            avg_loss.append(df['loss'].rolling(n).mean()[n])
        elif i > n:
            avg_gain.append(((n - 1) * avg_gain[i - 1] + gain[i]) / n)
            avg_loss.append(((n - 1) * avg_loss[i - 1] + loss[i]) / n)

    df['avg_gain'] = np.array(avg_gain)
    df['avg_loss'] = np.array(avg_loss)
    df['RS'] = df['avg_gain']/df['avg_loss']
    df['RSI'] = 100 - (100/(1+df['RS']))
    return df['RSI']

def MACD(DF, a=12, b=26, c=9):
    """function to calculate MACD
       typical values a(fast moving average) = 12;
                      b(slow moving average) =26;
                      c(signal line ma window) =9"""
    df = DF.copy()
    df["MA_Fast"] = df["Close"].ewm(span=a, min_periods=a).mean()
    df["MA_Slow"] = df["Close"].ewm(span=b, min_periods=b).mean()
    df["MACD"] = df["MA_Fast"] - df["MA_Slow"]
    df["Signal"] = df["MACD"].ewm(span=c, min_periods=c).mean()
    df.dropna(inplace=True)
    return df

def SMA(DF, n):
    df = DF.copy()
    df["SMA"] = df['Close'].rolling(n).mean()
    return df["SMA"]

def get_indicator_calculation(df):
  df['MACD'] = MACD(df, a=12, b=26, c=9)['MACD']
  df['Signal'] = MACD(df, a=12, b=26, c=9)['Signal']
  df['RSI'] =  RSI(df, n=7)
  df['SMA_8'] = SMA(df,n=8)
  df['SMA_20'] = SMA(df, n=20)
  df.dropna(inplace=True)
  return df

#Create indicator values
df = get_indicator_calculation(df)
df = df.round(3)

entry_date = ''
exit_date = ''
trading_signal = ''
buy_price = 0
stoploss_price = 0
exit_price = 0
open_position = False
rsi_flag = False
rsi_confirmation_days = 3
df['Trade_Signal'] = ''

leher_trade_log = pd.DataFrame(columns=['Entry_Date','Direction','Buy_Price','Buy_Exit_Price','Exit_Date','PnL'])

for i in range(1, len(df)):
    try:
        #Long Entry conditions
        RSI_7 = (df.iloc[i]['RSI'] > 50) & (df.iloc[i-1]['RSI']<50)
        SMA_8_20 = (df.iloc[i]['SMA_8']> df.iloc[i]['SMA_20']) & (df.iloc[i-1]['SMA_8']< df.iloc[i-1]['SMA_20'])
        MAC_D = (df.iloc[i]['MACD']>df.iloc[i]['Signal']) & (df.iloc[i-1]['MACD']<df.iloc[i-1]['Signal'])

        #Stoploss conditions
        RSI_7_sl = (df.iloc[i]['RSI'] < 50) & (df.iloc[i - 1]['RSI'] > 50)
        SMA_8_20_sl = (df.iloc[i]['SMA_8'] < df.iloc[i]['SMA_20']) & (df.iloc[i - 1]['SMA_8'] > df.iloc[i - 1]['SMA_20'])
        MAC_D_sl = (df.iloc[i]['MACD'] < df.iloc[i]['Signal']) & (df.iloc[i - 1]['MACD'] > df.iloc[i - 1]['Signal'])

        if (trading_signal == '') & (open_position==False):
            if (RSI_7 or SMA_8_20 or MAC_D):
                trading_signal = "Long"
                df.iloc[i]['Trade_Signal'] = 'Long'
                open_position = True
                entry_date = df.iloc[i]['Date']
                buy_price = df.iloc[i]['Close']
                stoploss_price = buy_price*0.97

        elif (trading_signal == 'Long') & (open_position==True): #& (rsi_flag == True)
            if ((df.iloc[i]['RSI'] < 50) & (df.iloc[i-1]['RSI'] > 50)):
                trading_signal = ''
                df.iloc[i]['Trade_Signal'] = 'SqOff'
                open_position = False
                exit_date = df.iloc[i]['Date']
                exit_price = df.iloc[i]['Close']
                pnl = round(exit_price-buy_price,2)
                stoploss_price = 0
                leher_trade_log = leher_trade_log.append({'Entry_Date': entry_date,
                                                          'Direction': trading_signal,
                                                          'Buy_Price': buy_price,
                                                          'Buy_Exit_Price': exit_price,
                                                          'Exit_Date': exit_date,
                                                          'PnL': pnl}, ignore_index=True)

            elif ((df.iloc[i]['SMA_8'] < df.iloc[i]['SMA_20']) & (df.iloc[i-1]['SMA_8'] > df.iloc[i-1]['SMA_20'])):
                trading_signal = ''
                df.iloc[i]['Trade_Signal'] = 'SqOff'
                open_position = False
                exit_date = df.iloc[i]['Date']
                exit_price = df.iloc[i]['Close']
                pnl = round(exit_price-buy_price,2)
                stoploss_price = 0
                leher_trade_log = leher_trade_log.append({'Entry_Date': entry_date,
                                                          'Direction': trading_signal,
                                                          'Buy_Price': buy_price,
                                                          'Buy_Exit_Price': exit_price,
                                                          'Exit_Date': exit_date,
                                                          'PnL': pnl}, ignore_index=True)

            elif ((df.iloc[i]['MACD'] < df.iloc[i]['Signal']) & (df.iloc[i-1]['MACD']>df.iloc[i-1]['Signal'])):
                trading_signal = ''
                df.iloc[i]['Trade_Signal'] = 'SqOff'
                open_position = False
                exit_date = df.iloc[i]['Date']
                exit_price = df.iloc[i]['Close']
                pnl = round(exit_price-buy_price,2)
                stoploss_price = 0
                leher_trade_log = leher_trade_log.append({'Entry_Date': entry_date,
                                                          'Direction': trading_signal,
                                                          'Buy_Price': buy_price,
                                                          'Buy_Exit_Price': exit_price,
                                                          'Exit_Date': exit_date,
                                                          'PnL': pnl}, ignore_index=True)

            elif ((df.iloc[i]['Close'] <= stoploss_price) or (df.iloc[i]['Close'] < df.iloc[i-1]['Close'])): #|
                trading_signal = ''
                df.iloc[i]['Trade_Signal'] = 'SqOff'
                open_position = False
                exit_date = df.iloc[i]['Date']
                exit_price = df.iloc[i]['Close']
                pnl = round(exit_price-buy_price,2)
                stoploss_price = 0
                leher_trade_log = leher_trade_log.append({'Entry_Date': entry_date,
                                                          'Direction': trading_signal,
                                                          'Buy_Price': buy_price,
                                                          'Buy_Exit_Price': exit_price,
                                                          'Exit_Date': exit_date,
                                                          'PnL': pnl}, ignore_index=True)

        elif (trading_signal == 'Long') & (open_position==True) & ((rsi_confirmation_days!=0) & (rsi_flag==False)):
            if (SMA_8_20 or MAC_D):
                rsi_flag = True
            else:
                rsi_confirmation_days -=1
                if rsi_confirmation_days == 0:
                    trading_signal = ''
                    df.iloc[i]['Trade_Signal'] = 'SqOff'
                    open_position = False
                    exit_date = df.iloc[i]['Date']
                    exit_price = df.iloc[i]['Close']
                    pnl = round(exit_price-buy_price,2)
                    stoploss_price = 0
                    leher_trade_log = leher_trade_log.append({'Entry_Date': entry_date,
                                                      'Direction': trading_signal,
                                                      'Buy_Price': buy_price,
                                                      'Buy_Exit_Price' : exit_price,
                                                      'Exit_Date' : exit_date,
                                                      'PnL': pnl}, ignore_index=True)
    except Exception as Ex:
        print(Ex)


print(df)
print(leher_trade_log)

#Tradelog file directory
trade_log_dir = 'C:/Users/Sachin M/PycharmProjects/IB_Projects/Algo_1/Interview_MSFL/tradelog'

#Storing trade log in csv file
leher_trade_log.to_csv("BN_Daily_Tradelog_rev2.csv")











