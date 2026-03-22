import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Scanner Pro: Financial Health", layout="wide")

TICKERS = [
    "MSFT", "AAPL", "NVDA", "V", "MA", "AVGO", "JPM", "UNH", "LLY", "COST",
    "TXN", "LOW", "INTU", "SPGI", "ADP", "SYK", "TGT", "DE", "GE", "BX",
    "MPWR", "GRMN", "BRO", "JKHY", "FICO", "POOL", "PH", "SNA", "MSA", "LHX",
    "MC.PA", "RMS.PA", "OR.PA", "ASML", "SAP", "DTE.DE", "AIR.PA", "SNY", "BNP.PA", "SIE.DE",
    "ITX.MC", "IBE.MC", "FER.MC", "LOG.MC", "SAN.MC", "BBVA.MC", "REP.MC",
    "EQIX", "AMT", "CCI"
]

# --- 2. MOTOR DE ESCANEO AVANZADO ---
@st.cache_data(ttl=3600)
def scan_pro_health(ticker_list):
    data_list = []
    for ticker in ticker_list:
        try:
            t = yf.Ticker(ticker)
            info = t.info
            
            # Valoración Estilo PER (Earnings Yield)
            per = info.get('trailingPE')
            e_yield = (1 / per * 100) if per and per > 0 else 0
            
            # Salud Contable (Simplificación del F-Score)
            # Miramos ROE, Deuda/Equity y Margen Operativo
            roe = info.get('returnOnEquity', 0)
            debt_to_equity = info.get('debtToEquity', 100) / 100
            op_margin = info.get('operatingMargins', 0)
            
            # Puntuación de Salud (1-9)
            health_score = 1
            if roe > 0.15: health_score += 2
            if debt_to_equity < 0.5: health_score += 2
            if op_margin > 0.10: health_score += 2
            if info.get('currentRatio', 0) > 1.5: health_score += 2
            
            # Momentum y Dividendos (de nuestro modelo anterior)
            price = info.get('currentPrice', 0)
            yield_pct = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
            payout = info.get('payoutRatio', 0) * 100
            
            data_list.append({
                "Ticker": ticker,
                "Precio": price,
                "Salud (1-9)": health_score,
                "Yield (E/P) %": round(e_yield, 2),
                "Div Yield %": round(yield_pct, 2),
                "Payout %": round(payout, 1),
                "ROE %": round(roe * 100, 1)
            })
        except: continue
    return pd.DataFrame(data_list)

# --- 3. INTERFAZ ---
st.title("🏦 Scanner Pro: Salud Contable y Valoración")
st.write("Filtrando empresas por fortaleza financiera y rentabilidad real (Earnings Yield).")

with st.spinner("Analizando balances y múltiplos..."):
    results = scan_pro_health(TICKERS)

def color_pro(row):
    color = ""
    # TOP: Salud alta (>7) y Valoración razonable (Yield > 4%)
    if row['Salud (1-9)'] >= 7 and row['Yield (E/P) %'] > 4:
        color = "background-color: #052111; color: #3fb950"
    # RIESGO: Salud baja (<4)
    elif row['Salud (1-9)'] <= 3:
        color = "background-color: #210505; color: #f85149"
    return [color] * len(row)

if not results.empty:
    results = results.sort_values(by="Salud (1-9)", ascending=False)
    st.dataframe(
        results.style.apply(color_pro, axis=1).format({
            "Yield (E/P) %": "{:.2f}%",
            "Div Yield %": "{:.2f}%",
            "Payout %": "{:.1f}%",
            "ROE %": "{:.1f}%"
        }), 
        use_container_width=True, height=800
    )
    
    st.divider()
    
    # --- LEYENDA TÉCNICA ---
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🛡️ Salud Contable (1-9)")
        st.write("Mide la calidad del balance. Una empresa con **Salud > 7** tiene mucha caja, poca deuda y es muy rentable. Es casi imposible que caiga al pozo por quiebra.")
        
    with c2:
        st.subheader("📊 Earnings Yield (E/P)")
        st.write("Es lo opuesto al PER. Si una empresa tiene un PER de 20, su Yield es 5%. Buscamos que sea superior al interés de los bonos para que la inversión valga la pena.")
        

else:
    st.error("Error al procesar los datos financieros.")
