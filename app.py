import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px

# --- 1. CONFIGURACIÓN DE PÁGINA (Debe ser el primer comando de Streamlit) ---
st.set_page_config(page_title="Halcón 4.0 Pro Terminal", layout="wide", page_icon="🦅")

# --- 2. MOTOR DE CÁLCULO CUANTITATIVO ---
@st.cache_data(ttl=600)
def fetch_and_calculate(tickers):
    results = []
    for ticker in tickers:
        try:
            # Descarga de histórico (65 días para ventana de 40)
            df_hist = yf.download(ticker, period="65d", interval="1d", progress=False)
            
            # Limpieza de Multi-index y NaNs (Yahoo Finance Compatibility)
            if isinstance(df_hist.columns, pd.MultiIndex):
                df_hist.columns = df_hist.columns.get_level_values(0)
            df_hist = df_hist.dropna()

            if len(df_hist) > 41:
                prices = df_hist['Close'].values.flatten().astype(float)
                actual_price = prices[-1]
                
                # --- CÁLCULOS DE ADN ---
                window = prices[-40:]
                ma40 = np.mean(window)
                std40 = np.std(window)
                z_diff = (actual_price - ma40) / std40 if std40 != 0 else 0
                
                # R-Squared (Convicción del movimiento)
                x = np.arange(40)
                coeffs = np.polyfit(x, window, 1)
                p = np.poly1d(coeffs)
                y_hat = p(x)
                ss_res = np.sum((window - y_hat)**2)
                ss_tot = np.sum((window - np.mean(window))**2)
                r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
                
                # Amihud (Iliquidez / Dureza del mercado)
                prices_ami = prices[-21:]
                returns_ami = np.abs(np.diff(prices_ami)) / prices_ami[:-1]
                amihud = np.mean(returns_ami) * 10**6
                
                # Ajustes específicos de mercado
                if "NZD" in ticker: amihud *= 5
                
                volatilidad = np.std(returns_ami)

                results.append({
                    'Ticker': ticker,
                    'Precio': round(actual_price, 4),
                    'Z-Diff': round(z_diff, 2),
                    'R2': round(r2, 3),
                    'Amihud': round(amihud, 2),
                    'Volatilidad': volatilidad,
                    'MA40': ma40
                })
        except Exception as e:
            st.error(f"Error en {ticker}: {e}")
            continue
    return pd.DataFrame(results)

# --- 3. INTERFAZ DE USUARIO ---
st.title("🦅 Halcón 4.0: Global Quantitative Terminal")
st.markdown("Dashboard de alta frecuencia para detección de ineficiencias estadísticas.")

# Definición de activos (Forex Majors, Crypto, Commodities, Index)
assets = [
    'EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X', 
    'NZDUSD=X', 'USDCAD=X', 'USDCHF=X', 
    'BTC-USD', 'GC=F', 'ES=F'
]

with st.spinner('Escaneando el ecosistema financiero...'):
    df = fetch_and_calculate(assets)

# Cálculo de prioridad (Score Halcón)
df['Score_Halcon'] = (abs(df['Z-Diff']) * (1 - df['R2'])).round(2)
df = df.sort_values(by='Score_Halcon', ascending=False)

# --- 4. VISUALIZACIÓN: RADAR Y SCATTER ---
col_table, col_scatter = st.columns([1, 1])

with col_table:
    st.subheader("📊 Matriz de Oportunidad")
    # Intentamos aplicar estilos, si falla por falta de matplotlib, mostramos tabla simple
    try:
        st.dataframe(
            df.style.background_gradient(subset=['Score_Halcon'], cmap='YlOrRd')
            .format({'Precio': '{:.4f}', 'R2': '{:.3f}'}),
            use_container_width=True, height=400
        )
    except:
        st.dataframe(df, use_container_width=True, height=400)

with col_scatter:
    st.subheader("🎯 Radar de Ineficiencias")
    fig_scatter = px.scatter(
        df, x="Z-Diff", y="R2", text="Ticker", size="Amihud", color="Score_Halcon",
        color_continuous_scale="Viridis", range_x=[-4, 4], range_y=[0, 1]
    )
    # Guías visuales de reversión
    fig_scatter.add_vline(x=1.6, line_dash="dash", line_color="red", opacity=0.5)
    fig_scatter.add_vline(x=-1.6, line_dash="dash", line_color="green", opacity=0.5)
    fig_scatter.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_scatter, use_container_width=True)

# --- 5. DEEP DIVE Y NUBE DE PROBABILIDAD ---
st.divider()
selected = st.selectbox("Selecciona Activo para Análisis de Reversión:", df['Ticker'])
asset_data = df[df['Ticker'] == selected].iloc[0]

c_rev, c_monte = st.columns(2)

with c_rev:
    st.subheader("📉 Gap de Reversión a la Media")
    fig_rev = go.Figure()
    fig_rev.add_trace(go.Scatter(x=['Mercado', 'Media Justa (40d)'], y=[asset_data['Precio'], asset_data['MA40']],
                                mode='lines+markers+text',
                                text=[f"Precio: {asset_data['Precio']}", f"MA40: {asset_data['MA40']:.4f}"],
                                textposition="top center", line=dict(color='gold', width=4, dash='dot')))
    fig_rev.update_layout(height=400)
    st.plotly_chart(fig_rev, use_container_width=True)

with c_monte:
    st.subheader("🎲 Nube de Probabilidad (5 días)")
    # Simulación Montecarlo con Nube de Percentiles
    sims, days = 250, 5
    retornos_sim = np.random.normal(0, asset_data['Volatilidad'], (days, sims))
    caminos = np.zeros((days + 1, sims))
    caminos[0] = asset_data['Precio']
    for t in range(1, days + 1):
        caminos[t] = caminos[t-1] * (1 + retornos_sim[t-1])
    
    # Percentiles para el Fan Chart
    p10, p25, p50, p75, p90 = [np.percentile(caminos, p, axis=1) for p in [10, 25, 50, 75, 90]]
    eje_x = list(range(days + 1))

    fig_mc = go.Figure()
    # Rango 80% (P10 - P90)
    fig_mc.add_trace(go.Scatter(x=eje_x + eje_x[::-1], y=list(p90) + list(p10[::-1]),
                                fill='toself', fillcolor='rgba(0, 150, 255, 0.1)',
                                line=dict(color='rgba(255,255,255,0)'), name='Confianza 80%'))
    # Rango 50% (P25 - P75)
    fig_mc.add_trace(go.Scatter(x=eje_x + eje_x[::-1], y=list(p75) + list(p25[::-1]),
                                fill='toself', fillcolor='rgba(0, 150, 255, 0.2)',
                                line=dict(color='rgba(255,255,255,0)'), name='Confianza 50%'))
    # Media Proyectada
    fig_mc.add_trace(go.Scatter(x=eje_x, y=p50, mode='lines', line=dict(color='cyan', width=3), name="Trayectoria Central"))
    fig_mc.update_layout(height=400, hovermode="x", legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig_mc, use_container_width=True)

# --- 6. VERDICTO FINAL ---
st.divider()
prob_confianza = min(50 + (abs(asset_data['Z-Diff']) * 15), 95)
v_col1, v_col2 = st.columns([1, 2])

with v_col1:
    st.metric("Probabilidad de Giro", f"{prob_confianza:.1f}%")
    st.progress(prob_confianza / 100)

with v_col2:
    if asset_data['Z-Diff'] > 1.6 and asset_data['R2'] < 0.2:
        st.error(f"🚨 ALERTA DE VENTA: {selected} está en un extremo de ficción estadística. Se espera caída hacia {asset_data['MA40']:.4f}.")
    elif asset_data['Z-Diff'] < -1.6 and asset_data['R2'] < 0.2:
        st.success(f"🚀 ALERTA DE COMPRA: {selected} está infravalorado por el mercado. Se espera rebote hacia {asset_data['MA40']:.4f}.")
    else:
        st.info(f"💡 ESTADO NEUTRAL: {selected} se mueve dentro de parámetros normales o bajo tendencia institucional sólida.")
