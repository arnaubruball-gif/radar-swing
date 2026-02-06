import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# --- 1. CONFIGURACIÓN (Sin cambios) ---
st.set_page_config(page_title="ARGOS v6.4 - Pro Execution Updates", layout="wide")

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

# --- 2. MOTOR DE CÁLCULO (Sin cambios) ---
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

# --- 3. LISTA DE ACTIVOS (Sin cambios) ---
ASSETS = ['EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'USDCAD=X', 'USDJPY=X', 'GC=F', 'BTC-USD', '^GSPC']

# --- 4. PESTAÑAS ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 ADN", "🎯 Ejecución Pro", "🎲 Montecarlo", "🛡️ Sentinel", "🌊 Vol-Monitor", "🏦 Banks Detector"])

with tab1:
    if st.button('📡 ESCANEO ADN'):
        results = []
        for t in ASSETS:
            d = analyze_asset(t)
            if d:
                status = "🚨 VENTA" if d['z'] > 1.6 else "🟢 COMPRA" if d['z'] < -1.6 else "⚪ NEUTRAL"
                results.append([t.replace('=X',''), d['price'], round(d['r2'],3), round(d['z'],2), round(d['hurst'],2), status])
        st.dataframe(pd.DataFrame(results, columns=['Activo', 'Precio', 'R2', 'Z-Diff', 'Hurst', 'Veredicto']), use_container_width=True)

# --- MODIFICACIÓN EN TAB 2: EJECUCIÓN PRO ---
with tab2:
    st.subheader("🎯 Niveles de Salida Dinámicos (Probabilidad de Distribución)")
    target_e = st.selectbox("Seleccionar Activo:", ASSETS, key="exec_s")
    de = analyze_asset(target_e)
    if de:
        p, v, z = de['price'], de['vol'], de['z']
        sl_dist = v * 1.5
        sl = p * (1 + sl_dist) if z > 0 else p * (1 - sl_dist)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 📅 Objetivos Diarios")
            # Sustitución de EMA 21 por TP Diario Basado en 1 Desviación Estándar
            tp_d = p * (1 - v if z > 0 else 1 + v)
            st.markdown(f'<div class="tp-card">TP Diario (1σ): {tp_d:.5f}<br><small>Prob. Alcance: 32%</small></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="sl-card">Stop Loss Estadístico: {sl:.5f}</div>', unsafe_allow_html=True)
            
        with c2:
            st.markdown("### 🗓️ Objetivos Semanales")
            v_w = v * np.sqrt(5)
            # TP Semanal 1 (1.2 Sigma)
            tp_w1 = p * (1 - v_w * 1.2 if z > 0 else 1 + v_w * 1.2)
            # TP Semanal 2 (2.0 Sigma - Extremo)
            tp_w2 = p * (1 - v_w * 2.0 if z > 0 else 1 + v_w * 2.0)
            
            st.markdown(f'<div class="tp-card">TP Semanal Prime (1.2σ): {tp_w1:.5f}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="tp-card" style="border-top-color:#ffd700">TP Semanal Extremo (2σ): {tp_w2:.5f}</div>', unsafe_allow_html=True)

# --- RESTO DE PESTAÑAS (INTACTAS) ---
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

with tab4:
    st.subheader("🛡️ Sentinel Macro: S&P 500 vs VIX")
    def get_safe_data(ticker):
        d = yf.download(ticker, period='20d', progress=False)['Close'].ffill()
        if isinstance(d, pd.DataFrame): d = d.iloc[:, 0]
        return d
    try:
        sp_df, vix_df, dxy_df = get_safe_data('^GSPC'), get_safe_data('^VIX'), get_safe_data('DX-Y.NYB')
        m1, m2, m3 = st.columns(3)
        sp_last, vix_last, dxy_last = sp_df.iloc[-1], vix_df.iloc[-1], dxy_df.iloc[-1]
        m1.metric("S&P 500", f"{sp_last:.2f}", f"{sp_df.pct_change().iloc[-1]*100:.2f}%")
        m2.metric("VIX Index", f"{vix_last:.2f}", f"{vix_last - vix_df.iloc[-2]:+.2f}")
        m3.metric("DXY Index", f"{dxy_last:.2f}")
        fig_sent = go.Figure()
        fig_sent.add_trace(go.Scatter(x=sp_df.index, y=sp_df, name="S&P 500", line=dict(color='#00ffcc', width=2), yaxis="y1"))
        fig_sent.add_trace(go.Scatter(x=vix_df.index, y=vix_df, name="VIX", line=dict(color='#ff4b4b', width=2, dash='dot'), yaxis="y2"))
        fig_sent.update_layout(template="plotly_dark", yaxis=dict(title="S&P 500", side="left", showgrid=False),
            yaxis2=dict(title="VIX", side="right", overlaying="y", showgrid=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), height=450)
        st.plotly_chart(fig_sent, use_container_width=True)
        score = 0
        if vix_last > 20: score += 1
        if dxy_last > 104.5: score += 1
        if sp_df.pct_change(5).iloc[-1] < -0.02: score += 1
        labels = ["ESTABLE", "PRECAUCIÓN", "RIESGO ALTO", "PÁNICO"]; colors = ["#00ffcc", "#ffd700", "#ff8c00", "#ff4b4b"]
        st.markdown(f'<div class="risk-banner" style="background-color:{colors[min(score, 3)]};">ESTADO MACRO: {labels[min(score, 3)]}</div>', unsafe_allow_html=True)
    except: st.error("Error en Sentinel.")

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
        st.write("**Global Yield Sp
