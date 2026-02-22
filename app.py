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
        
        # Básicos
        df['Ret'] = df['Close'].pct_change()
        df['Vol_Proxy'] = (df['High'] - df['Low']) * 100000
        df['RMF'] = df['Close'] * df['Vol_Proxy']
        df['RVOL'] = df['Vol_Proxy'] / df['Vol_Proxy'].rolling(20).mean()
        
        # ADN Lógica Original
        r2_series = []
        for i in range(len(df)):
            if i < 30: r2_series.append(0); continue
            subset = df.iloc[i-30:i].dropna()
            r2 = sm.OLS(subset['Ret'], sm.add_constant(subset['RMF'])).fit().rsquared
            r2_series.append(r2)
        df['R2_Dynamic'] = r2_series
        
        diff = df['Ret'].rolling(40).sum() - df['RMF'].pct_change().rolling(40).sum()
        z_series = (diff - diff.rolling(40).mean()) / (diff.rolling(40).std() + 1e-10)
        df['Z-Diff'] = z_series
        
        # Kaufman Efficiency Ratio (ER)
        n_er = 10
        change = abs(df['Close'] - df['Close'].shift(n_er))
        volatility = abs(df['Close'] - df['Close'].shift(1)).rolling(n_er).sum()
        df['ER'] = change / volatility
        
        # Momentum e Indicadores de Fuerza
        df['ROC'] = ((df['Close'] - df['Close'].shift(10)) / df['Close'].shift(10)) * 100
        
        # ADX
        plus_dm = df['High'].diff()
        minus_dm = df['Low'].diff()
        tr = pd.concat([df['High']-df['Low'], abs(df['High']-df['Close'].shift(1)), abs(df['Low']-df['Close'].shift(1))], axis=1).max(axis=1)
        atr_14 = tr.rolling(14).mean()
        plus_di = 100 * (plus_dm.rolling(14).mean() / (atr_14 + 1e-10))
        minus_di = 100 * (minus_dm.rolling(14).mean() / (atr_14 + 1e-10))
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        df['ADX'] = dx.rolling(14).mean()
        
        return {
            'df': df, 'price': float(df['Close'].iloc[-1]), 'z': z_series.iloc[-1], 
            'r2': df['R2_Dynamic'].iloc[-1], 'vol': df['Ret'].tail(30).std(), 
            'rvol': df['RVOL'].iloc[-1], 'er': df['ER'].iloc[-1],
            'adx': df['ADX'].iloc[-1], 'roc': df['ROC'].iloc[-1]
        }
    except Exception as e:
        st.error(f"Error analizando {ticker}: {e}")
        return None

# --- 3. LISTA DE ACTIVOS ---
ASSETS = ['EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'USDCAD=X', 'USDJPY=X', 'USDCHF=X', 'GC=F', 'BTC-USD', '^GSPC']

# --- 4. PESTAÑAS ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📊 ADN", "🎯 Auditoría Señal", "🎲 Montecarlo", "🛡️ Sentinel", 
    "🌊 Vol-Monitor Pro", "🏦 Banks Detector", "🏛️ COT Insight", "💰 GESTIÓN RIESGO"
])

with tab1:
    if st.button('📡 ESCANEO ADN ESTRUCTURAL'):
        results = []
        for t in ASSETS:
            d = analyze_asset(t)
            if d:
                status = "🚨 VENTA" if d['z'] > 1.6 else "🟢 COMPRA" if d['z'] < -1.6 else "⚪ NEUTRAL"
                results.append([t.replace('=X',''), d['price'], round(d['r2'],3), round(d['z'],2), status])
        st.dataframe(pd.DataFrame(results, columns=['Activo', 'Precio', 'R2', 'Z-Diff', 'Veredicto']), use_container_width=True)

with tab2:
    st.subheader("🎯 Auditoría de los Últimos 5 Días")
    target_e = st.selectbox("Seleccionar Activo para Historial:", ASSETS, key="exec_s")
    de = analyze_asset(target_e)
    if de:
        df_h = de['df'].tail(5).copy()
        df_h['ADN_Signal'] = df_h['Z-Diff'].apply(lambda x: "🟢 COMPRA" if x < -1.6 else ("🚨 VENTA" if x > 1.6 else "⚪ Neutral"))
        
        # Recuperamos el formato de tabla limpia que querías
        audit_df = df_h[['Close', 'Z-Diff', 'ADN_Signal']].copy()
        audit_df.index = audit_df.index.strftime('%Y-%m-%d')
        
        st.write(f"### Historial Reciente para {target_e}")
        st.table(audit_df.style.format({'Close': '{:.5f}', 'Z-Diff': '{:.2f}'}))
        
        st.info("💡 **Tip:** Busca persistencia. Si el Z-Diff lleva 3 días en verde/rojo, la señal es mucho más fiable.")

with tab5:
    st.subheader("🌊 Vol-Monitor Pro: Confluencia de Fuerza")
    target_v = st.selectbox("Activo Detalle Fuerza:", ASSETS, key="v_s")
    dv = analyze_asset(target_v)
    if dv:
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(f'<div class="metric-box"><b>RVOL (Interés)</b><br><h2>{dv["rvol"]:.2f}x</h2></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="metric-box"><b>Eficiencia (ER)</b><br><h2>{dv["er"]:.2f}</h2></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="metric-box"><b>Fuerza (ADX)</b><br><h2>{dv["adx"]:.1f}</h2></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="metric-box"><b>Velocidad (ROC)</b><br><h2>{dv["roc"]:+.2f}%</h2></div>', unsafe_allow_html=True)

        score = sum([dv['rvol'] > 1.5, dv['er'] > 0.55, dv['adx'] > 25, abs(dv['roc']) > 0.5])
        
        if score >= 3:
            v_color, v_text = "#00ffcc", "🚀 ALTA CALIDAD: Movimiento Institucional"
        elif score == 2:
            v_color, v_text = "#ffd700", "⚠️ CALIDAD MEDIA: Fuerza en desarrollo"
        else:
            v_color, v_text = "#ff4b4b", "🚫 RUIDO: Evitar operativa estructural"

        st.markdown(f'<div style="background-color:{v_color}; padding:20px; border-radius:10px; color:black; text-align:center; font-weight:bold; font-size:1.2rem;">{v_text}</div>', unsafe_allow_html=True)

with tab8:
    st.subheader("💰 Gestión de Riesgo Corregida")
    capital = st.number_input("Capital Cuenta ($):", value=1000)
    riesgo_p = st.slider("Riesgo por trade (%)", 0.5, 2.0, 1.0)
    target_r = st.selectbox("Activo:", ASSETS, key="risk_sel")
    dr = analyze_asset(target_r)
    
    if dr:
        r_usd = capital * (riesgo_p / 100)
        p, v = dr['price'], dr['vol']
        dist_sl = p * (v * 2.5) 
        
        if "USD" in target_r and "BTC" not in target_r: 
            lotaje = r_usd / (dist_sl * 100000)
        elif "BTC" in target_r: 
            lotaje = r_usd / dist_sl
        elif "GC=F" in target_r: 
            lotaje = r_usd / (dist_sl * 100)
        else: 
            lotaje = r_usd / dist_sl

        st.markdown(f"""
        <div style="background-color:#1e2130; padding:20px; border-radius:10px; border-left: 5px solid #00ffcc;">
            <h3>Plan de Riesgo</h3>
            Riesgo: <b>${r_usd:.2f}</b> | SL Distancia: <b>{dist_sl:.5f}</b>
            <h1 style="color:#00ffcc;">{lotaje:.3f} Lotes</h1>
        </div>
        """, unsafe_allow_html=True)
