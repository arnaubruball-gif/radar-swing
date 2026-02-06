import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# --- 1. CONFIGURACIÓN (Mantenida) ---
st.set_page_config(page_title="ARGOS v6.1 - Sentinel Enhanced", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #000000; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3d4463; }
    .tp-card { background-color: #161b22; padding: 20px; border-radius: 10px; border-top: 4px solid #00ffcc; text-align: center; margin-bottom:10px; }
    .sl-card { background-color: #161b22; padding: 20px; border-radius: 10px; border-top: 4px solid #ff4b4b; text-align: center; }
    .bank-card { background-color: #0e1117; padding: 10px; border-left: 5px solid #ffd700; margin-bottom: 5px; font-size: 0.85rem; }
    .risk-banner { padding: 20px; border-radius: 10px; text-align: center; font-weight: bold; font-size: 1.5rem; margin-top: 10px; color: black; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE CÁLCULO (Mantenido intacto) ---
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
        r2_series = []
        for i in range(len(df)):
            if i < 30: r2_series.append(0); continue
            subset = df.iloc[i-30:i].dropna()
            r2 = sm.OLS(subset['Ret'], sm.add_constant(subset['RMF'])).fit().rsquared
            r2_series.append(r2)
        df['R2_Dynamic'] = r2_series
        diff = df['Ret'].rolling(40).sum() - df['RMF'].pct_change().rolling(40).sum()
        z_val = ((diff - diff.rolling(40).mean()) / (diff.rolling(40).std() + 1e-10)).iloc[-1]
        hurst = calcular_hurst(df['Close'].tail(50).values.flatten())
        ema_21 = df['Close'].ewm(span=21, adjust=False).mean().iloc[-1]
        return {'df': df, 'price': float(df['Close'].iloc[-1]), 'z': z_val, 'r2': df['R2_Dynamic'].iloc[-1], 'hurst': hurst, 'ema': float(ema_21), 'vol': df['Ret'].tail(30).std()}
    except: return None

# --- 3. LISTA DE ACTIVOS (Mantenida) ---
ASSETS = ['EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'USDCAD=X', 'USDJPY=X', 'GC=F', 'BTC-USD', '^GSPC']

# --- 4. PESTAÑAS ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 ADN", "🎯 Ejecución Pro", "🎲 Montecarlo", "🛡️ Sentinel", "🌊 Vol-Monitor", "🏦 Banks Detector"])

# Pestañas 1, 2, 3, 5 y 6 se mantienen igual que en v6.0
with tab1:
    if st.button('📡 ESCANEO ADN'):
        results = []
        for t in ASSETS:
            d = analyze_asset(t)
            if d:
                status = "🚨 VENTA" if d['z'] > 1.6 else "🟢 COMPRA" if d['z'] < -1.6 else "⚪ NEUTRAL"
                results.append([t.replace('=X',''), d['price'], round(d['r2'],3), round(d['z'],2), round(d['hurst'],2), status])
        st.dataframe(pd.DataFrame(results, columns=['Activo', 'Precio', 'R2', 'Z-Diff', 'Hurst', 'Veredicto']), use_container_width=True)

with tab2:
    st.subheader("🎯 Ejecución Pro")
    target_e = st.selectbox("Activo:", ASSETS, key="exec_s")
    de = analyze_asset(target_e)
    if de:
        p, v, z = de['price'], de['vol'], de['z']
        sl = p * (1 + v*1.5) if z > 0 else p * (1 - v*1.5)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="tp-card">TP Diario (EMA 21): {de["ema"]:.5f}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="sl-card">SL Estadístico: {sl:.5f}</div>', unsafe_allow_html=True)
        with c2:
            v_w = v * np.sqrt(5)
            st.markdown(f'<div class="tp-card">Swing Target 1σ: {p*(1-v_w if z > 0 else 1+v_w):.5f}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="tp-card" style="border-top-color:#ffd700">Swing Target 2σ: {p*(1-v_w*2 if z > 0 else 1+v_w*2):.5f}</div>', unsafe_allow_html=True)

with tab3:
    st.subheader("🎲 Montecarlo")
    target_m = st.selectbox("Simular:", ASSETS, key="mc_s")
    dm = analyze_asset(target_m)
    if dm:
        sims, dias = 1000, 15
        rets = np.random.normal(dm['df']['Ret'].mean(), dm['vol'], (sims, dias))
        caminos = dm['price'] * (1 + rets).cumprod(axis=1)
        fig_m = go.Figure()
        for i in range(15): fig_m.add_trace(go.Scatter(y=caminos[i], line=dict(width=1), opacity=0.3, showlegend=False))
        fig_m.add_trace(go.Scatter(y=np.percentile(caminos, 50, axis=0), line=dict(color='#00ffcc', width=4), name="Mediana"))
        st.plotly_chart(fig_m.update_layout(template="plotly_dark", height=400), use_container_width=True)

# --- REPARACIÓN DE TAB 4: SENTINEL ---
with tab4:
    st.subheader("🛡️ Sentinel Macro: S&P 500 vs VIX")
    try:
        # Descarga de datos
        s_data = yf.download(['^GSPC', '^VIX', 'DX-Y.NYB'], period='60d', progress=False)['Close']
        sp = s_data['^GSPC']
        vix = s_data['^VIX']
        dxy = s_data['DX-Y.NYB']

        # Métricas principales
        m1, m2, m3 = st.columns(3)
        m1.metric("S&P 500", f"{sp.iloc[-1]:.2f}", f"{sp.pct_change().iloc[-1]*100:.2f}%")
        m2.metric("VIX Index", f"{vix.iloc[-1]:.2f}", f"{vix.iloc[-1]-vix.iloc[-2]:+.2f}")
        m3.metric("DXY Index", f"{dxy.iloc[-1]:.2f}")

        # Gráfico S&P 500 vs VIX (Doble Eje)
        fig_sent = go.Figure()
        fig_sent.add_trace(go.Scatter(x=sp.index, y=sp, name="S&P 500", line=dict(color='#00ffcc', width=2), yaxis="y1"))
        fig_sent.add_trace(go.Scatter(x=vix.index, y=vix, name="VIX (Miedo)", line=dict(color='#ff4b4b', width=2, dash='dot'), yaxis="y2"))
        
        fig_sent.update_layout(
            template="plotly_dark",
            yaxis=dict(title="Precio S&P 500", side="left", showgrid=False),
            yaxis2=dict(title="Nivel VIX", side="right", overlaying="y", showgrid=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=450
        )
        st.plotly_chart(fig_sent, use_container_width=True)

        # Semáforo de Riesgo Lógica
        vix_val = vix.iloc[-1]
        dxy_val = dxy.iloc[-1]
        sp_ret_5d = sp.pct_change(5).iloc[-1]
        
        score = 0
        if vix_val > 20: score += 1
        if vix_val > 28: score += 1
        if dxy_val > 104.5: score += 1
        if sp_ret_5d < -0.02: score += 1
        
        labels = ["RISK-ON: Mercado Estable", "PRECAUCIÓN: Ruido detectado", "RIESGO ALTO: Salida de capital", "PÁNICO: Risk-Off Extremo"]
        colors = ["#00ffcc", "#ffd700", "#ff8c00", "#ff4b4b"]
        idx = min(score, 3)
        
        st.markdown(f'<div class="risk-banner" style="background-color:{colors[idx]};">ESTADO MACRO: {labels[idx]}</div>', unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Error cargando Sentinel: {e}")

with tab5:
    st.subheader("🌊 Vol-Monitor")
    target_v = st.selectbox("Activo Detalle:", ASSETS, key="v_s")
    dv = analyze_asset(target_v)
    if dv:
        fig_h = px.histogram(dv['df'], x="Ret", nbins=50, title="Distribución de Riesgo")
        fig_h.add_vline(x=dv['df']['Ret'].iloc[-1], line_color="red", line_width=4)
        st.plotly_chart(fig_h.update_layout(template="plotly_dark"), use_container_width=True)

with tab6:
    st.subheader("🏦 Banks Detector")
    col_b1, col_b2 = st.columns([2, 1])
    with col_b1:
        target_b = st.selectbox("Shadow RMF:", ASSETS, key="b_s")
        db = analyze_asset(target_b)
        if db:
            df_b = db['df'].copy()
            df_b['Anom'] = df_b['RMF'].abs() / df_b['RMF'].abs().rolling(20).mean()
            clrs = ['#ffd700' if x > 2.5 else '#3d4463' for x in df_b['Anom']]
            st.plotly_chart(go.Figure(data=[go.Bar(x=df_b.index, y=df_b['RMF'].abs(), marker_color=clrs)]).update_layout(template="plotly_dark"), use_container_width=True)
    with col_b2:
        st.write("**Global Yield Spreads (10Y)**")
        yield_data = {'US10Y': 4.25, 'GER10Y': 2.40, 'UK10Y': 4.10, 'CAN10Y': 3.50, 'AUS10Y': 4.40, 'JPN10Y': 0.85}
        spreads = {"EUR/USD": yield_data['GER10Y'] - yield_data['US10Y'], "GBP/USD": yield_data['UK10Y'] - yield_data['US10Y'], "CAD/USD": yield_data['CAN10Y'] - yield_data['US10Y'], "AUD/USD": yield_data['AUS10Y'] - yield_data['US10Y'], "JPY/USD": yield_data['JPN10Y'] - yield_data['US10Y']}
        for pair, val in spreads.items():
            color = "#00ffcc" if val > -1.5 else "#ff4b4b"
            st.markdown(f'<div class="bank-card">{pair} Spread: <span style="color:{color}">{val:+.2f}%</span></div>', unsafe_allow_html=True)
