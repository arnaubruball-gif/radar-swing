import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Halcón 4.0 - Cross Pairs Edition", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 10px; border-radius: 10px; border: 1px solid #3d4463; }
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
        
        # Lógica Original Matriz
        df['Ret'] = df['Close'].pct_change()
        df['Vol_Proxy'] = (df['High'] - df['Low']) * 100000
        df['RMF'] = df['Close'] * df['Vol_Proxy']
        
        # R2 Dinámico (30d)
        r2_series = []
        for i in range(len(df)):
            if i < 30: r2_series.append(0); continue
            subset = df.iloc[i-30:i].dropna()
            r2 = sm.OLS(subset['Ret'], sm.add_constant(subset['RMF'])).fit().rsquared
            r2_series.append(r2)
        df['R2_Dynamic'] = r2_series
        
        # Z-Diff (40d)
        diff = df['Ret'].rolling(40).sum() - df['RMF'].pct_change().rolling(40).sum()
        z_val = ((diff - diff.rolling(40).mean()) / (diff.rolling(40).std() + 1e-10)).iloc[-1]
        
        # Hurst y Volatilidad para Montecarlo
        hurst = calcular_hurst(df['Close'].values.flatten()[-50:])
        vol = df['Ret'].tail(30).std()
        drift = df['Ret'].tail(7).mean() # Drift de corto plazo para máxima sensibilidad
        
        return {
            'df': df, 'price': df['Close'].iloc[-1], 'z': z_val, 
            'r2': df['R2_Dynamic'].iloc[-1], 'hurst': hurst, 
            'vol': vol, 'drift': drift
        }
    except: return None

# --- 3. DASHBOARD ---
st.title("🦅 Halcón de Guerra 4.0 | Cross Pairs Intelligence")

tab1, tab2, tab3 = st.tabs(["📊 Matriz Principal", "🦅 Radar Fractal", "🎲 Montecarlo de Cruces"])

# Activos fijos para Matriz
ASSETS = ['EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'JPY=X', 'BTC-USD', 'GC=F', '^SPX']

with tab1:
    st.subheader("Ineficiencias en Pares Base")
    results = []
    for t in ASSETS:
        data = analyze_asset(t)
        if data:
            v = "⚪ NEUTRAL"
            if data['r2'] < 0.10:
                if data['z'] > 1.6: v = "🚨 VENTA (Ficción)"
                elif data['z'] < -1.6: v = "🟢 COMPRA (Oportunidad)"
            elif data['r2'] > 0.30: v = "💎 TENDENCIA REAL"
            results.append([t.replace('=X',''), f"{data['price']:.4f}", round(data['r2'],3), round(data['z'],2), v])
    
    df_res = pd.DataFrame(results, columns=['Activo', 'Precio', 'R2', 'Z-Diff', 'Veredicto'])
    st.dataframe(df_res.style.applymap(lambda x: 'color: #ff4b4b' if 'VENTA' in str(x) else ('color: #00ffcc' if 'COMPRA' in str(x) else ''), subset=['Veredicto']), use_container_width=True)

with tab2:
    st.subheader("Análisis de Memoria y Fractalidad")
    # Gráfico de Radar Hurst
    h_data = []
    for t in ASSETS:
        d = analyze_asset(t)
        if d: h_data.append({'Activo': t, 'Hurst': d['hurst'], 'Z-Diff': d['z']})
    
    df_h = pd.DataFrame(h_data)
    fig_h = px.scatter(df_h, x="Z-Diff", y="Hurst", text="Activo", color="Hurst", color_continuous_scale="RdYlGn_r")
    fig_h.add_hline(y=0.5, line_dash="dash", line_color="white")
    st.plotly_chart(fig_h, use_container_width=True)

with tab3:
    st.subheader("Simulación Direccional para Cruces Exóticos")
    c1, c2 = st.columns([1, 3])
    with c1:
        cross_ticker = st.text_input("Introduce el Cruce (ej: GBPAUD=X, EURJPY=X):", "GBPAUD=X")
        sim_days = st.slider("Días de proyección", 5, 20, 10)
        
    cross_data = analyze_asset(cross_ticker)
    
    if cross_data:
        # Lógica Montecarlo Direccional
        mu = cross_data['drift'] 
        sigma = cross_data['vol']
        last_p = cross_data['price']
        
        sims = 200
        paths = np.zeros((sim_days + 1, sims))
        paths[0] = last_p
        
        for t in range(1, sim_days + 1):
            # Modelo de Caminata Aleatoria con Drift (Inercia)
            paths[t] = paths[t-1] * (1 + np.random.normal(mu, sigma, sims))
        
        p10, p50, p90 = np.percentile(paths, 10, axis=1), np.percentile(paths, 50, axis=1), np.percentile(paths, 90, axis=1)
        
        with c2:
            fig_mc = go.Figure()
            # Nube de Probabilidad
            fig_mc.add_trace(go.Scatter(x=list(range(sim_days+1))+list(range(sim_days+1))[::-1], y=list(p90)+list(p10[::-1]), fill='toself', fillcolor='rgba(0,255,150,0.1)', line=dict(color='rgba(255,255,255,0)'), name="80% Confianza"))
            # Línea Central Direccional
            fig_mc.add_trace(go.Scatter(x=list(range(sim_days+1)), y=p50, line=dict(color='#00ffcc', width=4), name="Inercia (Drift)"))
            fig_mc.update_layout(template="plotly_dark", height=500, title=f"Direccionalidad Probable: {cross_ticker}")
            st.plotly_chart(fig_mc, use_container_width=True)
        
        # Métricas de sensibilidad
        m1, m2, m3 = st.columns(3)
        m1.metric("Drift (Inercia 7d)", f"{mu*100:.4f}%", help="Inclinación de la nube")
        m2.metric("Hurst (Memoria)", round(cross_data['hurst'], 2))
        m3.metric("Z-Diff", round(cross_data['z'], 2))
    else:
        st.error("Introduce un ticker válido de Yahoo Finance (ej: EURGBP=X)")

st.sidebar.info("""
**¿Cómo leer el Montecarlo en Cruces?**
1. **Nube hacia arriba**: El par tiene inercia alcista fuerte (Drift positivo).
2. **Nube hacia abajo**: Inercia bajista.
3. **Nube ancha**: Alta volatilidad (peligro para el Stop Loss).
4. **Nube estrecha**: Mercado comprimido, posible explosión.
""")
