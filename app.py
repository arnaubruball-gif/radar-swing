import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as go
import plotly.express as px

# --- 1. CONFIGURACIÓN ARGOS ---
st.set_page_config(page_title="ARGOS - Full Market Terminal", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 10px; border-radius: 10px; border: 1px solid #3d4463; }
    .veredicto-box { padding: 20px; border-radius: 10px; border: 2px solid #3d4463; background-color: #161b22; margin-top: 20px; }
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
        vol = df['Ret'].tail(30).std()
        drift = df['Ret'].tail(7).mean() 
        
        return {
            'df': df, 'price': float(df['Close'].iloc[-1]), 'z': z_val, 
            'r2': df['R2_Dynamic'].iloc[-1], 'hurst': hurst, 
            'vol': vol, 'drift': drift
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
    vix_val = float(risk_data['VIX']['Close'].iloc[-1])
    ratio_gold_spx = risk_data['GOLD']['Close'] / risk_data['SPX']['Close']
    dxy_mom = float(risk_data['DXY']['Close'].pct_change(10).iloc[-1] * 100)
    score = 0
    if vix_val > 20: score += 25
    if vix_val > risk_data['VIX']['Close'].rolling(20).mean().iloc[-1]: score += 25
    if dxy_mom > 0: score += 25
    if ratio_gold_spx.iloc[-1] > ratio_gold_spx.rolling(20).mean().iloc[-1]: score += 25
    return vix_val, ratio_gold_spx, dxy_mom, score, risk_data['VIX']

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("👁️ ARGOS SYSTEM")
    st.markdown("---")
    st.subheader("Manual de Operaciones")
    st.info("**Hurst < 0.50:** El mercado busca su media.")
    st.info("**Z-Diff > 1.6:** Goma estirada (Sobreventa/compra).")
    st.info("**R2 < 0.10:** El movimiento es ruido, no hay dinero real detrás.")
    st.markdown("---")
    st.caption("Argos Terminal | v1.8")

# --- 4. DEFINICIÓN DE PESTAÑAS (Orden Crítico) ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Matriz ADN", 
    "🎯 Radar Fractal", 
    "🎲 Montecarlo", 
    "🛡️ Sentinel",
    "🌊 Vol-Monitor"
])

ASSETS = {
    'MAJORS': ['EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'NZDUSD=X', 'USDJPY=X', 'USDCHF=X', 'USDCAD=X'],
    'CROSSES': ['EURGBP=X', 'EURJPY=X', 'GBPJPY=X', 'EURAUD=X', 'GBPAUD=X', 'AUDJPY=X', 'CHFJPY=X'],
    'OTHERS': ['BTC-USD', 'ETH-USD', 'GC=F', 'SI=F', '^SPX', '^IXIC', '^FTSE']
}
all_tickers = ASSETS['MAJORS'] + ASSETS['CROSSES'] + ASSETS['OTHERS']

# Llenado de Pestañas
with tab1:
    st.subheader("Escaneo de Ineficiencias")
    if st.button('📡 INICIAR ESCANEO'):
        results = []
        for t in all_tickers:
            data = analyze_asset(t)
            if data:
                v = "⚪ NEUTRAL"
                if data['r2'] < 0.10:
                    if data['z'] > 1.6: v = "🚨 VENTA (Ficción)"
                    elif data['z'] < -1.6: v = "🟢 COMPRA (Oportunidad)"
                results.append([t.replace('=X',''), f"{data['price']:.4f}", round(data['r2'],3), round(data['z'],2), v])
        df_res = pd.DataFrame(results, columns=['Activo', 'Precio', 'R2', 'Z-Diff', 'Veredicto'])
        st.dataframe(df_res, use_container_width=True)

with tab2:
    st.subheader("Mapa Hurst vs Z-Diff")
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
    st.subheader("🎲 Proyección de Montecarlo & Dispersión")
    mc_col1, mc_col2 = st.columns([1, 3])
    
    with mc_col1:
        ticker_mc = st.text_input("Activo:", "GBPUSD=X", key="mc_ticker")
        dias_sim = st.slider("Días", 5, 30, 15)
        
    data_mc = analyze_asset(ticker_mc)
    if data_mc:
        # Simulación
        num_sim = 100
        simulaciones = np.zeros((dias_sim + 1, num_sim))
        simulaciones[0] = data_mc['price']
        for i in range(1, dias_sim + 1):
            simulaciones[i] = simulaciones[i-1] * (1 + np.random.normal(data_mc['drift'], data_mc['vol'], num_sim))
        
        p10, p50, p90 = np.percentile(simulaciones, 10, axis=1), np.percentile(simulaciones, 50, axis=1), np.percentile(simulaciones, 90, axis=1)
        
        with mc_col1:
            st.metric("Drift", f"{data_mc['drift']*100:.4f}%")
            st.metric("Z-Diff", round(data_mc['z'], 2))
            st.metric("Hurst", round(data_mc['hurst'], 2))
            
        with mc_col2:
            fig_mc = go.Figure()
            # Nube
            fig_mc.add_trace(go.Scatter(x=list(range(dias_sim+1)) + list(range(dias_sim+1))[::-1], y=list(p90) + list(p10[::-1]), fill='toself', fillcolor='rgba(0, 255, 204, 0.1)', line=dict(color='rgba(255,255,255,0)'), name='Rango 80%'))
            # Línea central
            fig_mc.add_trace(go.Scatter(x=list(range(dias_sim+1)), y=p50, line=dict(color='#00ffcc', width=3), name='Trayectoria Esperada'))
            fig_mc.update_layout(template="plotly_dark", height=500, margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig_mc, use_container_width=True)

with tab4:
    st.subheader("🛡️ Sentinel")
    vix_v, g_spx, dxy_m, r_score, vix_df = fetch_risk_metrics()
    k1, k2, k3 = st.columns(3)
    k1.metric("SCORE RIESGO", f"{r_score}%")
    k2.metric("VIX", f"{vix_v:.2f}")
    k3.metric("MOMENTUM DXY", f"{dxy_m:.2f}%")
    st.plotly_chart(px.area(vix_df, y='Close').update_layout(template="plotly_dark", height=300), use_container_width=True)

with tab5:
    st.subheader("🌊 Vol-Monitor & Veredicto")
    vol_ticker = st.text_input("Activo:", "GBPUSD=X", key="vol_ticker")
    v_data = analyze_asset(vol_ticker)
    if v_data:
        st.markdown('<div class="veredicto-box">', unsafe_allow_html=True)
        st.write("### 🧠 Veredicto ARGOS")
        if v_data['hurst'] < 0.45 and abs(v_data['z']) > 1.6:
            st.error(f"🚨 SEÑAL FUERTE DE REVERSIÓN: {'VENTA' if v_data['z'] > 0 else 'COMPRA'}")
        else:
            st.success("⚪ RÉGIMEN ESTABLE / RUIDO")
        st.write(f"Confianza: {int((1-v_data['r2'])*100)}% | Hurst: {v_data['hurst']:.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
