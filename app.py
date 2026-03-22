import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Alpha Quant Terminal", layout="wide", page_icon="🌊")

TICKERS = [
    "MSFT", "AAPL", "NVDA", "V", "MA", "AVGO", "ASML", "MC.PA", "OR.PA", "ITX.MC",
    "IBE.MC", "SAN.MC", "BBVA.MC", "REP.MC", "STNG", "FRO", "MOS", "CF", "LMT", "RTX",
    "COST", "WMT", "KO", "PEP", "LLY", "UNH", "EQIX", "AMT", "CCI", "ICE"
]

# --- 2. MOTOR CUANTITATIVO (Z-MONEY FLOW + SALUD) ---
@st.cache_data(ttl=600)
def get_full_market_scan(ticker_list):
    results = []
    # Descarga masiva para velocidad
    raw_data = yf.download(ticker_list, period="1y", group_by='ticker', silent=True)
    
    for t in ticker_list:
        try:
            df = raw_data[t]
            if df.empty: continue
            
            # --- CÁLCULO Z-MONEY FLOW (Tu fórmula) ---
            df['TP'] = (df['High'] + df['Low'] + df['Close']) / 3
            df['Raw_MF'] = np.where(df['TP'].diff() > 0, df['TP'] * df['Volume'], 
                           np.where(df['TP'].diff() < 0, -df['TP'] * df['Volume'], 0))
            rmf = df['Raw_MF'].rolling(20).sum()
            mu = rmf.rolling(20).mean()
            sigma = rmf.rolling(20).std()
            z_money = (rmf - mu) / sigma
            
            # --- CÁLCULO SALUD Y VALORACIÓN ---
            # Nota: Algunos datos requieren Ticker.info, los bajamos bajo demanda
            info = yf.Ticker(t).info
            per = info.get('trailingPE', 0)
            ey = (1/per*100) if per > 0 else 0
            roe = info.get('returnOnEquity', 0) * 100
            
            health = 0
            if roe > 15: health += 3
            if info.get('debtToEquity', 100) < 60: health += 3
            if info.get('operatingMargins', 0) > 0.15: health += 3

            results.append({
                "Ticker": t,
                "Precio": round(df['Close'].iloc[-1], 2),
                "Z-Money Flow": round(z_money.iloc[-1], 2),
                "Salud (1-9)": health,
                "E. Yield %": round(ey, 2),
                "Div %": round(info.get('dividendYield', 0)*100, 2),
                "Sector": info.get('sector')
            })
        except: continue
    return pd.DataFrame(results)

# --- 3. INTERFAZ ---
st.title("🏛️ Alpha Quant: Scanner & Flow Terminal")

# Sidebar para alternar vistas
view = st.sidebar.radio("Vista", ["🌐 Market Scanner (50)", "🔍 Deep Dive (Z-Diff)"])

if view == "🌐 Market Scanner (50)":
    st.subheader("Clasificación por Flujo de Dinero y Salud Contable")
    
    with st.spinner("Escaneando subasta institucional..."):
        df_scan = get_full_market_scan(TICKERS)
    
    # Lógica de colores basada en tu Z-Diff de Flujo
    def color_scanner(row):
        # COMPRA: Dinero entrando (>1.5) + Saludable (>6)
        if row['Z-Money Flow'] > 1.5 and row['Salud (1-9)'] >= 6:
            return ['background-color: #052111; color: #3fb950'] * len(row)
        # VENTA: Dinero saliendo (<-1.5)
        elif row['Z-Money Flow'] < -1.5:
            return ['background-color: #210505; color: #f85149'] * len(row)
        return [''] * len(row)

    st.dataframe(df_scan.style.apply(color_scanner, axis=1), use_container_width=True, height=700)
    
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.success("**VERDE:** Smart Money entrando + Balance fuerte.")
    c2.info("**GRIS:** Subasta en equilibrio. Sin mano fuerte.")
    c3.error("**ROJO:** Distribución institucional. El dinero está huyendo.")

else:
    # --- VISTA DEEP DIVE ---
    selected = st.sidebar.selectbox("Selecciona Ticker", TICKERS)
    st.subheader(f"Análisis de Flujo Detallado: {selected}")
    
    t = yf.Ticker(selected)
    df_h = t.history(period="1y")
    
    # Re-calculamos flujo para el gráfico
    df_h['TP'] = (df_h['High'] + df_h['Low'] + df_h['Close']) / 3
    df_h['Raw_MF'] = np.where(df_h['TP'].diff() > 0, df_h['TP'] * df_h['Volume'], 
                     np.where(df_h['TP'].diff() < 0, -df_h['TP'] * df_h['Volume'], 0))
    rmf = df_h['Raw_MF'].rolling(20).sum()
    df_h['Z_Money_Flow'] = (rmf - rmf.rolling(20).mean()) / rmf.rolling(20).std()
    
    col_a, col_b = st.columns([2, 1])
    
    with col_a:
        st.write("**Histórico de Z-Money Flow (20 periodos)**")
        chart_data = df_h[['Z_Money_Flow']].tail(60).copy()
        chart_data['Upper'] = 1.5
        chart_data['Lower'] = -1.5
        st.line_chart(chart_data)
        

    with col_b:
        z_now = df_h['Z_Money_Flow'].iloc[-1]
        st.metric("Z-Money Actual", f"{z_now:.2f}")
        
        if z_now > 1.5:
            st.success("INICIATIVA ALCISTA: Los bancos están barriendo la oferta.")
        elif z_now < -1.5:
            st.error("DISTRIBUCIÓN: El Smart Money está liquidando posiciones.")
        else:
            st.info("BALANCE: No hay dominancia institucional clara.")

    with st.expander("📖 Resumen de Empresa"):
        st.write(t.info.get('longBusinessSummary'))
