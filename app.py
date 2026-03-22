import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Global Dividend Hunter", layout="wide")

# Lista diversificada: USA (Mega, Large, Mid) + EUROPA (España, Alemania, Francia, Holanda)
TICKERS = [
    # --- MEGA CAPS USA (>200B) ---
    "MSFT", "AAPL", "NVDA", "V", "MA", "AVGO", "JPM", "UNH", "LLY", "COST",
    # --- LARGE CAPS USA (50B - 200B) ---
    "TXN", "LOW", "INTU", "SPGI", "ADP", "SYK", "TGT", "DE", "GE", "BX",
    # --- MID CAPS USA (10B - 50B) ---
    "MPWR", "GRMN", "BRO", "JKHY", "FICO", "POOL", "PH", "SNA", "MSA", "LHX",
    # --- EUROPA: CALIDAD Y CRECIMIENTO ---
    "MC.PA", "RMS.PA", "OR.PA", "ASML", "SAP", "DTE.DE", "AIR.PA", "SNY", "BNP.PA", "SIE.DE",
    # --- ESPAÑA E IBEX ---
    "ITX.MC", "IBE.MC", "FER.MC", "LOG.MC", "SAN.MC", "BBVA.MC", "REP.MC",
    # --- DIVIDENDO SEGURO / INFRAESTRUCTURA ---
    "EQIX", "AMT", "CCI"
]

# --- 2. MOTOR DE ESCANEO CON DIVIDEND SCORE ---
@st.cache_data(ttl=600)
def scan_global_dividends(ticker_list):
    data_list = []
    for ticker in ticker_list:
        try:
            t = yf.Ticker(ticker)
            info = t.info
            hist = t.history(period="1mo")
            if hist.empty: continue
            
            price = hist['Close'].iloc[-1]
            yield_pct = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
            payout = info.get('payoutRatio', 0) * 100
            mom = (price / hist['Close'].iloc[0] - 1) * 100
            mcap = info.get('marketCap', 0) / 1e9 # En Billions
            
            # --- CÁLCULO DEL DIVIDEND SCORE (1-10) ---
            # Premiamos: Payout bajo, Yield moderado y Momentum positivo
            score = 5 # Base
            if payout < 50: score += 2
            if 1 < yield_pct < 4: score += 1 # Yield sostenible
            if mom > 2: score += 2
            if payout > 85: score -= 3 # Castigo por riesgo de recorte
            
            data_list.append({
                "Ticker": ticker,
                "Market Cap (B)": round(mcap, 1),
                "Yield (%)": round(yield_pct, 2),
                "Payout (%)": round(payout, 1),
                "Momentum (%)": round(mom, 2),
                "Div Score": min(max(score, 1), 10) # Forzar rango 1-10
            })
        except: continue
    return pd.DataFrame(data_list)

# --- 3. INTERFAZ ---
st.title("🏛️ Radar Global: Dividendos & Momentum")
st.write("Analizando 50 joyas de Europa y América para detectar crecimiento sano.")

with st.spinner("Escaneando mercados globales..."):
    results = scan_global_dividends(TICKERS)

def color_rows(row):
    # Lógica visual: Score alto + Momentum = Oportunidad
    color = ""
    if row['Div Score'] >= 8:
        color = "background-color: #052111; color: #3fb950" # TOP
    elif row['Div Score'] <= 3:
        color = "background-color: #210505; color: #f85149" # RIESGO DE POZO
    return [color] * len(row)

if not results.empty:
    # Ordenar por Score de mayor a menor por defecto
    results = results.sort_values(by="Div Score", ascending=False)
    
    st.dataframe(
        results.style.apply(color_rows, axis=1).format({
            "Market Cap (B)": "${:.1f}B",
            "Yield (%)": "{:.2f}%",
            "Payout (%)": "{:.1f}%",
            "Momentum (%)": "{:+.2f}%"
        }), 
        use_container_width=True, height=800
    )
    
    st.divider()
    
    # --- EXPLICACIÓN DE MARKET CAPS ---
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("**Mega Caps (>$200B):** Son los tanques (MSFT, LVMH). Menos volátiles, dividendos muy seguros.")
    with c2:
        st.info("**Mid/Large Caps ($30B-$100B):** El punto dulce del crecimiento. Aquí es donde el dividendo suele subir más rápido.")
    with c3:
        st.info("**Mid Caps Euro/USA (<$30B):** Acciones como Logista o Garmin. Pueden 'acelerar' tu capital mucho más rápido si el momentum es verde.")

else:
    st.error("No se han podido cargar los datos de la lista maestra.")
