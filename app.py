import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. Configuración de la App
st.set_page_config(page_title="Halcón 4.0 - Matriz de Fuerza", layout="wide")

st.title("🦅 Halcón 4.0: Matriz de Fuerza Relativa (Base USD)")
st.write(f"### Análisis de Ineficiencias Globales - Feb 2, 2026")

# --- 2. LISTA DE ACTIVOS (TODOS VS USD + BENCHMARKS) ---
ASSETS = {
    'EUR/USD': 'EURUSD=X',
    'GBP/USD': 'GBPUSD=X',
    'AUD/USD': 'AUDUSD=X',
    'NZD/USD': 'NZDUSD=X',
    'USD/JPY': 'JPY=X',   # Nota: JPY está invertido (USD es base)
    'USD/CHF': 'CHF=X',   # Nota: CHF está invertido
    'USD/CAD': 'CAD=X',   # Nota: CAD está invertido
    'BITCOIN': 'BTC-USD',
    'ORO (Spot)': 'GC=F',
    'S&P 500': '^SPX',
    'NASDAQ 100': '^IXIC'
}

def analyze_asset_swing(name, ticker):
    try:
        # Cargamos datos suficientes para las medias móviles de 30/40 días
        df = yf.download(ticker, period='180d', interval='1d', progress=False)
        if df.empty: return None, None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        df['Ret'] = df['Close'].pct_change()
        df['Vol_Proxy'] = (df['High'] - df['Low']) * 100000
        df['RMF'] = df['Close'] * df['Vol_Proxy']
        
        # R2 Dinámico - SWING (30 DÍAS)
        r2_series = []
        for i in range(len(df)):
            if i < 30: r2_series.append(0); continue
            subset = df.iloc[i-30:i].dropna()
            r2 = sm.OLS(subset['Ret'], sm.add_constant(subset['RMF'])).fit().rsquared
            r2_series.append(r2)
        df['R2_Dynamic'] = r2_series
        
        # Z-Diff - SWING (40 DÍAS)
        diff = df['Ret'].rolling(40).sum() - df['RMF'].pct_change().rolling(40).sum()
        z_val = ((diff - diff.rolling(40).mean()) / (diff.rolling(40).std() + 1e-10)).iloc[-1]
        
        # Amihud (Iliquidez)
        amihud = (df['Ret'].abs() / (df['RMF'].replace(0, np.nan) / 1e6)).fillna(df['Ret'].abs() * 100).rolling(20).mean().iloc[-1]
        
        last_r2 = df['R2_Dynamic'].iloc[-1]
        last_price = df['Close'].iloc[-1]
        std_dev = df['Ret'].tail(40).std()
        
        veredicto = "⚪ NEUTRAL"
        tp_val = "N/A"
        
        # Lógica de Veredicto Swing
        if last_r2 < 0.10:
            if z_val > 1.6: 
                veredicto = "🚨 DEBILIDAD USD (Corto)" if "USD/" in name else "🚨 VENTA (Trampa)"
                tp_val = f"{last_price * (1 - (abs(z_val) * std_dev)):.4f}"
            elif z_val < -1.6: 
                veredicto = "🟢 FUERZA USD (Largo)" if "USD/" in name else "🟢 COMPRA (Oportunidad)"
                tp_val = f"{last_price * (1 + (abs(z_val) * std_dev)):.4f}"
        elif last_r2 > 0.30: 
            veredicto = "💎 TENDENCIA REAL"

        return df, [name, f"{last_price:.4f}", round(last_r2, 3), round(z_val, 2), round(amihud, 4), veredicto, tp_val]
    except:
        return None, None

# --- 3. INTERFAZ DE USUARIO ---
st.write("---")
if st.button('📡 ESCANEAR MATRIZ DE FUERZA RELATIVA'):
    all_data = []
    with st.spinner('Midiendo la salud del Dólar y sus contrapartes...'):
        for name, ticker in ASSETS.items():
            _, s = analyze_asset_swing(name, ticker)
            if s: all_data.append(s)
    
    df_res = pd.DataFrame(all_data, columns=['Activo', 'Precio', 'R2 (30d)', 'Z-Diff (40d)', 'Amihud', 'Veredicto', 'TP Swing'])
    
    # Aplicar estilos
    def highlight_trade(val):
        if 'VENTA' in val or 'DEBILIDAD' in val: return 'background-color: #4b0000; color: white'
        if 'COMPRA' in val or 'FUERZA' in val: return 'background-color: #004b00; color: white'
        if 'TENDENCIA' in val: return 'background-color: #00004b; color: white'
        return ''

    st.dataframe(df_res.style.applymap(highlight_trade, subset=['Veredicto']), use_container_width=True)

st.info("""
    **Guía de Cruces:**
    * Si **EUR/USD** es COMPRA y **GBP/USD** es VENTA -> Opera **Largo en EUR/GBP**.
    * Si **AUD/USD** es COMPRA y **NZD/USD** es VENTA -> Opera **Largo en AUD/NZD**.
    * Esto te permite operar monedas sin importar lo que haga el Dólar.
""")
