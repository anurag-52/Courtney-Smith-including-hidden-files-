import pandas as pd
def channel_breakout(df: pd.DataFrame, lookback: int = 55):
    if len(df) < lookback + 1: 
        return None
    hh = df['CLOSE'].rolling(lookback).max().iloc[-2]
    ll = df['CLOSE'].rolling(lookback).min().iloc[-2]
    close = df['CLOSE'].iloc[-1]
    if close > hh:
        return {"action": "BUY", "buy_price": float(close), "stop_loss": float(ll)}
    return None
def five_day_condition(df: pd.DataFrame):
    if len(df) < 6: 
        return None
    last5_high = df['HIGH'].iloc[-6:-1].max()
    last5_low = df['LOW'].iloc[-6:-1].min()
    close = df['CLOSE'].iloc[-1]
    if close > last5_high:
        sl = last5_low
        return {"action": "BUY", "buy_price": float(close), "stop_loss": float(sl)}
    return None
def trend_filter(df: pd.DataFrame):
    if len(df) < 220:
        return None
    sma50 = df['CLOSE'].rolling(50).mean().iloc[-1]
    sma200 = df['CLOSE'].rolling(200).mean().iloc[-1]
    close = df['CLOSE'].iloc[-1]
    if close > sma200 and sma50 > sma200:
        tr1 = df['HIGH'] - df['LOW']
        tr2 = (df['HIGH'] - df['CLOSE'].shift()).abs()
        tr3 = (df['LOW'] - df['CLOSE'].shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(14).mean().iloc[-1]
        return {"action": "BUY", "buy_price": float(close), "stop_loss": float(close - 3*atr)}
    return None
def pyramid_trend(df: pd.DataFrame):
    if len(df) < 60:
        return None
    ema20 = df['CLOSE'].ewm(span=20, adjust=False).mean().iloc[-1]
    close = df['CLOSE'].iloc[-1]
    tr1 = df['HIGH'] - df['LOW']
    tr2 = (df['HIGH'] - df['CLOSE'].shift()).abs()
    tr3 = (df['LOW'] - df['CLOSE'].shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().iloc[-1]
    if close > ema20:
        return {"action": "BUY", "buy_price": float(close), "stop_loss": float(close - 2.5*atr), "pyramid_step": float(2*atr)}
    return None