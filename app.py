import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import google.generativeai as genai
import json
import re
import time

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OrderFlow PRO — Swing 3D",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── STYLES ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Rajdhani:wght@600;700&display=swap');
html, body, [class*="css"] { font-family: 'JetBrains Mono', monospace; }
.main { background: #04070d; }
.metric-card {
    background: #0a1019;
    border: 1px solid #1a2d40;
    border-radius: 4px;
    padding: 16px 20px;
    margin-bottom: 12px;
}
.big-prob { font-family: 'Rajdhani', sans-serif; font-size: 72px; font-weight: 700; line-height: 1; }
.bull-color  { color: #00e676; }
.bear-color  { color: #ff1744; }
.order-box { border-radius: 4px; padding: 20px 24px; margin: 12px 0; }
.order-buy  { background: rgba(0,230,118,.04); border: 1px solid rgba(0,230,118,.3); }
.order-sell { background: rgba(255,23,68,.04);  border: 1px solid rgba(255,23,68,.3);  }
.order-warn { background: rgba(255,214,0,.04);  border: 1px solid rgba(255,214,0,.3);  }
</style>
""", unsafe_allow_html=True)

# ─── MATH HELPERS ─────────────────────────────────────────────────────────────
def calc_order_flow(df: pd.DataFrame, period: int = 20):
    df = df.copy().dropna()
    if len(df) < period: return df
    
    # Typical Price
    df["tp"] = (df["High"] + df["Low"] + df["Close"]) / 3
    df["tp_prev"] = df["tp"].shift(1)
    
    # Raw Money Flow (Corrección del ValueError)
    tp = df["tp"].values
    tp_prev = df["tp_prev"].values
    vol = df["Volume"].values
    
    raw_mf = np.where(tp > tp_prev, tp * vol,
             np.where(tp < tp_prev, -tp * vol, 0))
    df["raw_mf"] = raw_mf
    
    # RMF y Z-Diff
    df["rmf"] = df["raw_mf"].rolling(window=period, min_periods=1).sum()
    rmf_mean = df["rmf"].rolling(window=period).mean()
    rmf_std = df["rmf"].rolling(window=period).std()
    
    df["z_diff"] = (df["rmf"] - rmf_mean) / rmf_std.replace(0, np.nan)
    return df.fillna(0)

def monte_carlo_multistep(price, returns, sims, steps, z_adj, vol_mult):
    mu = returns.mean()
    sigma = returns.std() * vol_mult
    drift = mu + z_adj * sigma * 0.15
    shocks = np.random.default_rng().standard_normal((sims, steps))
    paths = price * np.exp(np.cumsum((drift - 0.5 * sigma**2) + sigma * shocks, axis=1))
    return paths[:, -1], sigma, drift

def get_expiry_date(days):
    d = datetime.now()
    added = 0
    while added < days:
        d += timedelta(days=1)
        if d.weekday() < 5: added += 1
    return d.strftime("%a %d %b %Y")

# ─── GEMINI IA HELPERS ────────────────────────────────────────────────────────
def get_gemini_context(ticker, asset_type, horizon, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    prompt = f"""Analista Swing. Activo: {ticker} ({asset_type}). Horizonte: {horizon} días. 
    Busca calendario económico y sentimiento macro. Responde SOLO JSON:
    {{"macro":0,"macro_label":"Neutral","macro_why":"...","news":0,"news_label":"Neutros","news_why":"...","vol":"normal","vol_label":"Normal","vol_why":"...","summary":"..."}}"""
    
    for _ in range(3):
        try:
            response = model.generate_content(prompt)
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            return json.loads(match.group()) if match else {}
        except Exception as e:
            if "ResourceExhausted" in str(e): time.sleep(5); continue
            return None
    return None

def get_gemini_analysis(ticker, price, z, bull, bear, mc_mean, macro, news, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    prompt = f"Trader Pro. Activo: {ticker}. Precio: {price}. Z-Diff: {z}. Prob Alcista: {bull}%. Sesgo Macro: {macro}. Da veredicto de 4 frases."
    try:
        response = model.generate_content(prompt)
        return response.text
    except: return "Análisis IA temporalmente no disponible."

# ─── CHARTS ───────────────────────────────────────────────────────────────────
def plot_mc_histogram(final_prices, ref_price, entry, sl, tp):
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=final_prices[final_prices <= ref_price], marker_color="#ff1744", name="Bearish"))
    fig.add_trace(go.Histogram(x=final_prices[final_prices > ref_price], marker_color="#00e676", name="Bullish"))
    fig.update_layout(template="plotly_dark", height=300, barmode='overlay', paper_bgcolor="#04070d", margin=dict(l=0,r=0,t=30,b=0))
    return fig

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Configuración")
    api_key = st.text_input("🔑 Gemini API Key", type="password")
    quick = st.selectbox("Activo", ["EURUSD=X", "GC=F", "^GSPC", "BTC-USD"])
    ticker = st.text_input("Ticker", value=quick)
    asset_type = st.selectbox("Tipo", ["forex", "commodity", "index", "crypto"])
    horizon = st.slider("Días Swing", 1, 5, 3)
    account = st.number_input("Capital ($)", value=10000)
    risk_pct = st.slider("Riesgo %", 0.5, 5.0, 1.0)
    instr = st.selectbox("Contrato", ["Forex std", "XAU/USD", "CFD"])

# ─── MAIN ─────────────────────────────────────────────────────────────────────
st.title("ORDERFLOW PRO 💎")

if st.button("▶ ANALIZAR MERCADO", use_container_width=True, type="primary"):
    if not api_key: st.error("Falta API Key")
    else:
        with st.spinner("Sincronizando..."):
            raw = yf.download(ticker, period="1mo", interval="1h")
            if raw.empty: st.error("Ticker no encontrado")
            else:
                if isinstance(raw.columns, pd.MultiIndex): raw.columns = raw.columns.get_level_values(0)
                df = calc_order_flow(raw.tail(40))
                ctx = get_gemini_context(ticker, asset_type, horizon, api_key) or {}
                
                price = float(df["Close"].iloc[-1])
                returns = np.diff(np.log(df["Close"].values.astype(float)))
                z_adj = np.clip(float(df["z_diff"].iloc[-1]), -2, 2)
                vol_m = 0.8 if ctx.get('vol') == 'low' else 1.3 if ctx.get('vol') == 'high' else 1.0
                
                final_p, sigma, drift = monte_carlo_multistep(price, returns, 5000, horizon*16, z_adj, vol_m)
                bull_pct = float(np.sum(final_p > price) / 5000 * 100)
                adj_bull = np.clip(bull_pct + (ctx.get('macro', 0)*5), 5, 95)
                
                st.subheader(f"Veredicto: {'COMPRA' if adj_bull > 55 else 'VENTA' if adj_bull < 45 else 'NEUTRAL'}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Prob. Alcista", f"{adj_bull:.1f}%")
                c2.metric("Z-Diff", f"{df['z_diff'].iloc[-1]:.2f}")
                c3.metric("Precio", f"{price:.4f}")
                
                st.plotly_chart(plot_mc_histogram(final_p, price, price, 0, 0), use_container_width=True)
                
                st.markdown(f"### 🤖 Análisis Gemini")
                st.write(get_gemini_analysis(ticker, price, z_adj, adj_bull, 100-adj_bull, final_p.mean(), ctx.get('macro',0), 0, api_key))
