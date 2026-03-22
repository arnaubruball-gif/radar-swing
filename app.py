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

# --- 2. MOTOR CUANTITATIVO ---
@st.cache_data(ttl=600)
def get_full_market_scan(ticker_list):
    results = []
    for t in ticker_list:
        try:
            stock = yf.Ticker(t)
            df = stock.history(period="1y")
            if df.empty or len(df) < 40: continue
            
            # --- Z-MONEY FLOW ---
            df['TP'] = (df['High'] + df['Low'] + df['Close']) / 3
            df['Raw_MF'] = np.where(df['TP'].diff() > 0, df['TP'] * df['Volume'], 
                           np.where(df['TP'].diff() < 0, -df['TP'] * df['Volume'], 0))
            rmf = df['Raw_MF'].rolling(20).sum()
            mu, sigma = rmf.rolling(20).mean(), rmf.rolling(20).std()
            z_money = (rmf - mu) / sigma if sigma.iloc[-1] != 0 else 0
            
            # --- FUNDAMENTALES Y DIVIDENDOS ---
            info = stock.info
            fcf = info.get('freeCashflow', 0)
            mcap = info.get('marketCap', 1)
            fcf_yield = (fcf / mcap) * 100 if fcf else 0
            
            # Salud y Crecimiento
            payout = info.get('payoutRatio', 0) * 100
            dgr_5y = info.get('fiveYearAvgDividendYield', 0) # Proxy de crecimiento
            
            results.append({
                "Ticker": t,
                "Precio": round(info.get('currentPrice', df['Close'].iloc[-1]), 2),
                "Z-Money Flow": round(z_money.iloc[-1], 2),
                "Salud (1-9)": (3 if info.get('returnOnEquity', 0) > 0.15 else 0) + 
                               (3 if info.get('debtToEquity', 100) < 60 else 0) + 
                               (3 if info.get('operatingMargins', 0) > 0.15 else 0),
                "FCF Yield %": round(fcf_yield, 2),
                "Div Yield %": round((info.get('dividendYield', 0) or 0) * 100, 2),
                "Payout %": round(payout, 1),
                "Hist. Div (5y)": round(dgr_5y, 2)
            })
        except: continue
    return pd.DataFrame(results)

# --- 3. INTERFAZ ---
st.title("🏛️ Alpha Quant: Cash Flow & Dividend Radar")

view = st.sidebar.radio("Vista", ["🌐 Market Scanner (50)", "🔍 Deep Dive (Z-Diff)"])

if view == "🌐 Market Scanner (50)":
    with st.spinner("Escaneando flujos de caja y dividendos..."):
        df_scan = get_full_market_scan(TICKERS)
    
    if not df_scan.empty:
        def color_scanner(row):
            # Lógica: Verde si hay flujo de dinero Y el dividendo está cubierto por FCF (FCF Yield > Div Yield)
            if row['Z-Money Flow'] > 1.5 and row['FCF Yield %'] > row['Div Yield %']:
                return ['background-color: #052111; color: #3fb950'] * len(row)
            elif row['Z-Money Flow'] < -1.5 or row['Payout %'] > 90:
                return ['background-color: #210505; color: #f85149'] * len(row)
            return [''] * len(row)

        st.dataframe(df_scan.style.apply(color_scanner, axis=1), use_container_width=True, height=700)
    
    st.info("💡 **FCF Yield > Div Yield**: Es la señal de seguridad máxima. La empresa genera más efectivo del que reparte.")

else:
    selected = st.sidebar.selectbox("Selecciona Ticker", TICKERS)
    t = yf.Ticker(selected)
    info = t.info
    
    st.subheader(f"Deep Dive: {selected} - Expectativa de Cash Flow")
    
    c1, c2, c3 = st.columns(3)
    # Visualización de la "Cobertura del Dividendo"
    fcf_y = (info.get('freeCashflow', 0) / info.get('marketCap', 1)) * 100
    div_y = (info.get('dividendYield', 0) or 0) * 100
    
    c1.metric("FCF Yield (Caja)", f"{fcf_y:.2f}%")
    c2.metric("Dividend Yield", f"{div_y:.2f}%")
    c3.metric("Margen de Seguridad Div.", f"{fcf_y - div_y:.2f}%", delta="Sostenible" if fcf_y > div_y else "Riesgo")

    # Gráfico de flujo (Z-Money Flow)
    df_h = t.history(period="1y")
    df_h['TP'] = (df_h['High'] + df_h['Low'] + df_h['Close']) / 3
    df_h['Raw_MF'] = np.where(df_h['TP'].diff() > 0, df_h['TP'] * df_h['Volume'], 
                     np.where(df_h['TP'].diff() < 0, -df_h['TP'] * df_h['Volume'], 0))
    rmf = df_h['Raw_MF'].rolling(20).sum()
    df_h['Z_Money_Flow'] = (rmf - rmf.rolling(20).mean()) / rmf.rolling(20).std()
    
    st.line_chart(df_h[['Z_Money_Flow']].tail(60))
