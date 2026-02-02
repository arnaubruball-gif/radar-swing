import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Radar de Ineficiencias v2.0", layout="wide")
st.title("🎯 Radar de Ineficiencias de Mercado")
st.markdown("---")

# --- BARRA LATERAL (PARÁMETROS SENSIBLES) ---
with st.sidebar:
    st.header("Configuración de Sensibilidad")
    activos = ["GBPUSD=X", "EURUSD=X", "JPY=X", "AUDUSD=X", "BTC-USD", "GC=F"]
    ticket = st.selectbox("Selecciona Activo", activos, index=0)
    
    # Hemos bajado los días para hacerlo más reactivo
    ventana_conviccion = st.slider("Ventana de Convicción (R2)", 5, 30, 15)
    ventana_exceso = st.slider("Ventana de Exceso (Z-Score)", 5, 40, 20)
    
    st.info("💡 Menos días = Más sensibilidad a movimientos recientes.")

# --- OBTENCIÓN DE DATOS ---
@st.cache_data(ttl=3600)
def cargar_datos(symbol):
    df = yf.download(symbol, period="1y", interval="1d")
    return df

data = cargar_datos(ticket)

# --- CÁLCULO DE MÉTRICAS (Lógica de Ineficiencia) ---
def calcular_metricas(df, v_conv, v_exceso):
    temp = df.copy()
    
    # 1. Retornos y Volatilidad (Sensible)
    temp['Retornos'] = temp['Close'].pct_change()
    temp['Volatilidad'] = temp['Retornos'].rolling(window=10).std()
    
    # 2. Z-Score (Exceso)
    temp['Media_Ema'] = temp['Close'].ewm(span=v_exceso).mean()
    temp['Std_Ema'] = temp['Close'].rolling(window=v_exceso).std()
    temp['Z-Score'] = (temp['Close'] - temp['Media_Ema']) / temp['Std_Ema']
    
    # 3. R-Cuadrado (Convicción/Inercia)
    # Comparamos el precio contra una línea de tiempo para ver la fuerza de la tendencia
    y = np.array(range(v_conv))
    def get_r2(x):
        if len(x) < v_conv: return 0
        slope, intercept = np.polyfit(y, x, 1)
        r_squared = 1 - (np.sum((x - (slope * y + intercept))**2) / ((len(x) - 1) * np.var(x)))
        return r_squared

    temp['R2'] = temp['Close'].rolling(window=v_conv).apply(get_r2)
    
    return temp.dropna()

df_analisis = calcular_metricas(data, ventana_conviccion, ventana_exceso)
latest = df_analisis.iloc[-1]
precio_actual = latest['Close']

# --- INTERFAZ PRINCIPAL ---
col1, col2, col3 = st.columns(3)
col1.metric("Precio Actual", f"{precio_actual:.4f}")
col2.metric("Z-Score (Desviación)", f"{latest['Z-Score']:.2d}", delta=f"{latest['Z-Score']:.2f}")
col3.metric("Convicción (R2)", f"{latest['R2']*100:.1f}%")

st.markdown("---")

col_left, col_right = st.columns([1.5, 1])

# --- GRÁFICO TÉCNICO ---
with col_left:
    st.subheader("Análisis de Desviación y Regresión")
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(x=df_analisis.index, y=df_analisis['Close'], name="Precio"))
    fig_price.add_trace(go.Scatter(x=df_analisis.index, y=df_analisis['Media_Ema'], 
                                   line=dict(dash='dash', color='gray'), name="Media Base"))
    fig_price.update_layout(height=450, template="plotly_dark")
    st.plotly_chart(fig_price, use_container_width=True)

# --- MONTECARLO SENSIBLE ---
with col_right:
    st.subheader("🎲 Proyección Montecarlo (7D)")
    
    # Parámetros de la simulación
    dias_proyectados = 7
    n_simulaciones = 200
    
    # Volatilidad anualizada de corto plazo
    vol = latest['Volatilidad'] 
    
    # Calculamos el "Drift" (Si el Z-score es alto, la tendencia es a volver a la media)
    drift = -(latest['Z-Score'] * 0.005) 
    
    # Simulación de retornos logarítmicos
    sim_retornos = np.random.normal(drift, vol, (dias_proyectados, n_simulaciones))
    caminos_precio = precio_actual * (1 + sim_retornos).cumprod(axis=0)
    
    # Eje X para la proyección
    fechas_futuras = [df_analisis.index[-1] + timedelta(days=i) for i in range(1, dias_proyectados + 1)]
    
    # Percentiles para la nube
    p95 = np.percentile(caminos_precio, 95, axis=1)
    p5 = np.percentile(caminos_precio, 5, axis=1)
    p50 = np.percentile(caminos_precio, 50, axis=1)

    fig_mc = go.Figure()
    
    # Nube de probabilidad (Abanico)
    fig_mc.add_trace(go.Scatter(
        x=fechas_futuras + fechas_futuras[::-1],
        y=list(p95) + list(p5[::-1]),
        fill='toself',
        fillcolor='rgba(0, 176, 246, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Área de Probabilidad (90%)'
    ))

    # Trayectoria central
    fig_mc.add_trace(go.Scatter(x=fechas_futuras, y=p50, 
                               line=dict(color='#00B0F6', width=3), name="Mediana"))
    
    # Precio actual como punto de inicio
    fig_mc.add_vline(x=df_analisis.index[-1], line_dash="dash", line_color="orange")

    fig_mc.update_layout(height=450, template="plotly_dark", showlegend=False,
                        yaxis=dict(tickformat=".4f"))
    st.plotly_chart(fig_mc, use_container_width=True)

# --- PANEL DE DECISIÓN ---
st.subheader("📋 Diagnóstico del Radar")
if abs(latest['Z-Score']) > 2 and latest['R2'] > 0.6:
    st.error(f"⚠️ ALERTA DE INEFICIENCIA: El activo está extremadamente {'Sobrecomprado' if latest['Z-Score'] > 0 else 'Sobrevendido'}. Probabilidad de reversión alta.")
elif latest['R2'] < 0.3:
    st.warning("⚠️ RUIDO ALTO: El mercado no tiene una dirección clara. Los modelos predictivos tienen menos fiabilidad ahora mismo.")
else:
    st.success("✅ MERCADO EN EQUILIBRIO: El precio sigue su inercia estadística normal.")
