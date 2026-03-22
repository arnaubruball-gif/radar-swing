import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Quant Flow Terminal", layout="wide", page_icon="🌊")

TICKERS = [
    "MSFT", "NVDA", "AAPL", "V", "ASML", "MC.PA", "ITX.MC", "IBE.MC", "STNG", "MOS",
    "GOLD", "EURUSD=X", "BTC-USD", "ICE", "EQIX"
]

# --- 2. MOTOR DE FLUJO MONETARIO (Z-DIFF MONEY FLOW) ---
def get_money_flow_z(df, n=20):
    # 1. Precio Típico
    df['TP'] = (df['High'] + df['Low'] + df['Close']) / 3
    
    # 2. Raw Money Flow (RMF)
    df['TP_Diff'] = df['TP'].diff()
    df['Raw_MF'] = np.where(df['TP_Diff'] > 0, df['TP'] * df['Volume'], 
                   np.where(df['TP_Diff'] < 0, -df['TP'] * df['Volume'], 0))
    
    # 3. Flujo Monetario Relativo (Suavizado)
    df['RMF'] = df['Raw_MF'].rolling(window=n).sum()
    
    # 4. Normalización Z (Z-Diff)
    mu = df['RMF'].rolling(window=n).mean()
    sigma = df['RMF'].rolling(window=n).std()
    df['Z_Money_Flow'] = (df['RMF'] - mu) / sigma
    
    # Derivada del flujo (para ver aceleración)
    df['Flow_Accel'] = df['Z_Money_Flow'].diff()
    
    return df

@st.cache_data(ttl=600)
def fetch_market_data(tickers):
    data = {}
    for t in tickers:
        try:
            d = yf.Ticker(t).history(period="1y")
            if not d.empty:
                data[t] = get_money_flow_z(d)
        except: continue
    return data

# --- 3. INTERFAZ ---
st.title("🌊 Terminal de Flujo Monetario Cuántico")
st.sidebar.header("🕹️ Control de Radar")
selected = st.sidebar.selectbox("Selecciona Activo", TICKERS)

all_data = fetch_market_data(TICKERS)

if selected in all_data:
    df = all_data[selected]
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    # --- PANTALLA DE ESTADO ---
    z_val = curr['Z_Money_Flow']
    accel = curr['Flow_Accel']
    
    col1, col2, col3 = st.columns(3)
    
    # Lógica de Semáforo basada en tu fórmula
    if z_val > 1.5:
        state, color = "🔥 COMPRA FUERTE (Iniciativa Bancaria)", "green"
    elif z_val < -1.5:
        state, color = "🚨 VENTA FUERTE (Distribución)", "red"
    else:
        state, color = "⚖️ NEUTRAL (Subasta en Balance)", "gray"

    st.markdown(f"""
        <div style="padding:20px; border-radius:10px; border:2px solid {color}; background-color:rgba(0,0,0,0.2); text-align:center;">
            <h1 style="color:{color};">{state}</h1>
            <p>Z-Diff de Flujo: <b>{z_val:.2f}</b> | Aceleración: <b>{accel:.2f}</b></p>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    # --- VISUALIZACIÓN ---
    tab1, tab2 = st.tabs(["📊 Gráfico de Flujo", "📋 Datos Contables"])
    
    with tab1:
        st.subheader(f"Inyección de Dinero en {selected}")
        
        # Mostramos el Z-Money Flow frente a niveles clave
        df_chart = df[['Z_Money_Flow']].tail(60).copy()
        df_chart['Suelo'] = -1.5
        df_chart['Techo'] = 1.5
        st.line_chart(df_chart)
        st.caption("Cuando la línea azul cruza los niveles punteados, el 'Smart Money' está tomando una dirección clara.")

    with tab2:
        info = yf.Ticker(selected).info
        c1, c2 = st.columns(2)
        c1.write(f"**Market Cap:** ${info.get('marketCap',0)/1e9:.1f}B")
        c1.write(f"**ROE:** {info.get('returnOnEquity',0)*100:.1f}%")
        c2.write(f"**EPS (Trailing):** {info.get('trailingEps')}")
        c2.write(f"**Volumen 24h:** {info.get('volume')}")

else:
    st.error("Error al cargar datos de flujo.")
