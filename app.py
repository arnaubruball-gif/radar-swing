import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as go
from datetime import datetime

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="JDetector - Institutional Edge", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #000000; }
    .metric-box { background-color: #0e1117; padding: 15px; border-radius: 8px; border: 1px solid #30363d; text-align: center; }
    .status-buy { color: #00ffcc; font-weight: bold; }
    .status-sell { color: #ff4b4b; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE CÁLCULO ---
@st.cache_data(ttl=600)
def analyze_asset(ticker):
    try:
        df = yf.download(ticker, period='200d', interval='1d', progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # ADN Lógica
        df['Ret'] = df['Close'].pct_change()
        df['Vol_Proxy'] = (df['High'] - df['Low']) * 100000
        df['RMF'] = df['Close'] * df['Vol_Proxy']
        df['RVOL'] = df['Vol_Proxy'] / df['Vol_Proxy'].rolling(20).mean()
        
        r2_series = []
        for i in range(len(df)):
            if i < 30: r2_series.append(0); continue
            subset = df.iloc[i-30:i].dropna()
            r2 = sm.OLS(subset['Ret'], sm.add_constant(subset['RMF'])).fit().rsquared
            r2_series.append(r2)
        df['R2_Dynamic'] = r2_series
        
        diff = df['Ret'].rolling(40).sum() - df['RMF'].pct_change().rolling(40).sum()
        df['Z-Diff'] = (diff - diff.rolling(40).mean()) / (diff.rolling(40).std() + 1e-10)
        
        # Indicadores para Vol-Monitor
        n_er = 10
        change = abs(df['Close'] - df['Close'].shift(n_er))
        volat = abs(df['Close'] - df['Close'].shift(1)).rolling(n_er).sum()
        df['ER'] = change / volat
        df['ROC'] = df['Close'].pct_change(10) * 100

        return df
    except: return None

# --- 3. LISTA DE ACTIVOS ---
ASSETS = ['EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'USDCAD=X', 'USDJPY=X', 'USDCHF=X', 'GC=F', 'BTC-USD', '^GSPC']

# --- 4. INTERFAZ ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📊 ADN", "🎯 Auditoría", "🎲 Montecarlo", "🛡️ Sentinel", 
    "🌊 Vol-Monitor", "🏦 Banks Detector", "🏛️ COT", "💰 RIESGO"
])

with tab1:
    st.subheader("📡 Radar de ADN Institucional")
    target = st.selectbox("Activo a Analizar:", ASSETS)
    df = analyze_asset(target)
    
    if df is not None:
        # Gráfica Z-Diff con límites
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Z-Diff'], name="Z-Diff ADN", line=dict(color='#00ffcc')))
        fig.add_hline(y=1.6, line_dash="dash", line_color="red", annotation_text="Venta")
        fig.add_hline(y=-1.6, line_dash="dash", line_color="green", annotation_text="Compra")
        fig.update_layout(title=f"Estructura ADN: {target}", template="plotly_dark", height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabla resumen rápida
        last_z = df['Z-Diff'].iloc[-1]
        status = "🚨 VENTA" if last_z > 1.6 else "🟢 COMPRA" if last_z < -1.6 else "⚪ Neutral"
        st.metric("Estado Actual", status, f"Z-Score: {last_z:.2f}")

with tab2:
    st.subheader("🎯 Auditoría Histórica (Últimos 5 días)")
    if df is not None:
        audit = df.tail(5).copy()
        audit['Veredicto'] = audit['Z-Diff'].apply(lambda x: "🟢 COMPRA" if x < -1.6 else ("🚨 VENTA" if x > 1.6 else "⚪ Neutral"))
        st.table(audit[['Close', 'Z-Diff', 'Veredicto']].style.format({'Close': '{:.5f}', 'Z-Diff': '{:.2f}'}))

with tab3:
    st.subheader("🎲 Simulación Montecarlo (Proyección 30d)")
    if df is not None:
        returns = df['Ret'].dropna()
        last_price = df['Close'].iloc[-1]
        simulations = []
        for _ in range(50):
            sim_rets = np.random.choice(returns, size=30)
            sim_prices = last_price * (1 + sim_rets).cumsum()
            simulations.append(sim_prices)
        
        fig_m = go.Figure()
        for s in simulations:
            fig_m.add_trace(go.Scatter(y=s, mode='lines', line=dict(width=1), opacity=0.3, showlegend=False))
        fig_m.update_layout(template="plotly_dark", title="Caminos Aleatorios")
        st.plotly_chart(fig_m, use_container_width=True)

with tab4:
    st.subheader("🛡️ Sentinel: Radar de Fuerza Relativa")
    sentinel_data = []
    for t in ASSETS:
        d = analyze_asset(t)
        if d is not None:
            sentinel_data.append({'Ticker': t, 'R2': d['R2_Dynamic'].iloc[-1], 'Z': d['Z-Diff'].iloc[-1]})
    st.dataframe(pd.DataFrame(sentinel_data), use_container_width=True)

with tab5:
    st.subheader("🌊 Vol-Monitor Pro")
    if df is not None:
        c1, c2, c3 = st.columns(3)
        c1.metric("RVOL (Interés)", f"{df['RVOL'].iloc[-1]:.2f}x")
        c2.metric("Eficiencia (ER)", f"{df['ER'].iloc[-1]:.2f}")
        c3.metric("Momentum (ROC)", f"{df['ROC'].iloc[-1]:+.2f}%")

with tab6:
    st.subheader("🏦 Banks Detector: Huella de Volumen")
    if df is not None:
        df['Spread'] = (df['High'] - df['Low'])
        df['VSA'] = df['Vol_Proxy'] / (df['Spread'] + 1e-10)
        fig_v = px.bar(df.tail(20), y='VSA', title="Esfuerzo vs Resultado (Institucional)")
        st.plotly_chart(fig_v, use_container_width=True)

with tab7:
    st.subheader("🏛️ COT Insight (Simulado)")
    st.warning("Los datos COT reales requieren API premium. Mostrando estimación de sentimiento basada en ADN.")
    cot_val = np.clip((df['Z-Diff'].iloc[-1] * -1) * 10, -100, 100) if df is not None else 0
    st.progress((cot_val + 100) / 200)
    st.write(f"Sentimiento Neto Estructural: {cot_val:.2f}%")

with tab8:
    st.subheader("💰 Gestión de Riesgo Profesional")
    cap = st.number_input("Capital ($)", value=1000)
    risk = st.slider("Riesgo (%)", 0.5, 2.0, 1.0)
    if df is not None:
        vol_diaria = df['Ret'].tail(30).std()
        dist_sl = df['Close'].iloc[-1] * (vol_diaria * 2.5)
        riesgo_usd = cap * (risk/100)
        lotaje = riesgo_usd / (dist_sl * 100000) if "USD" in target else riesgo_usd / dist_sl
        st.success(f"Lotaje sugerido: {lotaje:.3f} Lotes")
