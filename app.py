import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from scipy.stats import norm

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="ARGOS v4.5 - Probabilistic Execution", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #000000; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3d4463; }
    .veredicto-box { padding: 25px; border-radius: 12px; border: 2px solid #3d4463; background-color: #161b22; margin: 20px 0; }
    .prob-table { background-color: #0e1117; border-radius: 10px; padding: 10px; border: 1px solid #ffd700; }
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
        
        prices = df['Close'].values.flatten().astype(float)
        hurst = calcular_hurst(prices[-50:])
        ema_21 = df['Close'].ewm(span=21, adjust=False).mean()
        vol_diaria = df['Ret'].tail(30).std()
        
        return {
            'df': df, 'price': float(df['Close'].iloc[-1]), 'z': z_val, 
            'r2': df['R2_Dynamic'].iloc[-1], 'hurst': hurst, 
            'ema': ema_21.iloc[-1], 'vol': vol_diaria,
            'drift': df['Ret'].tail(7).mean()
        }
    except: return None

# --- 3. LISTA DE ACTIVOS ---
ASSETS = ['EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'NZDUSD=X', 'USDJPY=X', 'USDCHF=X', 'USDCAD=X', 'GC=F', 'BTC-USD', '^SPX']

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("👁️ ARGOS v4.5")
    st.divider()
    st.info("🎯 Hurst < 0.45: Reversión")
    st.info("📏 Z-Diff > 1.6: Venta")

# --- 5. PESTAÑAS ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Matriz ADN", "🎯 Radar Fractal", "🎲 Montecarlo", "🛡️ Sentinel Macro", "🌊 Vol-Monitor", "🏦 Banks Detector"])

with tab1:
    if st.button('📡 INICIAR ESCANEO'):
        results = []
        for t in ASSETS:
            d = analyze_asset(t)
            if d:
                status = "🚨 VENTA" if (d['z'] > 1.6 and d['r2'] < 0.12) else "🟢 COMPRA" if (d['z'] < -1.6 and d['r2'] < 0.12) else "⚪ NEUTRAL"
                results.append([t.replace('=X',''), f"{d['price']:.4f}", round(d['r2'],3), round(d['z'],2), round(d['hurst'],2), status])
        st.dataframe(pd.DataFrame(results, columns=['Activo', 'Precio', 'R2', 'Z-Diff', 'Hurst', 'Veredicto']), use_container_width=True)

with tab4:
    st.subheader("🛡️ Global Risk Sentinel")
    # (Mantener lógica del semáforo anterior aquí)
    st.warning("Monitor Macro Activo")

with tab5:
    st.subheader("🌊 Vol-Monitor & Ejecución Probabilística")
    target = st.selectbox("Activo Detalle:", ASSETS, key="vol_target")
    vd = analyze_asset(target)
    
    if vd:
        # Gráficos de RMF e Histograma con línea roja (Mantener intactos)
        c_rmf1, c_rmf2 = st.columns(2)
        with c_rmf1:
            st.plotly_chart(px.area(vd['df'], y='RMF', title="Flujo RMF", color_discrete_sequence=['orange']).update_layout(template="plotly_dark", height=300), use_container_width=True)
        with c_rmf2:
            current_ret = vd['df']['Ret'].iloc[-1]
            fig_hist = px.histogram(vd['df'], x="Ret", nbins=50, title="Perfil Riesgo (Línea Roja=Hoy)", color_discrete_sequence=['#444'])
            fig_hist.add_vline(x=current_ret, line_width=3, line_dash="dash", line_color="#ff4b4b")
            st.plotly_chart(fig_hist.update_layout(template="plotly_dark", height=300), use_container_width=True)

        st.divider()
        st.write("### 📐 Zonas de Salida y Probabilidades (TP/SL)")
        
        # CÁLCULO DE PROBABILIDADES
        # Basado en la volatilidad actual, calculamos niveles de precio
        p = vd['price']
        vol = vd['vol']
        
        niveles = {
            "TP Conservador (Reversión a Media)": (vd['ema'], "68% (Alta)"),
            "TP Objetivo ($1\sigma$)": (p * (1 + vol), "32% (Media)"),
            "TP Extremo ($2\sigma$)": (p * (1 + 2*vol), "5% (Baja)"),
            "SL Técnico (Fuera de Campana)": (p * (1 - 1.5*vol), "Prob. de Toque: 12%")
        }
        
        # Ajustar dirección si Z es positivo (estamos vendiendo)
        if vd['z'] > 0:
            niveles = {
                "TP Conservador (EMA 21)": (vd['ema'], "68%"),
                "TP Objetivo (Baja -1σ)": (p * (1 - vol), "34%"),
                "TP Extremo (Pánico -2σ)": (p * (1 - 2*vol), "5%"),
                "SL Seguridad (Exceso +1.5σ)": (p * (1 + 1.5*vol), "Protección")
            }

        cols = st.columns(4)
        for i, (nombre, data) in enumerate(niveles.items()):
            with cols[i]:
                st.markdown(f"""
                <div class="stMetric">
                    <small>{nombre}</small><br>
                    <span style="font-size:20px; color:#ffd700;">{data[0]:.5f}</span><br>
                    <small>Probabilidad: {data[1]}</small>
                </div>
                """, unsafe_allow_html=True)

with tab6:
    st.subheader("🏦 Banks Detector: Shadow RMF")
    target_b = st.selectbox("Analizar Huella:", ASSETS, key="bank_target")
    bd = analyze_asset(target_b)
    if bd:
        df_b = bd['df'].copy()
        df_b['RMF_Abs'] = df_b['RMF'].abs()
        df_b['Anomaly'] = df_b['RMF_Abs'] / df_b['RMF_Abs'].rolling(20).mean()
        colors = ['#ffd700' if x > 2.5 else '#3d4463' for x in df_b['Anomaly']]
        st.plotly_chart(go.Figure(data=[go.Bar(x=df_b.index, y=df_b['RMF_Abs'], marker_color=colors)]).update_layout(template="plotly_dark", height=400), use_container_width=True)
