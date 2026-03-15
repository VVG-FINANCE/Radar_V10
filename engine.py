import pandas as pd
import numpy as np
import yfinance as yf

# =========================
# Função para obter dados
# =========================
def get_data_v10(ticker="EURUSD=X"):
    try:
        # Dados robustos de 1 mês para múltiplos intervalos
        data = yf.download(ticker, period="1mo", interval="15m", progress=False)
        if data.empty: return pd.DataFrame(), 0.0
        
        p_atual = float(data['Close'].iloc[-1])
        p_ontem = float(yf.download(ticker, period="2d", interval="1d", progress=False)['Close'].iloc[-2])
        pips_diff = (p_atual - p_ontem) * 10000
        
        df = data[['Open', 'High', 'Low', 'Close']].copy()
        df.columns = ['open', 'high', 'low', 'close']
        return df, float(pips_diff)
    except:
        return pd.DataFrame(), 0.0

# =========================
# DFA – Detrended Fluctuation Analysis
# =========================
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
            rms.append(np.sqrt(np.mean((seg - trend)**2)))
        fluct.append(np.mean(rms))
    coeffs = np.polyfit(np.log(scales), np.log(fluct), 1)
    return coeffs[0]

# =========================
# Hawkes Effect – Auto-excitação
# =========================
def hawkes_effect(price_changes, decay=0.8):
    intensity = 0
    for delta in price_changes[-10:]:
        intensity = decay*intensity + abs(delta)
    return intensity

# =========================
# Energia de partículas
# =========================
def particle_energy(df, k=0.5):
    v = np.log(df['close'] / df['close'].shift(1)).fillna(0)
    K = 0.5 * v**2
    ma = df['close'].rolling(20).mean().iloc[-1]
    U = 0.5 * k * (df['close'].iloc[-1] - ma)**2
    E = K.iloc[-1] + U
    return K.iloc[-1], U, E

# =========================
# Desvio padrão adaptativo
# =========================
def adaptive_std(df, window=20):
    returns = df['close'].pct_change().fillna(0)
    sigma = returns.rolling(window).std().iloc[-1]
    return sigma

# =========================
# Radar econofísico
# =========================
def calculate_radar(df, mode="DAY", trend_direction=0):
    if df.empty: return None
    p_atual = float(df['close'].iloc[-1])
    
    # Configurações por horizonte
    params = {
        "SCALPER": {"p": 10, "m": 1.5},
        "DAY": {"p": 24, "m": 2.2},
        "SWING": {"p": 50, "m": 3.8},
        "POSITION": {"p": 120, "m": 5.5}
    }
    p = params[mode]["p"]
    m = params[mode]["m"]

    # =========================
    # Z-Score Adaptativo
    # =========================
    ma = df['close'].rolling(p).mean().iloc[-1]
    std = df['close'].rolling(p).std().iloc[-1] + 1e-9
    z_score = (p_atual - ma) / std

    # Filtro de alinhamento institucional
    if mode != "POSITION" and trend_direction != 0:
        if (trend_direction > 0 and z_score < 0) or (trend_direction < 0 and z_score > 0):
            return None

    # ATR
    atr = (df['high'] - df['low']).rolling(p).mean().iloc[-1]

    # Zonas de entrada adaptativas
    sigma = adaptive_std(df, window=p)
    z_inf = p_atual - (atr * 0.4) - sigma*0.5
    z_sup = p_atual + (atr * 0.4) + sigma*0.5

    # Energia e indicadores econofísicos
    K, U, E = particle_energy(df)
    alpha = dfa(df['close'])
    intensity = hawkes_effect(df['close'].diff())

    # Lógica de gatilho
    data = None
    if z_score > 1.3:
        data = {
            "tipo": "COMPRA",
            "z_inf": z_inf,
            "z_sup": z_sup,
            "tp": [p_atual + (atr*m), p_atual + (atr*m*1.3)],
            "sl": [p_atual - (atr*m*0.7), p_atual - (atr*m)],
        }
    elif z_score < -1.3:
        data = {
            "tipo": "VENDA",
            "z_inf": z_inf,
            "z_sup": z_sup,
            "tp": [p_atual - (atr*m), p_atual - (atr*m*1.3)],
            "sl": [p_atual + (atr*m*0.7), p_atual + (atr*m)],
        }

    # Ajuste de probabilidade combinando fatores
    if data:
        prob = min(65 + abs(z_score)**1.5, 98.8)
        prob *= (1 + 0.1*(alpha-0.5))       # DFA
        prob *= (1 + 0.05*intensity)       # Hawkes
        prob *= (1 + 0.1*E*10000)          # Energia total
        prob *= (1 + 0.5*sigma)            # Desvio padrão
        data["prob"] = min(prob, 99.9)
        data["K"] = K
        data["U"] = U
        data["E"] = E
        data["sigma"] = sigma

    return data
