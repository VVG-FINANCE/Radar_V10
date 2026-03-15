import pandas as pd
import numpy as np
import time
import requests
import yfinance as yf

# -----------------------------
# Configurações fixas EUR/USD
# -----------------------------
EXCHANGE_RATE_API_KEY = "SUA_CHAVE_EXCHANGERATE_API"
BASE_CURRENCY = "EUR"
TARGET_CURRENCY = "USD"

# Backoff
MIN_INTERVAL = 5        # segundos
MAX_INTERVAL = 60       # segundos
BACKOFF_FACTOR = 2

# EMA
EMA_PERIOD = 5  # quantidade de pontos para EMA

# Histórico para EMA
price_history = []

# -----------------------------
# Funções para obter dados EUR/USD
# -----------------------------
def fetch_exchangerate_api():
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}/latest/{BASE_CURRENCY}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        return data['conversion_rates'][TARGET_CURRENCY]
    except Exception as e:
        print(f"Erro ExchangeRate-API: {e}")
        return None

def fetch_frankfurter_api():
    url = f"https://api.frankfurter.app/latest?from={BASE_CURRENCY}&to={TARGET_CURRENCY}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        return data['rates'][TARGET_CURRENCY]
    except Exception as e:
        print(f"Erro Frankfurter API: {e}")
        return None

def fetch_yfinance():
    symbol = f"{BASE_CURRENCY}{TARGET_CURRENCY}=X"
    try:
        ticker = yf.Ticker(symbol)
        price = ticker.history(period="1d")['Close'][-1]
        return float(price)
    except Exception as e:
        print(f"Erro yfinance: {e}")
        return None

# -----------------------------
# Função de EMA
# -----------------------------
def calculate_ema(prices, period=EMA_PERIOD):
    if not prices:
        return None
    series = pd.Series(prices)
    return series.ewm(span=period, adjust=False).mean().iloc[-1]

# -----------------------------
# Função principal EUR/USD
# -----------------------------
def get_average_price():
    global price_history
    prices = []
    for fetcher in [fetch_exchangerate_api, fetch_frankfurter_api, fetch_yfinance]:
        price = fetcher()
        if price is not None:
            prices.append(price)
    if prices:
        avg_price = sum(prices)/len(prices)
        price_history.append(avg_price)
        ema_price = calculate_ema(price_history)
        return ema_price
    return None

# -----------------------------
# Funções econofísicas (mantidas)
# -----------------------------
def dfa(series, scale_min=4, scale_max=50):
    x = np.cumsum(series - np.mean(series))
    scales = np.arange(scale_min, scale_max)
    fluct = []
    for s in scales:
        segments = len(x)//s
        rms = []
        for i in range(segments):
            seg = x[i*s:(i+1)*s]
            poly = np.polyfit(np.arange(s), seg, 1)
            trend = np.polyval(poly, np.arange(s))
            rms.append(np.sqrt(np.mean((seg-trend)**2)))
        fluct.append(np.mean(rms))
    coeffs = np.polyfit(np.log(scales), np.log(fluct), 1)
    return coeffs[0]

def hawkes_effect(price_changes, decay=0.8):
    intensity = 0
    for delta in price_changes[-10:]:
        intensity = decay*intensity + abs(delta)
    return intensity

def particle_energy(series, k=0.5):
    v = np.log(series/series.shift(1)).fillna(0)
    K = 0.5*v**2
    ma = series.rolling(20).mean().iloc[-1]
    U = 0.5*k*(series.iloc[-1]-ma)**2
    E = K.iloc[-1]+U
    return K.iloc[-1], U, E

def adaptive_std(series, window=20):
    returns = series.pct_change().fillna(0)
    return returns.rolling(window).std().iloc[-1]

# -----------------------------
# Radar econofísico
# -----------------------------
def calculate_radar(series, mode="DAY", trend_direction=0):
    if series is None or len(series)<10:
        return None
    p_atual = float(series.iloc[-1])
    params = {"SCALPER":{"p":10,"m":1.5},"DAY":{"p":24,"m":2.2},"SWING":{"p":50,"m":3.8},"POSITION":{"p":120,"m":5.5}}
    p = params[mode]["p"]
    m = params[mode]["m"]

    ma = series.rolling(p).mean().iloc[-1]
    std = series.rolling(p).std().iloc[-1]+1e-9
    z_score = (p_atual - ma)/std

    if mode!="POSITION" and trend_direction!=0:
        if (trend_direction>0 and z_score<0) or (trend_direction<0 and z_score>0):
            return None

    atr = (series.rolling(p).max() - series.rolling(p).min()).iloc[-1]
    sigma = adaptive_std(series, window=p)
    z_inf = p_atual-(atr*0.4)-sigma*0.5
    z_sup = p_atual+(atr*0.4)+sigma*0.5

    K,U,E = particle_energy(series)
    alpha = dfa(series)
    intensity = hawkes_effect(series.diff())

    data = None
    if z_score>1.3:
        data = {"tipo":"COMPRA","z_inf":z_inf,"z_sup":z_sup,"tp":[p_atual+atr*m,p_atual+atr*m*1.3],"sl":[p_atual-atr*m*0.7,p_atual-atr*m]}
    elif z_score<-1.3:
        data = {"tipo":"VENDA","z_inf":z_inf,"z_sup":z_sup,"tp":[p_atual-atr*m,p_atual-atr*m*1.3],"sl":[p_atual+atr*m*0.7,p_atual+atr*m]}

    if data:
        prob = min(65+abs(z_score)**1.5, 98.8)
        prob *= (1+0.1*(alpha-0.5))
        prob *= (1+0.05*intensity)
        prob *= (1+0.1*E*10000)
        prob *= (1+0.5*sigma)
        data.update({"prob":min(prob,99.9),"K":K,"U":U,"E":E,"sigma":sigma})

    return data
