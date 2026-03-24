import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json
import re

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OrderFlow PRO — H4 Swing",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── STYLES ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Rajdhani:wght@600;700&display=swap');
html, body, [class*="css"] { font-family: 'JetBrains Mono', monospace; }
.metric-card {
    background: #0a1019; border: 1px solid #1a2d40;
    border-radius: 4px; padding: 16px 20px; margin-bottom: 12px;
}
.big-prob { font-family: 'Rajdhani', sans-serif; font-size: 72px; font-weight: 700; line-height: 1; }
.bull-color { color: #00e676; }
.bear-color { color: #ff1744; }
.order-box  { border-radius: 4px; padding: 20px 24px; margin: 12px 0; }
.order-warn { background: rgba(255,214,0,.04); border: 1px solid rgba(255,214,0,.3); }
</style>
""", unsafe_allow_html=True)

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
TF_LABEL    = "H4"
TF_INTERVAL = "4h"
TF_PERIOD   = "60d"   # Yahoo range for 4h
H4_FX       = 6       # H4 candles per day — forex/crypto (24h)
H4_EQ       = 4       # H4 candles per day — equity/index (~16h)

# ─── MATH ─────────────────────────────────────────────────────────────────────
def calc_order_flow(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Z-Diff con volumen adaptativo.
    Forex no tiene volumen centralizado en Yahoo → usa rango (H-L) como proxy,
    igual que hacen la mayoría de plataformas para el Money Flow Index en FX.
    """
    df = df.copy()
    df["tp"]      = (df["High"] + df["Low"] + df["Close"]) / 3
    df["tp_prev"] = df["tp"].shift(1)

    # Detectar si el volumen es útil
    vol = df["Volume"].fillna(0)
    vol_ok = (vol.sum() > 0) and (vol.nunique() > 3)

    if vol_ok:
        effective_vol = vol.replace(0, np.nan).ffill().fillna(1.0)
    else:
        # Proxy: rango normalizado × precio típico (refleja actividad sin volumen)
        rng = (df["High"] - df["Low"])
        mean_rng = rng.mean()
        effective_vol = (rng / mean_rng * df["tp"].mean() * 10000).fillna(1.0)

    df["raw_mf"] = np.where(
        df["tp"] > df["tp_prev"],  df["tp"] * effective_vol,
        np.where(df["tp"] < df["tp_prev"], -df["tp"] * effective_vol, 0)
    )
    df["rmf"]    = df["raw_mf"].rolling(window=period, min_periods=1).sum()
    mu           = df["rmf"].rolling(window=period, min_periods=2).mean()
    sigma        = df["rmf"].rolling(window=period, min_periods=2).std()
    df["z_diff"] = ((df["rmf"] - mu) / sigma.replace(0, np.nan)).fillna(0)
    return df


def interpret_zdiff(z: float, df: pd.DataFrame, macro: int = 0) -> dict:
    """
    Interpreta Z-Diff usando el contexto completo del precio:
      1. Posición en rango (¿está el precio arriba o abajo de su rango reciente?)
      2. Momentum reciente (¿está subiendo o bajando en las últimas velas?)
      3. Estructura: ¿está rompiendo un máximo/mínimo o rebotando en un nivel?
      4. Magnitud Z (momentum vs agotamiento estadístico)
      5. Sesgo macro
    """
    closes = df["Close"].values
    highs  = df["High"].values
    lows   = df["Low"].values
    n      = len(closes)

    # ── 1. Posición en rango ──────────────────────────────────────────────────
    # ¿Dónde está el precio respecto al rango de las últimas 14 velas H4 (~2.5 días)?
    lookback    = min(14, n)
    range_high  = highs[-lookback:].max()
    range_low   = lows[-lookback:].min()
    range_span  = range_high - range_low if range_high != range_low else 1e-10
    # 0 = en mínimos del rango, 1 = en máximos
    price_pct   = (closes[-1] - range_low) / range_span

    in_top    = price_pct > 0.75    # precio en el 25% superior del rango
    in_bottom = price_pct < 0.25    # precio en el 25% inferior del rango
    in_middle = not in_top and not in_bottom

    # ── 2. Momentum reciente ──────────────────────────────────────────────────
    # Pendiente de las últimas 3 velas vs las 3 anteriores
    if n >= 6:
        avg_recent = closes[-3:].mean()
        avg_prev   = closes[-6:-3].mean()
        rising     = avg_recent > avg_prev
    else:
        rising = closes[-1] > closes[-2] if n >= 2 else True

    # ── 3. ¿Ruptura o rebote? ─────────────────────────────────────────────────
    # Ruptura: precio supera el máximo/mínimo de las 5 velas anteriores
    prev_high = highs[-6:-1].max() if n >= 6 else range_high
    prev_low  = lows[-6:-1].min()  if n >= 6 else range_low
    breaking_up   = closes[-1] > prev_high   # ruptura alcista
    breaking_down = closes[-1] < prev_low    # ruptura bajista

    # ── 4. Magnitud Z ─────────────────────────────────────────────────────────
    abs_z = abs(z)

    # ── MOTOR DE DECISIÓN ─────────────────────────────────────────────────────
    if abs_z > 2.2:
        # ZONA EXTREMA — el contexto del precio es determinante
        if z > 0:
            if in_top and not breaking_up:
                # Flujo alcista extremo + precio en techo + sin ruptura = DISTRIBUCIÓN
                signal = "DISTRIBUCIÓN EN TECHO"
                label  = "▼ VENTA — distribución en máximos"
                color  = "#ff1744"
                expl   = (f"Z-Diff extremo ({z:.2f}) con el precio en el {price_pct*100:.0f}% "
                          f"superior del rango y sin ruptura confirmada. "
                          f"Patrón clásico de distribución institucional en techo. "
                          f"El flujo comprador extremo suele preceder la caída.")
                bull   = False
            elif breaking_up:
                # Flujo alcista extremo + ruptura real = MOMENTUM FUERTE
                signal = "RUPTURA ALCISTA"
                label  = "▲ COMPRA — ruptura con flujo institucional"
                color  = "#00e676"
                expl   = (f"Z-Diff extremo ({z:.2f}) confirmando ruptura del máximo previo. "
                          f"Iniciativa compradora institucional genuina. "
                          f"El flujo y el precio se alinean — entrada Stop válida.")
                bull   = True
            elif in_bottom:
                # Flujo alcista extremo + precio en suelos = ACUMULACIÓN AGRESIVA
                signal = "ACUMULACIÓN EN SUELO"
                label  = "▲ COMPRA — acumulación institucional en mínimos"
                color  = "#00e676"
                expl   = (f"Z-Diff extremo ({z:.2f}) con el precio en la zona baja del rango "
                          f"({price_pct*100:.0f}%). Los institucionales están acumulando "
                          f"agresivamente en zona de valor. Entrada Limit en retroceso.")
                bull   = True
            else:
                # Zona media con flujo extremo = posible agotamiento
                signal = "AGOTAMIENTO ALCISTA"
                label  = "⚠ PRECAUCIÓN — Z extremo en zona media"
                color  = "#ff9100"
                expl   = (f"Z-Diff extremo ({z:.2f}) pero el precio está en zona media del rango "
                          f"({price_pct*100:.0f}%). Flujo comprador insostenible estadísticamente. "
                          f"Posible pullback antes de continuar. Espera retroceso.")
                bull   = None
        else:
            if in_bottom and not breaking_down:
                # Flujo bajista extremo + precio en suelo + sin ruptura = CAPITULACIÓN
                signal = "CAPITULACIÓN EN SUELO"
                label  = "▲ COMPRA — capitulación vendedora en mínimos"
                color  = "#00e676"
                expl   = (f"Z-Diff extremo negativo ({z:.2f}) con el precio en el {price_pct*100:.0f}% "
                          f"inferior del rango. Capitulación vendedora: el flujo bajista extremo "
                          f"en suelos suele marcar el final de la caída. Entrada Limit en soporte.")
                bull   = True
            elif breaking_down:
                # Flujo bajista extremo + ruptura bajista = MOMENTUM BAJISTA
                signal = "RUPTURA BAJISTA"
                label  = "▼ VENTA — ruptura con flujo institucional"
                color  = "#ff1744"
                expl   = (f"Z-Diff extremo negativo ({z:.2f}) confirmando ruptura del mínimo previo. "
                          f"Distribución institucional confirmada. Stop por ruptura bajista.")
                bull   = False
            elif in_top:
                # Flujo bajista extremo + precio en techo = DISTRIBUCIÓN REAL
                signal = "DISTRIBUCIÓN EN TECHO"
                label  = "▼ VENTA — flujo vendedor agresivo en máximos"
                color  = "#ff1744"
                expl   = (f"Z-Diff extremo negativo ({z:.2f}) con precio en máximos del rango "
                          f"({price_pct*100:.0f}%). Distribución institucional clara. "
                          f"Los institucionales están vendiendo en los altos.")
                bull   = False
            else:
                signal = "AGOTAMIENTO BAJISTA"
                label  = "⚠ PRECAUCIÓN — Z extremo negativo en zona media"
                color  = "#ff9100"
                expl   = (f"Z-Diff extremo negativo ({z:.2f}) en zona media del rango. "
                          f"Flujo vendedor insostenible. Posible rebote técnico inminente.")
                bull   = None

    elif abs_z > 1.5:
        # SEÑAL FUERTE — precio + macro definen la dirección
        if z > 0:
            if breaking_up or (rising and in_top and macro >= 0):
                signal = "COMPRA — MOMENTUM"
                label  = "▲ COMPRA (momentum + flujo confirmados)"
                color  = "#00e676"
                expl   = (f"Z-Diff {z:.2f} con {'ruptura del máximo previo' if breaking_up else 'precio en zona alta y subiendo'}. "
                          f"Flujo e impulso de precio alineados. "
                          f"{'Macro ' + ('alcista' if macro>0 else 'neutral') + ' confirma.' if macro>=0 else ''} "
                          f"Entrada Stop.")
                bull   = True
            elif in_bottom and rising:
                signal = "REBOTE EN SOPORTE"
                label  = "▲ COMPRA — rebote desde mínimos con flujo"
                color  = "#00e676"
                expl   = (f"Z-Diff {z:.2f} con precio rebotando desde la zona baja del rango "
                          f"({price_pct*100:.0f}%). El flujo comprador confirma el rebote en soporte. "
                          f"Entrada Limit en retroceso a zona de valor.")
                bull   = True
            elif in_top and not rising:
                signal = "DISTRIBUCIÓN"
                label  = "▼ VENTA — flujo alto pero precio cede en techo"
                color  = "#ff1744"
                expl   = (f"Z-Diff {z:.2f} elevado pero el precio está cediendo desde máximos "
                          f"({price_pct*100:.0f}% del rango). Patrón de distribución. "
                          f"El flujo no está traduciendo en subida de precio.")
                bull   = False
            elif macro < 0:
                signal = "PRECAUCIÓN ALCISTA"
                label  = "⚡ FLUJO ALCISTA — macro en contra"
                color  = "#ffd600"
                expl   = (f"Z-Diff {z:.2f} positivo pero contexto macro bajista. "
                          f"Precio en {price_pct*100:.0f}% del rango. "
                          f"Reduce tamaño o espera confirmación de precio.")
                bull   = True
            else:
                signal = "SESGO ALCISTA"
                label  = "↑ FLUJO ALCISTA — precio en zona media"
                color  = "#69f0ae"
                expl   = (f"Z-Diff {z:.2f} con precio en zona media del rango ({price_pct*100:.0f}%). "
                          f"Flujo positivo sin contexto extremo claro. Monitoriza ruptura.")
                bull   = True
        else:
            if breaking_down or (not rising and in_bottom and macro <= 0):
                signal = "VENTA — MOMENTUM"
                label  = "▼ VENTA (momentum + flujo confirmados)"
                color  = "#ff1744"
                expl   = (f"Z-Diff {z:.2f} con {'ruptura del mínimo previo' if breaking_down else 'precio en zona baja y cayendo'}. "
                          f"Flujo e impulso alineados en bajista. "
                          f"{'Macro bajista confirma.' if macro<0 else ''} Entrada Stop bajista.")
                bull   = False
            elif in_top and not rising:
                signal = "RECHAZO EN RESISTENCIA"
                label  = "▼ VENTA — rechazo desde máximos con flujo"
                color  = "#ff1744"
                expl   = (f"Z-Diff {z:.2f} negativo con precio rechazando desde la zona alta del rango "
                          f"({price_pct*100:.0f}%). Flujo vendedor confirma el rechazo en resistencia. "
                          f"Entrada Limit short en retroceso al alza.")
                bull   = False
            elif in_bottom and rising:
                signal = "DIVERGENCIA ALCISTA"
                label  = "⚡ POSIBLE GIRO — precio sube vs flujo bajo"
                color  = "#ffd600"
                expl   = (f"Z-Diff {z:.2f} negativo pero precio subiendo desde mínimos. "
                          f"Posible giro alcista — el precio anticipa al flujo. "
                          f"Espera confirmación antes de operar.")
                bull   = None
            elif macro > 0:
                signal = "PRECAUCIÓN BAJISTA"
                label  = "⚡ FLUJO BAJISTA — macro en contra"
                color  = "#ffd600"
                expl   = (f"Z-Diff {z:.2f} negativo pero contexto macro alcista. "
                          f"Posible corrección temporal. No agresivo en cortos.")
                bull   = False
            else:
                signal = "SESGO BAJISTA"
                label  = "↓ FLUJO BAJISTA — precio en zona media"
                color  = "#ff6b6b"
                expl   = (f"Z-Diff {z:.2f} con precio en zona media ({price_pct*100:.0f}%). "
                          f"Flujo negativo sin contexto extremo. Monitoriza ruptura bajista.")
                bull   = False

    elif abs_z > 0.5:
        if z > 0:
            signal = "SESGO ALCISTA"
            label  = "↑ SESGO LARGO MODERADO"
            color  = "#69f0ae"
            expl   = (f"Flujo positivo moderado ({z:.2f}). Precio en {price_pct*100:.0f}% del rango. "
                      f"{'Zona alta: cuidado con resistencia.' if in_top else 'Zona baja: buena zona de valor.' if in_bottom else 'Zona media: neutral.'}")
            bull   = True
        else:
            signal = "SESGO BAJISTA"
            label  = "↓ SESGO CORTO MODERADO"
            color  = "#ff6b6b"
            expl   = (f"Flujo negativo moderado ({z:.2f}). Precio en {price_pct*100:.0f}% del rango. "
                      f"{'Zona baja: cuidado con soporte.' if in_bottom else 'Zona alta: posible distribución lenta.' if in_top else 'Zona media: neutral.'}")
            bull   = False
    else:
        signal = "NEUTRAL"
        label  = "➡ NEUTRAL — subasta en equilibrio"
        color  = "#ffd600"
        expl   = (f"Z-Diff en zona neutral ({z:.2f}). Precio en {price_pct*100:.0f}% del rango. "
                  f"No hay mano fuerte dominante. Evita entradas direccionales.")
        bull   = None

    return {
        "signal":    signal,
        "label":     label,
        "color":     color,
        "expl":      expl,
        "bull":      bull,
        "rising":    rising,
        "abs_z":     abs_z,
        "extreme":   abs_z > 2.2,
        "price_pct": price_pct,       # posición en rango 0-1
        "in_top":    in_top,
        "in_bottom": in_bottom,
        "breaking_up":   breaking_up,
        "breaking_down": breaking_down,
    }


def monte_carlo_multistep(price, returns, sims, steps, z_adj, vol_mult):
    mu    = returns.mean()
    sigma = returns.std() * vol_mult
    drift = mu + z_adj * sigma * 0.15
    rng   = np.random.default_rng()
    eps   = rng.standard_normal((sims, steps))
    final = price * np.exp(((drift - 0.5*sigma**2) + sigma*eps).sum(axis=1))
    return final, sigma, drift


def get_expiry_date(days: int) -> str:
    d, added = datetime.now(), 0
    while added < days:
        d += timedelta(days=1)
        if d.weekday() < 5:
            added += 1
    return d.strftime("%a %d %b %Y") + " 23:59h"


def calc_lots(entry, sl, account, risk_pct, instr):
    risk_usd = account * (risk_pct / 100)
    sl_dist  = abs(entry - sl)
    if sl_dist == 0:
        return 0, 0, "—"
    if instr == "Forex std (100k)":
        lots  = risk_usd / ((sl_dist / 0.0001) * 10)
        label = f"{lots:.2f} lotes std ({lots*100000:,.0f} u.)"
    elif instr == "Forex mini (10k)":
        lots  = risk_usd / ((sl_dist / 0.0001) * 1)
        label = f"{lots:.2f} mini lotes"
    elif instr == "XAU/USD":
        lots  = risk_usd / (sl_dist * 100)
        label = f"{lots:.3f} lotes XAU ({lots*100:.1f} oz)"
    else:
        lots  = risk_usd / sl_dist
        label = f"{lots:.2f} contratos CFD"
    return lots, risk_usd, label

# ─── PROMPTS PARA COPIAR/PEGAR EN IA GRATUITA ────────────────────────────────
def build_context_prompt(ticker, asset_type, horizon) -> str:
    today = datetime.now().strftime("%A, %d de %B de %Y")
    return f"""Hoy es {today}. Eres un analista swing trader experto.

Analiza el contexto actual de mercado para {ticker} ({asset_type}) para los próximos {horizon} días.
Considera: calendario económico de esta semana, tendencia macro, eventos de riesgo y sentimiento institucional.

Responde SOLO con este JSON exacto, sin texto extra, sin backticks, sin explicaciones:
{{"macro":0,"macro_label":"Neutral","macro_why":"1 frase corta explicando el sesgo macro","news":0,"news_label":"Neutros","news_why":"1 frase con los eventos clave de esta semana","vol":"normal","vol_label":"Normal","vol_why":"1 frase sobre volatilidad esperada","summary":"2-3 frases sobre el sesgo swing {horizon}d de {ticker}: tendencia, eventos y recomendación direccional"}}

Valores: macro y news = entero entre -2 y 2 · vol = "low", "normal" o "high"."""


def build_analysis_prompt(ticker, price, last_z, last_rmf, bull_pct,
                           sigma, atr, mc_mean, macro, news,
                           asset_type, horizon, n_candles, ctx_summary, dec) -> str:
    macro_lbl = ["muy bajista","bajista","neutral","alcista","muy alcista"][macro+2]
    news_lbl  = ["muy negativos","negativos","neutros","positivos","muy positivos"][news+2]
    ctx_block = f"\nContexto de mercado actual: {ctx_summary}" if ctx_summary else ""
    return f"""Eres un trader institucional swing. Escribe un análisis técnico en español (4-5 frases). Sin asteriscos ni markdown.

Activo: {ticker} ({asset_type}) | Horizonte: {horizon}d | Timeframe: {TF_LABEL}
Precio actual: {price:.{dec}f} | Precio esperado MC ({horizon}d): {mc_mean:.{dec}f}
Z-Diff {TF_LABEL}: {last_z:.3f} — señal contextual: ver análisis del modelo
RMF acumulado: {last_rmf:,.0f} | Probabilidad alcista: {bull_pct:.1f}%
Volatilidad σ {TF_LABEL}: {sigma*100:.3f}% | ATR {TF_LABEL} real: {atr:.{dec}f}
Contexto macro ({horizon}d): {macro_lbl} | Noticias/eventos: {news_lbl}{ctx_block}
Velas {TF_LABEL} analizadas: {n_candles}

Valida si el Z-Diff {TF_LABEL} confirma el sesgo del Monte Carlo multi-step. Describe la presencia institucional en el Order Flow. Justifica si la entrada debe ser Stop (ruptura) o Limit (pullback) para un swing GTC de {horizon} días."""


def parse_context_json(raw: str) -> dict:
    """Extrae el JSON de la respuesta pegada por el usuario."""
    try:
        m = re.search(r'\{[\s\S]*\}', raw)
        if not m:
            raise ValueError("No se encontró JSON en la respuesta")
        return json.loads(m.group())
    except Exception as e:
        st.error(f"No se pudo leer el JSON: {e}\nAsegúrate de copiar solo el bloque JSON.")
        return None

# ─── CHARTS ───────────────────────────────────────────────────────────────────
def plot_candles_zdiff(df):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                         row_heights=[0.65, 0.35], vertical_spacing=0.04)
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing_fillcolor="#00e676", increasing_line_color="#00e676",
        decreasing_fillcolor="#ff1744", decreasing_line_color="#ff1744",
        name=TF_LABEL
    ), row=1, col=1)
    colors = df["z_diff"].apply(
        lambda z: "#00e676" if z>1.5 else "#69f0ae" if z>0.5
        else "#ffd600" if z>-0.5 else "#ff6b6b" if z>-1.5 else "#ff1744"
    )
    fig.add_trace(go.Bar(x=df.index, y=df["z_diff"],
                          marker_color=colors, name="Z-Diff", opacity=0.9), row=2, col=1)
    for y, col in [(1.5,"rgba(0,230,118,.35)"),(-1.5,"rgba(255,23,68,.35)"),(0,"rgba(255,255,255,.15)")]:
        fig.add_hline(y=y, line_dash="dash", line_color=col, row=2, col=1)
    fig.update_layout(template="plotly_dark", paper_bgcolor="#04070d",
                       plot_bgcolor="#0a1019", height=520,
                       margin=dict(l=10,r=10,t=10,b=10),
                       xaxis_rangeslider_visible=False, showlegend=False)
    fig.update_yaxes(title_text=f"Precio {TF_LABEL}", row=1, col=1)
    fig.update_yaxes(title_text="Z-Diff", row=2, col=1)
    return fig


def plot_mc_histogram(final_prices, ref_price, entry, sl, tp, bull):
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=[p for p in final_prices if p<=ref_price], nbinsx=50,
        name="Bajista", marker_color="rgba(255,23,68,0.7)"))
    fig.add_trace(go.Histogram(
        x=[p for p in final_prices if p>ref_price], nbinsx=50,
        name="Alcista", marker_color="rgba(0,230,118,0.7)"))
    for val, col, lbl in [
        (ref_price,"rgba(255,255,255,0.85)","PRECIO"),
        (entry,"rgba(0,229,255,1)","ENTRADA"),
        (sl,"rgba(255,23,68,0.9)","SL"),
        (tp,"rgba(0,230,118,0.85)","TP p80"),
    ]:
        fig.add_vline(x=val, line_color=col, line_dash="dot", line_width=2,
                       annotation_text=lbl, annotation_font_color=col, annotation_position="top")
    fig.update_layout(barmode="overlay", template="plotly_dark",
                       paper_bgcolor="#04070d", plot_bgcolor="#0a1019",
                       height=300, margin=dict(l=10,r=10,t=30,b=10),
                       legend=dict(orientation="h", y=1.1),
                       xaxis_title="Precio proyectado", yaxis_title="Simulaciones")
    return fig

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuración")
    st.markdown("""
**Sin API Key necesaria.**
La app genera los prompts listos para copiar.
Pégalos en [Gemini](https://gemini.google.com), ChatGPT o cualquier IA gratuita
y pega la respuesta de vuelta aquí.
""")

    st.divider()
    st.markdown("### Activo")
    QUICK_MAP = {
        "EUR/USD":   ("EURUSD=X","forex"),
        "GBP/USD":   ("GBPUSD=X","forex"),
        "USD/JPY":   ("USDJPY=X","forex"),
        "XAU/USD 🥇":("GC=F","commodity"),
        "S&P 500":   ("^GSPC","index"),
        "DAX 40":    ("^GDAXI","index"),
        "NASDAQ":    ("^IXIC","index"),
        "— Manual —":("","forex"),
    }
    quick = st.selectbox("Acceso rápido", list(QUICK_MAP.keys()))
    default_sym, default_type = QUICK_MAP[quick]
    ticker     = st.text_input("Símbolo Yahoo Finance", value=default_sym,
                                 placeholder="EURUSD=X, GC=F, ^GSPC...")
    asset_type = st.selectbox("Tipo de activo",
                               ["forex","index","commodity","stock","crypto"],
                               index=["forex","index","commodity","stock","crypto"].index(default_type))

    st.divider()
    st.markdown(f"### Modelo — **{TF_LABEL}**")
    horizon   = st.selectbox("Horizonte operación", [3, 5, 7],
                               format_func=lambda x: f"{x} días (GTC)")
    n_candles = st.slider(f"Velas {TF_LABEL} a cargar", 20, 90, 42,
                           help="42 velas H4 ≈ 7 días")
    z_period  = st.slider("Periodo Z-Diff (velas H4)", 10, 30, 14)
    sims      = st.selectbox("Simulaciones MC", [2000, 5000, 10000], index=1)
    threshold = st.selectbox("Umbral mínimo %", [60, 65, 70], index=1)

    st.divider()
    st.markdown("### Gestión de riesgo")
    account  = st.number_input("Capital ($)", min_value=100, value=10000, step=500)
    risk_pct = st.slider("Riesgo por operación (%)", 0.5, 10.0, 2.0, 0.5)
    instr    = st.selectbox("Instrumento",
                             ["Forex std (100k)","Forex mini (10k)","XAU/USD","Índice CFD"])

    st.divider()
    st.caption("**Símbolos Yahoo Finance**\n\n"
               "Forex: `EURUSD=X` `GBPUSD=X` `USDJPY=X`\n\n"
               "XAU: `GC=F` · SP500: `^GSPC`\n\n"
               "DAX: `^GDAXI` · BTC: `BTC-USD`")

# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<h1 style='font-family:Rajdhani,sans-serif;font-size:32px;letter-spacing:4px;color:#00e5ff;margin-bottom:4px'>
  ORDER<span style='color:#ffd600'>FLOW</span> PRO
  <span style='font-size:16px;color:#ff9100;letter-spacing:2px;margin-left:8px'>{TF_LABEL} · SWING · IA LIBRE</span>
</h1>
<p style='color:#4a6080;font-size:11px;letter-spacing:2px;margin-bottom:20px'>
  MONTE CARLO MULTI-STEP · ORDER FLOW Z-DIFF · YAHOO FINANCE · GTC ORDERS
</p>
""", unsafe_allow_html=True)

st.info(
    "💡 **Sin API Key.** Esta app genera prompts listos para copiar. "
    "Pégalos en [Gemini gratis](https://gemini.google.com) o ChatGPT y pega la respuesta de vuelta. "
    "No necesitas cuenta de pago en ningún servicio."
)

# ─── SESSION STATE ────────────────────────────────────────────────────────────
for k in ["df","context","results","analysis_prompt"]:
    if k not in st.session_state:
        st.session_state[k] = None

# ─── CARGAR VELAS ────────────────────────────────────────────────────────────
load_btn = st.button(f"📡 CARGAR VELAS {TF_LABEL} — Yahoo Finance",
                      use_container_width=True, type="primary")

if load_btn:
    if not ticker:
        st.error("Introduce un símbolo primero.")
    else:
        with st.spinner(f"Descargando velas {TF_LABEL} de Yahoo Finance..."):
            try:
                raw = yf.download(ticker, period=TF_PERIOD, interval=TF_INTERVAL,
                                   auto_adjust=True, progress=False)
                if raw.empty:
                    st.error(f"Sin datos para '{ticker}'. Comprueba el símbolo.")
                else:
                    if isinstance(raw.columns, pd.MultiIndex):
                        raw.columns = raw.columns.get_level_values(0)
                    df = raw.tail(n_candles).copy()
                    df.index = pd.to_datetime(df.index)
                    st.session_state.df      = df
                    st.session_state.results = None
                    lp  = float(df["Close"].iloc[-1])
                    dec_p = 1 if lp>1000 else 2 if lp>100 else 5
                    st.success(f"✓ {len(df)} velas {TF_LABEL} · {ticker} · Precio: **{lp:.{dec_p}f}**")
            except Exception as e:
                st.error(f"Error: {e}")

# ─── CONTEXTO — PASO 1: COPIAR PROMPT ────────────────────────────────────────
st.markdown("---")
st.markdown("### 🤖 Paso 1 — Contexto de mercado (copia el prompt → pega en IA → pega respuesta)")

with st.expander("📋 Ver prompt para contexto de mercado", expanded=False):
    ctx_prompt = build_context_prompt(ticker, asset_type, horizon)
    st.code(ctx_prompt, language="text")
    st.caption("👆 Copia todo el texto de arriba y pégalo en Gemini, ChatGPT o cualquier IA gratuita.")

ctx_response = st.text_area(
    "📥 Pega aquí la respuesta de la IA (el bloque JSON):",
    height=120,
    placeholder='{"macro":1,"macro_label":"Alcista","macro_why":"...","news":0,...}',
    key="ctx_response_input"
)

if st.button("✅ Procesar contexto", use_container_width=True):
    if ctx_response.strip():
        parsed = parse_context_json(ctx_response)
        if parsed:
            st.session_state.context = parsed
            st.success("✓ Contexto procesado correctamente")
            st.rerun()
    else:
        st.warning("Pega primero la respuesta de la IA.")

# ── Mostrar contexto procesado ─────────────────────────────────────────────
if st.session_state.context:
    ctx = st.session_state.context
    sc  = lambda v: "#00e676" if v>0 else "#ff1744" if v<0 else "#ffd600"
    vc  = lambda v: "#ff9100" if v=="high" else "#00e5ff" if v=="low" else "#cdd9e5"
    c1, c2, c3 = st.columns(3)
    for col, lbl, vk, lk, wk, cfn in [
        (c1, f"SESGO MACRO ({horizon}d)", "macro","macro_label","macro_why", sc),
        (c2, "EVENTOS SEMANA",            "news", "news_label", "news_why",  sc),
        (c3, "VOLATILIDAD ESPERADA",      "vol",  "vol_label",  "vol_why",   vc),
    ]:
        with col:
            st.markdown(f"""<div class='metric-card'>
                <div style='font-size:9px;letter-spacing:3px;color:#4a6080;
                    text-transform:uppercase;margin-bottom:6px'>{lbl}</div>
                <div style='font-family:Rajdhani,sans-serif;font-size:22px;
                    font-weight:700;color:{cfn(ctx[vk])}'>{ctx[lk]}</div>
                <div style='font-size:10px;color:#4a6080;margin-top:4px'>{ctx[wk]}</div>
            </div>""", unsafe_allow_html=True)
    st.info(f"💬 {ctx['summary']}")

# ── Candle chart ──────────────────────────────────────────────────────────────
if st.session_state.df is not None:
    df = st.session_state.df.copy()
    df = calc_order_flow(df, z_period)
    st.markdown(f"### 📈 Velas {TF_LABEL} + Z-Diff Order Flow")
    st.plotly_chart(plot_candles_zdiff(df), use_container_width=True)

    run_btn = st.button("▶  EJECUTAR MODELO COMPLETO",
                         use_container_width=True, type="primary")

    if run_btn:
        with st.spinner("Ejecutando motor cuantitativo..."):
            prog = st.progress(0, text=f"Calculando Order Flow {TF_LABEL}...")

            last_z    = float(df["z_diff"].iloc[-1])
            last_rmf  = float(df["rmf"].iloc[-1])
            # Interpret Z-Diff in context (needs macro from context, default 0)
            macro_pre = (st.session_state.context or {}).get("macro", 0)
            zdiff_ctx = interpret_zdiff(last_z, df, macro_pre)
            prog.progress(15, text="Calculando log-retornos...")

            closes  = df["Close"].values.astype(float)
            returns = np.diff(np.log(closes))
            prog.progress(25, text=f"Monte Carlo multi-step {TF_LABEL}...")

            ctx     = st.session_state.context or {}
            macro   = ctx.get("macro", 0)
            news_v  = ctx.get("news",  0)
            vol_v   = ctx.get("vol",   "normal")
            ctx_sum = ctx.get("summary","")
            vm      = 0.7 if vol_v=="low" else 1.5 if vol_v=="high" else 1.0
            z_adj   = float(np.clip(last_z, -2, 2))
            h4day   = H4_FX if asset_type in ["forex","crypto"] else H4_EQ
            mc_steps= horizon * h4day

            final_prices, sigma, drift = monte_carlo_multistep(
                float(closes[-1]), returns, sims, mc_steps, z_adj, vm
            )
            prog.progress(55, text="Proyectando distribución...")

            price    = float(closes[-1])
            sorted_p = np.sort(final_prices)
            adj_bull = float(np.clip(
                np.sum(final_prices>price)/sims*100 + (macro+news_v)/4*8, 10, 90
            ))
            adj_bear = 100 - adj_bull
            mc_mean  = float(final_prices.mean())
            p5, p95  = float(np.percentile(sorted_p,5)), float(np.percentile(sorted_p,95))
            atr      = float((df.tail(14)["High"]-df.tail(14)["Low"]).mean())

            prog.progress(68, text="Calculando niveles GTC...")

            pct = lambda p: float(np.percentile(sorted_p, p))

            # Direction: combine MC probability + Z-Diff context
            mc_bull   = adj_bull > adj_bear
            z_bull    = zdiff_ctx["bull"]
            if z_bull is None:
                # Neutral Z: follow Monte Carlo
                prim_bull = mc_bull
            elif z_bull == mc_bull:
                # Agreement: strong signal
                prim_bull = mc_bull
            else:
                # Disagreement: use MC but flag it
                prim_bull = mc_bull
            last3     = df.tail(3)
            e_stop    = (float(last3["High"].max()) + atr*0.08 if prim_bull
                         else float(last3["Low"].min()) - atr*0.08)
            e_lim     = pct(38) if prim_bull else pct(62)
            sl        = pct(8)  if prim_bull else pct(92)
            tp        = pct(80) if prim_bull else pct(20)
            use_stop  = last_z > 0.8 if prim_bull else last_z < -0.8
            entry     = e_stop if use_stop else e_lim
            o_type    = "STOP" if use_stop else "LIMIT"
            exp_date  = get_expiry_date(horizon)

            prog.progress(82, text="Preparando prompt de análisis...")

            dec = 1 if price>1000 else 2 if price>100 else 4
            # Guardar prompt de análisis en session_state para mostrarlo tras el modelo
            st.session_state.analysis_prompt = build_analysis_prompt(
                ticker, price, last_z, last_rmf, adj_bull,
                sigma, atr, mc_mean, macro, news_v,
                asset_type, horizon, len(df), ctx_sum, dec
            )
            ai_text = ""  # se rellenará cuando el usuario pegue la respuesta

            prog.progress(100, text="¡Completado!")
            prog.empty()

            st.session_state.results = dict(
                zdiff_ctx=zdiff_ctx,
                price=price, last_z=last_z, last_rmf=last_rmf,
                adj_bull=adj_bull, adj_bear=adj_bear,
                mc_mean=mc_mean, p5=p5, p95=p95,
                sigma=sigma, atr=atr, z_adj=z_adj,
                final_prices=final_prices,
                prim_bull=prim_bull, use_stop=use_stop, o_type=o_type,
                entry=entry, sl=sl, tp=tp, exp_date=exp_date,
                mc_steps=mc_steps, ai_text=ai_text, macro=macro, df_of=df
            )

# ─── RESULTS ──────────────────────────────────────────────────────────────────
if st.session_state.results:
    r   = st.session_state.results
    dec = 1 if r["price"]>1000 else 2 if r["price"]>100 else 4

    st.divider()
    bc = "#00e676" if r["adj_bull"]>=60 else "#ff1744" if r["adj_bull"]<=40 else "#ffd600"
    bt = ("SESGO ALCISTA ▲" if r["adj_bull"]>=60
          else "SESGO BAJISTA ▼" if r["adj_bull"]<=40 else "SESGO NEUTRAL ➡")
    cf = "Alta" if r["adj_bull"]>65 or r["adj_bull"]<35 else "Media" if r["adj_bull"]>58 or r["adj_bull"]<42 else "Baja"

    st.markdown(f"""
    <h2 style='font-family:Rajdhani,sans-serif;font-size:22px;letter-spacing:3px;color:{bc}'>
      {bt}
      <span style='font-size:13px;color:#4a6080;font-weight:400'>
        &nbsp;·&nbsp; {TF_LABEL} · {horizon}d GTC · exp. {r["exp_date"]}
        &nbsp;·&nbsp; MC {sims:,} sims · {r["mc_steps"]} pasos {TF_LABEL}
        &nbsp;·&nbsp; Confianza: {cf}
      </span>
    </h2>""", unsafe_allow_html=True)

    # Probabilities
    cb, cs = st.columns(2)
    with cb:
        st.markdown(f"""<div class='metric-card' style='border-top:2px solid #00e676'>
            <div style='font-size:9px;letter-spacing:3px;color:#00e676;text-transform:uppercase;margin-bottom:8px'>▲ POSITIVO EN {horizon} DÍAS</div>
            <div class='big-prob bull-color'>{r["adj_bull"]:.1f}%</div>
            <div style='font-size:10px;color:#4a6080;margin-top:6px'>IC 95%: [{r["p5"]:.{dec}f}, {r["p95"]:.{dec}f}]</div>
        </div>""", unsafe_allow_html=True)
    with cs:
        st.markdown(f"""<div class='metric-card' style='border-top:2px solid #ff1744'>
            <div style='font-size:9px;letter-spacing:3px;color:#ff1744;text-transform:uppercase;margin-bottom:8px'>▼ NEGATIVO EN {horizon} DÍAS</div>
            <div class='big-prob bear-color'>{r["adj_bear"]:.1f}%</div>
            <div style='font-size:10px;color:#4a6080;margin-top:6px'>IC 95%: [{r["p5"]:.{dec}f}, {r["p95"]:.{dec}f}]</div>
        </div>""", unsafe_allow_html=True)

    # Mini stats
    z   = r["last_z"]
    zctx= r.get("zdiff_ctx", {})
    zs  = zctx.get("label", "—")
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric(f"Z-Diff {TF_LABEL}", f"{z:.3f}", delta=zs,
                        delta_color="normal" if z>0 else "inverse" if z<0 else "off")
    with c2: st.metric("Precio esperado (MC)", f"{r['mc_mean']:.{dec}f}",
                        delta=f"{((r['mc_mean']/r['price'])-1)*100:+.3f}%")
    with c3: st.metric(f"Volatilidad σ {TF_LABEL}", f"{r['sigma']*100:.3f}%")
    with c4: st.metric(f"ATR {TF_LABEL} real", f"{r['atr']:.{dec}f}")

    # ── Z-Diff interpretación contextual ────────────────────────────────────
    zctx_color  = zctx.get("color", "#ffd600")
    zctx_signal = zctx.get("signal", "—")
    zctx_expl   = zctx.get("expl", "—")
    zctx_rising = zctx.get("rising", True)
    zctx_ext    = zctx.get("extreme", False)

    # Divergence warning if Z and MC disagree
    z_bull_val = zctx.get("bull")
    mc_bull    = r["prim_bull"]
    divergence = (z_bull_val is not None) and (z_bull_val != mc_bull)

    price_pct_val  = zctx.get("price_pct", 0.5)
    in_top_val     = zctx.get("in_top", False)
    in_bottom_val  = zctx.get("in_bottom", False)
    brk_up_val     = zctx.get("breaking_up", False)
    brk_dn_val     = zctx.get("breaking_down", False)

    range_label = ("🔝 En máximos del rango" if in_top_val
                   else "🔻 En mínimos del rango" if in_bottom_val
                   else "↔ En zona media del rango")
    struct_label = ("💥 Rompiendo máximo previo" if brk_up_val
                    else "💥 Rompiendo mínimo previo" if brk_dn_val
                    else "— Sin ruptura")

    st.markdown(f"""
    <div style='background:#0a1019;border:1px solid {zctx_color};border-left:4px solid {zctx_color};
        border-radius:4px;padding:16px 20px;margin-bottom:12px'>
        <div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;flex-wrap:wrap;gap:8px'>
            <div style='font-family:Rajdhani,sans-serif;font-size:20px;font-weight:700;
                color:{zctx_color};letter-spacing:2px'>{zctx_signal}</div>
            <div style='display:flex;gap:16px;font-size:10px;color:#4a6080;flex-wrap:wrap'>
                <span>Z-Diff: <b style='color:{zctx_color}'>{z:.3f}</b></span>
                <span>Precio: <b style='color:{"#00e676" if zctx_rising else "#ff1744"}'>{"↑ subiendo" if zctx_rising else "↓ cayendo"}</b></span>
                <span>Rango: <b style='color:#cdd9e5'>{price_pct_val*100:.0f}%</b> — {range_label}</span>
                <span style='color:{"#ff9100" if brk_up_val or brk_dn_val else "#4a6080"}'>{struct_label}</span>
                {"<span style='color:#ff9100'>⚠ ZONA EXTREMA</span>" if zctx_ext else ""}
            </div>
        </div>
        <div style='font-size:12px;color:#cdd9e5;line-height:1.7'>{zctx_expl}</div>
        {"<div style='margin-top:8px;padding:8px 12px;background:rgba(255,145,0,.08);border:1px solid rgba(255,145,0,.3);border-radius:3px;font-size:11px;color:#ff9100'>⚡ <b>Divergencia Z vs MC:</b> El Order Flow y Monte Carlo apuntan en direcciones opuestas. Reduce el tamaño de posición y espera confirmación.</div>" if divergence else ""}
    </div>
    """, unsafe_allow_html=True)

    # Z-Diff gauge
    zc = "#00e676" if z>1.5 else "#69f0ae" if z>0.5 else "#ffd600" if z>-0.5 else "#ff6b6b" if z>-1.5 else "#ff1744"
    fig_g = go.Figure(go.Indicator(
        mode="gauge+number", value=float(np.clip(z,-3,3)),
        title={"text": f"Z-Diff Order Flow {TF_LABEL}", "font":{"size":14}},
        gauge={
            "axis":{"range":[-3,3],"tickwidth":1,"tickcolor":"#4a6080"},
            "bar":{"color":zc,"thickness":0.25},
            "bgcolor":"#0a1019","borderwidth":1,"bordercolor":"#1a2d40",
            "steps":[
                {"range":[-3,-1.5],"color":"rgba(255,23,68,.2)"},
                {"range":[-1.5,-.5],"color":"rgba(255,107,107,.1)"},
                {"range":[-.5,.5], "color":"rgba(255,214,0,.1)"},
                {"range":[.5,1.5], "color":"rgba(105,240,174,.1)"},
                {"range":[1.5,3],  "color":"rgba(0,230,118,.2)"},
            ],
            "threshold":{"line":{"color":"white","width":3},"value":z}
        },
        number={"font":{"color":zc,"size":28}}
    ))
    fig_g.update_layout(height=220, paper_bgcolor="#04070d",
                         font_color="#cdd9e5", margin=dict(l=20,r=20,t=40,b=20))
    st.plotly_chart(fig_g, use_container_width=True)

    # MC histogram
    st.markdown(f"### 📊 Distribución MC — {r['mc_steps']} pasos {TF_LABEL} ({horizon} días)")
    st.plotly_chart(plot_mc_histogram(
        r["final_prices"], r["price"], r["entry"], r["sl"], r["tp"], r["prim_bull"]
    ), use_container_width=True)

    # Order
    st.markdown(f"### 📋 Orden GTC — Swing {horizon} Días")
    prob = r["adj_bull"] if r["prim_bull"] else r["adj_bear"]

    if prob < threshold:
        st.markdown(f"""<div class='order-box order-warn'>
            <div style='font-family:Rajdhani,sans-serif;font-size:24px;font-weight:700;
                color:#ffd600;letter-spacing:3px;margin-bottom:8px'>⚠ NO OPERAR — CONVICCIÓN INSUFICIENTE</div>
            <div style='font-size:12px;color:#4a6080;line-height:1.9'>
                Probabilidad: <span style='color:#ffd600'>{prob:.1f}%</span>
                — por debajo del umbral de <span style='color:#cdd9e5'>{threshold}%</span><br>
                Z-Diff {TF_LABEL}: <span style='color:#cdd9e5'>{r["last_z"]:.3f}</span>
                — {"sin direccionalidad clara" if abs(r["last_z"])<0.5 else "señal débil"}<br>
                <span style='color:#ffd600'>💡 Preservar capital también es una posición válida.</span>
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        side  = "BUY" if r["prim_bull"] else "SELL"
        sc    = "#00e676" if r["prim_bull"] else "#ff1744"
        rr    = abs(r["tp"]-r["entry"]) / max(abs(r["entry"]-r["sl"]), 1e-10)
        scov  = np.mean(((r["final_prices"]>=r["entry"])&(r["final_prices"]<=r["tp"]))
                        if r["prim_bull"] else
                        ((r["final_prices"]<=r["entry"])&(r["final_prices"]>=r["tp"])))*100
        zr    = (f"Z-Diff {r['last_z']:.2f} — ruptura {'alcista' if r['prim_bull'] else 'bajista'}"
                 if r["use_stop"] else
                 f"Z-Diff {r['last_z']:.2f} — pullback percentil {'38' if r['prim_bull'] else '62'} MC")

        oc1,oc2,oc3,oc4,oc5 = st.columns([1.2,1.5,1.2,2.2,1])
        with oc1:
            st.markdown(f"""<div style='text-align:center;
                background:{"rgba(0,230,118,.1)" if r["prim_bull"] else "rgba(255,23,68,.1)"};
                border:1px solid {sc};border-radius:4px;padding:14px 8px'>
                <div style='font-family:Rajdhani,sans-serif;font-size:22px;
                    font-weight:700;color:{sc};letter-spacing:2px'>{side}</div>
                <div style='font-size:12px;color:{sc}'>{r["o_type"]}</div>
            </div>""", unsafe_allow_html=True)
        with oc2:
            st.markdown(f"""<div>
                <div style='font-family:Rajdhani,sans-serif;font-size:26px;font-weight:700'>{r["entry"]:.{dec}f}</div>
                <div style='font-size:9px;color:#4a6080'>GTC · exp. {r["exp_date"]}</div>
            </div>""", unsafe_allow_html=True)
        with oc3:
            st.markdown(f"""<div style='font-size:12px;line-height:2.1'>
                SL: <span style='color:#ff1744;font-weight:600'>{r["sl"]:.{dec}f}</span><br>
                TP: <span style='color:#00e676;font-weight:600'>{r["tp"]:.{dec}f}</span><br>
                RR: <span style='color:#cdd9e5'>1:{rr:.1f}</span>
            </div>""", unsafe_allow_html=True)
        with oc4:
            st.markdown(f"""<div style='font-size:10px;color:#4a6080;line-height:1.7'>
                {zr}<br>{scov:.0f}% simulaciones MC entre entrada y TP (p80)
            </div>""", unsafe_allow_html=True)
        with oc5:
            st.markdown(f"""<div style='font-family:Rajdhani,sans-serif;font-size:32px;
                font-weight:700;color:{sc};text-align:right'>{prob:.1f}%</div>""",
                unsafe_allow_html=True)

        # Lot calculator
        st.markdown("#### 💰 Calculadora de Posición")
        lots, risk_usd, lot_label = calc_lots(r["entry"], r["sl"], account, risk_pct, instr)
        profit = risk_usd * rr if lots > 0 else 0
        lc1,lc2,lc3,lc4 = st.columns(4)
        with lc1: st.metric("Tamaño posición", lot_label)
        with lc2: st.metric("Riesgo en $",    f"${risk_usd:.0f}")
        with lc3: st.metric("Beneficio pot.", f"${profit:.0f}")
        with lc4: st.metric("Ratio R:R",      f"1:{rr:.1f}")

    # ── Paso 2: Análisis IA (prompt copy/paste) ─────────────────────────────
    st.markdown("---")
    st.markdown("### 🤖 Paso 2 — Análisis institucional (copia el prompt → pega en IA → pega respuesta)")

    with st.expander("📋 Ver prompt para análisis institucional", expanded=True):
        if "analysis_prompt" in st.session_state and st.session_state.analysis_prompt:
            st.code(st.session_state.analysis_prompt, language="text")
            st.caption("👆 Copia este prompt y pégalo en Gemini, ChatGPT o cualquier IA gratuita.")
        else:
            st.info("Ejecuta el modelo primero para generar el prompt de análisis.")

    analysis_response = st.text_area(
        "📥 Pega aquí el análisis de la IA:",
        value=r.get("ai_text", ""),
        height=160,
        placeholder="Pega aquí el texto de análisis que te devuelva la IA...",
        key="analysis_response_input"
    )
    if st.button("✅ Guardar análisis", key="save_analysis"):
        if analysis_response.strip():
            st.session_state.results["ai_text"] = analysis_response
            st.success("✓ Análisis guardado")
            st.rerun()

    if r.get("ai_text"):
        st.markdown("**Análisis guardado:**")
        st.info(r["ai_text"])

    # OF table
    with st.expander(f"📋 Tabla Order Flow {TF_LABEL} completa"):
        df_show = r["df_of"][["Open","High","Low","Close","Volume",
                               "tp","raw_mf","rmf","z_diff"]].copy()
        df_show.columns = ["Open","High","Low","Close","Vol","TP","Raw MF","RMF Acum.","Z-Diff"]
        df_show = df_show.round(5)
        def cz(v):
            if   v >  1.5: return "color:#00e676;font-weight:bold"
            elif v >  0.5: return "color:#69f0ae"
            elif v > -0.5: return "color:#ffd600"
            elif v > -1.5: return "color:#ff6b6b"
            else:          return "color:#ff1744;font-weight:bold"
        st.dataframe(df_show.style.applymap(cz, subset=["Z-Diff"]), use_container_width=True)

# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='font-size:10px;color:#4a6080;text-align:center;line-height:1.8'>
⚠️ Modelo educativo-cuantitativo. No constituye asesoramiento financiero.<br>
Monte Carlo multi-step GBM · Z-Diff Order Flow normalizado · Datos: Yahoo Finance · IA: Gemini 2.0 Flash
</div>
""", unsafe_allow_html=True)
