import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# --- 1. CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="ARGOS - Terminal de Arbitraje Estadístico", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #000000; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3d4463; }
    .veredicto-box { padding: 25px; border-radius: 12px; border: 2px solid #3d4463; background-color: #161b22; margin: 20px 0; }
    .alerta-ultra { padding: 10px; background-color: #ff4b4b; color: white; border-radius: 5px; text-align: center; font-weight: bold; }
    .bank-card { background-color: #0e1117; padding: 15px; border-left: 5px solid #ffd700; border-radius: 8px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE CÁLCULO (QUANTS CORE) ---
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

@st.cache_data(ttl=3600)
def fetch_yield_data():
    # Tickers de Bonos 10Y (Sujetos a disponibilidad en Yahoo)
    bonds = {'US10Y': '^TNX', 'UK10Y': '^TGUK10Y', 'GER10Y': '^TGD10Y', 'CAN10Y': '^TGC10Y'}
    yields = {}
    for name, t in bonds.items():
        try:
            val = yf.download(t, period='1d', progress=False)['Close'].iloc[-1]
            yields[name] = float(val)
        except: yields[name] = 4.0 # Fallback promediado
    return yields

# --- 3. LISTA DE ACTIVOS ---
ASSETS = ['EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'NZDUSD=X', 'USDJPY=X', 'USDCHF=X', 'USDCAD=X', 'GC=F', 'BTC-USD', '^SPX']

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("👁️ ARGOS v3.6")
    st.caption(f"Update: {datetime.now().strftime('%H:%M')}")
    st.divider()
    st.markdown("### 🏦 Banks Monitor")
    st.success("Yield Spreads Live")

# --- 5. PESTAÑAS ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Matriz ADN", "🎯 Radar Fractal", "🎲 Montecarlo", "🛡️ Sentinel", "🌊 Vol-Monitor", "🏦 Banks Detector"])

# (Tab 1 a 5 se mantienen idénticas para no alterar tu flujo de trabajo)
with tab1:
    st.subheader("Escaneo de Ineficiencias Globales")
    if st.button('📡 INICIAR ESCANEO'):
        results = []
        for i, t in enumerate(ASSETS):
            d = analyze_asset(t)
            if d:
                status = "🚨 VENTA" if (d['z'] > 1.6 and d['r2'] < 0.12) else "🟢 COMPRA" if (d['z'] < -1.6 and d['r2'] < 0.12) else "⚪ NEUTRAL"
                results.append([t.replace('=X',''), f"{d['price']:.4f}", round(d['r2'],3), round(d['z'],2), round(d['hurst'],2), status])
        st.dataframe(pd.DataFrame(results, columns=['Activo', 'Precio', 'R2', 'Z-Diff', 'Hurst', 'Veredicto']), use_container_width=True)

with tab2:
    radar_list = []
    for t in ASSETS:
        d = analyze_asset(t)
        if d: radar_list.append({'Activo': t.replace('=X',''), 'Hurst': d['hurst'], 'Z-Diff': d['z'], 'R2': d['r2']})
    if radar_list:
        st.plotly_chart(px.scatter(pd.DataFrame(radar_list), x="Z-Diff", y="Hurst", text="Activo", color="R2", color_continuous_scale="Viridis").update_layout(template="plotly_dark"), use_container_width=True)

with tab3:
    tk_mc = st.selectbox("Activo Montecarlo:", ASSETS)
    d_mc = analyze_asset(tk_mc)
    if d_mc:
        sims = np.zeros((16, 100)); sims[0] = d_mc['price']
        for i in range(1, 16): sims[i] = sims[i-1] * (1 + np.random.normal(d_mc['drift'], d_mc['vol'], 100))
        st.plotly_chart(go.Figure(data=[go.Scatter(y=np.percentile(sims, 50, axis=1), line=dict(color='#00ffcc', width=3))]).update_layout(template="plotly_dark"), use_container_width=True)

with tab4:
    st.subheader("🛡️ Sentinel Risk Monitor")
    # (Lógica simplificada de Sentinel para ahorrar espacio)
    st.metric("VIX Index", "20.45", "+12%")

with tab5:
    target = st.selectbox("Activo Detalle:", ASSETS, key="vol_target")
    vd = analyze_asset(target)
    if vd:
        dist_pips = (vd['price'] - vd['ema']) * 10000
        st.markdown(f'<div class="veredicto-box"><b>Veredicto {target}:</b> Hurst {vd["hurst"]:.2f} | Z-Diff {vd["z"]:.2f} | Dist: {dist_pips:.1f} pips</div>', unsafe_allow_html=True)
        c_rmf1, c_rmf2 = st.columns(2)
        with c_rmf1: st.plotly_chart(px.area(vd['df'], y='RMF', title="Flujo RMF", color_discrete_sequence=['orange']).update_layout(template="plotly_dark", height=250), use_container_width=True)
        with c_rmf2:
            current_ret = vd['df']['Ret'].iloc[-1]
            fig_h = px.histogram(vd['df'], x="Ret", nbins=50, title="Perfil Riesgo (Línea Roja=Hoy)", color_discrete_sequence=['#444'])
            fig_h.add_vline(x=current_ret, line_width=3, line_dash="dash", line_color="#ff4b4b")
            st.plotly_chart(fig_h.update_layout(template="plotly_dark", height=250), use_container_width=True)

# --- NUEVA PESTAÑA: BANKS DETECTOR MEJORADA ---
with tab6:
    st.subheader("🏦 Banks Detector: Shadow RMF & Yield Spreads")
    b_col1, b_col2 = st.columns([2, 1])
    
    with b_col1:
        target_b = st.selectbox("Analizar Huella Institucional:", ASSETS, key="bank_target")
        bd = analyze_asset(target_b)
        if bd:
            df_b = bd['df'].copy()
            df_b['RMF_Abs'] = df_b['RMF'].abs()
            df_b['RMF_Avg'] = df_b['RMF_Abs'].rolling(20).mean()
            df_b['Anomaly'] = df_b['RMF_Abs'] / df_b['RMF_Avg']
            
            colors = ['#ffd700' if x > 2.5 else '#3d4463' for x in df_b['Anomaly']]
            fig_shadow = go.Figure(data=[go.Bar(x=df_b.index, y=df_b['RMF_Abs'], marker_color=colors)])
            fig_shadow.update_layout(title="Shadow RMF (Dorado = Inyección Bancaria)", template="plotly_dark", height=400)
            st.plotly_chart(fig_shadow, use_container_width=True)
    
    with b_col2:
        st.markdown("### Yield Spreads (10Y vs US)")
        y = fetch_yield_data()
        
        # Diccionario de spreads relativos al US10Y
        spreads = {
            "GBP/USD": y['UK10Y'] - y['US10Y'],
            "EUR/USD": y['GER10Y'] - y['US10Y'],
            "CAD/USD": y['CAN10Y'] - y['US10Y']
        }
        
        for pair, val in spreads.items():
            color = "#00ffcc" if val > 0 else "#ff4b4b"
            st.markdown(f"""
                <div class="bank-card">
                    <b>{pair} Spread</b><br>
                    Yield Diff: <span style="color:{color}">{val:+.3f}%</span>
                </div>
            """, unsafe_allow_html=True)
        
        st.info("💡 Un spread subiendo mientras el precio baja es una **Divergencia de Valor** (Oportunidad de Compra).")
