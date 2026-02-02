import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# --- 1. CONFIGURACIÓN DE ÉLITE ---
st.set_page_config(page_title="Halcón 4.0 - Hurst & Volume", layout="wide", page_icon="🦅")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3d4463; }
    </style>
    """, unsafe_allow_html=True)

st.title("🦅 Halcón de Guerra 4.0 | Pro Terminal")
st.write("Análisis Fractal (Hurst), Ineficiencias Estructurales y Presión de Volumen")

# --- 2. MOTOR MATEMÁTICO AVANZADO ---

def calcular_hurst(ts):
    """Mide la memoria del mercado: <0.5 Reversión, >0.5 Tendencia"""
    if len(ts) < 30: return 0.5
    lags = range(2, 20)
    tau = [np.sqrt(np.std(np.subtract(ts[lag:], ts[:-lag]))) for lag in lags]
    poly = np.polyfit(np.log(lags), np.log(tau), 1)
    return poly[0] * 2.0

@st.cache_data(ttl=600)
def fetch_and_analyze():
    ASSETS = {
        'EUR/USD': 'EURUSD=X', 'GBP/USD': 'GBPUSD=X', 'AUD/USD': 'AUDUSD=X',
        'NZD/USD': 'NZDUSD=X', 'USD/JPY': 'JPY=X', 'USD/CHF': 'CHF=X',
        'BITCOIN': 'BTC-USD', 'ORO (Spot)': 'GC=F', 'S&P 500': '^SPX'
    }
    
    all_results = []
    plot_data = {}

    for name, ticker in ASSETS.items():
        try:
            df = yf.download(ticker, period='100d', interval='1d', progress=False)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            # Cálculos Base
            prices = df['Close'].values.flatten().astype(float)
            volumes = df['Volume'].values.flatten().astype(float)
            
            # 1. Hurst (50 días)
            h_val = calcular_hurst(prices[-50:])
            
            # 2. R2 Dinámico (30 días)
            rets = np.diff(prices[-31:]) / prices[-31:-1]
            x = np.arange(30)
            y = prices[-30:]
            coeffs = np.polyfit(x, y, 1)
            y_hat = np.poly1d(coeffs)(x)
            r2 = 1 - (np.sum((y - y_hat)**2) / np.sum((y - np.mean(y))**2))
            
            # 3. Z-Diff (40 días)
            ma40 = np.mean(prices[-40:])
            z_val = (prices[-1] - ma40) / (np.std(prices[-40:]) + 1e-10)
            
            # 4. Volumen Relativo (Ficción)
            vol_rel = volumes[-1] / (np.mean(volumes[-20:]) + 1e-10) if volumes[-1] > 0 else 1.0
            
            # Veredicto Lógica Halcón
            veredicto = "⚪ NEUTRAL"
            confianza = "Baja"
            
            # REVERSIÓN (Hurst < 0.45)
            if h_val < 0.48:
                if z_val > 1.6 and vol_rel < 1.0: 
                    veredicto = "🚨 VENTA (Ficción)"
                    confianza = "Alta"
                elif z_val < -1.6 and vol_rel < 1.0: 
                    veredicto = "🟢 COMPRA (Oportunidad)"
                    confianza = "Alta"
            # TENDENCIA (Hurst > 0.55)
            elif h_val > 0.52 and r2 > 0.3:
                veredicto = "💎 TENDENCIA REAL"
                confianza = "Institucional"

            all_results.append({
                'Activo': name, 'Precio': round(prices[-1], 4), 
                'Hurst': round(h_val, 2), 'R2': round(r2, 2),
                'Z-Diff': round(z_val, 2), 'Vol_Rel': round(vol_rel, 2),
                'Veredicto': veredicto, 'Confianza': confianza
            })
            plot_data[name] = df
        except: continue
        
    return pd.DataFrame(all_results), plot_data

# --- 3. PANEL VISUAL ---

tab1, tab2 = st.tabs(["📊 Radar de Ineficiencias", "🎲 Proyección Probabilística"])

df_res, all_plots = fetch_and_analyze()

with tab1:
    if not df_res.empty:
        st.subheader("Matriz de Inteligencia Fractal")
        
        def style_v(val):
            if 'VENTA' in val: return 'background-color: #441111; color: #ff4b4b; font-weight: bold'
            if 'COMPRA' in val: return 'background-color: #114433; color: #00ffcc; font-weight: bold'
            if 'TENDENCIA' in val: return 'background-color: #112244; color: #1c83e1; font-weight: bold'
            return ''
        
        st.dataframe(df_res.style.applymap(style_v, subset=['Veredicto']), use_container_width=True)
        
        # Gráfico Scatter de Ineficiencia
        st.write("### 🎯 Mapa de Acción Halcón")
        fig_scatter = px.scatter(df_res, x="Z-Diff", y="Hurst", size="Vol_Rel", 
                                 text="Activo", color="Hurst", 
                                 color_continuous_scale="RdYlGn_r",
                                 range_x=[-4,4], range_y=[0.3, 0.7])
        fig_scatter.add_hline(y=0.5, line_dash="dash", line_color="white")
        fig_scatter.update_layout(template="plotly_dark", height=450)
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.warning("No se pudieron obtener datos. Reintenta en unos segundos.")

with tab2:
    if not df_res.empty:
        selected = st.selectbox("Seleccionar Activo para Simulación:", df_res['Activo'].unique())
        asset_row = df_res[df_res['Activo'] == selected].iloc[0]
        df_asset = all_plots[selected]
        
        # Montecarlo Basado en Volatilidad Real
        returns = df_asset['Close'].pct_change().dropna()
        vol = returns.tail(20).std()
        last_price = asset_row['Precio']
        
        sims, days = 200, 5
        mc_results = np.zeros((days + 1, sims))
        mc_results[0] = last_price
        for t in range(1, days + 1):
            mc_results[t] = mc_results[t-1] * (1 + np.random.normal(0, vol, sims))
        
        p10 = np.percentile(mc_results, 10, axis=1)
        p50 = np.percentile(mc_results, 50, axis=1)
        p90 = np.percentile(mc_results, 90, axis=1)
        
        # Visualización Pro
        fig_mc = go.Figure()
        fig_mc.add_trace(go.Scatter(x=list(range(6))+list(range(6))[::-1], 
                                    y=list(p90)+list(p10[::-1]), 
                                    fill='toself', fillcolor='rgba(0,176,246,0.2)', 
                                    line=dict(color='rgba(255,255,255,0)'), name="Nube 80%"))
        fig_mc.add_trace(go.Scatter(x=list(range(6)), y=p50, line=dict(color='cyan', width=3), name="Tendencia Probable"))
        fig_mc.update_layout(title=f"Proyección Montecarlo 5 Días: {selected}", template="plotly_dark", height=400)
        st.plotly_chart(fig_mc, use_container_width=True)
        
        # Métricas de salida
        c1, c2, c3 = st.columns(3)
        c1.metric("Volumen Relativo", asset_row['Vol_Rel'], help="< 1.0 = Movimiento sin gasolina")
        c2.metric("Hurst", asset_row['Hurst'], help="< 0.5 = Elástico, > 0.5 = Tren")
        c3.metric("R2 (Convicción)", asset_row['R2'])

# --- SIDEBAR ---
st.sidebar.markdown(f"""
### 🧠 Manual Halcón 4.0
**1. El Filtro Hurst:**
* Si **Hurst < 0.48**, el mercado es antipersistente. Confía en el **Z-Diff** para buscar reversiones.
* Si **Hurst > 0.52**, el mercado tiene memoria. No busques techos ni suelos.

**2. El Filtro Volumen:**
* Si **Vol_Rel < 1.0** y el precio está en un extremo, es **Ficción**. El institucional no está apoyando el movimiento.

**3. Z-Diff:**
* Busca extremos > 1.6 o < -1.6 para trades de alta probabilidad.
""")

if st.sidebar.button("🗑️ Limpiar Caché"):
    st.cache_data.clear()
    st.rerun()
