import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ARGOS v5.7 - Institutional Suite", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #000000; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3d4463; }
    .tp-card { background-color: #161b22; padding: 20px; border-radius: 10px; border-top: 4px solid #00ffcc; text-align: center; margin-bottom:10px; }
    .sl-card { background-color: #161b22; padding: 20px; border-radius: 10px; border-top: 4px solid #ff4b4b; text-align: center; }
    .risk-alert { padding: 15px; border-radius: 10px; text-align: center; font-weight: bold; margin-bottom: 10px; color: black; }
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
        df = df[['Close', 'Open', 'High', 'Low']].copy()
        df['Ret'] = df['Close'].pct_change()
        df['Vol_Proxy'] = (df['High'] - df['Low']) * 100000
        df['RMF'] = df['Close'] * df['Vol_Proxy']
        
        diff = df['Ret'].rolling(40).sum() - df['RMF'].pct_change().rolling(40).sum()
        z_val = ((diff - diff.rolling(40).mean()) / (diff.rolling(40).std() + 1e-10)).iloc[-1]
        hurst = calcular_hurst(df['Close'].tail(50).values.flatten())
        ema_21 = df['Close'].ewm(span=21, adjust=False).mean().iloc[-1]
        
        return {'df': df, 'price': float(df['Close'].iloc[-1]), 'z': z_val, 'hurst': hurst, 'ema': float(ema_21), 'vol': df['Ret'].tail(30).std()}
    except Exception as e:
        return None

# --- LISTA DE ACTIVOS ---
ASSETS = ['EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'USDJPY=X', 'USDCAD=X', 'GC=F', 'BTC-USD', '^GSPC']

# --- PESTAÑAS ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 ADN", "🎯 Ejecución Pro", "🎲 Montecarlo", "🛡️ Sentinel", "🌊 Vol-Monitor", "🏦 Banks Detector"])

with tab1:
    if st.button('📡 ESCANEO'):
        results = []
        for t in ASSETS:
            d = analyze_asset(t)
            if d:
                status = "🚨 VENTA" if d['z'] > 1.6 else "🟢 COMPRA" if d['z'] < -1.6 else "⚪ NEUTRAL"
                results.append([t.replace('=X',''), d['price'], round(d['z'],2), round(d['hurst'],2), status])
        st.dataframe(pd.DataFrame(results, columns=['Activo', 'Precio', 'Z', 'H', 'Status']), use_container_width=True)

with tab4:
    st.subheader("🛡️ Sentinel Macro: Vigilancia S&P 500 y Miedo")
    try:
        # Descarga múltiple para Sentinel
        sent_df = yf.download(['^GSPC', '^VIX', 'DX-Y.NYB'], period='30d', progress=False)
        if isinstance(sent_df.columns, pd.MultiIndex):
            closes = sent_df['Close']
        else:
            closes = sent_df
            
        sp_val = float(closes['^GSPC'].iloc[-1])
        vix_val = float(closes['^VIX'].iloc[-1])
        dxy_val = float(closes['DX-Y.NYB'].iloc[-1])
        
        c1, c2, c3 = st.columns(3)
        c1.metric("S&P 500 Index", f"{sp_val:.2f}", f"{closes['^GSPC'].pct_change().iloc[-1]*100:.2f}%")
        c2.metric("VIX (Miedo)", f"{vix_val:.2f}")
        c3.metric("DXY (Dólar)", f"{dxy_val:.2f}")
        
        # Gráfico Sentinel SP500 vs VIX
        fig_s = go.Figure()
        fig_s.add_trace(go.Scatter(x=closes.index, y=closes['^GSPC'], name="S&P 500", yaxis="y1", line=dict(color="#00ffcc")))
        fig_s.add_trace(go.Scatter(x=closes.index, y=closes['^VIX'], name="VIX", yaxis="y2", line=dict(color="red", dash="dot")))
        fig_s.update_layout(
            template="plotly_dark",
            yaxis=dict(title="S&P 500"),
            yaxis2=dict(title="VIX", overlaying="y", side="right"),
            height=350,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_s, use_container_width=True)
        
        # Semáforo
        score = 0
        if vix_val > 22: score += 1
        if dxy_val > 104.5: score += 1
        if closes['^GSPC'].pct_change(5).iloc[-1] < -0.02: score += 1
        
        labels = ["ESTABLE", "PRECAUCIÓN", "RIESGO ALTO", "PÁNICO MACRO"]
        clrs = ["#00ffcc", "#ffd700", "#ff8c00", "#ff4b4b"]
        st.markdown(f'<div class="risk-alert" style="background-color:{clrs[score]};">SENTIMIENTO GLOBAL: {labels[score]}</div>', unsafe_allow_html=True)
    except:
        st.error("Error en Sentinel: Datos no disponibles temporalmente.")

with tab5:
    st.subheader("🌊 Volatilidad y Perfil de Retornos")
    target_v = st.selectbox("Analizar Activo:", ASSETS, key="v_box")
    vd = analyze_asset(target_v)
    
    if vd:
        df_v = vd['df'].dropna()
        col_v1, col_v2 = st.columns(2)
        
        with col_v1:
            # Flujo RMF acumulado para ver la presión
            st.write("**Presión de Flujo (RMF)**")
            fig_rmf = px.area(df_v, y='RMF', color_discrete_sequence=['orange'])
            fig_rmf.update_layout(template="plotly_dark", height=300, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_rmf, use_container_width=True)
            
        with col_v2:
            # Perfil de riesgo con línea roja de hoy
            st.write("**Distribución de Retornos (Riesgo)**")
            fig_h = px.histogram(df_v, x="Ret", nbins=50, color_discrete_sequence=['#444'])
            fig_h.add_vline(x=df_v['Ret'].iloc[-1], line_color="red", line_width=4, line_dash="dash")
            fig_h.update_layout(template="plotly_dark", height=300, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_h, use_container_width=True)
            
        st.info(f"La línea roja muestra dónde se sitúa el movimiento de hoy respecto a los últimos 150 días en {target_v}.")

with tab6:
    st.subheader("🏦 Banks Detector")
    target_b = st.selectbox("Huella Institucional:", ASSETS, key="b_box")
    bd = analyze_asset(target_b)
    if bd:
        df_b = bd['df'].copy()
        df_b['Anomaly'] = bd['df']['RMF'].abs() / bd['df']['RMF'].abs().rolling(20).mean()
        clrs = ['#ffd700' if x > 2.5 else '#3d4463' for x in df_b['Anomaly']]
        st.plotly_chart(go.Figure(data=[go.Bar(x=df_b.index, y=bd['df']['RMF'].abs(), marker_color=clrs)]).update_layout(template="plotly_dark", title="Shadow RMF"), use_container_width=True)
