import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# --- 1. CONFIGURACIÓN DE ÉLITE ---
st.set_page_config(page_title="Halcón 4.0 - Swing Terminal", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3d4463; }
    </style>
    """, unsafe_allow_html=True)

st.title("🦅 Halcón de Guerra 4.0 | Swing Intelligence")

# --- 2. MOTOR DE ANÁLISIS ---
ASSETS = {
    'EUR/USD': 'EURUSD=X', 'GBP/USD': 'GBPUSD=X', 'AUD/USD': 'AUDUSD=X',
    'NZD/USD': 'NZDUSD=X', 'USD/JPY': 'JPY=X', 'USD/CHF': 'CHF=X',
    'USD/CAD': 'CAD=X', 'BITCOIN': 'BTC-USD', 'ORO (Spot)': 'GC=F',
    'S&P 500': '^SPX'
}

def calcular_hurst(ts):
    if len(ts) < 30: return 0.5
    lags = range(2, 20)
    tau = [np.sqrt(np.std(np.subtract(ts[lag:], ts[:-lag]))) for lag in lags]
    poly = np.polyfit(np.log(lags), np.log(tau), 1)
    return poly[0] * 2.0

def analyze_full(name, ticker):
    try:
        df = yf.download(ticker, period='200d', interval='1d', progress=False)
        if df.empty: return None, None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # --- LOGICA ORIGINAL (TU MATRIZ) ---
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
        
        # Amihud
        amihud = (df['Ret'].abs() / (df['RMF'].replace(0, np.nan) / 1e6)).fillna(df['Ret'].abs() * 100).rolling(20).mean().iloc[-1]
        
        # --- LOGICA NUEVA (HURST Y VOL) ---
        prices = df['Close'].values.flatten().astype(float)
        hurst = calcular_hurst(prices[-50:])
        vol_rel = df['Volume'].iloc[-1] / (df['Volume'].tail(20).mean() + 1e-10) if 'Volume' in df else 1.0

        last_price = df['Close'].iloc[-1]
        last_r2 = df['R2_Dynamic'].iloc[-1]
        
        veredicto = "⚪ NEUTRAL"
        if last_r2 < 0.10:
            if z_val > 1.6: veredicto = "🚨 VENTA (Ficción)"
            elif z_val < -1.6: veredicto = "🟢 COMPRA (Oportunidad)"
        elif last_r2 > 0.30: veredicto = "💎 TENDENCIA REAL"

        return df, {
            'original': [name, f"{last_price:.4f}", round(last_r2, 3), round(z_val, 2), round(amihud, 4), veredicto],
            'extra': [name, round(hurst, 2), round(vol_rel, 2)],
            'stats': {'price': last_price, 'volatilidad': df['Ret'].tail(30).std(), 'drift': df['Ret'].tail(10).mean()}
        }
    except: return None, None

# --- 3. PANEL DE CONTROL ---
tab1, tab2, tab3 = st.tabs(["📊 Matriz ADN (Original)", "🦅 Radar Hurst/Vol", "🎲 Montecarlo Direccional"])

all_results = {}
if st.sidebar.button('📡 ESCANEAR MERCADOS'):
    for name, ticker in ASSETS.items():
        d, s = analyze_full(name, ticker)
        if s: all_results[name] = (d, s)
    st.session_state['data'] = all_results

if 'data' in st.session_state:
    data = st.session_state['data']
    
    with tab1:
        # LA MATRIZ TAL CUAL LA PASASTE
        m_data = [v[1]['original'] for v in data.values()]
        df_res = pd.DataFrame(m_data, columns=['Activo', 'Precio', 'R2 (30d)', 'Z-Diff (40d)', 'Amihud', 'Veredicto'])
        
        def style_v(val):
            if 'VENTA' in val: return 'color: #ff4b4b; font-weight: bold'
            if 'COMPRA' in val: return 'color: #00ffcc; font-weight: bold'
            if 'TENDENCIA' in val: return 'color: #1c83e1; font-weight: bold'
            return ''
        
        st.dataframe(df_res.style.applymap(style_v, subset=['Veredicto']), use_container_width=True)
        
        # ADN Visual
        selected = st.selectbox("🎯 ADN del Activo:", list(data.keys()))
        df_p = data[selected][0]
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(x=df_p.index, open=df_p['Open'], high=df_p['High'], low=df_p['Low'], close=df_p['Close'], name="Precio"), row=1, col=1)
        fig.add_trace(go.Bar(x=df_p.index, y=df_p['R2_Dynamic'], name="R2"), row=2, col=1)
        fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        # PESTAÑA EXTRA PARA HURST Y VOLUMEN
        st.subheader("Análisis Fractal y Presión de Volumen")
        e_data = [v[1]['extra'] for v in data.values()]
        df_extra = pd.DataFrame(e_data, columns=['Activo', 'Hurst (Memoria)', 'Volumen Relativo'])
        
        c1, c2 = st.columns([1, 2])
        c1.dataframe(df_extra, use_container_width=True)
        
        with c2:
            fig_h = px.scatter(df_extra, x="Hurst (Memoria)", y="Volumen Relativo", text="Activo", 
                               size="Volumen Relativo", color="Hurst (Memoria)", color_continuous_scale="Viridis")
            fig_h.add_vline(x=0.5, line_dash="dash", line_color="gray")
            fig_h.update_layout(template="plotly_dark", height=400)
            st.plotly_chart(fig_h, use_container_width=True)

    with tab3:
        # MONTECARLO SENSIBLE Y DIRECCIONAL
        st.subheader("Simulación de Trayectoria Direccional (Drift-Adjusted)")
        sel_m = st.selectbox("Proyectar Activo:", list(data.keys()), key="mc_sel")
        stats = data[sel_m][1]['stats']
        
        # Montecarlo con Drift (direccionalidad)
        sims, days = 100, 10
        dt = 1
        # El drift hace que no sea plano: usa la media de retornos recientes
        mu = stats['drift'] 
        sigma = stats['volatilidad']
        
        mc_paths = np.zeros((days + 1, sims))
        mc_paths[0] = stats['price']
        
        for t in range(1, days + 1):
            # Ecuación de Movimiento Browniano Geométrico
            shock = np.random.normal(mu, sigma, sims)
            mc_paths[t] = mc_paths[t-1] * (1 + shock)
        
        p10, p50, p90 = np.percentile(mc_paths, 10, axis=1), np.percentile(mc_paths, 50, axis=1), np.percentile(mc_paths, 90, axis=1)
        
        fig_mc = go.Figure()
        fig_mc.add_trace(go.Scatter(x=list(range(days+1))+list(range(days+1))[::-1], y=list(p90)+list(p10[::-1]), fill='toself', fillcolor='rgba(0,255,200,0.1)', line=dict(color='rgba(255,255,255,0)'), name="Área de Probabilidad"))
        fig_mc.add_trace(go.Scatter(x=list(range(days+1)), y=p50, line=dict(color='#00ffcc', width=4), name="Trayectoria Direccional"))
        fig_mc.update_layout(template="plotly_dark", height=500, title=f"Predicción Direccional 10 Días: {sel_m}")
        st.plotly_chart(fig_mc, use_container_width=True)
        
        st.info("💡 Este modelo usa 'Drift Adjust': Si el activo tiene inercia alcista/bajista reciente, la nube se inclinará en esa dirección en lugar de ser plana.")
