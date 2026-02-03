import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# --- 1. CONFIGURACIÓN ARGOS ---
st.set_page_config(page_title="ARGOS - Full Market Terminal", layout="wide")

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

@st.cache_data(ttl=3600)
def fetch_risk_metrics():
    tickers = {'VIX': '^VIX', 'DXY': 'DX-Y.NYB', 'GOLD': 'GC=F', 'SPX': '^GSPC'}
    risk_data = {}
    for name, t in tickers.items():
        df = yf.download(t, period='60d', interval='1d', progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        risk_data[name] = df
    
    vix_val = risk_data['VIX']['Close'].iloc[-1]
    ratio_gold_spx = risk_data['GOLD']['Close'] / risk_data['SPX']['Close']
    dxy_mom = risk_data['DXY']['Close'].pct_change(10).iloc[-1] * 100
    
    score = 0
    if vix_val > 20: score += 25
    if vix_val > risk_data['VIX']['Close'].rolling(20).mean().iloc[-1]: score += 25
    if dxy_mom > 0: score += 25
    if ratio_gold_spx.iloc[-1] > ratio_gold_spx.rolling(20).mean().iloc[-1]: score += 25
    
    return vix_val, ratio_gold_spx, dxy_mom, score, risk_data['VIX']

# --- 3. PANEL DE CONTROL ARGOS ---
st.title("👁️ ARGOS | Full Market Terminal")

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Matriz ADN", 
    "🎯 Radar Fractal", 
    "🎲 Montecarlo Direccional", 
    "🛡️ Sentinel: Riesgo Global"
])

ASSETS = {
    'MAJORS': ['EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'NZDUSD=X', 'USDJPY=X', 'USDCHF=X', 'USDCAD=X'],
    'CROSSES': ['EURGBP=X', 'EURJPY=X', 'GBPJPY=X', 'EURAUD=X', 'GBPAUD=X', 'AUDJPY=X', 'CHFJPY=X'],
    'OTHERS': ['BTC-USD', 'ETH-USD', 'GC=F', 'SI=F', '^SPX', '^IXIC', '^FTSE']
}
all_tickers = ASSETS['MAJORS'] + ASSETS['CROSSES'] + ASSETS['OTHERS']

with tab1:
    st.subheader("Ineficiencias Detectadas")
    if st.button('📡 ESCANEAR MERCADOS'):
        results = []
        with st.spinner('Procesando...'):
            for t in all_tickers:
                data = analyze_asset(t)
                if data:
                    v = "⚪ NEUTRAL"
                    if data['r2'] < 0.10:
                        if data['z'] > 1.6: v = "🚨 VENTA (Ficción)"
                        elif data['z'] < -1.6: v = "🟢 COMPRA (Oportunidad)"
                    elif data['r2'] > 0.30: v = "💎 TENDENCIA REAL"
                    results.append([t.replace('=X',''), f"{data['price']:.4f}", round(data['r2'],3), round(data['z'],2), round(data['amihud'], 4), v])
        df_res = pd.DataFrame(results, columns=['Activo', 'Precio', 'R2', 'Z-Diff', 'Amihud', 'Veredicto'])
        def style_v(val):
            if 'VENTA' in val: return 'background-color: #441111; color: #ff4b4b; font-weight: bold'
            if 'COMPRA' in val: return 'background-color: #114433; color: #00ffcc; font-weight: bold'
            if 'TENDENCIA' in val: return 'background-color: #112244; color: #1c83e1; font-weight: bold'
            return ''
        st.dataframe(df_res.style.applymap(style_v, subset=['Veredicto']), use_container_width=True)

with tab2:
    st.subheader("Mapa de Memoria (Hurst vs Z-Diff)")
    h_data = []
    for t in all_tickers:
        d = analyze_asset(t)
        if d: h_data.append({'Activo': t.replace('=X',''), 'Hurst': d['hurst'], 'Z-Diff': d['z']})
    if h_data:
        df_h = pd.DataFrame(h_data)
        fig_h = px.scatter(df_h, x="Z-Diff", y="Hurst", text="Activo", color="Hurst", color_continuous_scale="RdYlGn_r", range_x=[-4, 4], range_y=[0.2, 0.8])
        fig_h.add_hline(y=0.5, line_dash="dash", line_color="white")
        fig_h.update_layout(template="plotly_dark", height=500)
        st.plotly_chart(fig_h, use_container_width=True)

with tab3:
    st.subheader("Simulación Direccional")
    c1, c2 = st.columns([1, 3])
    with c1:
        cross_ticker = st.text_input("Ticker (ej: AUDUSD=X):", "AUDUSD=X")
        sim_days = st.slider("Días", 5, 20, 10)
    cross_data = analyze_asset(cross_ticker)
    if cross_data:
        paths = np.zeros((sim_days + 1, 250))
        paths[0] = cross_data['price']
        for t in range(1, sim_days + 1):
            paths[t] = paths[t-1] * (1 + np.random.normal(cross_data['drift'], cross_data['vol'], 250))
        p10, p50, p90 = np.percentile(paths, 10, axis=1), np.percentile(paths, 50, axis=1), np.percentile(paths, 90, axis=1)
        with c2:
            fig_mc = go.Figure()
            fig_mc.add_trace(go.Scatter(x=list(range(sim_days+1))+list(range(sim_days+1))[::-1], y=list(p90)+list(p10[::-1]), fill='toself', fillcolor='rgba(0,255,150,0.1)', line=dict(color='rgba(255,255,255,0)'), name="Probabilidad"))
            fig_mc.add_trace(go.Scatter(x=list(range(sim_days+1)), y=p50, line=dict(color='#00ffcc', width=4), name="Drift Argos"))
            fig_mc.update_layout(template="plotly_dark", height=500)
            st.plotly_chart(fig_mc, use_container_width=True)
        m1, m2, m3 = st.columns(3)
        m1.metric("Inercia", f"{cross_data['drift']*100:.4f}%")
        m2.metric("Z-Score", round(cross_data['z'], 2))
        m3.metric("Hurst", round(cross_data['hurst'], 2))

with tab4:
    st.subheader("🛡️ Sentinel: Riesgo Global")
    vix_v, g_spx, dxy_m, r_score, vix_df = fetch_risk_metrics()
    k1, k2, k3 = st.columns(3)
    k1.metric("SCORE RIESGO", f"{r_score}%", "🔴" if r_score >= 75 else "🟢")
    k2.metric("VIX", f"{vix_v:.2f}")
    k3.metric("MOMENTUM DXY", f"{dxy_m:.2f}%")
    st.divider()
    cl, cr = st.columns(2)
    with cl:
        st.plotly_chart(px.area(vix_df, y='Close', title="VIX Monitor").update_layout(template="plotly_dark", height=300), use_container_width=True)
    with cr:
        st.plotly_chart(px.line(g_spx, title="Ratio Oro/SPX").update_layout(template="plotly_dark", height=300), use_container_width=True)

st.sidebar.markdown("### 👁️ Sistema ARGOS\n Vigil
