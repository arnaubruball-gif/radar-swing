import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. Configuración de la App
st.set_page_config(page_title="Halcón 4.0 - Terminal de Guerra", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3d4463; }
    </style>
    """, unsafe_allow_html=True)

st.title("🦅 Halcón de Guerra 4.0: Visual Intelligence")
st.write(f"### Análisis de Mercado - 2 de Febrero, 2026")

# --- 2. TERMÓMETRO DE PÁNICO (VIX) ---
def get_vix_data():
    try:
        vix = yf.download('^VIX', period='5d', interval='1d', progress=False)
        if isinstance(vix.columns, pd.MultiIndex): vix.columns = vix.columns.get_level_values(0)
        current_vix = vix['Close'].iloc[-1]
        prev_vix = vix['Close'].iloc[-2]
        return current_vix, current_vix - prev_vix
    except:
        return 20.0, 0.0

vix_val, vix_delta = get_vix_data()
col_vix, col_info = st.columns([1, 4])
with col_vix:
    st.metric(label="Miedo Global (VIX)", value=f"{vix_val:.2f}", delta=f"{vix_delta:.2f}", delta_color="inverse")
with col_info:
    if vix_val > 20:
        st.warning("⚠️ VOLATILIDAD ALTA: El mercado está nervioso. Las trampas de liquidez son más comunes.")
    else:
        st.success("✅ CALMA RELATIVA: Los flujos institucionales suelen ser más estables.")

# --- 3. MOTOR DE ANÁLISIS PRO ---
ASSETS = {
    'AUD/USD': 'AUDUSD=X', 'EUR/AUD': 'EURAUD=X', 'BITCOIN': 'BTC-USD', 
    'ORO': 'GC=F', 'S&P 500': '^SPX', 'GBP/USD': 'GBPUSD=X', 'USD/JPY': 'JPY=X',
    'EUR/USD': 'EURUSD=X', 'NASDAQ 100': '^IXIC', 'CHF/JPY': 'CHFJPY=X'
}

def analyze_asset(name, ticker):
    try:
        df = yf.download(ticker, period='100d', interval='1d', progress=False)
        if df.empty: return None, None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # Métricas de Flujo
        df['Ret'] = df['Close'].pct_change()
        df['Vol_Proxy'] = (df['High'] - df['Low']) * 100000
        df['RMF'] = df['Close'] * df['Vol_Proxy']
        
        # R2 Dinámico (Convicción)
        r2_series = []
        for i in range(len(df)):
            if i < 15: r2_series.append(0); continue
            subset = df.iloc[i-15:i].dropna()
            if len(subset) < 10: r2_series.append(0); continue
            r2 = sm.OLS(subset['Ret'], sm.add_constant(subset['RMF'])).fit().rsquared
            r2_series.append(r2)
        df['R2_Dynamic'] = r2_series
        
        # Z-Diff (Exceso) y Amihud (Iliquidez)
        diff = df['Ret'].rolling(20).sum() - df['RMF'].pct_change().rolling(20).sum()
        z_val = ((diff - diff.rolling(20).mean()) / (diff.rolling(20).std() + 1e-10)).iloc[-1]
        amihud = (df['Ret'].abs() / (df['RMF'].replace(0, np.nan) / 1e6)).fillna(df['Ret'].abs() * 100).rolling(14).mean().iloc[-1]
        
        # Lógica de Veredicto y TP
        last_r2 = df['R2_Dynamic'].iloc[-1]
        last_price = df['Close'].iloc[-1]
        std_dev = df['Ret'].tail(20).std()
        
        veredicto = "⚪ NEUTRAL"
        tp_val = "N/A"
        
        if last_r2 < 0.12:
            if z_val > 1.4: 
                veredicto = "🚨 CORTO (Trampa)"
                tp_val = f"{last_price * (1 - (abs(z_val) * std_dev)):.4f}"
            elif z_val < -1.4: 
                veredicto = "🟢 LARGO (Oportunidad)"
                tp_val = f"{last_price * (1 + (abs(z_val) * std_dev)):.4f}"
        elif last_r2 > 0.25: 
            veredicto = "💎 TENDENCIA"

        return df, [name, f"{last_price:.2f}", round(last_r2, 3), round(z_val, 2), round(amihud, 4), veredicto, tp_val]
    except:
        return None, None

# --- 4. INTERFAZ VISUAL ---
st.write("---")
asset_to_plot = st.selectbox("🎯 Selecciona Activo para Análisis de ADN:", list(ASSETS.keys()))

if asset_to_plot:
    full_df, summary = analyze_asset(asset_to_plot, ASSETS[asset_to_plot])
    if full_df is not None:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        colors = ['cyan' if r > 0.25 else ('lightgrey' if r < 0.12 else 'orange') for r in full_df['R2_Dynamic']]
        fig.add_trace(go.Candlestick(x=full_df.index, open=full_df['Open'], high=full_df['High'], low=full_df['Low'], close=full_df['Close'], name="Precio"), row=1, col=1)
        fig.add_trace(go.Bar(x=full_df.index, y=full_df['R2_Dynamic'], marker_color=colors, name="Convicción R2"), row=2, col=1)
        fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False, title=f"ADN: {asset_to_plot}")
        st.plotly_chart(fig, use_container_width=True)

# --- 5. PANEL DE ESCANEO TOTAL ---
st.write("---")
if st.button('📡 ESCANEAR MERCADO COMPLETO'):
    all_data = []
    with st.spinner('Analizando ineficiencias...'):
        for name, ticker in ASSETS.items():
            _, s = analyze_asset(name, ticker)
            if s: all_data.append(s)
    df_res = pd.DataFrame(all_data, columns=['Activo', 'Precio', 'R2', 'Z-Diff', 'Amihud', 'Veredicto', 'TP Objetivo'])
    def color_verdict(val):
        if 'CORTO' in val: return 'color: #ff4b4b'
        if 'LARGO' in val: return 'color: #00ffcc'
        if 'TENDENCIA' in val: return 'color: #1c83e1'
        return ''
    st.table(df_res.style.applymap(color_verdict, subset=['Veredicto']))

# --- 6. GUÍA RÁPIDA ---
with st.expander("📖 Manual de Operativa"):
    st.write("1. Busca Velas Grises + Z-Diff extremo: Es una trampa.")
    st.write("2. Velas Azules: Dinero institucional real.")
    st.write("3. TP Objetivo: Precio estadístico de equilibrio.")
