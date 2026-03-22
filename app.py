import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Alpha Terminal Pro", layout="wide")

TICKERS = [
    "MSFT", "AAPL", "NVDA", "V", "MA", "AVGO", "JPM", "UNH", "LLY", "COST",
    "TXN", "LOW", "INTU", "SPGI", "ADP", "SYK", "TGT", "DE", "GE", "BX",
    "MC.PA", "RMS.PA", "OR.PA", "ASML", "SAP", "DTE.DE", "AIR.PA", "ITX.MC", "IBE.MC", "LOG.MC"
] # Lista reducida para velocidad, puedes añadir las 50

# --- 2. MOTOR DE DATOS ---
@st.cache_data(ttl=3600)
def get_market_data(ticker_list):
    rows = []
    for t in ticker_list:
        try:
            stock = yf.Ticker(t)
            inf = stock.info
            # Salud y Valoración
            per = inf.get('trailingPE', 0)
            ey = (1/per*100) if per > 0 else 0
            roe = inf.get('returnOnEquity', 0) * 100
            health = 0
            if roe > 15: health += 3
            if inf.get('debtToEquity', 100) < 50: health += 3
            if inf.get('operatingMargins', 0) > 0.15: health += 3
            
            rows.append({
                "Ticker": t,
                "Precio": inf.get('currentPrice'),
                "Salud (1-9)": health,
                "E. Yield %": round(ey, 2),
                "Div %": round(inf.get('dividendYield', 0)*100, 2),
                "ROE %": round(roe, 1),
                "Sector": inf.get('sector')
            })
        except: continue
    return pd.DataFrame(rows)

# --- 3. INTERFAZ PRINCIPAL ---
st.title("🏦 Alpha Terminal: Global Scanner")

# Sidebar para selección rápida
st.sidebar.header("🎯 Selección de Activo")
selected_ticker = st.sidebar.selectbox("Elige un Ticker para Deep Dive", ["Niguno"] + TICKERS)

if selected_ticker == "Niguno":
    # MODO SCANNER: Vista General
    st.subheader("Clasificación General de Calidad y Valoración")
    df_market = get_market_data(TICKERS)
    
    def highlight_best(row):
        if row['Salud (1-9)'] >= 6 and row['E. Yield %'] > 4:
            return ['background-color: #052111; color: #3fb950'] * len(row)
        return [''] * len(row)

    st.dataframe(df_market.style.apply(highlight_best, axis=1), use_container_width=True, height=600)
    st.info("💡 Selecciona un Ticker en el menú de la izquierda para ver el análisis detallado.")

else:
    # MODO DEEP DIVE: Pestaña de Detalle
    st.button("⬅️ Volver al Scanner", on_click=lambda: st.write("")) 
    
    stock = yf.Ticker(selected_ticker)
    info = stock.info
    hist = stock.history(period="1y")
    
    st.header(f"{info.get('longName')} ({selected_ticker})")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 Evolución de Precio y Momentum")
        hist['MA20'] = hist['Close'].rolling(20).mean()
        st.line_chart(hist[['Close', 'MA20']])
        
        # Cálculo de Z-Score y Momentum rápido
        z = (hist['Close'].iloc[-1] - hist['MA20'].iloc[-1]) / hist['Close'].rolling(20).std().iloc[-1]
        mom = (hist['Close'].iloc[-1] / hist['Close'].iloc[-10] - 1) * 100
        
        c_z, c_m = st.columns(2)
        c_z.metric("Z-Score (Tensión)", f"{z:.2f}", delta="Sobrecompra" if z > 2 else "Sano")
        c_m.metric("Momentum 10d", f"{mom:.2f}%")

    with col2:
        st.subheader("📋 Resumen Contable")
        st.write(f"**Sector:** {info.get('sector')}")
        st.write(f"**Margen Operativo:** {info.get('operatingMargins', 0)*100:.1f}%")
        st.write(f"**Deuda/Patrimonio:** {info.get('debtToEquity', 0):.1f}%")
        st.write(f"**Payout Ratio:** {info.get('payoutRatio', 0)*100:.1f}%")
        
        with st.expander("Ver Descripción del Negocio"):
            st.write(info.get('longBusinessSummary'))

    # --- MÉTRICA DE RIESGO DE "CAÍDA AL POZO" ---
    st.divider()
    st.subheader("⚠️ Análisis de Riesgo")
    if z > 2.2:
        st.error(f"ALTO RIESGO: {selected_ticker} está muy extendida sobre su media. Probabilidad de corrección alta.")
    elif z < -1.5 and mom > 0:
        st.success(f"OPORTUNIDAD: {selected_ticker} está recuperando tras una caída fuerte. Buen timing.")
    else:
        st.info("Situación neutral: No hay un desequilibrio estadístico claro.")
