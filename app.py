import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# --- DATOS DE ENTRADA (Mantenemos tu foto actual) ---
data = {
    'Ticker': ['GBPUSD=X', 'AUDUSD=X', 'NZDUSD=X', 'BTC-USD', 'GC=F'],
    'Precio': [1.3520, 0.6910, 0.6120, 78998.53, 2650.10],
    'Z-Diff': [2.78, -1.86, 0.47, -1.32, 0.10],
    'R2': [0.007, 0.044, 0.07, 0.173, 0.392],
    'Volatilidad': [0.005, 0.006, 0.008, 0.025, 0.012] # Volatilidad estimada
}
df = pd.DataFrame(data)

# --- 1. MATRIZ DE OPORTUNIDAD (RANKING ALPHA) ---
st.header("🦅 Módulo 1: Matriz de Oportunidad")
# El Score Halcón premia Z alto y R2 bajo (ineficiencia pura)
df['Score_Halcon'] = (abs(df['Z-Diff']) * (1 - df['R2'])).round(2)
df = df.sort_values(by='Score_Halcon', ascending=False)

# Estilizado de la tabla
st.dataframe(df.style.background_gradient(subset=['Score_Halcon'], cmap='YlOrRd'), use_container_width=True)

# --- 2. GRÁFICO DE REVERSIÓN Y MONTECARLO ---
st.divider()
target_asset = st.selectbox("Selecciona Activo para Simulación Probabilística:", df['Ticker'])
asset_data = df[df['Ticker'] == target_asset].iloc[0]

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📉 Gráfico de Reversión a la Media")
    # Calculamos el Precio de Equilibrio (donde Z-Diff sería 0)
    # Aproximación: Precio / (1 + (Z * Vol))
    precio_justo = asset_data['Precio'] / (1 + (asset_data['Z-Diff'] * asset_data['Volatilidad']))
    
    fig_rev = go.Figure()
    fig_rev.add_trace(go.Scatter(x=['Actual', 'Objetivo (Media)'], y=[asset_data['Precio'], precio_justo],
                                mode='lines+markers+text',
                                text=[f"Actual: {asset_data['Precio']}", f"Equilibrio: {precio_justo:.4f}"],
                                textposition="top center",
                                line=dict(color='royalblue', width=4, dash='dot')))
    fig_rev.update_layout(yaxis_title="Precio", height=400)
    st.plotly_chart(fig_rev, use_container_width=True)
    st.info(f"El 'Gap' de beneficio estimado es de {abs(asset_data['Precio'] - precio_justo):.4f} unidades.")

with col_right:
    st.subheader("🎲 Simulación de Montecarlo (5 días)")
    # Configuración de simulación
    simulaciones = 100
    dias = 5
    precio_init = asset_data['Precio']
    vol = asset_data['Volatilidad']
    
    # Generación de caminos aleatorios (Random Walk)
    retornos_sim = np.random.normal(0, vol, (dias, simulaciones))
    caminos = precio_init * (1 + retornos_sim).cumprod(axis=0)
    
    fig_mc = go.Figure()
    for i in range(simulaciones):
        fig_mc.add_trace(go.Scatter(y=caminos[:, i], mode='lines', 
                                   line=dict(width=0.5, color='rgba(100, 100, 100, 0.3)'),
                                   showlegend=False))
    
    # Añadimos la media de las simulaciones
    fig_mc.add_trace(go.Scatter(y=caminos.mean(axis=1), mode='lines', 
                               line=dict(color='red', width=3), name="Trayectoria Media"))
    
    fig_mc.update_layout(xaxis_title="Días (Pasos)", yaxis_title="Precio Simulado", height=400)
    st.plotly_chart(fig_mc, use_container_width=True)

# --- 3. VERDICTO FINAL ---
st.divider()
prob_exito = 85 if abs(asset_data['Z-Diff']) > 2 else 55 # Lógica simplificada
st.subheader(f"🧠 Veredicto de Probabilidad: {prob_exito}%")
st.progress(prob_exito / 100)
if asset_data['Z-Diff'] > 1.6:
    st.error(f"ALERTA: El modelo sugiere una REVERSIÓN BAJISTA inminente para {target_asset}.")
elif asset_data['Z-Diff'] < -1.6:
    st.success(f"ALERTA: El modelo sugiere una REVERSIÓN ALCISTA inminente para {target_asset}.")
else:
    st.warning("Estado Neutral: Esperando ineficiencia estadística.")
