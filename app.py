import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm

# Configuración profesional
st.set_page_config(page_title="Halcón de Guerra: Swing Trading", layout="wide")
st.title("🦅 Halcón de Guerra: Radar de Ineficiencias")

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
        
        # 1. Flujo y Convicción
        df['Ret'] = df['Close'].pct_change()
        df['Vol_Proxy'] = (df['High'] - df['Low']) * 100000
        df['TP_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
        df['RMF'] = df['TP_Price'] * df['Vol_Proxy']
        
        # MFI y R2
        pos = df['RMF'].where(df['TP_Price'] > df['TP_Price'].shift(1), 0).rolling(14).sum()
        neg = df['RMF'].where(df['TP_Price'] < df['TP_Price'].shift(1), 0).rolling(14).sum()
        mfi = 100 - (100 / (1 + pos / (neg + 1e-10)))
        
        subset = df[['Ret', 'RMF']].dropna().tail(20)
        r2 = sm.OLS(subset['Ret'], sm.add_constant(subset['RMF'])).fit().rsquared
        
        # 2. Gestión de Riesgo (ATR para Stop Loss)
        df['TR'] = np.maximum(df['High'] - df['Low'], 
                             np.maximum(abs(df['High'] - df['Close'].shift(1)), 
                                        abs(df['Low'] - df['Close'].shift(1))))
        atr = df['TR'].rolling(14).mean().iloc[-1]
        
        price = df['Close'].iloc[-1]
        curr_mfi = mfi.iloc[-1]
        
        # 3. Lógica de Señales y Niveles
        status = "⚪ NEUTRAL"
        sl, tp = 0.0, 0.0
        
        if r2 < 0.08 and curr_mfi > 75: 
            status = "🚨 VENTA (FICCIÓN)"
            sl = price + (atr * 1.5)  # 1.5 veces la volatilidad
            tp = price - (atr * 2.0)
        elif r2 < 0.08 and curr_mfi < 25: 
            status = "🟢 COMPRA (FICCIÓN)"
            sl = price - (atr * 1.5)
            tp = price + (atr * 2.0)
        elif r2 > 0.18: 
            status = "💎 INSTITUCIONAL"
            
        return [ticker, round(price, 4), round(r2, 4), round(curr_mfi, 2), status, round(sl, 4), round(tp, 4)]
    except:
        return None

if st.button('📡 ESCANEAR TODOS LOS MERCADOS'):
    results = []
    for name, ticker in ASSETS.items():
        res = analyze(ticker)
        if res:
            res[0] = name
            results.append(res)
    
    df_final = pd.DataFrame(results, columns=['Activo', 'Precio', 'R2', 'MFI', 'Estado', 'Stop Loss', 'Take Profit'])
    
    # Estilo visual
    def color_status(val):
        if 'VENTA' in val: return 'background-color: #ffcccc; color: black'
        if 'COMPRA' in val: return 'background-color: #ccffcc; color: black'
        if 'INSTITUCIONAL' in val: return 'background-color: #fff3cd; color: black'
        return ''

    st.dataframe(df_final.style.applymap(color_status, subset=['Estado']), use_container_width=True)
    st.warning("⚠️ Recuerda: Ejecuta el trade solo si el R2 es menor a 0.10 y el MFI es extremo.")
