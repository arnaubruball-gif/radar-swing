import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. Configuración de la App
st.set_page_config(page_title="Halcón 4.0 - Swing Edition", layout="wide")

st.title("🦅 Halcón de Guerra 4.0: SWING STRATEGY")
st.write(f"### Análisis de Inercia Estructural - Feb 2026")

# --- 2. MOTOR DE ANÁLISIS SWING (FILTRO LENTO) ---
ASSETS = {
    'AUD/USD': 'AUDUSD=X', 'EUR/AUD': 'EURAUD=X', 'BITCOIN': 'BTC-USD', 
    'ORO': 'GC=F', 'S&P 500': '^SPX', 'GBP/USD': 'GBPUSD=X', 'USD/JPY': 'JPY=X',
    'EUR/USD': 'EURUSD=X', 'NASDAQ 100': '^IXIC', 'CHF/JPY': 'CHFJPY=X'
}

def analyze_asset_swing(name, ticker):
    try:
        df = yf.download(ticker, period='150d', interval='1d', progress=False)
        if df.empty: return None, None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        df['Ret'] = df['Close'].pct_change()
        df['Vol_Proxy'] = (df['High'] - df['Low']) * 100000
        df['RMF'] = df['Close'] * df['Vol_Proxy']
        
        # R2 Dinámico - VENTANA SWING (30 DÍAS)
        r2_series = []
        for i in range(len(df)):
            if i < 30: r2_series.append(0); continue
            subset = df.iloc[i-30:i].dropna()
            r2 = sm.OLS(subset['Ret'], sm.add_constant(subset['RMF'])).fit().rsquared
            r2_series.append(r2)
        df['R2_Dynamic'] = r2_series
        
        # Z-Diff - VENTANA SWING (40 DÍAS)
        diff = df['Ret'].rolling(40).sum() - df['RMF'].pct_change().rolling(40).sum()
        z_val = ((diff - diff.rolling(40).mean()) / (diff.rolling(40).std() + 1e-10)).iloc[-1]
        
        # Amihud suavizado (20 días)
        amihud = (df['Ret'].abs() / (df['RMF'].replace(0, np.nan) / 1e6)).fillna(df['Ret'].abs() * 100).rolling(20).mean().iloc[-1]
        
        last_r2 = df['R2_Dynamic'].iloc[-1]
        last_price = df['Close'].iloc[-1]
        std_dev = df['Ret'].tail(40).std()
        
        veredicto = "⚪ NEUTRAL"
        tp_val = "N/A"
        
        # Umbrales Swing más exigentes
        if last_r2 < 0.10: # Solo si hay muy poca convicción mensual
            if z_val > 1.6: 
                veredicto = "🚨 CORTO SWING"
                tp_val = f"{last_price * (1 - (abs(z_val) * std_dev)):.4f}"
            elif z_val < -1.6: 
                veredicto = "🟢 LARGO SWING"
                tp_val = f"{last_price * (1 + (abs(z_val) * std_dev)):.4f}"
        elif last_r2 > 0.30: 
            veredicto = "💎 TENDENCIA MENSUAL"

        return df, [name, f"{last_price:.4f}", round(last_r2, 3), round(z_val, 2), round(amihud, 4), veredicto, tp_val]
    except:
        return None, None

# --- 3. INTERFAZ ---
asset_to_plot = st.selectbox("🎯 Análisis de ADN Mensual:", list(ASSETS.keys()))

if asset_to_plot:
    full_df, summary = analyze_asset_swing(asset_to_plot, ASSETS[asset_to_plot])
    if full_df is not None:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        colors = ['cyan' if r > 0.30 else ('lightgrey' if r < 0.10 else 'orange') for r in full_df['R2_Dynamic']]
        fig.add_trace(go.Candlestick(x=full_df.index, open=full_df['Open'], high=full_df['High'], low=full_df['Low'], close=full_df['Close'], name="Precio"), row=1, col=1)
        fig.add_trace(go.Bar(x=full_df.index, y=full_df['R2_Dynamic'], marker_color=colors, name="Convicción R2"), row=2, col=1)
        fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

if st.button('📡 ESCANEAR OPORTUNIDADES SWING'):
    all_data = []
    with st.spinner('Filtrando ruido de mercado...'):
        for name, ticker in ASSETS.items():
            _, s = analyze_asset_swing(name, ticker)
            if s: all_data.append(s)
    df_res = pd.DataFrame(all_data, columns=['Activo', 'Precio', 'R2 (30d)', 'Z-Diff (40d)', 'Amihud', 'Veredicto', 'TP Swing'])
    st.table(df_res)
