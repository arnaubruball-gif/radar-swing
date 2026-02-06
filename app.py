import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ARGOS v5.0 - Professional Terminal", layout="wide")

# Estilos CSS
st.markdown("""
    <style>
    .main { background-color: #000000; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3d4463; }
    .veredicto-box { padding: 25px; border-radius: 12px; border: 2px solid #3d4463; background-color: #161b22; margin: 20px 0; }
    .risk-alert { padding: 15px; border-radius: 10px; text-align: center; font-weight: bold; font-size: 1.2rem; margin-bottom: 10px; }
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
        
        # Z-Diff y Hurst
        diff = df['Ret'].rolling(40).sum() - df['RMF'].pct_change().rolling(40).sum()
        z_val = ((diff - diff.rolling(40).mean()) / (diff.rolling(40).std() + 1e-10)).iloc[-1]
        hurst = calcular_hurst(df['Close'].tail(50).values.flatten())
        ema_21 = df['Close'].ewm(span=21, adjust=False).mean().iloc[-1]
        
        return {'df': df, 'price': float(df['Close'].iloc[-1]), 'z': z_val, 'hurst': hurst, 'ema': ema_21, 'vol': df['Ret'].tail(30).std()}
    except: return None

# --- LISTA DE ACTIVOS ---
ASSETS = ['EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'USDJPY=X', 'USDCAD=X', 'GC=F', 'BTC-USD', '^GSPC', 'HG=F']

# --- PESTAÑAS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Matriz ADN", "🎲 Montecarlo Pro", "🛡️ Sentinel Macro", "🌊 Vol-Monitor", "🏦 Banks Detector"])

with tab1:
    if st.button('📡 ESCANEO TOTAL'):
        results = []
        for t in ASSETS:
            d = analyze_asset(t)
            if d:
                status = "🚨 VENTA" if d['z'] > 1.6 else "🟢 COMPRA" if d['z'] < -1.6 else "⚪ NEUTRAL"
                results.append([t.replace('=X',''), d['price'], round(d['z'],2), round(d['hurst'],2), status])
        st.dataframe(pd.DataFrame(results, columns=['Activo', 'Precio', 'Z-Diff', 'Hurst', 'Veredicto']), use_container_width=True)

with tab2:
    st.subheader("🎲 Simulación Montecarlo (Análisis de Probabilidad)")
    tk_mc = st.selectbox("Seleccionar Activo:", ASSETS, key="mc_box")
    d_mc = analyze_asset(tk_mc)
    
    if d_mc:
        # 1,000 simulaciones a 15 días
        dias = 15
        sims = 1000
        returns = np.random.normal(d_mc['df']['Ret'].mean(), d_mc['vol'], (sims, dias))
        price_paths = d_mc['price'] * (1 + returns).cumprod(axis=1)
        
        fig_mc = go.Figure()
        for i in range(15): # Dibujamos solo 15 caminos para no saturar
            fig_mc.add_trace(go.Scatter(y=price_paths[i], line=dict(width=1), opacity=0.3, showlegend=False))
        
        # Mediana y Conos
        mediana = np.median(price_paths, axis=0)
        p95 = np.percentile(price_paths, 95, axis=0)
        p5 = np.percentile(price_paths, 5, axis=0)
        
        fig_mc.add_trace(go.Scatter(y=mediana, line=dict(color='#00ffcc', width=4), name="Mediana"))
        fig_mc.add_trace(go.Scatter(y=p95, line=dict(color='gray', dash='dash'), name="95% Prob"))
        fig_mc.add_trace(go.Scatter(y=p5, line=dict(color='gray', dash='dash'), name="5% Prob"))
        
        st.plotly_chart(fig_mc.update_layout(template="plotly_dark", title=f"Proyección 15 días: {tk_mc}"), use_container_width=True)
        
        # Análisis profundo
        final_prices = price_paths[:, -1]
        prob_subir = (final_prices > d_mc['price']).sum() / sims * 100
        var_95 = (d_mc['price'] - np.percentile(final_prices, 5)) 
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Prob. Alcista", f"{prob_subir:.1f}%")
        c2.metric("VaR 95% (Riesgo Máx)", f"{var_95:.4f}")
        c3.metric("Objetivo Mediano", f"{mediana[-1]:.4f}")

with tab3:
    st.subheader("🛡️ Sentinel Macro: Vigilancia de Riesgo")
    # Tickers: VIX, DXY, Oro, Cobre (HG=F)
    sentinel_data = {}
    for n, t in zip(['VIX', 'DXY', 'ORO', 'COBRE'], ['^VIX', 'DX-Y.NYB', 'GC=F', 'HG=F']):
        df_s = yf.download(t, period='5d', progress=False)
        if isinstance(df_s.columns, pd.MultiIndex): df_s.columns = df_s.columns.get_level_values(0)
        sentinel_data[n] = df_s['Close'].iloc[-1]
    
    ratio_gc = sentinel_data['ORO'] / sentinel_data['COBRE']
    
    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("VIX (Miedo)", f"{sentinel_data['VIX']:.2f}")
    col_s2.metric("DXY (Dólar)", f"{sentinel_data['DXY']:.2f}")
    col_s3.metric("Ratio Oro/Cobre", f"{ratio_gc:.2f}")
    
    # Semáforo
    risk_score = 0
    if sentinel_data['VIX'] > 20: risk_score += 1
    if ratio_gc > 500: risk_score += 1
    if sentinel_data['DXY'] > 104: risk_score += 1
    
    labels = ["RISK-ON (Bajo)", "MODERADO", "PRECAUCIÓN", "RISK-OFF (Peligro)"]
    clrs = ["#00ffcc", "#ffd700", "#ff8c00", "#ff4b4b"]
    st.markdown(f'<div class="risk-alert" style="background-color:{clrs[risk_score]}; color:black;">ESTADO DEL MERCADO: {labels[risk_score]}</div>', unsafe_allow_html=True)

with tab4:
    # Vol-Monitor intacto con histograma y línea roja
    target_v = st.selectbox("Activo Detalle:", ASSETS, key="vol_target")
    vd = analyze_asset(target_v)
    if vd:
        c_v1, c_v2 = st.columns(2)
        with c_v1: st.plotly_chart(px.area(vd['df'], y='RMF', title="Flujo RMF").update_layout(template="plotly_dark", height=300), use_container_width=True)
        with c_v2:
            fig_h = px.histogram(vd['df'], x="Ret", nbins=50, title="Perfil de Riesgo (Hoy = Roja)")
            fig_h.add_vline(x=vd['df']['Ret'].iloc[-1], line_color="red", line_width=3)
            st.plotly_chart(fig_h.update_layout(template="plotly_dark", height=300), use_container_width=True)

with tab5:
    # Banks Detector intacto
    target_b = st.selectbox("Huella Institucional:", ASSETS, key="bank_target")
    bd = analyze_asset(target_b)
    if bd:
        df_b = bd['df'].copy()
        df_b['Anomaly'] = bd['df']['RMF'].abs() / bd['df']['RMF'].abs().rolling(20).mean()
        colors = ['#ffd700' if x > 2.5 else '#3d4463' for x in df_b['Anomaly']]
        st.plotly_chart(go.Figure(data=[go.Bar(x=df_b.index, y=bd['df']['RMF'].abs(), marker_color=colors)]).update_layout(template="plotly_dark", title="Shadow RMF"), use_container_width=True)
