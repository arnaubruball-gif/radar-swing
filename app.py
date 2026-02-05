import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# --- 1. CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="ARGOS v4.0 - Global Risk Sentinel", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #000000; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3d4463; }
    .veredicto-box { padding: 25px; border-radius: 12px; border: 2px solid #3d4463; background-color: #161b22; margin: 20px 0; }
    .alerta-ultra { padding: 10px; background-color: #ff4b4b; color: white; border-radius: 5px; text-align: center; font-weight: bold; }
    .risk-card { padding: 15px; border-radius: 8px; margin-bottom: 10px; border: 1px solid #3d4463; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE CÁLCULO (INTACTO) ---
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
        
        return {
            'df': df, 'price': float(df['Close'].iloc[-1]), 'z': z_val, 
            'r2': df['R2_Dynamic'].iloc[-1], 'hurst': hurst, 
            'ema': ema_21.iloc[-1], 'vol': df['Ret'].tail(30).std(),
            'drift': df['Ret'].tail(7).mean()
        }
    except: return None

# --- 3. LISTA DE ACTIVOS ---
ASSETS = ['EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'NZDUSD=X', 'USDJPY=X', 'USDCHF=X', 'USDCAD=X', 'GC=F', 'BTC-USD', '^SPX', 'HG=F']

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("👁️ ARGOS v4.0")
    st.caption(f"Update: {datetime.now().strftime('%H:%M')}")
    st.divider()
    st.write("Sentinel Risk Core: **ACTIVE**")
    st.info("🎯 Hurst < 0.45: Reversión")
    st.info("📏 Z-Diff > 1.6: Venta")

# --- 5. PESTAÑAS ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Matriz ADN", "🎯 Radar Fractal", "🎲 Montecarlo", "🛡️ Sentinel Macro", "🌊 Vol-Monitor", "🏦 Banks Detector"])

with tab1:
    st.subheader("Escaneo de Ineficiencias Globales")
    if st.button('📡 INICIAR ESCANEO'):
        results = []
        pbar = st.progress(0)
        for i, t in enumerate(ASSETS):
            d = analyze_asset(t)
            if d:
                status = "🚨 VENTA" if (d['z'] > 1.6 and d['r2'] < 0.12) else "🟢 COMPRA" if (d['z'] < -1.6 and d['r2'] < 0.12) else "⚪ NEUTRAL"
                results.append([t.replace('=X',''), f"{d['price']:.4f}", round(d['r2'],3), round(d['z'],2), round(d['hurst'],2), status])
            pbar.progress((i + 1) / len(ASSETS))
        st.dataframe(pd.DataFrame(results, columns=['Activo', 'Precio', 'R2', 'Z-Diff', 'Hurst', 'Veredicto']), use_container_width=True)

with tab2:
    radar_list = []
    for t in ASSETS:
        d = analyze_asset(t)
        if d: radar_list.append({'Activo': t.replace('=X',''), 'Hurst': d['hurst'], 'Z-Diff': d['z'], 'R2': d['r2']})
    if radar_list:
        df_radar = pd.DataFrame(radar_list)
        fig_radar = px.scatter(df_radar, x="Z-Diff", y="Hurst", text="Activo", color="R2", color_continuous_scale="Viridis")
        fig_radar.add_hline(y=0.5, line_dash="dash", line_color="red")
        fig_radar.update_layout(template="plotly_dark", height=500)
        st.plotly_chart(fig_radar, use_container_width=True)

with tab3:
    tk_mc = st.selectbox("Activo Montecarlo:", ASSETS, key="mc_select")
    d_mc = analyze_asset(tk_mc)
    if d_mc:
        sims = np.zeros((16, 100)); sims[0] = d_mc['price']
        for i in range(1, 16): sims[i] = sims[i-1] * (1 + np.random.normal(d_mc['drift'], d_mc['vol'], 100))
        fig_mc = go.Figure()
        p50 = np.percentile(sims, 50, axis=1)
        fig_mc.add_trace(go.Scatter(y=p50, line=dict(color='#00ffcc', width=3), name='Eje Central'))
        st.plotly_chart(fig_mc.update_layout(template="plotly_dark", height=450), use_container_width=True)

with tab4:
    st.subheader("🛡️ Sentinel: El Búnker de Riesgo Global")
    risk_tickers = {'VIX': '^VIX', 'DXY': 'DX-Y.NYB', 'GOLD': 'GC=F', 'COPPER': 'HG=F', 'HYG': 'HYG'}
    rd = {}
    for n, t in risk_tickers.items():
        tmp = yf.download(t, period='60d', progress=False)
        if isinstance(tmp.columns, pd.MultiIndex): tmp.columns = tmp.columns.get_level_values(0)
        rd[n] = tmp
    
    c1, c2, c3, c4 = st.columns(4)
    vix_now = rd['VIX']['Close'].iloc[-1]
    c1.metric("VIX (MIEDO)", f"{vix_now:.2f}", f"{((vix_now/rd['VIX']['Close'].iloc[-2])-1)*100:.1f}%")
    dxy_now = rd['DXY']['Close'].iloc[-1]
    c2.metric("DXY (DÓLAR)", f"{dxy_now:.2f}", f"{((dxy_now/rd['DXY']['Close'].iloc[-10])-1)*100:.1f}%")
    gold_copper = rd['GOLD']['Close'].iloc[-1] / rd['COPPER']['Close'].iloc[-1]
    c3.metric("GOLD/COPPER", f"{gold_copper:.2f}", "DEFENSIVO" if gold_copper > 500 else "PRO-RIESGO")
    hyg_ret = rd['HYG']['Close'].pct_change(5).iloc[-1] * 100
    c4.metric("HIGH YIELD", f"{rd['HYG']['Close'].iloc[-1]:.2f}", f"{hyg_ret:.2f}% (5d)")

    # Semáforo de Riesgo
    score = 0
    if vix_now > 20: score += 25
    if gold_copper > 550: score += 25
    if dxy_now > 104: score += 25
    if hyg_ret < -1: score += 25
    idx = min(score // 25, 3)
    colors = ["#00ffcc", "#ffd700", "#ff8c00", "#ff4b4b"]
    labels = ["BAJO", "MODERADO", "ALTO", "EXTREMO"]
    st.markdown(f'<div style="background-color:{colors[idx]}; color:black; padding:15px; text-align:center; border-radius:10px; font-weight:bold;">RIESGO GLOBAL: {labels[idx]} ({score}%)</div>', unsafe_allow_html=True)

with tab5:
    target = st.selectbox("Activo Detalle:", ASSETS, key="vol_target")
    vd = analyze_asset(target)
    if vd:
        dist_pips = (vd['price'] - vd['ema']) * 10000
        st.markdown(f'<div class="veredicto-box"><b>Veredicto {target}:</b> Hurst {vd["hurst"]:.2f} | Z-Diff {vd["z"]:.2f} | Dist: {dist_pips:.1f} pips</div>', unsafe_allow_html=True)
        c_rmf1, c_rmf2 = st.columns(2)
        with c_rmf1:
            st.plotly_chart(px.area(vd['df'], y='RMF', title="Flujo RMF", color_discrete_sequence=['orange']).update_layout(template="plotly_dark", height=250), use_container_width=True)
        with c_rmf2:
            current_ret = vd['df']['Ret'].iloc[-1]
            fig_hist = px.histogram(vd['df'], x="Ret", nbins=50, title="Perfil Riesgo (Rojo=Hoy)", color_discrete_sequence=['#444'])
            fig_hist.add_vline(x=current_ret, line_width=3, line_dash="dash", line_color="#ff4b4b")
            st.plotly_chart(fig_hist.update_layout(template="plotly_dark", height=250), use_container_width=True)

with tab6:
    st.subheader("🏦 Banks Detector: Shadow RMF")
    target_b = st.selectbox("Analizar Huella Institucional:", ASSETS, key="bank_target")
    bd = analyze_asset(target_b)
    if bd:
        df_b = bd['df'].copy()
        df_b['RMF_Abs'] = df_b['RMF'].abs()
        df_b['Anomaly'] = df_b['RMF_Abs'] / df_b['RMF_Abs'].rolling(20).mean()
        colors = ['#ffd700' if x > 2.5 else '#3d4463' for x in df_b['Anomaly']]
        st.plotly_chart(go.Figure(data=[go.Bar(x=df_b.index, y=df_b['RMF_Abs'], marker_color=colors)]).update_layout(title="Shadow RMF (Barras Doradas = Institucional)", template="plotly_dark", height=400), use_container_width=True)
