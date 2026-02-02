import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Halcón 4.0 - News Management", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 10px; border-radius: 10px; border: 1px solid #3d4463; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE ANÁLISIS ---
def calcular_hurst(ts):
    if len(ts) < 30: return 0.5
    lags = range(2, 20)
    tau = [np.sqrt(np.std(np.subtract(ts[lag:], ts[:-lag]))) for lag in lags]
    poly = np.polyfit(np.log(lags), np.log(tau), 1)
    return poly[0] * 2.0

@st.cache_data(ttl=300)
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
        
        amihud = (df['Ret'].abs() / (df['RMF'].replace(0, np.nan) / 1e6)).fillna(df['Ret'].abs() * 100).rolling(20).mean().iloc[-1]
        
        # Hurst y Volatilidad Direccional
        prices = df['Close'].values.flatten().astype(float)
        hurst = calcular_hurst(prices[-50:])
        vol = df['Ret'].tail(30).std()
        drift = df['Ret'].tail(7).mean() 
        
        return {
            'df': df, 'price': df['Close'].iloc[-1], 'z': z_val, 
            'r2': df['R2_Dynamic'].iloc[-1], 'hurst': hurst, 
            'vol': vol, 'drift': drift, 'amihud': amihud
        }
    except: return None

# --- 3. INTERFAZ ---
st.title("🦅 Halcón de Guerra 4.0 | News Stress Terminal")

tab1, tab2, tab3 = st.tabs(["📊 Matriz ADN", "🦅 Radar Fractal", "🎲 Montecarlo & Niveles"])

ASSETS = ['EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'NZDUSD=X', 'USDJPY=X', 'USDCAD=X', 'GBPAUD=X', 'EURAUD=X']

with tab1:
    results = []
    for t in ASSETS:
        data = analyze_asset(t)
        if data:
            v = "⚪ NEUTRAL"
            if data['r2'] < 0.10:
                if data['z'] > 1.6: v = "🚨 VENTA (Ficción)"
                elif data['z'] < -1.6: v = "🟢 COMPRA (Oportunidad)"
            elif data['r2'] > 0.30: v = "💎 TENDENCIA REAL"
            results.append([t.replace('=X',''), f"{data['price']:.4f}", round(data['r2'],3), round(data['z'],2), round(data['amihud'], 4), v])
    
    df_res = pd.DataFrame(results, columns=['Activo', 'Precio', 'R2', 'Z-Diff', 'Amihud', 'Veredicto'])
    st.dataframe(df_res.style.applymap(lambda x: 'color: #ff4b4b' if 'VENTA' in str(x) else ('color: #00ffcc' if 'COMPRA' in str(x) else ''), subset=['Veredicto']), use_container_width=True)

with tab2:
    h_data = [{'Activo': t, 'Hurst': analyze_asset(t)['hurst'], 'Z-Diff': analyze_asset(t)['z']} for t in ASSETS if analyze_asset(t)]
    df_h = pd.DataFrame(h_data)
    fig_h = px.scatter(df_h, x="Z-Diff", y="Hurst", text="Activo", color="Hurst", color_continuous_scale="RdYlGn_r", range_y=[0.2, 0.8])
    fig_h.add_hline(y=0.5, line_dash="dash", line_color="white")
    st.plotly_chart(fig_h, use_container_width=True)

with tab3:
    st.subheader("Simulación de Escenarios y Niveles de Salida")
    c1, c2 = st.columns([1, 3])
    with c1:
        sel_t = st.selectbox("Cruce para operar:", ASSETS, index=6) # Por defecto GBPAUD
        days = st.slider("Días de Proyección", 1, 10, 5)
        risk_mult = st.slider("Multiplicador de Stress (Noticia)", 1.0, 3.0, 1.5)
        
    d = analyze_asset(sel_t)
    if d:
        # Simulación Montecarlo
        sims = 500
        paths = np.zeros((days + 1, sims))
        paths[0] = d['price']
        for t in range(1, days + 1):
            paths[t] = paths[t-1] * (1 + np.random.normal(d['drift'], d['vol'], sims))
        
        p10, p50, p90 = np.percentile(paths, 10, axis=1), np.percentile(paths, 50, axis=1), np.percentile(paths, 90, axis=1)
        
        # --- CÁLCULO DE SL Y TP ---
        # Si Hurst es 0.34, el TP debe ser el regreso a la media (P50)
        tp_price = p50[-1]
        
        # El SL de Pánico se ajusta por el multiplicador de stress para aguantar el "spike" de la noticia
        if d['z'] > 0: # Buscamos VENTA
            sl_price = p90[-1] + (abs(p90[-1] - p50[-1]) * (risk_mult - 1))
            trade_type = "VENTA"
        else: # Buscamos COMPRA
            sl_price = p10[-1] - (abs(p50[-1] - p10[-1]) * (risk_mult - 1))
            trade_type = "COMPRA"

        with c2:
            st.write(f"### 🛡️ Niveles de Trading: {sel_t}")
            m1, m2, m3 = st.columns(3)
            m1.metric("ENTRADA ACTUAL", f"{d['price']:.5f}")
            m2.metric("TAKE PROFIT (Media)", f"{tp_price:.5f}", delta=f"{tp_price - d['price']:.5f}")
            m3.metric("STOP LOSS (Pánico)", f"{sl_price:.5f}", delta=f"{sl_price - d['price']:.5f}", delta_color="inverse")
            
            fig_mc = go.Figure()
            # Nube
            fig_mc.add_trace(go.Scatter(x=list(range(days+1))+list(range(days+1))[::-1], y=list(p90)+list(p10[::-1]), fill='toself', fillcolor='rgba(0,255,150,0.1)', line=dict(color='rgba(255,255,255,0)'), name="Área Probable"))
            # TP y SL
            fig_mc.add_hline(y=tp_price, line_dash="dot", line_color="#00ffcc", annotation_text="TAKE PROFIT")
            fig_mc.add_hline(y=sl_price, line_dash="dot", line_color="#ff4b4b", annotation_text="STOP LOSS PÁNICO")
            fig_mc.update_layout(template="plotly_dark", height=500)
            st.plotly_chart(fig_mc, use_container_width=True)

st.sidebar.markdown(f"""
### 📊 Status Pre-Noticia
**Activo:** {sel_t}
**Hurst:** {d['hurst'] if d else 0:.2f}
**Z-Diff:** {d['z'] if d else 0:.2f}

**Estrategia:**
Con un Hurst de **0.34**, el mercado está en máxima "antipersistencia". Cualquier movimiento brusco por la noticia tiene una alta probabilidad de ser una mecha que regrese al nivel de **Take Profit** marcado.
""")
