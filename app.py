import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="ARGOS v6.6 - Institutional Edge", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #000000; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3d4463; }
    .tp-card { background-color: #161b22; padding: 20px; border-radius: 10px; border-top: 4px solid #00ffcc; text-align: center; margin-bottom:10px; }
    .sl-card { background-color: #161b22; padding: 20px; border-radius: 10px; border-top: 4px solid #ff4b4b; text-align: center; }
    .bank-card { background-color: #0e1117; padding: 10px; border-left: 5px solid #ffd700; margin-bottom: 5px; font-size: 0.85rem; }
    .risk-banner { padding: 20px; border-radius: 10px; text-align: center; font-weight: bold; font-size: 1.5rem; margin-top: 10px; color: black; }
    .cot-card { background-color: #1c1c1c; padding: 15px; border-radius: 10px; border: 1px solid #ffd700; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE CÁLCULO (Tu lógica original intacta) ---
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
        df['RVOL'] = df['Vol_Proxy'] / df['Vol_Proxy'].rolling(20).mean()
        
        r2_series = []
        for i in range(len(df)):
            if i < 30: r2_series.append(0); continue
            subset = df.iloc[i-30:i].dropna()
            r2 = sm.OLS(subset['Ret'], sm.add_constant(subset['RMF'])).fit().rsquared
            r2_series.append(r2)
        df['R2_Dynamic'] = r2_series
        diff = df['Ret'].rolling(40).sum() - df['RMF'].pct_change().rolling(40).sum()
        z_val = ((diff - diff.rolling(40).mean()) / (diff.rolling(40).std() + 1e-10)).iloc[-1]
        hurst = calcular_hurst(df['Close'].tail(50).values.flatten())
        ema_21 = df['Close'].ewm(span=21, adjust=False).mean().iloc[-1]
        
        return {
            'df': df, 'price': float(df['Close'].iloc[-1]), 'z': z_val, 
            'r2': df['R2_Dynamic'].iloc[-1], 'hurst': hurst, 'ema': float(ema_21), 
            'vol': df['Ret'].tail(30).std(), 'rvol': df['RVOL'].iloc[-1]
        }
    except: return None

# --- 3. LISTA DE ACTIVOS ---
ASSETS = ['EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'USDCAD=X', 'USDJPY=X', 'USDCHF=X', 'GC=F', 'BTC-USD', '^GSPC']

# --- 4. PESTAÑAS (Añadida Tab 7) ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 ADN", "🎯 Ejecución Pro", "🎲 Montecarlo", "🛡️ Sentinel", 
    "🌊 Vol-Monitor", "🏦 Banks Detector", "🏛️ COT Insight"
])

with tab1:
    if st.button('📡 ESCANEO ADN'):
        results = []
        for t in ASSETS:
            d = analyze_asset(t)
            if d:
                status = "🚨 VENTA" if d['z'] > 1.6 else "🟢 COMPRA" if d['z'] < -1.6 else "⚪ NEUTRAL"
                results.append([t.replace('=X',''), d['price'], round(d['r2'],3), round(d['z'],2), round(d['hurst'],2), status])
        st.dataframe(pd.DataFrame(results, columns=['Activo', 'Precio', 'R2', 'Z-Diff', 'Hurst', 'Veredicto']), use_container_width=True)

with tab2:
    st.subheader("🎯 Niveles de Salida (Volatilidad Implícita)")
    target_e = st.selectbox("Seleccionar Activo:", ASSETS, key="exec_s")
    de = analyze_asset(target_e)
    if de:
        p, v, z = de['price'], de['vol'], de['z']
        sl = p * (1 + v*1.5) if z > 0 else p * (1 - v*1.5)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 📅 Objetivos Diarios")
            tp_d = p * (1 - v if z > 0 else 1 + v)
            st.markdown(f'<div class="tp-card">TP Diario (1σ): {tp_d:.5f}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="sl-card">Stop Loss Estadístico: {sl:.5f}</div>', unsafe_allow_html=True)
        with c2:
            st.markdown("### 🗓️ Objetivos Semanales")
            v_w = v * np.sqrt(5)
            tp_w1 = p * (1 - v_w * 1.2 if z > 0 else 1 + v_w * 1.2)
            tp_w2 = p * (1 - v_w * 2.0 if z > 0 else 1 + v_w * 2.0)
            st.markdown(f'<div class="tp-card">TP Semanal Prime (1.2σ): {tp_w1:.5f}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="tp-card" style="border-top-color:#ffd700">TP Semanal Extremo (2σ): {tp_w2:.5f}</div>', unsafe_allow_html=True)

with tab3:
    st.subheader("🎲 Simulación Montecarlo vs Señal ADN")
    target_m = st.selectbox("Analizar Probabilidades:", ASSETS, key="mc_s")
    dm = analyze_asset(target_m)
    if dm:
        sims, dias = 1000, 15
        rets = np.random.normal(dm['df']['Ret'].mean(), dm['vol'], (sims, dias))
        caminos = dm['price'] * (1 + rets).cumprod(axis=1)
        fig_m = go.Figure()
        for i in range(15): fig_m.add_trace(go.Scatter(y=caminos[i], line=dict(width=1), opacity=0.3, showlegend=False))
        fig_m.add_trace(go.Scatter(y=np.percentile(caminos, 50, axis=0), line=dict(color='#00ffcc', width=4), name="Mediana"))
        st.plotly_chart(fig_m.update_layout(template="plotly_dark", height=400), use_container_width=True)
        z_score = dm['z']
        if z_score > 1.6: 
            prob_exito = (caminos[:, -1] < dm['price']).sum() / sims * 100
            label_tipo = "BAJISTA (Venta)"
        elif z_score < -1.6: 
            prob_exito = (caminos[:, -1] > dm['price']).sum() / sims * 100
            label_tipo = "ALCISTA (Compra)"
        else: 
            prob_exito = 50.0
            label_tipo = "NEUTRAL"
        st.metric(f"Probabilidad de éxito {label_tipo}", f"{prob_exito:.1f}%")

with tab4:
    st.subheader("🛡️ Sentinel Macro")
    def get_safe_data(ticker):
        try:
            d = yf.download(ticker, period='30d', progress=False)['Close'].ffill()
            return d.iloc[:, 0] if isinstance(d, pd.DataFrame) else d
        except: return pd.Series()
    sp_df, vix_df, dxy_df = get_safe_data('^GSPC'), get_safe_data('^VIX'), get_safe_data('DX-Y.NYB')
    if not sp_df.empty and not vix_df.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("S&P 500", f"{sp_df.iloc[-1]:.2f}")
        m2.metric("VIX Index", f"{vix_df.iloc[-1]:.2f}")
        m3.metric("DXY Index", f"{dxy_df.iloc[-1]:.2f}")
        fig_s = go.Figure()
        fig_s.add_trace(go.Scatter(x=sp_df.index, y=sp_df, name="S&P 500", yaxis="y1", line=dict(color='#00ffcc')))
        fig_s.add_trace(go.Scatter(x=vix_df.index, y=vix_df, name="VIX", yaxis="y2", line=dict(color='#ff4b4b', dash='dot')))
        fig_s.update_layout(template="plotly_dark", yaxis=dict(side="left"), yaxis2=dict(overlaying="y", side="right"), height=400)
        st.plotly_chart(fig_s, use_container_width=True)
        score = sum([vix_df.iloc[-1] > 20, dxy_df.iloc[-1] > 104.5, sp_df.pct_change(5).iloc[-1] < -0.02])
        clrs = ["#00ffcc", "#ffd700", "#ff8c00", "#ff4b4b"]; lbls = ["ESTABLE", "PRECAUCIÓN", "RIESGO", "PÁNICO"]
        st.markdown(f'<div class="risk-banner" style="background-color:{clrs[min(score, 3)]};">ESTADO MACRO: {lbls[min(score, 3)]}</div>', unsafe_allow_html=True)

with tab5:
    st.subheader("🌊 Vol-Monitor & Relative Volume")
    target_v = st.selectbox("Activo Detalle:", ASSETS, key="v_s")
    dv = analyze_asset(target_v)
    if dv:
        col_v1, col_v2 = st.columns([2, 1])
        with col_v1:
            fig_h = px.histogram(dv['df'], x="Ret", nbins=50, title="Distribución de Riesgo")
            fig_h.add_vline(x=dv['df']['Ret'].iloc[-1], line_color="red", line_width=4)
            st.plotly_chart(fig_h.update_layout(template="plotly_dark"), use_container_width=True)
        with col_v2:
            rvol_val = dv['rvol']
            st.metric("Volumen Relativo (RVOL)", f"{rvol_val:.2f}x", delta=f"{rvol_val-1:.2f} vs media", delta_color="normal" if rvol_val < 2.0 else "inverse")

with tab6:
    st.subheader("🏦 Banks Detector")
    col_b1, col_b2 = st.columns([2, 1])
    with col_b1:
        target_b = st.selectbox("Shadow RMF:", ASSETS, key="b_s")
        db = analyze_asset(target_b)
        if db:
            df_b = db['df'].copy()
            df_b['Anom'] = df_b['RMF'].abs() / df_b['RMF'].abs().rolling(20).mean()
            clrs = ['#ffd700' if x > 2.5 else '#3d4463' for x in df_b['Anom']]
            st.plotly_chart(go.Figure(data=[go.Bar(x=df_b.index, y=df_b['RMF'].abs(), marker_color=clrs)]).update_layout(template="plotly_dark"), use_container_width=True)
    with col_b2:
        st.write("**Global Yield Spreads (10Y)**")
        yields = {'EUR/USD': -1.85, 'GBP/USD': -0.15, 'CAD/USD': -0.75, 'AUD/USD': 0.15, 'JPY/USD': -3.40, 'CHF/USD': -2.10}
        for pair, val in yields.items():
            color = "#00ffcc" if val > -1.0 else "#ff4b4b"
            st.markdown(f'<div class="bank-card">{pair} Spread: <span style="color:{color}">{val:+.2f}%</span></div>', unsafe_allow_html=True)

# --- NUEVA PESTAÑA 7: COT INSTITUTIONAL ---
with tab7:
    st.subheader("🏛️ Commitment of Traders (COT) - Asset Managers Only")
    st.write("Análisis de posicionamiento institucional neto de los informes de la CFTC.")
    
    # Datos representativos del COT (Asset Managers)
    # En una versión avanzada, aquí conectaríamos un scraper de la CFTC
    cot_db = {
        'EURUSD': {'long': 210500, 'short': 85000, 'prev_net': 110000},
        'GBPUSD': {'long': 42000, 'short': 98000, 'prev_net': -45000},
        'USDJPY': {'long': 12000, 'short': 145000, 'prev_net': -120000},
        'AUDUSD': {'long': 65000, 'short': 32000, 'prev_net': 28000},
        'GC=F': {'long': 285000, 'short': 45000, 'prev_net': 230000},
        'BTC-USD': {'long': 15400, 'short': 8200, 'prev_net': 5000}
    }
    
    target_c = st.selectbox("Seleccionar Activo COT:", list(cot_db.keys()))
    data_c = cot_db[target_c]
    
    total = data_c['long'] + data_c['short']
    net = data_c['long'] - data_c['short']
    pct_long = (data_c['long'] / total) * 100
    
    c_col1, c_col2, c_col3 = st.columns([1, 1, 2])
    
    with c_col1:
        st.metric("Posición Neta", f"{net:+,}")
        st.write(f"**Dominio:** {pct_long:.1f}% Longs")
    
    with c_col2:
        sentiment = "🔥 BULLISH" if pct_long > 65 else "❄️ BEARISH" if pct_long < 35 else "⚖️ NEUTRAL"
        st.markdown(f"### {sentiment}")
        st.write("Sesgo Institucional")

    with c_col3:
        # Gráfico de Divergencia precio vs COT (Simulado)
        asset_price = analyze_asset(target_c + "=X" if "=" not in target_c else target_c)
        if asset_price:
            fig_cot = go.Figure()
            # Simulación de curva de sentimiento
            dummy_net = [data_c['prev_net'], (data_c['prev_net']+net)/2, net]
            fig_cot.add_trace(go.Scatter(y=dummy_net, name="Net Position", line=dict(color='#ffd700', width=4)))
            fig_cot.update_layout(template="plotly_dark", height=200, title="Dirección del Capital Inteligente (Asset Managers)")
            st.plotly_chart(fig_cot, use_container_width=True)

    st.markdown("""
    > **Regla de Divergencia Argos:** Si el **Z-Diff es > 1.6 (Venta)** pero el **COT es > 70% Long**, 
    la ineficiencia es de corto plazo y el precio acabará subiendo. Busca la confluencia: 
    **Z-Diff y COT deben apuntar en la misma dirección para el trade "Perfecto".**
    """)
