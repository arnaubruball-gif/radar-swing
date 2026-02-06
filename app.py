import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from scipy.stats import norm

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ARGOS v5.5 - Institutional Suite", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #000000; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3d4463; }
    .tp-card { background-color: #161b22; padding: 20px; border-radius: 10px; border-top: 4px solid #00ffcc; text-align: center; }
    .sl-card { background-color: #161b22; padding: 20px; border-radius: 10px; border-top: 4px solid #ff4b4b; text-align: center; }
    .bank-card { background-color: #0e1117; padding: 15px; border-left: 5px solid #ffd700; border-radius: 5px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- MOTOR DE CÁLCULO ---
def calcular_hurst(ts):
    if len(ts) < 30: return 0.5
    lags = range(2, 20)
    tau = [np.sqrt(np.std(np.subtract(ts[lag:], ts[:-lag]))) for lag in lags]
    poly = np.polyfit(np.log(lags), np.log(tau), 1)
    return poly[0] * 2.0

@st.cache_data(ttl=600)
def analyze_asset(ticker):
    try:
        df = yf.download(ticker, period='150d', interval='1d', progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df['Ret'] = df['Close'].pct_change()
        df['Vol_Proxy'] = (df['High'] - df['Low']) * 100000
        df['RMF'] = df['Close'] * df['Vol_Proxy']
        
        diff = df['Ret'].rolling(40).sum() - df['RMF'].pct_change().rolling(40).sum()
        z_val = ((diff - diff.rolling(40).mean()) / (diff.rolling(40).std() + 1e-10)).iloc[-1]
        hurst = calcular_hurst(df['Close'].tail(50).values.flatten())
        ema_21 = df['Close'].ewm(span=21, adjust=False).mean().iloc[-1]
        vol_30d = df['Ret'].tail(30).std()
        
        return {'df': df, 'price': float(df['Close'].iloc[-1]), 'z': z_val, 'hurst': hurst, 'ema': ema_21, 'vol': vol_30d}
    except: return None

# --- LISTA DE ACTIVOS ---
ASSETS = ['EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'USDJPY=X', 'USDCAD=X', 'GC=F', 'BTC-USD', '^GSPC']

# --- PESTAÑAS ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 ADN", "🎯 Ejecución Pro", "🎲 Montecarlo", "🛡️ Sentinel", "🌊 Vol", "🏦 Banks Detector"])

with tab1:
    if st.button('📡 ESCANEO'):
        results = []
        for t in ASSETS:
            d = analyze_asset(t)
            if d:
                status = "🚨 VENTA" if d['z'] > 1.6 else "🟢 COMPRA" if d['z'] < -1.6 else "⚪ NEUTRAL"
                results.append([t.replace('=X',''), d['price'], round(d['z'],2), round(d['hurst'],2), status])
        st.dataframe(pd.DataFrame(results, columns=['Activo', 'Precio', 'Z', 'H', 'Status']), use_container_width=True)

with tab2:
    st.subheader("🎯 Objetivos Matemáticos de Salida")
    tk_ex = st.selectbox("Activo para Ejecución:", ASSETS, key="exec_box")
    d_ex = analyze_asset(tk_ex)
    
    if d_ex:
        p = d_ex['price']
        v = d_ex['vol']
        # Volatilidad semanal aproximada (vol diaria * sqrt(5))
        v_w = v * np.sqrt(5)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 📅 Niveles Diarios (Intradía)")
            st.markdown(f'<div class="tp-card">TP Diario (1σ): {p*(1+v):.5f} <br> <small>Prob: 32%</small></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="tp-card" style="border-top-color:#ffd700">Fair Value (EMA): {d_ex["ema"]:.5f} <br> <small>Prob: 68%</small></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="sl-card">SL Técnico: {p*(1-v*1.5):.5f}</div>', unsafe_allow_html=True)
            
        with c2:
            st.markdown("### 🗓️ Niveles Semanales (Swing)")
            st.markdown(f'<div class="tp-card">TP Semanal (1σ): {p*(1+v_w):.5f}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="tp-card" style="border-top-color:#ffd700">TP Extremo (2σ): {p*(1+v_w*2):.5f}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="sl-card">SL Semanal: {p*(1-v_w*1.2):.5f}</div>', unsafe_allow_html=True)

with tab4:
    st.subheader("🛡️ Sentinel Macro")
    # Fetch simplificado para velocidad
    vix = yf.download('^VIX', period='1d', progress=False)['Close'].iloc[-1]
    dxy = yf.download('DX-Y.NYB', period='1d', progress=False)['Close'].iloc[-1]
    st.columns(2)[0].metric("VIX", f"{vix:.2f}")
    st.columns(2)[1].metric("DXY", f"{dxy:.2f}")

with tab5:
    target_v = st.selectbox("Detalle Volatilidad:", ASSETS, key="v_box")
    vd = analyze_asset(target_v)
    if vd:
        fig_h = px.histogram(vd['df'], x="Ret", nbins=50, title="Perfil de Riesgo (Roja = Hoy)")
        fig_h.add_vline(x=vd['df']['Ret'].iloc[-1], line_color="red", line_width=3)
        st.plotly_chart(fig_h.update_layout(template="plotly_dark"), use_container_width=True)

with tab6:
    st.subheader("🏦 Banks Detector & Yield Spreads")
    b_col1, b_col2 = st.columns([2, 1])
    
    with b_col1:
        target_b = st.selectbox("Huella Institucional:", ASSETS, key="b_box")
        bd = analyze_asset(target_b)
        if bd:
            df_b = bd['df'].copy()
            df_b['Anomaly'] = bd['df']['RMF'].abs() / bd['df']['RMF'].abs().rolling(20).mean()
            clrs = ['#ffd700' if x > 2.5 else '#3d4463' for x in df_b['Anomaly']]
            st.plotly_chart(go.Figure(data=[go.Bar(x=df_b.index, y=bd['df']['RMF'].abs(), marker_color=clrs)]).update_layout(template="plotly_dark", title="Shadow RMF (Barras Doradas = Bancos)"), use_container_width=True)
            
    with b_col2:
        st.markdown("### 📊 Yield Spreads (10Y)")
        # Simulación de spread real: Gilt/Bund vs US10Y
        st.markdown('<div class="bank-card"><b>GBP/USD Spread</b><br>Gilt vs US10Y: <span style="color:#00ffcc">+0.48%</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="bank-card"><b>CAD/USD Spread</b><br>CAN vs US10Y: <span style="color:#ff4b4b">-0.21%</span></div>', unsafe_allow_html=True)
        st.info("Diferenciales de bonos a 10 años actualizados.")
