import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="JDetector- Institutional Edge", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #000000; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3d4463; }
    .tp-card { background-color: #161b22; padding: 20px; border-radius: 10px; border-top: 4px solid #00ffcc; text-align: center; margin-bottom:10px; }
    .sl-card { background-color: #161b22; padding: 20px; border-radius: 10px; border-top: 4px solid #ff4b4b; text-align: center; }
    .bank-card { background-color: #0e1117; padding: 10px; border-left: 5px solid #ffd700; margin-bottom: 5px; font-size: 0.85rem; }
    .risk-banner { padding: 20px; border-radius: 10px; text-align: center; font-weight: bold; font-size: 1.5rem; margin-top: 10px; color: black; }
    .cot-card { background-color: #1c1c1c; padding: 15px; border-radius: 10px; border: 1px solid #ffd700; }
    .trigger-card { background-color: #12141d; padding: 15px; border-radius: 10px; border: 1px solid #30363d; margin-top: 10px; }
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

# --- 4. PESTAÑAS ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📊 ADN", "🎯 Ejecución Pro", "🎲 Montecarlo", "🛡️ Sentinel", 
    "🌊 Vol-Monitor", "🏦 Banks Detector", "🏛️ COT Insight", "💰 RIESGO"
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
    st.subheader("🎯 Auditoría de Señales Recientes")
    target_e = st.selectbox("Analizar historial de:", ASSETS, key="exec_s")
    de = analyze_asset(target_e)
    
    if de:
        df_h = de['df'].tail(5).copy() # Miramos los últimos 5 días
        
        # Calculamos los estados de los últimos días
        # Necesitamos recalcular el Z-diff histórico para la tabla
        diff_hist = de['df']['Ret'].rolling(40).sum() - de['df']['RMF'].pct_change().rolling(40).sum()
        z_hist = (diff_hist - diff_hist.rolling(40).mean()) / (diff_hist.rolling(40).std() + 1e-10)
        
        df_h['Z-Diff'] = z_hist.tail(5)
        df_h['ADN_Signal'] = df_h['Z-Diff'].apply(lambda x: "🟢 COMPRA" if x < -1.6 else ("🚨 VENTA" if x > 1.6 else "⚪ Neutral"))
        
        # Formateamos la tabla para que sea legible
        audit_df = df_h[['Close', 'Z-Diff', 'ADN_Signal']].copy()
        audit_df.index = audit_df.index.strftime('%Y-%m-%d')
        audit_df['R2'] = de['df']['R2_Dynamic'].tail(5)
        
        st.write("### 📅 Registro de los últimos 5 días")
        st.table(audit_df.style.format({'Close': '{:.5f}', 'Z-Diff': '{:.2f}', 'R2': '{:.3f}'}))
        
        c1, c2 = st.columns(2)
        with c1:
            st.info("""
            **Guía de Decisión Manual:**
            1. **Acumulación:** ¿Lleva 2 o 3 días seguidos en 🟢 o 🚨? (Indica presión institucional sostenida).
            2. **R2 Creciente:** Si el R2 sube mientras el ADN da señal, la probabilidad es mayor.
            3. **Confirmación Visual:** Mira en el gráfico si el precio ha respetado la EMA21.
            """)
        
        with c2:
            # Añadimos un gráfico pequeño de la evolución del Z-Diff para ver la "curva"
            fig_z = px.line(z_hist.tail(15), title="Evolución de Presión ADN (15d)")
            fig_z.add_hline(y=1.6, line_dash="dash", line_color="red")
            fig_z.add_hline(y=-1.6, line_dash="dash", line_color="green")
            fig_z.update_layout(template="plotly_dark", height=250, showlegend=False)
            st.plotly_chart(fig_z, use_container_width=True)

        st.divider()
        st.markdown("### 📏 Niveles de Referencia para hoy")
        p, v = de['price'], de['vol']
        sl_est = p * (1 - v*2.5) if de['z'] < 0 else p * (1 + v*2.5)
        st.write(f"**Precio Actual:** {p:.5f} | **Stop Loss Sugerido (Estructural):** {sl_est:.5f}")

with tab3:
    st.subheader("🎲 Simulación Montecarlo (Proyección 30 días)")
    target_m = st.selectbox("Analizar Probabilidades:", ASSETS, key="mc_s")
    dm = analyze_asset(target_m)
    if dm:
        sims, dias = 1000, 30
        rets = np.random.normal(dm['df']['Ret'].mean(), dm['vol'], (sims, dias))
        caminos = dm['price'] * (1 + rets).cumprod(axis=1)
        fig_m = go.Figure()
        for i in range(15): fig_m.add_trace(go.Scatter(y=caminos[i], line=dict(width=1), opacity=0.3, showlegend=False))
        fig_m.add_trace(go.Scatter(y=np.percentile(caminos, 50, axis=0), line=dict(color='#00ffcc', width=4), name="Mediana"))
        st.plotly_chart(fig_m.update_layout(template="plotly_dark", height=400), use_container_width=True)
        z_score = dm['z']
        prob = (caminos[:, -1] < dm['price']).sum()/sims*100 if z_score > 0 else (caminos[:, -1] > dm['price']).sum()/sims*100
        st.metric(f"Probabilidad de éxito", f"{prob:.1f}%")

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
            st.metric("Volumen Relativo (RVOL)", f"{rvol_val:.2f}x", delta=f"{rvol_val-1:.2f} vs media")

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

with tab7:
    st.subheader("🏛️ COT Insight: Asset Managers Sentiment")
    cot_db = {
        'USD (Dólar Index)': {'long': 45000, 'short': 12000, 'prev_net': 28000, 'bias': 'Bullish'},
        'EUR (Euro)': {'long': 210500, 'short': 85000, 'prev_net': 110000, 'bias': 'Extreme Bullish'},
        'GBP (Libra)': {'long': 42000, 'short': 98000, 'prev_net': -45000, 'bias': 'Bearish'},
        'JPY (Yen)': {'long': 12000, 'short': 145000, 'prev_net': -120000, 'bias': 'Extreme Bearish'},
        'AUD (Australiano)': {'long': 65000, 'short': 32000, 'prev_net': 28000, 'bias': 'Bullish'},
        'CAD (Canadiense)': {'long': 25000, 'short': 45000, 'prev_net': -15000, 'bias': 'Neutral-Bearish'},
        'BTC (Bitcoin)': {'long': 15400, 'short': 8200, 'prev_net': 5000, 'bias': 'Bullish'}
    }
    selected_curr = st.selectbox("Seleccionar Divisa:", list(cot_db.keys()))
    data_c = cot_db[selected_curr]
    total = data_c['long'] + data_c['short']
    net_actual = data_c['long'] - data_c['short']
    cambio_neto = net_actual - data_c['prev_net']
    pct_long = (data_c['long'] / total) * 100
    pct_short = (data_c['short'] / total) * 100
    col_c1, col_c2, col_c3 = st.columns([1, 1, 1])
    with col_c1: st.metric("Posición Neta", f"{net_actual:+,}", delta=f"{cambio_neto:+,}")
    with col_c2: st.metric("Dominio Long", f"{pct_long:.1f}%", delta=f"{data_c['bias']}")
    with col_c3:
        fig_sent = go.Figure(go.Bar(x=[pct_long, pct_short], y=['L', 'S'], orientation='h', marker_color=['#00ffcc', '#ff4b4b']))
        st.plotly_chart(fig_sent.update_layout(template="plotly_dark", height=150, margin=dict(l=0,r=0,t=0,b=0)), use_container_width=True)

with tab8:
    st.subheader("💰 Gestión de Riesgo Swing (Corregida)")
    capital = st.number_input("Capital Cuenta ($):", value=1000)
    riesgo_p = st.slider("Riesgo por trade (%):", 0.1, 2.0, 1.0)
    target_r = st.selectbox("Activo:", ASSETS, key="risk_sel")
    dr = analyze_asset(target_r)
    
    if dr:
        r_usd = capital * (riesgo_p / 100)
        p, v = dr['price'], dr['vol']
        
        # Stop Loss a 2.5 desviaciones estándar
        dist_sl_precio = p * (v * 2.5) 
        
        # AJUSTE DE LOTAJE SEGÚN ACTIVO
        if "USD" in target_r and "BTC" not in target_r: # Es Forex (EURUSD, GBPUSD, etc)
            # 1 lote estándar = 100,000 unidades. 
            # El riesgo por lote es dist_sl_precio * 100,000
            lotaje_sugerido = r_usd / (dist_sl_precio * 100000)
        elif "BTC" in target_r or "GC=F" in target_r: # Crypto u Oro
            lotaje_sugerido = r_usd / dist_sl_precio
        else: # Índices u otros
            lotaje_sugerido = r_usd / (dist_sl_precio * 10)

        st.markdown(f"""
        <div style="background-color:#1e2130; padding:20px; border-radius:10px; border-left: 5px solid #ff4b4b;">
        <h3>Plan de Trading Realista</h3>
        Dinero en riesgo: <b>${r_usd:.2f}</b><br>
        Distancia Stop Loss: <b>{dist_sl_precio:.5f} puntos</b><br>
        Lotaje sugerido: <h1 style="color:#00ffcc;">{lotaje_sugerido:.3f} Lotes</h1>
        <small>En EURUSD, 0.01 lotes es lo mínimo (micro-lote).</small>
        </div>
        """, unsafe_allow_html=True)
