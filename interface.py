import streamlit as st

def apply_ui_v10():
    st.markdown("""
        <style>
        .stApp { background-color:#040508; color:#ffffff; }
        .header-radar{background:linear-gradient(90deg,#0d1117 0%,#161b22 100%);padding:25px;border-radius:15px;border-bottom:2px solid #30363d;text-align:center;}
        .card-radar{background:#0d1117;border:1px solid #21262d;border-radius:10px;padding:15px;margin-bottom:15px;}
        .tag-buy{color:#3fb950;font-weight:bold;background:rgba(63,185,80,0.1);padding:2px 8px;border-radius:4px;}
        .tag-sell{color:#f85149;font-weight:bold;background:rgba(248,81,73,0.1);padding:2px 8px;border-radius:4px;}
        .zone-label{color:#8b949e;font-size:0.7rem;letter-spacing:1px;}
        </style>
    """,unsafe_allow_html=True)

def render_radar_block(title,data):
    if data:
        tag_class = "tag-buy" if data['tipo']=="COMPRA" else "tag-sell"
        st.markdown(f"""
            <div class='card-radar'>
            <div style='display:flex;justify-content:space-between;align-items:center;'>
            <span style='font-weight:bold;'>{title}</span>
            <span class='{tag_class}'>{data['tipo']}</span></div>
            <div style='margin-top:10px;'><span class='zone-label'>ZONA DE ENTRADA</span><br>
            <code style='color:#58a6ff;'>{data['z_inf']:.5f} — {data['z_sup']:.5f}</code></div>
            <div style='display:flex;gap:10px;margin-top:10px;'>
            <div style='flex:1;'><span class='zone-label' style='color:#3fb950;'>TP</span><br>
            <b>{data['tp'][0]:.5f}</b><br><b>{data['tp'][1]:.5f}</b></div>
            <div style='flex:1;'><span class='zone-label' style='color:#f85149;'>SL</span><br>
            <b>{data['sl'][0]:.5f}</b><br><b>{data['sl'][1]:.5f}</b></div></div>
            <div style='margin-top:10px;font-size:0.75rem;color:#8b949e;'>
            Probabilidade:<b>{data['prob']:.1f}%</b><br>Energias: K={data['K']:.6f}, U={data['U']:.6f}, E={data['E']:.6f}<br>σ={data['sigma']:.6f}
            </div></div>
        """,unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='card-radar' style='opacity:0.3;'><span style='font-weight:bold;'>{title}</span><br><span class='zone-label'>AGUARDANDO ALINHAMENTO...</span></div>",unsafe_allow_html=True)
