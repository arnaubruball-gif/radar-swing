import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm

# 1. Configuración de Estilo y Página
st.set_page_config(page_title="Halcón de Guerra 3.0 - Pro", layout="wide")

# CSS personalizado para mejorar la visibilidad
st.markdown("""
    <style>
    .metric-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🦅 Halcón de Guerra 3.0")
st.write("### Sistema de Detección de Ineficiencias y Trampas de Liquidez")

# Activos a vigilar
ASSETS = {
    'AUD/USD': 'AUDUSD=X', 'EUR/AUD': 'EURAUD=X',
    'BITCOIN': 'BTC-USD', 'ORO': 'GC=F',
    'GBP/USD': 'GBPUSD=X', 'USD/JPY': 'JPY=X',
    'S&P 500': '^SPX', 'PETROLEO': 'CL=F',
    'EUR/USD': 'EURUSD=X', 'NASDAQ 100': '^IXIC'
}

def analyze(ticker):
    try:
        df = yf.download(ticker, period='100d', interval='1d', progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # Cálculos de Motor
        df['Ret'] = df['Close'].pct_change()
        df['Vol_Proxy'] = (df['High'] - df['Low']) * 100000
        df['TP_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
        df['RMF'] = df['TP_Price'] * df['Vol_Proxy']
        
        # Amihud (Iliquidez)
        vol_clean = df['RMF'].replace(0, np.nan)
        df['Amihud'] = (df['Ret'].abs() / (vol_clean / 1e6)).fillna(df['Ret'].abs() * 100)
        amihud_val = df['Amihud'].rolling(14).mean().iloc[-1]
        
        # Z-Diff (Exceso de Retorno)
        cum_ret = df['Ret'].rolling(20).sum()
        cum_flow = df['RMF'].pct_change().rolling(20).sum()
        diff = cum_ret - cum_flow
        z_diff = (diff - diff.rolling(20).mean()) / (diff.rolling(20).std() + 1e-10)
        z_val = z_diff.iloc[-1]

        # R2 (Convicción)
        subset = df[['Ret', 'RMF']].dropna().tail(20)
        r2 = sm.OLS(subset['Ret'], sm.add_constant(subset['RMF'])).fit().rsquared
        
        # Lógica de Veredicto PRO
        if r2 < 0.10:
            if z_val > 1.5 and amihud_val > df['Amihud'].median():
                veredicto = "🚨 CORTO (Trampa de Liquidez)"
                color = "🔴"
            elif z_val < -1.5 and amihud_val > df['Amihud'].median():
                veredicto = "🟢 LARGO (Oportunidad Iliquidez)"
                color = "🟢"
            else:
                veredicto = "⏳ FICCIÓN (Sin Dirección)"
                color = "⚪"
        elif r2 > 0.25:
            veredicto = "💎 TENDENCIA INSTITUCIONAL"
            color = "🔵"
        else:
            veredicto = "⚪ NEUTRAL"
            color = "⚪"

        return [ticker, f"{df['Close'].iloc[-1]:.4f}", round(r2, 3), round(z_val, 2), round(amihud_val, 4), veredicto]
    except:
        return None

# --- INTERFAZ DE USUARIO ---
col1, col2 = st.columns([1, 4])

with col1:
    st.write("### 🛠️ Comandos")
    btn = st.button('📡 ESCANEAR MERCADO', use_container_width=True)
    st.markdown("---")
    st.write("**Leyenda Rápida:**")
    st.write("R2 < 0.1 = Mentira")
    st.write("Z > 1.5 = Inflado")
    st.write("Amihud alto = Frágil")

with col2:
    if btn:
        data = []
        for name, ticker in ASSETS.items():
            res = analyze(ticker)
            if res:
                res[0] = name
                data.append(res)
        
        df_final = pd.DataFrame(data, columns=['Activo', 'Precio', 'R2 (Convicción)', 'Z-Diff (Retorno)', 'Amihud (Iliquidez)', 'Veredicto'])
        
        # Tabla Principal
        st.dataframe(df_final.style.applymap(lambda x: 'color: red' if 'CORTO' in str(x) else ('color: green' if 'LARGO' in str(x) else '')), use_container_width=True)

# --- INFORME INTEGRADO ---
st.markdown("---")
st.write("## 📖 Informe de Análisis Profesional")

tabs = st.tabs(["🧐 Cómo Analizar", "📉 Guía de Métricas", "🛡️ Gestión de Riesgo"])

with tabs[0]:
    st.write("""
    ### Tu rutina Swing de 3 pasos:
    1. **Identifica la Ficción:** Busca activos con **R2 bajo**. Si el R2 es alto, no hay trampa, hay tendencia.
    2. **Busca el Exceso:** Si el **Z-Diff** es mayor a 1.5 o menor a -1.5, el precio se ha estirado como un elástico.
    3. **Confirma con Iliquidez:** Si el **Amihud** es alto, el giro será violento porque no hay órdenes que lo frenen.
    """)
    

with tabs[1]:
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.info("**R² (Convicción)**\n\nMide la verdad. Si es bajo, el precio se mueve por ruido minorista. Si es alto, los bancos están operando.")
    with col_b:
        st.info("**Z-Diff (Exceso)**\n\nMide la borrachera del precio. Nos dice si el retorno acumulado es mucho mayor a lo que el dinero real justifica.")
    with col_c:
        st.info("**Amihud (Fragilidad)**\n\nMide la profundidad. Un Amihud alto significa 'mercado vacío'. Perfecto para cazar reversiones rápidas.")
    

with tabs[2]:
    st.warning("**Regla de Oro:** Aunque el radar diga LARGO o CORTO, nunca operes sin un Stop Loss. La 'Ficción' puede durar más tiempo del que tu cuenta puede aguantar si hay noticias macro inesperadas.")
