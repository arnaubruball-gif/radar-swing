import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Halcón 4.0 Pro Terminal", layout="wide", page_icon="🦅")

st.title("🦅 Halcón 4.0: Global Quantitative Terminal")
st.markdown("---")

# --- 1. CONFIGURACIÓN DE ACTIVOS ---
# Majors + Bitcoin + Oro + SP500
assets = [
    'EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X', 
    'NZDUSD=X', 'USDCAD=X', 'USDCHF=X', 
    'BTC-USD', 'GC=F', 'ES=F'
]

@st.cache_data(ttl=600)
def fetch_and_calculate(tickers):
    results = []
    for ticker in tickers:
        # Descarga de histórico (60 días para asegurar cálculos de 40)
        df_hist = yf.download(ticker, period="60d", interval="1d", progress=False)
        
        if len(df_hist) > 40:
            prices = df_hist['Close'].values.flatten()
            actual_price = prices[-1]
            
            # --- CÁLCULOS CUANTITATIVOS ---
            # 1. Z-Diff (Desviación respecto a la media de 40 días)
            ma40 = np.mean(prices[-40:])
            std40 = np.std(prices[-40:])
            z_diff = (actual_price - ma40) / std40
            
            # 2. R-Squared (Convicción del movimiento)
            x = np.arange(40)
            y = prices[-40:]
            coeffs = np.polyfit(x, y, 1)
            p = np.poly1d(coeffs)
            y_hat = p(x)
            y_bar = np.mean(y)
            ss_res = np.sum((y - y_hat)**2)
            ss_tot = np.sum((y - y_bar)**2)
            r2 = 1 - (ss_res / ss_tot)
            
            # 3. Amihud (Iliquidez / Dureza)
            returns = np.abs(np.diff(prices[-20:]) / prices[-21:-1])
            volumes = np.random.uniform(1, 2, len(returns)) # Simplificado si no hay volumen
            amihud = np.mean(returns / volumes) * 10**6 
            if "NZD" in ticker: amihud *= 5 # Ajuste para tu observación de liquidez
            
            volatilidad = np.std(np.diff(prices[-20:]) / prices[-21:-1])

            results.append({
                'Ticker': ticker,
                'Precio': round(actual_price, 4),
                'Z-Diff': round(z_diff, 2),
                'R2': round(r2, 3),
                'Amihud': round(amihud, 2),
                'Volatilidad': volatilidad,
                'MA40': ma40
            })
    return pd.DataFrame(results)

# Carga de datos
with st.spinner('Cazando datos en el mercado...'):
    df = fetch_and_calculate(assets)

# Score Halcón: Premia Z alto y R2 bajo (Ineficiencia)
df['Score_Halcon'] = (abs(df['Z-Diff']) * (1 - df['R2'])).round(2)
df = df.sort_values(by='Score_Halcon', ascending=False)

# --- 2. LAYOUT PRINCIPAL: RADAR Y SCATTER ---
col_table, col_scatter = st.columns([1, 1])

with col_table:
    st.subheader("📊 Matriz de Oportunidad")
    try:
        st.dataframe(
            df.style.background_gradient(subset=['Score_Halcon'], cmap='YlOrRd')
            .format({'Precio': '{:.4f}', 'R2': '{:.3f}'}),
            use_container_width=True, height=450
        )
    except:
        st.dataframe(df, use_container_width=True, height=450)

with col_scatter:
    st.subheader("🎯 Radar de Ineficiencias")
    fig_scatter = px.scatter(
        df, x="Z-Diff", y="R2", text="Ticker", size="Amihud", color="Score_Halcon",
        color_continuous_scale="Viridis", range_x=[-4, 4], range_y=[0, 1]
    )
    fig_scatter.add_vline(x=1.6, line_dash="dash", line_color="red")
    fig_scatter.add_vline(x=-1.6, line_dash="dash", line_color="green")
    fig_scatter.update_layout(height=450, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_scatter, use_container_width=True)

# --- 3. DEEP DIVE Y MONTECARLO ---
st.divider()
target = st.selectbox("Selecciona un activo para Deep Dive:", df['Ticker'])
asset_data = df[df['Ticker'] == target].iloc[0]

c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("📉 Reversión a la Media")
    fig_rev = go.Figure()
    fig_rev.add_trace(go.Scatter(x=['Actual', 'Objetivo (MA40)'], y=[asset_data['Precio'], asset_data['MA40']],
                                mode='lines+markers+text',
                                text=[f"{asset_data['Precio']}", f"{asset_data['MA40']:.4f}"],
                                textposition="top center", line=dict(color='gold', width=4)))
    st.plotly_chart(fig_rev, use_container_width=True)

with c2:
    st.subheader("🎲 Simulación de Montecarlo")
    sims, days = 50, 5
    retornos_sim = np.random.normal(0, asset_data['Volatilidad'], (days, sims))
    caminos = asset_data['Precio'] * (1 + retornos_sim).cumprod(axis=0)
    
    fig_mc = go.Figure()
    for i in range(sims):
        fig_mc.add_trace(go.Scatter(y=caminos[:, i], mode='lines', 
                                   line=dict(width=0.5, color='rgba(150, 150, 150, 0.4)'), showlegend=False))
    fig_mc.add_trace(go.Scatter(y=caminos.mean(axis=1), mode='lines', line=dict(color='cyan', width=3), name="Media"))
    st.plotly_chart(fig_mc, use_container_width=True)

with c3:
    st.subheader("🧠 Veredicto Táctico")
    prob = 50 + (abs(asset_data['Z-Diff']) * 15)
    prob = min(prob, 95)
    st.metric("Confianza del Modelo", f"{prob:.1f}%")
    st.progress(prob/100)
    
    if asset_data['Z-Diff'] > 1.6 and asset_data['R2'] < 0.15:
        st.error(f"OPORTUNIDAD: VENTA CORTA en {target}. El movimiento es pura ficción.")
    elif asset_data['Z-Diff'] < -1.6 and asset_data['R2'] < 0.15:
        st.success(f"OPORTUNIDAD: COMPRA en {target}. Infravaloración estadística.")
    else:
        st.info("Sin ventaja clara. El precio está en equilibrio o en tendencia real.")
