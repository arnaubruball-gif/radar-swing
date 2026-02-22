import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="JDetector - Institutional Edge", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #000000; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3d4463; }
    .tp-card { background-color: #161b22; padding: 20px; border-radius: 10px; border-top: 4px solid #00ffcc; text-align: center; margin-bottom:10px; }
    .sl-card { background-color: #161b22; padding: 20px; border-radius: 10px; border-top: 4px solid #ff4b4b; text-align: center; }
    .metric-box { background-color: #0e1117; padding: 15px; border-radius: 8px; border: 1px solid #30363d; text-align: center; }
    .cot-card { background-color: #1c1c1c; padding: 15px; border-radius: 10px; border: 1px solid #ffd700; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE CÁLCULO ---
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
        
        # Cálculos Base
        df['Ret'] = df['Close'].pct_change()
        df['Vol_Proxy'] = (df['High'] - df['Low']) * 100000
        df['RMF'] = df['Close'] * df['Vol_Proxy']
        df['RVOL'] = df['Vol_Proxy'] / df['Vol_Proxy'].rolling(20).mean()
        
        # ADN Lógica
        r2_series = []
        for i in range(len(df)):
            if i < 30: 
                r2_series.append(0)
                continue
            subset = df.iloc[i-30:i].dropna()
            r2 = sm.OLS(subset['Ret'], sm.add_constant(subset['RMF'])).fit().rsquared
            r2_series.append(r2)
        df['R2_Dynamic'] = r2_series
        
        diff = df['Ret'].rolling(40).sum() - df['RMF'].pct_change().rolling(40).sum()
        z_val = ((diff - diff.rolling(40).mean()) / (diff.rolling(40).std() + 1e-10)).iloc[-1]
        
        # Eficiencia (ER) y ADX
        n_er = 10
        change = abs(df['Close'] - df['Close'].shift(n_er))
        volatility = abs(df['Close'] - df['Close'].shift(1)).rolling(n_er).sum()
        df['ER'] = change / volatility
        
        # ADX Básico
        plus_dm = df['High'].diff()
        minus_dm = df['Low'].diff()
        tr = pd.concat([df['High']-df['Low'], abs(df['High']-df['Close'].shift(1)), abs(df['Low']-df['Close'].shift(1))], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        df['ADX'] = (abs(plus_dm.rolling(14).mean() - minus_dm.rolling(14).mean()) / (plus_dm.rolling(14).mean() + minus_dm.rolling(14).mean()) * 100).rolling(14).mean()
        df['ROC'] = df['Close'].pct_change(10) * 100

        return {
            'df': df, 'price': float(df['Close'].iloc[-1]), 'z': z_val, 
            'r2': df['R2_Dynamic'].iloc[-1], 'vol': df['Ret'].tail(30).std(), 
            'rvol': df['RVOL'].iloc[-1], 'er': df['ER'].iloc[-1],
            'adx': df['ADX'].iloc[-1], 'roc': df['ROC'].iloc[-1]
        }
    except Exception as e:
        return None

# --- 3. LISTA DE ACTIVOS ---
ASSETS = ['EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'USDCAD=X', 'USDJPY=X', 'USDCHF=X', 'GC=F', 'BTC-USD', '^GSPC']

# --- 4. PESTAÑAS ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📊 ADN", "🎯 Auditoría Señal", "🎲 Montecarlo", "🛡️ Sentinel", 
    "🌊 Vol-Monitor Pro", "🏦 Banks Detector", "🏛️ COT Insight", "💰 GESTIÓN RIESGO"
])

with tab1:
    st.subheader("📡 Escaneo ADN")
    if st.button('🚀 EJECUTAR ESCANEO'):
        results = []
        for t in ASSETS:
            d = analyze_asset(t)
            if d:
                status = "🚨 VENTA" if d['z'] > 1.6 else "🟢 COMPRA" if d['z'] < -1.6 else "⚪ NEUTRAL"
                results.append([t.replace('=X',''), f"{d['price']:.5f}", round(d['r2'],3), round(d['z'],2), status])
        st.dataframe(pd.DataFrame(results, columns=['Activo', 'Precio', 'R2', 'Z-Diff', 'Veredicto']), use_container_width=True)

with tab2:
    st.subheader("🎯 Auditoría de los Últimos 5 Días")
    t_audit = st.selectbox("Activo:", ASSETS, key="aud_s")
    da = analyze_asset(t_audit)
    if da:
        hist = da['df'].tail(5).copy()
        st.table(hist[['Close', 'RVOL', 'ER']].style.format("{:.5f}"))

with tab5:
    st.subheader("🌊 Vol-Monitor Pro: Confluencia")
    t_vol = st.selectbox("Activo:", ASSETS, key="vol_s")
    dv = analyze_asset(t_vol)
    if dv:
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="metric-box"><b>RVOL</b><br><h2>{dv["rvol"]:.2f}x</h2></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-box"><b>ER</b><br><h2>{dv["er"]:.2f}</h2></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-box"><b>ADX</b><br><h2>{dv["adx"]:.1f}</h2></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-box"><b>ROC</b><br><h2>{dv["roc"]:+.2f}%</h2></div>', unsafe_allow_html=True)
        
        score = sum([dv['rvol'] > 1.5, dv['er'] > 0.55, dv['adx'] > 25, abs(dv['roc']) > 0.5])
        st.markdown(f"### Veredicto: {'🚀 ALTA CALIDAD' if score >= 3 else '⚠️ MEDIA' if score == 2 else '🚫 RUIDO'}")

with tab8:
    st.subheader("💰 Gestión de Riesgo Corregida")
    cap = st.number_input("Capital ($):", value=1000)
    risk = st.slider("Riesgo %:", 0.5, 2.0, 1.0)
    t_risk = st.selectbox("Activo:", ASSETS, key="risk_s")
    dr = analyze_asset(t_risk)
    if dr:
        usd_risk = cap * (risk/100)
        sl_points = dr['price'] * (dr['vol'] * 2.5)
        if "USD" in t_risk and "BTC" not in t_risk:
            lots = usd_risk / (sl_points * 100000)
        else:
            lots = usd_risk / sl_points
        st.metric("Lotaje Sugerido", f"{lots:.3f} Lotes")
