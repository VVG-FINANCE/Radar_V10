import streamlit as st
import time
from datetime import datetime
from engine import get_average_price, calculate_radar
from interface import apply_ui_v10, render_radar_block
import pandas as pd

st.set_page_config(page_title="AURAXIS V10 RADAR EUR/USD", layout="wide")
apply_ui_v10()
placeholder = st.empty()

# Histórico para séries econométricas
price_series = pd.Series(dtype=float)

interval = 5

while True:
    with placeholder.container():
        price = get_average_price()
        if price:
            price_series = price_series.append(pd.Series([price]), ignore_index=True)
            p_atual = float(price)
            # Trend semanal
            pos_signal = calculate_radar(price_series,"POSITION",0)
            trend_dir = 1 if pos_signal and pos_signal['tipo']=="COMPRA" else -1 if pos_signal else 0

            cor_pips = "#3fb950" if price_series.diff().iloc[-1]>=0 else "#f85149"
            st.markdown(f"<div class='header-radar'><h1 style='margin:0;font-family:monospace;'>{p_atual:.5f}</h1><span style='color:{cor_pips}; font-weight:bold;'>{'+' if price_series.diff().iloc[-1]>=0 else ''}{price_series.diff().iloc[-1]:.5f} HOJE</span></div>",unsafe_allow_html=True)
            st.write("")

            c1,c2,c3,c4 = st.columns(4)
            with c1: render_radar_block("SCALPER (1M/5M)", calculate_radar(price_series,"SCALPER",trend_dir))
            with c2: render_radar_block("DAY TRADE (15M/1H)", calculate_radar(price_series,"DAY",trend_dir))
            with c3: render_radar_block("SWING (4H/DIÁRIO)", calculate_radar(price_series,"SWING",trend_dir))
            with c4: render_radar_block("POSITION (SEMANAL)", pos_signal)

            st.caption(f"Radar V10 Econofísico EUR/USD | Sincronia: {datetime.now().strftime('%H:%M:%S')}")
            interval = 5
        else:
            st.warning("📡 Falha ao obter preço, tentando novamente...")
            interval = min(60, interval*2)
    time.sleep(interval)
