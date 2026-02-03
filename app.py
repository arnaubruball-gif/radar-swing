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

# --- 3. SIDEBAR: MANUAL DE OPERACIONES ---
with st.sidebar:
    st.title("👁️ ARGOS SYSTEM")
    st.markdown("---")
    st.subheader("Guía de Operación")
    st.info("**1. Matriz ADN:** Busca $R^2 < 0.10$ y $Z-Diff > 1.6$. Es la señal de 'Ficción'.")
    st.info("**2. Radar Fractal:** Confirma que el Hurst sea $< 0.45$. Esto asegura reversión.")
    st.info("**3. Vol-Monitor:** Si la volatilidad toca el 'Umbral de Pánico', el giro será violento.")
    st.warning("**Riesgo:** Si Sentinel marca > 75%, el mercado es irracional. Reduce el apalancamiento.")
    st.markdown("---")
    st.caption("Argos Terminal | v1.6")

# --- 4. PANEL DE CONTROL ARGOS ---
st.title("👁️ ARGOS | Full Market Terminal")

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

# ... (Tabs 1 a 4 se mantienen con su lógica original) ...

with tab1:
    st.subheader("Ineficiencias Detectadas")
    if st.button('📡 ESCANEAR MERCADOS'):
        results = []
        with st.spinner('Procesando flujo...'):
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
        cross_ticker = st.text_input("Ticker:", "AUDUSD=X")
        sim_days = st.slider("Días", 5, 20, 10)
    cross_data = analyze_asset(cross_ticker)
    if cross_data:
        paths = np.zeros((sim_days + 1, 250))
        paths[0] = cross_data['price']
        for t in range(1, sim_days + 1):
            paths[t] = paths[t-1] * (1 + np.random.normal(cross_data['drift'], cross_data['vol'], 250))
        p50 = np.percentile(paths, 50, axis=1)
        with c2:
            fig_mc = go.Figure()
            fig_mc.add_trace(go.Scatter(x=list(range(sim_days+1)), y=p50, line=dict(color='#00ffcc', width=4), name="Drift Argos"))
            fig_mc.update_layout(template="plotly_dark", height=500)
            st.plotly_chart(fig_mc, use_container_width=True)

with tab4:
    st.subheader("🛡️ Sentinel: Riesgo Global")
    vix_v, g_spx, dxy_m, r_score, vix_df = fetch_risk_metrics()
    k1, k2, k3 = st.columns(3)
    k1.metric("SCORE RIESGO", f"{r_score}%", "PELIGRO" if r_score >= 75 else "ESTABLE")
    k2.metric("VIX", f"{vix_v:.2f}")
    k3.metric("MOMENTUM DXY", f"{dxy_m:.2f}%")
    st.plotly_chart(px.area(vix_df, y='Close', title="VIX Monitor").update_layout(template="plotly_dark", height=300), use_container_width=True)

with tab5:
    st.subheader("🌊 Vol-Monitor & Veredicto Final")
    vol_ticker = st.text_input("Activo para Análisis Profundo:", "GBPUSD=X")
    vol_data = analyze_asset(vol_ticker)
    
    if vol_data:
        # --- VEREDICTO FINAL ARGOS ---
        st.markdown('<div class="veredicto-box">', unsafe_allow_html=True)
        st.write("### 🧠 Veredicto de Inteligencia ARGOS")
        
        # Lógica de Veredicto
        h = vol_data['hurst']
        z = vol_data['z']
        r2 = vol_data['r2']
        
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            if h < 0.45 and abs(z) > 1.6 and r2 < 0.15:
                st.error(f"🚨 ALERTA DE REVERSIÓN INMINENTE ({'VENTA' if z > 0 else 'COMPRA'})")
                st.write("El precio está en una burbuja fractal. El flujo de dinero no apoya este nivel y la memoria del mercado exige un regreso a la media.")
            elif r2 > 0.40:
                st.info("💎 TENDENCIA INSTITUCIONAL DETECTADA")
                st.write("Movimiento respaldado por volumen real. No busques el giro; el flujo de dinero está empujando el precio con convicción.")
            else:
                st.success("⚪ RÉGIMEN NEUTRAL / RUIDO")
                st.write("No hay una ventaja estadística clara. El mercado está en equilibrio o esperando un catalizador.")
        
        with col_v2:
            st.write(f"**Confianza Estadística:** {int((1-r2)*100)}%")
            st.write(f"**Nivel de Memoria (Hurst):** {h:.2f}")
            st.write(f"**Desviación (Z-Score):** {z:.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # --- GRÁFICOS DE VOLATILIDAD ---
        st.divider()
        df_vol = vol_data['df'].copy()
        df_vol['Vol_Mean'] = df_vol['Ret'].rolling(20).std()
        df_vol['Upper_Vol'] = df_vol['Vol_Mean'].rolling(20).mean() + (df_vol['Vol_Mean'].rolling(20).std() * 2)
        
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Scatter(x=df_vol.index, y=df_vol['Vol_Mean'], name="Volatilidad Actual", line=dict(color='#00ffcc')))
        fig_vol.add_trace(go.Scatter(x=df_vol.index, y=df_vol['Upper_Vol'], name="Umbral Crítico", line=dict(dash='dash', color='red')))
        fig_vol.update_layout(template="plotly_dark", title="Régimen de Volatilidad", height=400)
        st.plotly_chart(fig_vol, use_container_width=True)
    else:
        st.info("Introduce un ticker para generar el veredicto.")
