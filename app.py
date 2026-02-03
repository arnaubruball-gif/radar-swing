import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# --- 1. CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="ARGOS - Terminal de Arbitraje Estadístico", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3d4463; }
    .veredicto-box { padding: 25px; border-radius: 12px; border: 2px solid #3d4463; background-color: #161b22; margin: 20px 0; }
    .alerta-ultra { padding: 10px; background-color: #ff4b4b; color: white; border-radius: 5px; text-align: center; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE CÁLCULO (QUANTS CORE) ---
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
        
        # Cálculo de Retornos y Flujo (RMF)
        df['Ret'] = df['Close'].pct_change()
        df['Vol_Proxy'] = (df['High'] - df['Low']) * 100000
        df['RMF'] = df['Close'] * df['Vol_Proxy']
        
        # R-Cuadrado Dinámico
        r2_series = []
        for i in range(len(df)):
            if i < 30: r2_series.append(0); continue
            subset = df.iloc[i-30:i].dropna()
            r2 = sm.OLS(subset['Ret'], sm.add_constant(subset['RMF'])).fit().rsquared
            r2_series.append(r2)
        df['R2_Dynamic'] = r2_series
        
        # Z-Diff (Tensión)
        diff = df['Ret'].rolling(40).sum() - df['RMF'].pct_change().rolling(40).sum()
        z_val = ((diff - diff.rolling(40).mean()) / (diff.rolling(40).std() + 1e-10)).iloc[-1]
        
        # Hurst y EMA
        prices = df['Close'].values.flatten().astype(float)
        hurst = calcular_hurst(prices[-50:])
        ema_21 = df['Close'].ewm(span=21, adjust=False).mean()
        
        return {
            'df': df, 'price': float(df['Close'].iloc[-1]), 'z': z_val, 
            'r2': df['R2_Dynamic'].iloc[-1], 'hurst': hurst, 
            'ema': ema_21.iloc[-1], 'vol': df['Ret'].tail(30).std(),
            'drift': df['Ret'].tail(7).mean()
        }
    except: return None

@st.cache_data(ttl=3600)
def fetch_risk_metrics():
    tickers = {'VIX': '^VIX', 'GOLD': 'GC=F'}
    risk_data = {}
    for name, t in tickers.items():
        df = yf.download(t, period='60d', interval='1d', progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        risk_data[name] = df
    vix_val = float(risk_data['VIX']['Close'].iloc[-1])
    score = 50 if vix_val > 20 else 10
    return vix_val, score, risk_data['VIX']

# --- 3. LISTA DE ACTIVOS ---
ASSETS = [
    'EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'NZDUSD=X', 'USDJPY=X', 'USDCHF=X', 'USDCAD=X',
    'USDMXN=X', 'USDZAR=X', 'EURGBP=X', 'EURJPY=X', 'GBPJPY=X', 'EURAUD=X', 'GBPAUD=X',
    'GC=F', 'SI=F', 'BTC-USD', 'ETH-USD', '^SPX', '^IXIC'
]

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("👁️ ARGOS v3.0")
    st.caption(f"Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st.divider()
    st.info("🎯 Hurst < 0.45: Reversión")
    st.info("📏 Z-Diff > 1.6: Venta")
    st.info("☁️ R2 < 0.12: Ruido")

# --- 5. PESTAÑAS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Matriz ADN", "🎯 Radar", "🎲 Montecarlo", "🛡️ Sentinel", "🌊 Vol-Monitor"])

with tab1:
    if st.button('📡 ESCANEAR MERCADO'):
        results = []
        pbar = st.progress(0)
        for i, t in enumerate(ASSETS):
            d = analyze_asset(t)
            if d:
                status = "⚪ NEUTRAL"
                if d['r2'] < 0.12:
                    if d['z'] > 1.6: status = "🚨 VENTA"
                    elif d['z'] < -1.6: status = "🟢 COMPRA"
                results.append([t.replace('=X',''), f"{d['price']:.4f}", round(d['r2'],3), round(d['z'],2), round(d['hurst'],2), status])
            pbar.progress((i + 1) / len(ASSETS))
        st.dataframe(pd.DataFrame(results, columns=['Activo', 'Precio', 'R2', 'Z-Diff', 'Hurst', 'Veredicto']), use_container_width=True)

with tab3:
    tk_mc = st.selectbox("Activo Montecarlo:", ASSETS)
    d_mc = analyze_asset(tk_mc)
    if d_mc:
        days = 15
        sims = np.zeros((days + 1, 100))
        sims[0] = d_mc['price']
        for i in range(1, days + 1):
            sims[i] = sims[i-1] * (1 + np.random.normal(d_mc['drift'], d_mc['vol'], 100))
        
        fig_mc = go.Figure()
        x_axis = list(range(days + 1))
        fig_mc.add_trace(go.Scatter(x=x_axis + x_axis[::-1], y=list(np.percentile(sims, 90, axis=1)) + list(np.percentile(sims, 10, axis=1)[::-1]), fill='toself', fillcolor='rgba(0, 255, 204, 0.1)', line=dict(color='rgba(0,0,0,0)'), name='Confianza'))
        fig_mc.add_trace(go.Scatter(x=x_axis, y=np.percentile(sims, 50, axis=1), line=dict(color='#00ffcc', width=3), name='Trayectoria'))
        st.plotly_chart(fig_mc, use_container_width=True)

with tab5:
    target = st.selectbox("Análisis Detallado:", ASSETS)
    vd = analyze_asset(target)
    if vd:
        dist_pips = (vd['price'] - vd['ema']) * 10000
        st.markdown('<div class="veredicto-box">', unsafe_allow_html=True)
        st.write(f"### Veredicto: {target}")
        if abs(vd['z']) > 1.6 and vd['hurst'] < 0.45:
            st.error(f"⚠️ SEÑAL ACTIVA: {'VENTA' if vd['z'] > 0 else 'COMPRA'}")
            if abs(dist_pips) < 15: st.markdown('<div class="alerta-ultra">🎯 RECHAZO EN EMA 21</div>', unsafe_allow_html=True)
        else: st.info("Condición Neutral")
        st.write(f"Distancia a la Media: {dist_pips:.1f} pips")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Gráfico Volatilidad
        df_v = vd['df'].copy()
        df_v['Vol_M'] = df_v['Ret'].rolling(20).std()
        df_v['Up_V'] = df_v['Vol_M'].rolling(20).mean() + (df_v['Vol_M'].rolling(20).std() * 2)
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Scatter(x=df_v.index, y=df_v['Vol_M'], name="Vol", line=dict(color='#00ffcc')))
        fig_vol.add_trace(go.Scatter(x=df_v.index, y=df_v['Up_V'], name="Pánico", line=dict(dash='dash', color='red')))
        st.plotly_chart(fig_vol.update_layout(template="plotly_dark"), use_container_width=True)
