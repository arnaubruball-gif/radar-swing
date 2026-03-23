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

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OrderFlow PRO — Swing 3D (Gemini Engine)",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── STYLES (Mantenemos tu CSS original) ──────────────────────────────────────
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
.cyan-color  { color: #00e5ff; }
.orange-color{ color: #ff9100; }
.order-box { border-radius: 4px; padding: 20px 24px; margin: 12px 0; }
.order-buy  { background: rgba(0,230,118,.04); border: 1px solid rgba(0,230,118,.3); }
.order-sell { background: rgba(255,23,68,.04);  border: 1px solid rgba(255,23,68,.3);  }
.order-warn { background: rgba(255,214,0,.04);  border: 1px solid rgba(255,214,0,.3);  }
</style>
""", unsafe_allow_html=True)

# ─── MATH HELPERS (Tus fórmulas originales) ───────────────────────────────────
def calc_order_flow(df, period=20):
    df = df.copy()
    df["tp"] = (df["High"] + df["Low"] + df["Close"]) / 3
    df["tp_prev"] = df["tp"].shift(1)
    df["raw_mf"] = np.where(df["tp"] > df["tp_prev"], df["tp"] * df["Volume"],
                   np.where(df["tp"] < df["tp_prev"], -df["tp"] * df["Volume"], 0))
    df["rmf"] = df["raw_mf"].rolling(window=period).sum()
    df["z_diff"] = (df["rmf"] - df["rmf"].rolling(period).mean()) / df["rmf"].rolling(period).std()
    return df.fillna(0)

def monte_carlo_multistep(price, returns, sims, steps, z_adj, vol_mult):
    mu, sigma = returns.mean(), returns.std() * vol_mult
    drift = mu + z_adj * sigma * 0.15
    shocks = np.random.standard_normal((sims, steps))
    paths = price * np.exp(np.cumsum((drift - 0.5 * sigma**2) + sigma * shocks, axis=1))
    return paths[:, -1], sigma, drift

def get_expiry_date(days):
    d = datetime.now() + timedelta(days=days)
    return d.strftime("%a %d %b %Y")

def calc_lots(entry, sl, account, risk_pct, instr):
    risk_usd = account * (risk_pct / 100)
    sl_dist = abs(entry - sl)
    if sl_dist == 0: return 0, 0, "N/A"
    mult = 10 if "std" in instr else 1 if "mini" in instr else 100 if "XAU" in instr else 1
    lots = risk_usd / (sl_dist * mult) if "Forex" not in instr else risk_usd / ((sl_dist/0.0001) * mult)
    return lots, risk_usd, f"{lots:.2f} unidades"

# ─── GEMINI IA HELPERS ────────────────────────────────────────────────────────
def get_gemini_context(ticker, asset_type, horizon, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    prompt = f"""Analista Swing Trader. Activo: {ticker} ({asset_type}). 
    Horizonte: próximos {horizon} días. Investiga calendario económico y sentimiento macro.
    
    Responde estrictamente en formato JSON:
    {{
        "macro": 1, "macro_label": "Alcista", "macro_why": "motivo",
        "news": 0, "news_label": "Neutros", "news_why": "eventos",
        "vol": "normal", "vol_label": "Normal", "vol_why": "motivo",
        "summary": "resumen del sesgo"
    }}
    Valores: macro/news (-2 a 2), vol (low/normal/high)."""
    
    response = model.generate_content(prompt)
    # Limpieza de JSON para evitar errores de formato
    json_str = re.search(r'\{.*\}', response.text, re.DOTALL).group()
    return json.loads(json_str)

def get_gemini_analysis(data_dict, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    prompt = f"Eres un trader pro. Analiza estos datos y da un veredicto de 4 frases: {json.dumps(data_dict)}"
    response = model.generate_content(prompt)
    return response.text

# ─── CHARTS ───────────────────────────────────────────────────────────────────
def plot_mc_histogram(final_prices, ref_price, entry, sl, tp, bull):
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=final_prices[final_prices <= ref_price], marker_color="#ff1744", name="Bearish"))
    fig.add_trace(go.Histogram(x=final_prices[final_prices > ref_price], marker_color="#00e676", name="Bullish"))
    fig.update_layout(template="plotly_dark", height=300, barmode='overlay', paper_bgcolor="#04070d")
    return fig

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("💎 Configuración")
    api_key = st.text_input("Gemini API Key", type="password")
    quick = st.selectbox("Activo", ["EURUSD=X", "GC=F", "^GSPC", "^IXIC"])
    ticker = st.text_input("Ticker", value=quick)
    horizon = st.slider("Días Swing", 1, 5, 3)
    sims = st.selectbox("Simulaciones", [2000, 5000, 10000], index=1)
    st.divider()
    account = st.number_input("Balance ($)", value=10000)
    risk_pct = st.slider("Riesgo %", 0.5, 5.0, 1.0)
    instr = st.selectbox("Contrato", ["Forex std (100k)", "XAU/USD", "Índice CFD"])

# ─── MAIN LOGIC ───────────────────────────────────────────────────────────────
st.title("ORDERFLOW PRO 💎")

if st.button("📡 ANALIZAR CON GEMINI", use_container_width=True, type="primary"):
    if not api_key:
        st.error("Inserta tu API Key de Google Gemini.")
    else:
        with st.spinner("Sincronizando mercado y IA..."):
            # 1. Datos
            df = yf.download(ticker, period="1mo", interval="1h").tail(40)
            df = calc_order_flow(df)
            
            # 2. IA Contexto
            ctx = get_gemini_context(ticker, "asset", horizon, api_key)
            
            # 3. Monte Carlo
            price = df["Close"].iloc[-1]
            returns = np.diff(np.log(df["Close"].values.astype(float)))
            z_adj = np.clip(df["z_diff"].iloc[-1], -2, 2)
            vol_m = 0.8 if ctx['vol'] == 'low' else 1.3 if ctx['vol'] == 'high' else 1.0
            
            final_p, sigma, drift = monte_carlo_multistep(price, returns, sims, horizon*16, z_adj, vol_m)
            
            # Probabilidades con Boost de IA
            bull_raw = np.sum(final_p > price) / sims * 100
            adj_bull = np.clip(bull_raw + (ctx['macro'] * 5), 5, 95)
            
            # Niveles
            sl = np.percentile(final_p, 5 if adj_bull > 50 else 95)
            tp = np.percentile(final_p, 85 if adj_bull > 50 else 15)
            
            # UI
            st.subheader(f"Sesgo: {'ALCISTA' if adj_bull > 55 else 'BAJISTA' if adj_bull < 45 else 'NEUTRAL'}")
            
            c1, c2 = st.columns(2)
            c1.metric("Prob. Alcista", f"{adj_bull:.1f}%")
            c2.metric("Z-Diff", f"{df['z_diff'].iloc[-1]:.2f}")
            
            # Gráfico MC
            st.plotly_chart(plot_mc_histogram(final_p, price, price, sl, tp, adj_bull > 50), use_container_width=True)
            
            # Orden
            st.markdown(f"""
            <div class='order-box {"order-buy" if adj_bull > 50 else "order-sell"}'>
                <h3>ORDEN RECOMENDADA: {'BUY' if adj_bull > 50 else 'SELL'}</h3>
                <p>Entrada: {price:.5f} | SL: {sl:.5f} | TP: {tp:.5f}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Análisis Final
            st.markdown("### 🤖 Análisis Gemini")
            st.write(get_gemini_analysis({"ticker": ticker, "bull": adj_bull, "ctx": ctx}, api_key))
