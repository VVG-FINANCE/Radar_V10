import streamlit as st
import time
from datetime import datetime
from engine import get_data_v10, calculate_radar
from interface import apply_ui_v10, render_radar_block

st.set_page_config(page_title="AURAXIS V10 RADAR EUR/USD", layout="wide")
apply_ui_v10()
placeholder = st.empty()

while True:
    with placeholder.container():
        df,pips = get_data_v10("EURUSD=X")
        if not df.empty:
            p_atual = float(df['close'].iloc[-1])
            # Trend semanal
            pos_signal = calculate_radar(df,"POSITION",0)
            trend_dir = 1 if pos_signal and pos_signal['tipo']=="COMPRA" else -1 if pos_signal else 0

            cor_pips = "#3fb950" if pips>=0 else "#f85149"
            st.markdown(f"<div class='header-radar'><h1 style='margin:0;font-family:monospace;'>{p_atual:.5f}</h1><span style='color:{cor_pips}; font-weight:bold;'>{'+' if pips>=0 else ''}{pips:.1f} PIPS HOJE</span></div>",unsafe_allow_html=True)
            st.write("")
            
            c1,c2,c3,c4 = st.columns(4)
            with c1: render_radar_block("SCALPER (1M/5M)", calculate_radar(df,"SCALPER",trend_dir))
            with c2: render_radar_block("DAY TRADE (15M/1H)", calculate_radar(df,"DAY",trend_dir))
            with c3: render_radar_block("SWING (4H/DIÁRIO)", calculate_radar(df,"SWING",trend_dir))
            with c4: render_radar_block("POSITION (SEMANAL)", pos_signal)
            
            st.caption(f"Radar V10 Econofísico EUR/USD | Sincronia: {datetime.now().strftime('%H:%M:%S')}")
        else:
            st.warning("📡 Conectando aos Satélites de Dados Financeiros...")
    time.sleep(5)
