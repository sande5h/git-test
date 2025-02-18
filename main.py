
from bingx import call_bingx
import json
import pandas as pd
from ta.trend import EMAIndicator
from decimal import Decimal
from datetime import datetime
import time
import logging
import subprocess

date1 = datetime.now().strftime('%Y-%m-%d')

logging.basicConfig(filename=f'{date1}.log', level=logging.INFO, 
                    format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def round_to_min_decimal_places(min_value, sent_value):
    # Convert min_value to a Decimal and retrieve the number of decimal places
    decimal_places = -Decimal(str(min_value)).as_tuple().exponent

    # Round sent_value to the determined number of decimal places
    rounded_value = round(sent_value, decimal_places)
    return float(rounded_value)

def update_quantity(symbol):
    balance = 100
    df = pd.read_csv(f"data.csv")
    close = df.loc[df['symbol'] == symbol, 'close'].iloc[0]
    min_qty = df.loc[df['symbol'] == symbol, 'min_qty'].iloc[0]
    quantity = round_to_min_decimal_places(float(min_qty), float(balance / close))
    df.loc[df['symbol'] == symbol, 'quantity'] = quantity
    df.to_csv(f"data.csv", index=False)

    return  float(quantity)

def set_position(symbol , position):
    df = pd.read_csv(f"data.csv")
    df.loc[df['symbol'] == symbol, 'position'] = position
    df.to_csv(f"data.csv", index=False)

def set_candle(symbol , close , high , low ,ema):
    df = pd.read_csv(f"data.csv")
    df.loc[df['symbol'] == symbol, 'close'] = close
    df.loc[df['symbol'] == symbol, 'high'] = high
    df.loc[df['symbol'] == symbol, 'low'] = low
    df.loc[df['symbol'] == symbol, 'ema'] = ema
    df.to_csv(f"data.csv", index=False)

def set_ema_cross(symbol , ema_cross):
    df = pd.read_csv(f"data.csv")
    df.loc[df['symbol'] == symbol, 'ema_cross'] = ema_cross
    df.to_csv(f"data.csv", index=False)


def get_qty(symbol):
    df = pd.read_csv(f"data.csv")
    qty = df.loc[df['symbol'] == symbol, 'quantity'].iloc[0]
    return float(qty)

def get_data(symbol):
    df = pd.read_csv(f"data.csv")
    close = df.loc[df['symbol'] == symbol, 'close'].iloc[0]
    high = df.loc[df['symbol'] == symbol, 'high'].iloc[0]
    low = df.loc[df['symbol'] == symbol, 'low'].iloc[0]
    ema = df.loc[df['symbol'] == symbol, 'ema'].iloc[0]
    ema_cross = df.loc[df['symbol'] == symbol, 'ema_cross'].iloc[0]
    ema_diff = df.loc[df['symbol'] == symbol, 'ema_diff'].iloc[0]
    min_qty = df.loc[df['symbol'] == symbol, 'min_qty'].iloc[0]
    quantity = df.loc[df['symbol'] == symbol, 'quantity'].iloc[0]
    position = df.loc[df['symbol'] == symbol, 'position'].iloc[0]


    return float(close), float(high), float(low), float(ema), float(ema_cross), float(ema_diff), float(min_qty), float(quantity), position

def check(symbol):
    close , high , low , ema , ema_cross , ema_diff , min_qty , quantity , position = get_data(symbol)
    if low < ema and ema < high :
        ema_cross = ema
        print(f"Changed EMA Cross: {ema_cross}")
        set_ema_cross(symbol, ema_cross)
        if position == "SELL":
            close_position(symbol, "BUY")
        elif position == "BUY":
            close_position(symbol, "SELL")
        else:
            pass
    close , high , low , ema , ema_cross , ema_diff , min_qty , quantity , position = get_data(symbol)
    if ema_cross != 0:
        if low < ema_cross * (1 - ema_diff):
            if position == "SELL":
                print(f"{symbol} Closing Sell and opening Buy")
                close_position(symbol,"BUY")
                open_position(symbol, "BUY")
            elif position == "HOLD":
                print(f"{symbol}opening Buy")
                open_position(symbol, "BUY")

        elif high > ema_cross * (1 + ema_diff):
            if position == "BUY":
                print(f"{symbol} Closing Buy and opening Sell")
                close_position(symbol , "SELL")
                open_position(symbol, "SELL")
            elif position == "HOLD":
                print(f"{symbol} opening Sell")
                open_position(symbol, "SELL")



def close_position(symbol , side):
    set_position(symbol, "HOLD")
    qty = get_qty(symbol)
    place_order(symbol, side, qty)
    

def place_order(symbol, side, qty):
    payload = {}
    path = "/openApi/swap/v2/trade/order"
    method = "POST"
    paramsMap = {
        "symbol": symbol,
        "side": side,
        "positionSide": "BOTH",
        "type": "MARKET",
        "quantity": qty
    }

    try:
        response = call_bingx(payload, path, method, paramsMap)
        pass
    except Exception as e:
        print(f"Error placing order: {e}")
        logging.error(f"Error placing order: {e}")
        return None
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    trade_data = {
        'time': current_time,
        'symbol': symbol,
        'side': side,
        'quantity': qty,
        'response': response
    }

    logging.info(f"Trade Data: {trade_data}")
    git_push()

    return response

def open_position(symbol , side):
    set_position(symbol, side)
    qty = update_quantity(symbol)
    place_order(symbol, side, qty)


def git_push():
    try:
        # Pull latest changes from the remote
        subprocess.run(['git', 'pull'], check=True)
        
        # Add all changes
        subprocess.run(['git', 'add', '.'], check=True)
        
        # Commit changes with a message
        subprocess.run(['git', 'commit', '-m', 'auto'], check=True)
        
        # Push changes to the remote repository
        subprocess.run(['git', 'push'], check=True)
        
        print("Pulled and pushed changes to the repository successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        logging.error(f"An error occurred in git_push : {e}")


def get_candles(symbol, interval="5m", limit=1440):
    payload = {}
    path = "/openApi/swap/v3/quote/klines"
    method = "GET"
    paramsMap = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    data = call_bingx(payload, path, method, paramsMap)
    data = json.loads(data)
    df = pd.DataFrame(data['data'], columns=['time', 'open', 'high', 'low', 'close', 'volume'])
    df['time'] = pd.to_datetime(df['time'], unit='ms', utc=True).dt.strftime('%Y-%m-%d %H:%M')
    df.set_index('time', inplace=True)
    df = df[::-1]


    ema = EMAIndicator(EMAIndicator(df['close'], window=100).ema_indicator(), window=100).ema_indicator()

    ema = float(ema.iloc[-1])
    close = float(df['close'].iloc[-1])
    high = float(df['high'].iloc[-1])
    low = float(df['low'].iloc[-1])

    set_candle(symbol, close, high, low, round(ema, 4))

    return True


def main():

    symbols = ['BTC-USDT', 'ETH-USDT', 'BNB-USDT', 'ADA-USDT', 'XRP-USDT', 'AVAX-USDT', 'SOL-USDT', 'SUI-USDT', 'TRX-USDT']
    for symbol in symbols:
        get_candles(symbol)
        check(symbol)
        close, high, low, ema, ema_cross, ema_diff, min_qty, quantity, position = get_data(symbol)
        if ema_cross != 0:
            diff = round(((close - ema_cross) / ema_cross) * 100 , 2)
        else:
            diff = 0.00
        print(f"Symbol: {symbol}, EMA Cross: {ema_cross}, Diff: {diff}% , Position: {position}")
        logging.info(f"Symbol: {symbol}, EMA Cross: {ema_cross}, Diff: {diff}% , Position: {position}")

if __name__ == '__main__':
    while True:
        try:
            main()
            time.sleep(60)
            print('------------------------------------------------------------')
        except Exception as e:
            print(f"Error: {e}")
            logging.info(f"Error in main : {e}")
            time.sleep(60)

