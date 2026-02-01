import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm

st.set_page_config(page_title="Radar Swing 3.0: Amihud & Retorno", layout="wide")
st.title("🦅 Halcón de Guerra 3.0: Análisis de Iliquidez y Retorno")

ASSETS = {
    'AUD/USD': 'AUDUSD=X', 'EUR/AUD': 'EURAUD=X',
    'BITCOIN': 'BTC-USD', 'ORO': 'GC=F',
    'GBP/USD': 'GBPUSD=X', 'USD/JPY': 'JPY=X',
    'S&P 500': '^SPX', 'PETROLEO': 'CL=F'
}

def analyze(ticker):
    try:
        df = yf.download(ticker, period='100d', interval='1d', progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # 1. Variables Base
        df['Ret'] = df['Close'].pct_change()
        df['Vol_Proxy'] = (df['High'] - df['Low']) * 100000
        df['TP_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
        df['RMF'] = df['TP_Price'] * df['Vol_Proxy']
        
        # 2. Amihud Illiquidity (Retorno Absoluto / Volumen)
        # Valores altos = Precio moviéndose con poco dinero (frágil)
        df['Amihud'] = (df['Ret'].abs() / (df['RMF'] / 1e6)) * 100
        amihud_val = df['Amihud'].rolling(14).mean().iloc[-1]
        
        # 3. Diferencial de Retorno Acumulado (Z-Score de 20 días)
        # Compara Retorno vs Flujo Acumulado
        cum_ret = df['Ret'].rolling(20).sum()
        cum_flow = df['RMF'].pct_change().rolling(20).sum()
        diff = cum_ret - cum_flow
        z_diff = (diff - diff.rolling(20).mean()) / diff.rolling(20).std()
        z_val = z_diff.iloc[-1]

        # 4. R2 y MFI (Lo que ya teníamos)
        subset = df[['Ret', 'RMF']].dropna().tail(20)
        r2 = sm.OLS(subset['Ret'], sm.add_constant(subset['RMF'])).fit().rsquared
        
        # 5. Lógica de Señal Avanzada
        status = "⚪ NEUTRAL"
        # Si el precio sube pero el diferencial es negativo y Amihud es alto = TRAMPA
        if r2 < 0.10 and z_val > 1.5 and amihud_val > df['Amihud'].mean():
            status = "🚨 VENTA (FICCIÓN + ILIQUIDEZ)"
        elif r2 < 0.10 and z_val < -1.5 and amihud_val > df['Amihud'].mean():
            status = "🟢 COMPRA (FICCIÓN + ILIQUIDEZ)"
            
        return [ticker, f"{df['Close'].iloc[-1]:.4f}", round(r2, 3), round(z_val, 2), round(amihud_val, 4), status]
    except Exception as e:
        return None

if st.button('📡 ESCANEAR CON AMIHUD Y DIFERENCIAL'):
    data = []
    for name, ticker in ASSETS.items():
        res = analyze(ticker)
        if res:
            res[0] = name
            data.append(res)
    
    df_final = pd.DataFrame(data, columns=['Activo', 'Precio', 'R2 (Convicción)', 'Z-Diff (Retorno)', 'Amihud (Iliquidez)', 'Estado'])
    
    st.dataframe(df_final.style.background_gradient(subset=['Amihud (Iliquidez)'], cmap='YlOrRd'), use_container_width=True)
    st.info("💡 Z-Diff > 1.5: El precio ha subido mucho más que el dinero real (Burbuja local).")
    st.info("💡 Amihud Alto: El mercado está 'vacío'. Cualquier orden grande provocará un desplome.")
