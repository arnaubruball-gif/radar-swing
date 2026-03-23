import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import anthropic
import json

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OrderFlow PRO — Swing 3D",
    page_icon="📊",
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

.big-prob {
    font-family: 'Rajdhani', sans-serif;
    font-size: 72px;
    font-weight: 700;
    line-height: 1;
}

.bull-color  { color: #00e676; }
.bear-color  { color: #ff1744; }
.neu-color   { color: #ffd600; }
.cyan-color  { color: #00e5ff; }
.orange-color{ color: #ff9100; }

.order-box {
    border-radius: 4px;
    padding: 20px 24px;
    margin: 12px 0;
}
.order-buy  { background: rgba(0,230,118,.04); border: 1px solid rgba(0,230,118,.3); }
.order-sell { background: rgba(255,23,68,.04);  border: 1px solid rgba(255,23,68,.3);  }
.order-warn { background: rgba(255,214,0,.04);  border: 1px solid rgba(255,214,0,.3);  }

.tag {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 2px;
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    font-weight: 700;
}
.tag-bull { background: rgba(0,230,118,.15); color: #00e676; }
.tag-bear { background: rgba(255,23,68,.15);  color: #ff1744; }
.tag-neu  { background: rgba(255,214,0,.15);  color: #ffd600; }
</style>
""", unsafe_allow_html=True)

# ─── MATH HELPERS ─────────────────────────────────────────────────────────────
def calc_order_flow(df: pd.DataFrame, period: int = 20):
    """Z-Diff Order Flow: TP → Raw MF → RMF → Z-Score"""
    df = df.copy()
    df["tp"]     = (df["High"] + df["Low"] + df["Close"]) / 3
    df["tp_prev"]= df["tp"].shift(1)
    df["raw_mf"] = np.where(
        df["tp"] > df["tp_prev"],  df["tp"] * df["Volume"],
        np.where(df["tp"] < df["tp_prev"], -df["tp"] * df["Volume"], 0)
    )
    df["rmf"]    = df["raw_mf"].rolling(window=period, min_periods=1).sum()
    rmf_mean     = df["rmf"].rolling(window=period, min_periods=2).mean()
    rmf_std      = df["rmf"].rolling(window=period, min_periods=2).std()
    df["z_diff"] = (df["rmf"] - rmf_mean) / rmf_std.replace(0, np.nan)
    df["z_diff"] = df["z_diff"].fillna(0)
    return df

def monte_carlo_multistep(price: float, returns: np.ndarray, sims: int,
                           steps: int, z_adj: float, vol_mult: float):
    """GBM multi-step Monte Carlo"""
    mu    = returns.mean()
    sigma = returns.std() * vol_mult
    drift = mu + z_adj * sigma * 0.15

    rng    = np.random.default_rng()
    shocks = rng.standard_normal((sims, steps))
    log_r  = (drift - 0.5 * sigma**2) + sigma * shocks
    paths  = price * np.exp(log_r.cumsum(axis=1))
    return paths[:, -1], sigma, drift

def get_expiry_date(days: int) -> str:
    d = datetime.now()
    added = 0
    while added < days:
        d += timedelta(days=1)
        if d.weekday() < 5:
            added += 1
    return d.strftime("%a %d %b %Y") + " 23:59h"

def calc_lots(entry, sl, account, risk_pct, instr):
    risk_usd = account * (risk_pct / 100)
    sl_dist  = abs(entry - sl)
    if sl_dist == 0:
        return 0, 0, 0
    if instr == "Forex std (100k)":
        pips = sl_dist / 0.0001
        lots = risk_usd / (pips * 10)
        label = f"{lots:.2f} lotes std ({lots*100000:,.0f} u.)"
    elif instr == "Forex mini (10k)":
        pips = sl_dist / 0.0001
        lots = risk_usd / (pips * 1)
        label = f"{lots:.2f} mini lotes ({lots*10000:,.0f} u.)"
    elif instr == "XAU/USD":
        lots = risk_usd / (sl_dist * 100)
        label = f"{lots:.3f} lotes XAU ({lots*100:.1f} oz)"
    else:
        lots = risk_usd / sl_dist
        label = f"{lots:.2f} contratos CFD"
    return lots, risk_usd, label

# ─── AI HELPERS ───────────────────────────────────────────────────────────────
def get_ai_context(ticker: str, asset_type: str, horizon: int, api_key: str) -> dict:
    today = datetime.now().strftime("%A, %d de %B de %Y")
    prompt = f"""Hoy es {today}. Eres un analista swing trader.

Busca en la web el contexto de mercado para los próximos {horizon} días para {ticker} ({asset_type}).
Considera: calendario económico, tendencia macro, eventos de riesgo, posicionamiento institucional.

Responde ÚNICAMENTE con JSON (sin backticks):
{{"macro":0,"macro_label":"Neutral","macro_why":"1 frase","news":0,"news_label":"Neutros","news_why":"1 frase con eventos","vol":"normal","vol_label":"Normal","vol_why":"1 frase","summary":"2-3 frases sesgo swing {horizon}d de {ticker}"}}

macro y news = entero -2 a 2. vol = low/normal/high."""

    client = anthropic.Anthropic(api_key=api_key)
    resp   = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}]
    )
    raw = "".join(b.text for b in resp.content if b.type == "text")
    try:
        s, e = raw.index("{"), raw.rindex("}") + 1
        return json.loads(raw[s:e])
    except Exception:
        return {"macro": 0, "macro_label": "Neutral", "macro_why": "No disponible",
                "news": 0, "news_label": "Neutros", "news_why": "No disponible",
                "vol": "normal", "vol_label": "Normal", "vol_why": "Por defecto",
                "summary": "Contexto no disponible. Se usarán valores neutros."}

def get_ai_analysis(ticker, price, last_z, last_rmf, bull_pct, bear_pct,
                    sigma, atr, mcmean, macro, news, asset_type, horizon,
                    n_candles, ctx_summary, api_key):
    macro_map = ["muy bajista","bajista","neutral","alcista","muy alcista"]
    news_map  = ["muy negativos","negativos","neutros","positivos","muy positivos"]
    ctx_block = f"\nContexto swing web: {ctx_summary}" if ctx_summary else ""

    prompt = f"""Eres un trader institucional swing. Análisis en español, técnico y directo (4-5 frases). Sin asteriscos ni markdown.

Activo: {ticker} ({asset_type}) | Horizonte: {horizon} días
Precio: {price:.5f} | Media MC {horizon}d: {mcmean:.5f}
Z-Diff H1: {last_z:.3f} — {"COMPRA" if last_z>1.5 else "VENTA" if last_z<-1.5 else "NEUTRAL"}
RMF acumulado: {last_rmf:,.0f} | P(alcista): {bull_pct:.1f}% | σ H1: {sigma*100:.3f}%
ATR H1 real: {atr:.5f} | Macro {horizon}d: {macro_map[macro+2]} | Eventos: {news_map[news+2]}
Velas H1: {n_candles}{ctx_block}

Valida si Z-Diff H1 confirma el sesgo MC multi-step, describe contexto institucional y justifica Stop vs Limit para GTC {horizon}d."""

    client = anthropic.Anthropic(api_key=api_key)
    resp   = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=900,
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.content[0].text

# ─── CHARTS ───────────────────────────────────────────────────────────────────
def plot_mc_histogram(final_prices, ref_price, entry, sl, tp, bull):
    fig = go.Figure()
    bull_prices = [p for p in final_prices if p > ref_price]
    bear_prices = [p for p in final_prices if p <= ref_price]

    fig.add_trace(go.Histogram(
        x=bear_prices, nbinsx=50, name="Bajista",
        marker_color="rgba(255,23,68,0.7)", showlegend=True
    ))
    fig.add_trace(go.Histogram(
        x=bull_prices, nbinsx=50, name="Alcista",
        marker_color="rgba(0,230,118,0.7)", showlegend=True
    ))

    for val, color, label in [
        (ref_price, "rgba(255,255,255,0.8)", "PRECIO"),
        (entry,     "rgba(0,229,255,1)",     "ENTRADA"),
        (sl,        "rgba(255,23,68,0.9)",   "SL"),
        (tp,        "rgba(0,230,118,0.8)",   "TP p80"),
    ]:
        fig.add_vline(x=val, line_color=color, line_dash="dot", line_width=2,
                      annotation_text=label, annotation_font_color=color,
                      annotation_position="top")

    fig.update_layout(
        barmode="overlay",
        template="plotly_dark",
        paper_bgcolor="#04070d",
        plot_bgcolor="#0a1019",
        height=300,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", y=1.1),
        xaxis_title="Precio proyectado",
        yaxis_title="Simulaciones",
        title=dict(text="Distribución Monte Carlo — Precios al cierre del horizonte", font_size=12)
    )
    return fig

def plot_candles_zdiff(df):
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.65, 0.35],
        vertical_spacing=0.04
    )
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing_fillcolor="#00e676", increasing_line_color="#00e676",
        decreasing_fillcolor="#ff1744", decreasing_line_color="#ff1744",
        name="H1"
    ), row=1, col=1)

    # Z-Diff colored bars
    colors = df["z_diff"].apply(
        lambda z: "#00e676" if z > 1.5 else "#69f0ae" if z > 0.5
                  else "#ffd600" if z > -0.5 else "#ff6b6b" if z > -1.5 else "#ff1744"
    )
    fig.add_trace(go.Bar(
        x=df.index, y=df["z_diff"], name="Z-Diff",
        marker_color=colors, opacity=0.85
    ), row=2, col=1)

    fig.add_hline(y=1.5,  line_dash="dash", line_color="rgba(0,230,118,.4)", row=2, col=1)
    fig.add_hline(y=-1.5, line_dash="dash", line_color="rgba(255,23,68,.4)", row=2, col=1)
    fig.add_hline(y=0,    line_dash="dot",  line_color="rgba(255,255,255,.2)", row=2, col=1)

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#04070d",
        plot_bgcolor="#0a1019",
        height=500,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_rangeslider_visible=False,
        showlegend=False
    )
    fig.update_yaxes(title_text="Precio H1", row=1, col=1)
    fig.update_yaxes(title_text="Z-Diff", row=2, col=1)
    return fig

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuración")

    api_key = st.text_input("🔑 Anthropic API Key", type="password",
                             help="Obtén tu key en console.anthropic.com")

    st.divider()
    st.markdown("### Activo")

    quick = st.selectbox("Acceso rápido", [
        "EUR/USD (EURUSD=X)", "GBP/USD (GBPUSD=X)", "USD/JPY (USDJPY=X)",
        "XAU/USD (GC=F)", "S&P 500 (^GSPC)", "DAX 40 (^GDAXI)", "NASDAQ (^IXIC)",
        "— Manual —"
    ])

    QUICK_MAP = {
        "EUR/USD (EURUSD=X)": ("EURUSD=X", "forex"),
        "GBP/USD (GBPUSD=X)": ("GBPUSD=X", "forex"),
        "USD/JPY (USDJPY=X)": ("USDJPY=X", "forex"),
        "XAU/USD (GC=F)":     ("GC=F",     "commodity"),
        "S&P 500 (^GSPC)":    ("^GSPC",    "index"),
        "DAX 40 (^GDAXI)":    ("^GDAXI",   "index"),
        "NASDAQ (^IXIC)":     ("^IXIC",    "index"),
    }
    default_sym, default_type = QUICK_MAP.get(quick, ("EURUSD=X", "forex"))

    ticker     = st.text_input("Símbolo Yahoo Finance", value=default_sym)
    asset_type = st.selectbox("Tipo de activo",
                               ["forex", "index", "commodity", "stock", "crypto"],
                               index=["forex","index","commodity","stock","crypto"].index(default_type))

    st.divider()
    st.markdown("### Modelo")

    horizon   = st.selectbox("Horizonte operación", [1, 3, 5],
                              index=1, format_func=lambda x: f"{x} día{'s' if x>1 else ''} (GTC)")
    n_candles = st.slider("Velas H1 a cargar", 20, 60, 30)
    z_period  = st.slider("Periodo Z-Diff", 10, 40, 20)
    sims      = st.selectbox("Simulaciones MC", [2000, 5000, 10000], index=1)
    threshold = st.selectbox("Umbral mínimo %", [60, 65, 70], index=1)

    st.divider()
    st.markdown("### Gestión de riesgo")

    account   = st.number_input("Capital cuenta ($)", min_value=100, value=10000, step=500)
    risk_pct  = st.slider("Riesgo por operación (%)", 0.5, 10.0, 2.0, 0.5)
    instr     = st.selectbox("Instrumento", [
        "Forex std (100k)", "Forex mini (10k)", "XAU/USD", "Índice CFD"
    ])

# ─── MAIN ─────────────────────────────────────────────────────────────────────
st.markdown("""
<h1 style='font-family:Rajdhani,sans-serif;font-size:32px;letter-spacing:4px;color:#00e5ff;margin-bottom:4px'>
    ORDER<span style='color:#ffd600'>FLOW</span> PRO
    <span style='font-size:16px;color:#ff9100;letter-spacing:2px;margin-left:8px'>SWING {h}D</span>
</h1>
<p style='color:#4a6080;font-size:11px;letter-spacing:2px;margin-bottom:20px'>
    MONTE CARLO · ORDER FLOW Z-DIFF · YAHOO FINANCE · GTC ORDERS
</p>
""".format(h=horizon), unsafe_allow_html=True)

# ─── LOAD DATA ────────────────────────────────────────────────────────────────
col_load, col_ctx = st.columns([1, 1])

with col_load:
    load_btn = st.button("📡 CARGAR VELAS H1 — Yahoo Finance", use_container_width=True, type="primary")

with col_ctx:
    ctx_btn = st.button("🌐 OBTENER CONTEXTO (IA + Web)", use_container_width=True,
                         disabled=not api_key)

# Session state
if "df"      not in st.session_state: st.session_state.df      = None
if "context" not in st.session_state: st.session_state.context = None
if "results" not in st.session_state: st.session_state.results = None

if load_btn:
    with st.spinner(f"Descargando velas H1 de Yahoo Finance para {ticker}..."):
        try:
            raw = yf.download(ticker, period="7d", interval="1h",
                              auto_adjust=True, progress=False)
            if raw.empty:
                st.error(f"No se encontraron datos para {ticker}. Verifica el símbolo.")
            else:
                # Keep last n_candles rows, flatten MultiIndex if present
                if isinstance(raw.columns, pd.MultiIndex):
                    raw.columns = raw.columns.get_level_values(0)
                df = raw.tail(n_candles).copy()
                df.index = pd.to_datetime(df.index)
                st.session_state.df = df
                st.session_state.results = None
                st.success(f"✓ {len(df)} velas H1 cargadas · Precio actual: {df['Close'].iloc[-1]:.5f}")
        except Exception as e:
            st.error(f"Error: {e}")

if ctx_btn and api_key:
    with st.spinner("Buscando contexto de mercado con IA + web search..."):
        try:
            ctx = get_ai_context(ticker, asset_type, horizon, api_key)
            st.session_state.context = ctx
        except Exception as e:
            st.error(f"Error contexto: {e}")
            st.session_state.context = None

# Show context if available
if st.session_state.context:
    ctx = st.session_state.context
    sc  = lambda v: "#00e676" if v > 0 else "#ff1744" if v < 0 else "#ffd600"
    vc  = lambda v: "#ff9100" if v == "high" else "#00e5ff" if v == "low" else "#cdd9e5"

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class='metric-card'>
            <div style='font-size:9px;letter-spacing:3px;color:#4a6080;text-transform:uppercase;margin-bottom:6px'>SESGO MACRO ({horizon}d)</div>
            <div style='font-family:Rajdhani,sans-serif;font-size:22px;font-weight:700;color:{sc(ctx["macro"])}'>{ctx["macro_label"]}</div>
            <div style='font-size:10px;color:#4a6080;margin-top:4px'>{ctx["macro_why"]}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class='metric-card'>
            <div style='font-size:9px;letter-spacing:3px;color:#4a6080;text-transform:uppercase;margin-bottom:6px'>EVENTOS SEMANA</div>
            <div style='font-family:Rajdhani,sans-serif;font-size:22px;font-weight:700;color:{sc(ctx["news"])}'>{ctx["news_label"]}</div>
            <div style='font-size:10px;color:#4a6080;margin-top:4px'>{ctx["news_why"]}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class='metric-card'>
            <div style='font-size:9px;letter-spacing:3px;color:#4a6080;text-transform:uppercase;margin-bottom:6px'>VOLATILIDAD ESPERADA</div>
            <div style='font-family:Rajdhani,sans-serif;font-size:22px;font-weight:700;color:{vc(ctx["vol"])}'>{ctx["vol_label"]}</div>
            <div style='font-size:10px;color:#4a6080;margin-top:4px'>{ctx["vol_why"]}</div>
        </div>""", unsafe_allow_html=True)

    st.info(f"💬 {ctx['summary']}")

# Show candle chart if data loaded
if st.session_state.df is not None:
    df = st.session_state.df.copy()
    df = calc_order_flow(df, z_period)

    st.markdown("### 📈 Velas H1 + Z-Diff Order Flow")
    st.plotly_chart(plot_candles_zdiff(df), use_container_width=True)

    # ─── RUN MODEL ────────────────────────────────────────────────────────────
    run_btn = st.button("▶ EJECUTAR MODELO COMPLETO", use_container_width=True, type="primary")

    if run_btn:
        if not api_key:
            st.error("Introduce tu Anthropic API Key en la barra lateral.")
            st.stop()

        with st.spinner("Ejecutando motor cuantitativo..."):
            progress = st.progress(0, text="Calculando Order Flow...")

            # Step 1: OF metrics
            last_z   = float(df["z_diff"].iloc[-1])
            last_rmf = float(df["rmf"].iloc[-1])
            progress.progress(20, text="Ejecutando Monte Carlo multi-step...")

            # Step 2: Returns
            closes  = df["Close"].values.astype(float)
            returns = np.diff(np.log(closes))

            # Step 3: MC params
            ctx        = st.session_state.context or {}
            macro      = ctx.get("macro", 0)
            news_ctx   = ctx.get("news", 0)
            vol_ctx    = ctx.get("vol", "normal")
            ctx_sum    = ctx.get("summary", "")
            vol_mult   = 0.7 if vol_ctx == "low" else 1.5 if vol_ctx == "high" else 1.0
            z_adj      = float(np.clip(last_z, -2, 2))
            hrs_per_day= 24 if asset_type in ["forex","crypto"] else 16
            mc_steps   = horizon * hrs_per_day

            final_prices, sigma, drift = monte_carlo_multistep(
                float(closes[-1]), returns, sims, mc_steps, z_adj, vol_mult
            )
            progress.progress(50, text="Proyectando distribución de precios...")

            price   = float(closes[-1])
            sorted_p= np.sort(final_prices)
            bull_n  = np.sum(final_prices > price)
            raw_bull= bull_n / sims * 100
            ctx_boost= (macro + news_ctx) / 4 * 8
            adj_bull = float(np.clip(raw_bull + ctx_boost, 10, 90))
            adj_bear = 100 - adj_bull
            mc_mean  = float(final_prices.mean())
            p5       = float(np.percentile(sorted_p, 5))
            p95      = float(np.percentile(sorted_p, 95))

            # ATR real
            atr_window = df.tail(14)
            atr        = float((atr_window["High"] - atr_window["Low"]).mean())

            progress.progress(65, text="Calculando niveles de orden GTC...")

            # Order levels from MC distribution
            pct = lambda p: float(np.percentile(sorted_p, p))
            prim_bull = adj_bull > adj_bear

            # STOP: ruptura del rango H1 reciente + buffer
            last3     = df.tail(3)
            rec_high  = float(last3["High"].max())
            rec_low   = float(last3["Low"].min())
            buf       = atr * 0.08
            e_stop    = rec_high + buf if prim_bull else rec_low - buf

            # LIMIT: pullback al percentil 38/62
            e_lim     = pct(38) if prim_bull else pct(62)

            # SL y TP desde distribución MC
            sl = pct(8)  if prim_bull else pct(92)
            tp = pct(80) if prim_bull else pct(20)

            # Choose order type
            use_stop = last_z > 0.8 if prim_bull else last_z < -0.8
            entry    = e_stop if use_stop else e_lim
            o_type   = "STOP" if use_stop else "LIMIT"
            exp_date = get_expiry_date(horizon)

            progress.progress(80, text="Generando análisis institucional con IA...")

            try:
                ai_text = get_ai_analysis(
                    ticker, price, last_z, last_rmf, adj_bull, adj_bear,
                    sigma, atr, mc_mean, macro, news_ctx, asset_type,
                    horizon, len(df), ctx_sum, api_key
                )
            except Exception as e:
                ai_text = f"No se pudo generar el análisis IA: {e}"

            progress.progress(100, text="¡Análisis completado!")
            progress.empty()

            st.session_state.results = dict(
                price=price, last_z=last_z, last_rmf=last_rmf,
                adj_bull=adj_bull, adj_bear=adj_bear,
                mc_mean=mc_mean, p5=p5, p95=p95,
                sigma=sigma, atr=atr, z_adj=z_adj,
                final_prices=final_prices,
                prim_bull=prim_bull, use_stop=use_stop, o_type=o_type,
                entry=entry, sl=sl, tp=tp, exp_date=exp_date,
                mc_steps=mc_steps, ai_text=ai_text,
                macro=macro, df_of=df
            )

# ─── SHOW RESULTS ─────────────────────────────────────────────────────────────
if st.session_state.results:
    r   = st.session_state.results
    dec = 1 if r["price"] > 1000 else 2 if r["price"] > 100 else 4

    st.divider()
    st.markdown(f"""
    <h2 style='font-family:Rajdhani,sans-serif;font-size:22px;letter-spacing:3px;
        color:{"#00e676" if r["adj_bull"]>=60 else "#ff1744" if r["adj_bull"]<=40 else "#ffd600"}'>
        {"SESGO ALCISTA ▲" if r["adj_bull"]>=60 else "SESGO BAJISTA ▼" if r["adj_bull"]<=40 else "SESGO NEUTRAL ➡"}
        &nbsp;·&nbsp; <span style='font-size:14px;color:#4a6080'>Horizonte {horizon}d · GTC expira {r["exp_date"]} · MC {sims:,} sims · {r["mc_steps"]} pasos H1</span>
    </h2>
    """, unsafe_allow_html=True)

    # ── PROBABILITIES ─────────────────────────────────────────────────────────
    col_b, col_s = st.columns(2)
    with col_b:
        st.markdown(f"""<div class='metric-card' style='border-top:2px solid #00e676'>
            <div style='font-size:9px;letter-spacing:3px;color:#00e676;text-transform:uppercase;margin-bottom:8px'>▲ POSITIVO EN {horizon} DÍAS</div>
            <div class='big-prob bull-color'>{r["adj_bull"]:.1f}%</div>
            <div style='font-size:10px;color:#4a6080;margin-top:6px'>IC 95%: [{r["p5"]:.{dec}f}, {r["p95"]:.{dec}f}]</div>
        </div>""", unsafe_allow_html=True)
    with col_s:
        st.markdown(f"""<div class='metric-card' style='border-top:2px solid #ff1744'>
            <div style='font-size:9px;letter-spacing:3px;color:#ff1744;text-transform:uppercase;margin-bottom:8px'>▼ NEGATIVO EN {horizon} DÍAS</div>
            <div class='big-prob bear-color'>{r["adj_bear"]:.1f}%</div>
            <div style='font-size:10px;color:#4a6080;margin-top:6px'>IC 95%: [{r["p5"]:.{dec}f}, {r["p95"]:.{dec}f}]</div>
        </div>""", unsafe_allow_html=True)

    # ── MINI STATS ────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    z = r["last_z"]
    z_color = "#00e676" if z > 1.5 else "#69f0ae" if z > 0.5 else "#ffd600" if z > -0.5 else "#ff6b6b" if z > -1.5 else "#ff1744"
    z_state = "COMPRA" if z > 1.5 else "SESGO +" if z > 0.5 else "NEUTRAL" if z > -0.5 else "SESGO -" if z > -1.5 else "VENTA"

    with c1:
        st.metric("Z-Diff H1", f"{z:.3f}", delta=z_state,
                  delta_color="normal" if z > 0 else "inverse")
    with c2:
        st.metric("Precio esperado (MC)", f"{r['mc_mean']:.{dec}f}",
                  delta=f"{((r['mc_mean']/r['price'])-1)*100:+.3f}%")
    with c3:
        st.metric("Volatilidad σ H1", f"{r['sigma']*100:.3f}%")
    with c4:
        st.metric("ATR H1 real", f"{r['atr']:.{dec}f}")

    # ── Z-DIFF GAUGE ──────────────────────────────────────────────────────────
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=float(np.clip(z, -3, 3)),
        title={"text": "Z-Diff Order Flow", "font": {"size": 14}},
        gauge={
            "axis": {"range": [-3, 3], "tickwidth": 1, "tickcolor": "#4a6080"},
            "bar": {"color": z_color, "thickness": 0.25},
            "bgcolor": "#0a1019",
            "borderwidth": 1,
            "bordercolor": "#1a2d40",
            "steps": [
                {"range": [-3, -1.5], "color": "rgba(255,23,68,.2)"},
                {"range": [-1.5, -0.5], "color": "rgba(255,107,107,.1)"},
                {"range": [-0.5, 0.5], "color": "rgba(255,214,0,.1)"},
                {"range": [0.5, 1.5], "color": "rgba(105,240,174,.1)"},
                {"range": [1.5, 3], "color": "rgba(0,230,118,.2)"},
            ],
            "threshold": {"line": {"color": "white", "width": 3}, "value": z}
        },
        number={"font": {"color": z_color, "size": 28}, "suffix": ""}
    ))
    fig_gauge.update_layout(
        height=220, paper_bgcolor="#04070d",
        font_color="#cdd9e5", margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

    # ── MC HISTOGRAM ──────────────────────────────────────────────────────────
    st.markdown(f"### 📊 Distribución Monte Carlo — {r['mc_steps']} pasos H1 ({horizon} días)")
    fig_mc = plot_mc_histogram(
        r["final_prices"], r["price"], r["entry"], r["sl"], r["tp"], r["prim_bull"]
    )
    st.plotly_chart(fig_mc, use_container_width=True)

    # ── ORDER ─────────────────────────────────────────────────────────────────
    st.markdown(f"### 📋 Orden GTC — Swing {horizon} Días")
    prob = r["adj_bull"] if r["prim_bull"] else r["adj_bear"]

    if prob < threshold:
        st.markdown(f"""<div class='order-box order-warn'>
            <div style='font-family:Rajdhani,sans-serif;font-size:24px;font-weight:700;
                color:#ffd600;letter-spacing:3px;margin-bottom:8px'>⚠ NO OPERAR — CONVICCIÓN INSUFICIENTE</div>
            <div style='font-size:12px;color:#4a6080;line-height:1.9'>
                Probabilidad: <span style='color:#ffd600'>{prob:.1f}%</span> — por debajo del umbral de <span style='color:#cdd9e5'>{threshold}%</span><br>
                Z-Diff: <span style='color:#cdd9e5'>{r["last_z"]:.3f}</span> — {"sin direccionalidad clara" if abs(r["last_z"]) < 0.5 else "señal débil"}<br>
                <span style='color:#ffd600'>💡 Preservar capital también es una posición válida.</span>
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        side      = "BUY" if r["prim_bull"] else "SELL"
        side_cls  = "order-buy" if r["prim_bull"] else "order-sell"
        side_color= "#00e676" if r["prim_bull"] else "#ff1744"
        rr        = abs(r["tp"] - r["entry"]) / abs(r["entry"] - r["sl"])
        sim_cov   = np.mean(
            (r["final_prices"] >= r["entry"]) & (r["final_prices"] <= r["tp"])
            if r["prim_bull"] else
            (r["final_prices"] <= r["entry"]) & (r["final_prices"] >= r["tp"])
        ) * 100
        z_reason  = (f"Z-Diff {r['last_z']:.2f} — ruptura {'alcista' if r['prim_bull'] else 'bajista'} confirmada"
                     if r["use_stop"] else
                     f"Z-Diff {r['last_z']:.2f} moderado — pullback al percentil {'38' if r['prim_bull'] else '62'} MC")

        col_o1, col_o2, col_o3, col_o4, col_o5 = st.columns([1.2, 1.5, 1.2, 2, 1])
        with col_o1:
            st.markdown(f"""<div style='text-align:center;background:{"rgba(0,230,118,.1)" if r["prim_bull"] else "rgba(255,23,68,.1)"};
                border:1px solid {side_color};border-radius:4px;padding:14px 8px'>
                <div style='font-family:Rajdhani,sans-serif;font-size:20px;font-weight:700;
                    color:{side_color};letter-spacing:2px'>{side}</div>
                <div style='font-size:12px;color:{side_color}'>{r["o_type"]}</div>
            </div>""", unsafe_allow_html=True)
        with col_o2:
            st.markdown(f"""<div>
                <div style='font-family:Rajdhani,sans-serif;font-size:26px;font-weight:700'>{r["entry"]:.{dec}f}</div>
                <div style='font-size:9px;color:#4a6080'>GTC · exp. {r["exp_date"]}</div>
            </div>""", unsafe_allow_html=True)
        with col_o3:
            st.markdown(f"""<div style='font-size:12px;line-height:2'>
                SL: <span style='color:#ff1744;font-weight:600'>{r["sl"]:.{dec}f}</span><br>
                TP: <span style='color:#00e676;font-weight:600'>{r["tp"]:.{dec}f}</span><br>
                RR: <span style='color:#cdd9e5'>1:{rr:.1f}</span>
            </div>""", unsafe_allow_html=True)
        with col_o4:
            st.markdown(f"""<div style='font-size:10px;color:#4a6080;line-height:1.7'>
                {z_reason}<br>{sim_cov:.0f}% simulaciones MC entre entrada y TP (p80)
            </div>""", unsafe_allow_html=True)
        with col_o5:
            st.markdown(f"""<div style='font-family:Rajdhani,sans-serif;font-size:32px;
                font-weight:700;color:{side_color};text-align:right'>{prob:.1f}%</div>""",
                unsafe_allow_html=True)

        # ── LOT CALCULATOR ────────────────────────────────────────────────────
        st.markdown("#### 💰 Calculadora de Posición")
        lots, risk_usd, lot_label = calc_lots(r["entry"], r["sl"], account, risk_pct, instr)
        profit = risk_usd * rr if lots > 0 else 0

        lc1, lc2, lc3, lc4 = st.columns(4)
        with lc1:
            st.metric("Tamaño posición", lot_label)
        with lc2:
            st.metric("Riesgo en $", f"${risk_usd:.0f}")
        with lc3:
            st.metric("Beneficio potencial", f"${profit:.0f}")
        with lc4:
            st.metric("Ratio R:R", f"1:{rr:.1f}")

    # ── AI ANALYSIS ───────────────────────────────────────────────────────────
    st.markdown("### 🤖 Análisis Institucional — Claude")
    st.info(r["ai_text"])

    # ── ORDER FLOW TABLE ──────────────────────────────────────────────────────
    with st.expander("📋 Tabla Order Flow H1 completa"):
        df_show = r["df_of"][["Open","High","Low","Close","Volume","tp","raw_mf","rmf","z_diff"]].copy()
        df_show.columns = ["Open","High","Low","Close","Volume","TP","Raw MF","RMF Acum.","Z-Diff"]
        df_show = df_show.round(5)

        def color_zdiff(val):
            if val > 1.5:   return "color: #00e676; font-weight:bold"
            elif val > 0.5: return "color: #69f0ae"
            elif val > -0.5:return "color: #ffd600"
            elif val > -1.5:return "color: #ff6b6b"
            else:           return "color: #ff1744; font-weight:bold"

        styled = df_show.style.applymap(color_zdiff, subset=["Z-Diff"])
        st.dataframe(styled, use_container_width=True)

# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='font-size:10px;color:#4a6080;text-align:center;line-height:1.8'>
⚠️ Modelo educativo-cuantitativo. No constituye asesoramiento financiero ni recomendación de inversión.<br>
Monte Carlo multi-step asume GBM log-normal. Z-Diff basado en Money Flow normalizado con Z-Score.<br>
Datos de Yahoo Finance pueden tener retrasos. Opera siempre con gestión de riesgo estricta.
</div>
""", unsafe_allow_html=True)
