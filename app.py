import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm

# Configuración de la interfaz
st.set_page_config(page_title="Halcón de Guerra 3.0", layout="wide")
st.title("🦅 Halcón de Guerra 3.0: Terminal de Ineficiencias")
st.subheader("Análisis de Convicción, Iliquidez y Retorno Acumulado")

# Activos a vigilar
ASSETS = {
    'AUD/USD': 'AUDUSD=X', 'EUR/AUD': 'EURAUD=X',
    'BITCOIN': 'BTC-USD', 'ORO': 'GC=F',
    'GBP/USD': 'GBPUSD=X', 'USD/JPY': 'JPY=X',
    'S&P 500': '^SPX', 'PETROLEO': 'CL=F',
    'EUR/USD': 'EURUSD=X', 'DAX 40': '^GDAXI'
}

def analyze(ticker):
    try:
        # Descarga de datos
        df = yf.download(ticker, period='100d', interval='1d', progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # 1. Cálculo de Retornos y Flujo
        df['Ret'] = df['Close'].pct_change()
        df['Vol_Proxy'] = (df['High'] - df['Low']) * 100000
        df['TP_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
        df['RMF'] = df['TP_Price'] * df['Vol_Proxy']
        
        # 2. Amihud Blindado (Iliquidez)
        # Si el volumen es 0 o None, usamos una estimación basada en el rango
        vol = df['RMF'].replace(0, np.nan)
        df['Amihud'] = (df['Ret'].abs() / (vol / 1e6)).fillna(df['Ret'].abs() * 100)
        amihud_val = df['Amihud'].rolling(14).mean().iloc[-1]
        
        # 3. Diferencial de Retorno Acumulado (Z-Diff)
        cum_ret = df['Ret'].rolling(20).sum()
        cum_flow = df['RMF'].pct_change().rolling(20).sum()
        diff = cum_ret - cum_flow
        z_diff = (diff - diff.rolling(20).mean()) / (diff.rolling(20).std() + 1e-10)
        z_val = z_diff.iloc[-1]

        # 4. R2 (Convicción Institucional)
        subset = df[['Ret', 'RMF']].dropna().tail(20)
        if len(subset) < 20: return None
        y = subset['Ret']
        X = sm.add_constant(subset['RMF'])
        r2 = sm.OLS(y, X).fit().rsquared
        
        # 5. Lógica del Veredicto
        status = "⚪ NEUTRAL"
        if r2 < 0.10:
            if z_val > 1.5 and amihud_val > df['Amihud'].median():
                status = "🚨 BUSCAR CORTO (Trampa)"
            elif z_val < -1.5 and amihud_val > df['Amihud'].median():
                status = "🟢 BUSCAR LARGO (Oportunidad)"
            else:
                status = "⏳ ESPERAR (Ficción)"
        elif r2 > 0.20:
            status = "💎 TENDENCIA REAL"

        return [ticker, f"{df['Close'].iloc[-1]:.4f}", round(r2, 3), round(z_val, 2), round(amihud_val, 4), status]
    except Exception as e:
        return None

# Botón de ejecución
if st.button('📡 ESCANEAR MERCADO TOTAL'):
    data = []
    for name, ticker in ASSETS.items():
        res = analyze(ticker)
        if res:
            res[0] = name
            data.append(res)
    
    df_final = pd.DataFrame(data, columns=['Activo', 'Precio', 'R2 (Convicción)', 'Z-Diff (Retorno)', 'Amihud (Iliquidez)', 'Veredicto'])
    
    # Mostrar tabla
    st.dataframe(df_final, use_container_width=True)
    
    # Guía rápida para el usuario
    st.markdown("""
    ---
    ### 🧠 Guía de Operativa Swing:
    * **R2 < 0.10:** El precio está "mintiendo". No hay manos fuertes detrás.
    * **Z-Diff > 1.5 o < -1.5:** El precio se ha separado de la realidad del dinero.
    * **Amihud Alto:** El mercado está vacío. Los movimientos son frágiles y tienden a revertirse.
    """)
