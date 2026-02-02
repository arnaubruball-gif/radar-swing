import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# --- 1. CONFIGURACIÓN DE ÉLITE ---
st.set_page_config(page_title="Halcón 4.0 - Full Market Terminal", layout="wide")

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

@st.cache_data(ttl=600)
def analyze_asset(ticker):
    try:
        df = yf.download(ticker, period='150d', interval='1d', progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # --- Lógica Original Matriz ---
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
        
        # Amihud (Iliquidez)
        amihud = (df['Ret'].abs() / (df['RMF'].replace(0, np.nan) / 1e6)).fillna(df['Ret'].abs() * 100).rolling(20).mean().iloc[-1]
        
        # Hurst y Volatilidad
        hurst = calcular_hurst(df['Close'].values.flatten()[-50:])
        vol = df['Ret'].tail(30).std()
        drift = df['Ret'].tail(7).mean() 
        
        return {
            'df': df, 'price': df['Close'].iloc[-1], 'z': z_val, 
            'r2': df['R2_Dynamic'].iloc[-1], 'hurst': hurst, 
            'vol': vol, 'drift': drift, 'amihud': amihud
        }
    except: return None

# --- 3. PANEL DE CONTROL ---
st.title("🦅 Halcón de Guerra 4.0 | Full Market Intelligence")

tab1, tab2, tab3 = st.tabs(["📊 Matriz ADN Completa", "🦅 Radar Fractal", "🎲 Montecarlo de Cruces"])

# --- LISTA EXPANDIDA DE ACTIVOS ---
ASSETS = {
    'MAJORS': ['EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'NZDUSD=X', 'USDJPY=X', 'USDCHF=X', 'USDCAD=X'],
    'CROSSES': ['EURGBP=X', 'EURJPY=X', 'GBPJPY=X', 'EURAUD=X', 'GBPAUD=X', 'AUDJPY=X', 'CHFJPY=X'],
    'OTHERS': ['BTC-USD', 'ETH-USD', 'GC=F', 'SI=F', '^SPX', '^IXIC', '^FTSE']
}

all_tickers = ASSETS['MAJORS'] + ASSETS['CROSSES'] + ASSETS['OTHERS']

with tab1:
    st.subheader("Ineficiencias en Pares Mayores, Cruces y Commodities")
    
    if st.button('📡 ESCANEAR TODOS LOS MERCADOS'):
        results = []
        with st.spinner('Analizando liquidez y flujo...'):
            for t in all_tickers:
                data = analyze_asset(t)
                if data:
                    v = "⚪ NEUTRAL"
                    if data['r2'] < 0.10:
                        if data['z'] > 1.6: v = "🚨 VENTA (Ficción)"
                        elif data['z'] < -1.6: v = "🟢 COMPRA (Oportunidad)"
                    elif data['r2'] > 0.30: v = "💎 TENDENCIA REAL"
                    
                    results.append([
                        t.replace('=X',''), 
                        f"{data['price']:.4f}", 
                        round(data['r2'],3), 
                        round(data['z'],2), 
                        round(data['amihud'], 4),
                        v
                    ])
        
        df_res = pd.DataFrame(results, columns=['Activo', 'Precio', 'R2', 'Z-Diff', 'Amihud', 'Veredicto'])
        
        def style_v(val):
            if 'VENTA' in val: return 'background-color: #441111; color: #ff4b4b; font-weight: bold'
            if 'COMPRA' in val: return 'background-color: #114433; color: #00ffcc; font-weight: bold'
            if 'TENDENCIA' in val: return 'background-color: #112244; color: #1c83e1; font-weight: bold'
            return ''
        
        st.dataframe(df_res.style.applymap(style_v, subset=['Veredicto']), use_container_width=True)
    else:
        st.info("Haz clic en el botón superior para cargar la matriz completa.")

with tab2:
    st.subheader("Mapa de Memoria del Mercado (Hurst vs Z-Diff)")
    h_data = []
    with st.spinner('Calculando dimensiones fractales...'):
        for t in all_tickers:
            d = analyze_asset(t)
            if d: h_data.append({'Activo': t.replace('=X',''), 'Hurst': d['hurst'], 'Z-Diff': d['z']})
    
    if h_data:
        df_h = pd.DataFrame(h_data)
        fig_h = px.scatter(df_h, x="Z-Diff", y="Hurst", text="Activo", color="Hurst", 
                           color_continuous_scale="RdYlGn_r", range_x=[-4, 4], range_y=[0.3, 0.7])
        fig_h.add_hline(y=0.5, line_dash="dash", line_color="white", annotation_text="Eficiencia (Random Walk)")
        fig_h.update_layout(template="plotly_dark", height=500)
        st.plotly_chart(fig_h, use_container_width=True)
        
        

with tab3:
    st.subheader("Simulación Direccional (Especial para Cruces)")
    c1, c2 = st.columns([1, 3])
    with c1:
        cross_ticker = st.text_input("Introduce el Cruce (ej: EURGBP=X, CADJPY=X):", "EURGBP=X")
        sim_days = st.slider("Días de proyección", 5, 20, 10)
        
    cross_data = analyze_asset(cross_ticker)
    
    if cross_data:
        mu = cross_data['drift'] 
        sigma = cross_data['vol']
        last_p = cross_data['price']
        
        sims = 250
        paths = np.zeros((sim_days + 1, sims))
        paths[0] = last_p
        
        for t in range(1, sim_days + 1):
            # Modelo Direccional Sensible
            paths[t] = paths[t-1] * (1 + np.random.normal(mu, sigma, sims))
        
        p10, p50, p90 = np.percentile(paths, 10, axis=1), np.percentile(paths, 50, axis=1), np.percentile(paths, 90, axis=1)
        
        with c2:
            fig_mc = go.Figure()
            fig_mc.add_trace(go.Scatter(x=list(range(sim_days+1))+list(range(sim_days+1))[::-1], y=list(p90)+list(p10[::-1]), 
                                        fill='toself', fillcolor='rgba(0,255,150,0.1)', line=dict(color='rgba(255,255,255,0)'), name="Rango Probable"))
            fig_mc.add_trace(go.Scatter(x=list(range(sim_days+1)), y=p50, line=dict(color='#00ffcc', width=4), name="Inercia (Drift)"))
            fig_mc.update_layout(template="plotly_dark", height=500, title=f"Proyección de {cross_ticker}")
            st.plotly_chart(fig_mc, use_container_width=True)
            
            
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Drift (7d)", f"{mu*100:.4f}%")
        m2.metric("Z-Diff", round(cross_data['z'], 2))
        m3.metric("Hurst", round(cross_data['hurst'], 2))
    else:
        st.error("Introduce un ticker válido.")
    # ... (dentro de la lógica del Montecarlo en Tab 3)
        
        # Calculamos Niveles de Salida para dormir tranquilo
        tp_est = p50[-1]  # Regreso a la media (Eje Central)
        sl_panic = p10[-1] - (abs(p50[-1] - p10[-1]) * 0.5) # 5% de probabilidad extrema
        
        st.write(f"### 🛡️ Niveles Blindados para la Noticia ({cross_ticker})")
        c_tp, c_sl = st.columns(2)
        
        # Si vas a vender GBPAUD porque el AUD está fuerte:
        if cross_data['z'] > 0: # Caso de sobrecompra
            c_tp.metric("TAKE PROFIT (Media)", f"{tp_est:.4f}")
            c_sl.metric("STOP LOSS (Pánico)", f"{p90[-1]:.4f}")
        else: # Caso de sobreventa (como tu GBPAUD actual)
            c_tp.metric("TAKE PROFIT (Media)", f"{tp_est:.4f}")
            c_sl.metric("STOP LOSS (Pánico)", f"{sl_panic:.4f}")

        # Dibujamos en el gráfico
        fig_mc.add_hline(y=tp_est, line_dash="dot", line_color="green", annotation_text="TP (Media)")
        fig_mc.add_hline(y=sl_panic, line_dash="dot", line_color="red", annotation_text="SL (Pánico)")

st.sidebar.markdown("""
### 🧠 Guía de Operación
1. **Filtro Matriz**: Busca activos en **VENTA** o **COMPRA** donde el R2 sea muy bajo (<0.10).
2. **Confirmación Fractal**: Si el Z-Diff es extremo, verifica en el Radar que el **Hurst sea < 0.50**. Esto confirma que el precio tiende a volver.
3. **Cruces**: Usa la simulación para ver si la inercia (Drift) está a tu favor o en contra.
""")
