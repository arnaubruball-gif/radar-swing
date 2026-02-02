import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Halcón 4.0 Pro Terminal", layout="wide")
st.title("🦅 Halcón 4.0: Quantitative Alpha Terminal")

# --- SIMULACIÓN DE DATOS (Sustituye por tu lógica de cálculo) ---
# Aquí es donde el script que ya tenemos vuelca los resultados
data = {
    'Ticker': ['GBPUSD=X', 'AUDUSD=X', 'NZDUSD=X', 'BTC-USD', 'GC=F'],
    'R2': [0.007, 0.044, 0.07, 0.173, 0.392],
    'Z-Diff': [2.78, -1.86, 0.47, -1.32, 0.10],
    'Amihud': [1.2, 2.5, 19.0, 0.05, 0.02],
    'Precio': [1.3520, 0.6910, 0.6120, 78998.53, 2650.10]
}
df = pd.DataFrame(data)

# --- 1. SCATTER PLOT (EL CAZA-MENTIRAS) ---
st.subheader("🎯 Radar de Ineficiencias (Z-Diff vs R2)")
col1, col2 = st.columns([3, 1])

with col1:
    fig = px.scatter(
        df, x="Z-Diff", y="R2", 
        text="Ticker", size="Amihud", color="Z-Diff",
        color_continuous_scale="RdYlGn_r",
        range_x=[-4, 4], range_y=[0, 0.5],
        labels={"Z-Diff": "Desviación (Exceso)", "R2": "Convicción (Dinero Real)"}
    )
    # Líneas de seguridad
    fig.add_vline(x=1.6, line_dash="dash", line_color="red", annotation_text="Venta")
    fig.add_vline(x=-1.6, line_dash="dash", line_color="green", annotation_text="Compra")
    fig.add_hline(y=0.15, line_dash="dot", line_color="gray", annotation_text="Zona Ficción")
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.write("**Leyenda Táctica:**")
    st.info("Puntos ABAJO + EXTREMOS = Oportunidad de Reversión.")
    st.warning("Puntos ARRIBA = Tendencia Real (No tocar contra-tendencia).")
    st.error("Punto GRANDE = Mercado Hueco (Movimiento Rápido).")

# --- 2. DEEP DIVE (ANÁLISIS DE RAYOS X) ---
st.divider()
selected_ticker = st.selectbox("🔍 Selecciona un activo para Deep Dive:", df['Ticker'])

row = df[df['Ticker'] == selected_ticker].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Precio Actual", f"{row['Precio']:,}")
c2.metric("Z-Score (Desviación)", f"{row['Z-Diff']}", delta="Exceso" if abs(row['Z-Diff']) > 1.6 else "Normal")
c3.metric("Convicción (R2)", f"{row['R2']*100:.1f}%", delta_color="inverse")
c4.metric("Iliquidez (Amihud)", f"{row['Amihud']}")

# Simulación de Gráfico de Reversión (Deep Dive Visual)
st.write(f"### Proyección de Reversión: {selected_ticker}")
# Aquí dibujaríamos la distancia entre el precio y la media móvil de 40 días
fig_dive = go.Figure()
fig_dive.add_trace(go.Indicator(
    mode = "gauge+number",
    value = row['Z-Diff'],
    title = {'text': "Presión del Elástico"},
    gauge = {'axis': {'range': [-4, 4]},
             'steps' : [
                 {'range': [-4, -1.6], 'color': "lightgreen"},
                 {'range': [1.6, 4], 'color': "lightpink"}],
             'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': row['Z-Diff']}}
))
st.plotly_chart(fig_dive)
