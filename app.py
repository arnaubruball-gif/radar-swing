import streamlit as st
import streamlit.components.v1 as components

# Configuración de página ancha para que se vea profesional
st.set_page_config(page_title="ORDER FLOW PRO", layout="wide")

# Usamos st.cache_data para que no recargue el HTML todo el tiempo
@st.cache_data
def get_html():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <style>
            <!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ORDER FLOW PRO — Swing 3D</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Rajdhani:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#04070d;--s0:#060b13;--s1:#0a1019;--border:#12202e;--border2:#1a2d40;
  --green:#00e676;--green2:#69f0ae;--red:#ff1744;--red2:#ff6b6b;
  --blue:#0090ff;--blue2:#40b4ff;--yellow:#ffd600;--orange:#ff9100;
  --purple:#d500f9;--cyan:#00e5ff;--text:#cdd9e5;--muted:#4a6080;
  --mono:'JetBrains Mono',monospace;--display:'Rajdhani',sans-serif;
}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:var(--mono);min-height:100vh;overflow-x:hidden}
body::after{content:'';position:fixed;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,.07) 2px,rgba(0,0,0,.07) 4px);pointer-events:none;z-index:9999}
.wrap{position:relative;z-index:1;max-width:1120px;margin:0 auto;padding:20px 16px 80px}
.hdr{display:flex;align-items:center;justify-content:space-between;padding:14px 0 16px;border-bottom:1px solid var(--border2);margin-bottom:22px}
.logo{font-family:var(--display);font-size:26px;font-weight:700;letter-spacing:4px;color:var(--cyan);text-shadow:0 0 20px rgba(0,229,255,.3)}
.logo span{color:var(--yellow)}.logo sub{font-size:13px;color:var(--orange);letter-spacing:2px;vertical-align:middle;margin-left:6px}
.hdr-r{display:flex;gap:14px;align-items:center}
.clk{font-size:11px;color:var(--yellow);background:rgba(255,214,0,.06);border:1px solid rgba(255,214,0,.2);padding:5px 12px;border-radius:2px}
.live{display:flex;align-items:center;gap:6px;font-size:9px;letter-spacing:3px;color:var(--green);text-transform:uppercase}
.dot{width:7px;height:7px;border-radius:50%;background:var(--green);animation:blink 1.4s infinite}
@keyframes blink{0%,100%{opacity:1;box-shadow:0 0 6px var(--green)}50%{opacity:.3;box-shadow:none}}
.tabs{display:flex;gap:2px;margin-bottom:20px;border-bottom:1px solid var(--border2)}
.tab{font-family:var(--display);font-size:13px;font-weight:600;letter-spacing:2px;text-transform:uppercase;padding:10px 20px;cursor:pointer;color:var(--muted);border-bottom:2px solid transparent;transition:all .2s}
.tab.active{color:var(--cyan);border-bottom-color:var(--cyan)}.tab:hover:not(.active){color:var(--text)}
.tab-panel{display:none}.tab-panel.active{display:block}
.sec{font-size:9px;letter-spacing:4px;text-transform:uppercase;color:var(--blue2);margin-bottom:12px}.sec::before{content:'// ';color:var(--muted)}
.card{background:var(--s1);border:1px solid var(--border);border-radius:3px;padding:18px 20px;margin-bottom:14px}
.field{display:flex;flex-direction:column;gap:6px}
.field label{font-size:9px;letter-spacing:3px;text-transform:uppercase;color:var(--muted)}
.field input,.field select{background:var(--s0);border:1px solid var(--border2);color:var(--text);font-family:var(--mono);font-size:13px;padding:9px 12px;border-radius:2px;outline:none;transition:border-color .15s;width:100%}
.field input:focus,.field select:focus{border-color:var(--blue);box-shadow:0 0 0 2px rgba(0,144,255,.1)}
.field select option{background:var(--s1)}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.g3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px}
.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.pills{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}
.pill{font-family:var(--display);font-size:13px;font-weight:600;letter-spacing:2px;padding:7px 16px;border:1px solid var(--border2);border-radius:2px;cursor:pointer;color:var(--muted);background:transparent;transition:all .15s}
.pill:hover{color:var(--text);border-color:var(--blue2)}
.pill.active{color:var(--cyan);border-color:var(--cyan);background:rgba(0,229,255,.06)}
.pill.gold.active{color:var(--yellow);border-color:var(--yellow);background:rgba(255,214,0,.06)}
.pill.idx.active{color:var(--orange);border-color:var(--orange);background:rgba(255,145,0,.06)}
.sbar{display:flex;align-items:center;gap:10px;padding:9px 14px;border-radius:2px;font-size:10px;letter-spacing:2px;text-transform:uppercase;margin-bottom:10px;border:1px solid var(--border2);color:var(--muted);background:var(--s0)}
.sbar.ok{border-color:rgba(0,230,118,.3);color:var(--green);background:rgba(0,230,118,.04)}
.sbar.err{border-color:rgba(255,23,68,.3);color:var(--red2);background:rgba(255,23,68,.04)}
.sbar.loading{border-color:rgba(255,214,0,.3);color:var(--yellow);background:rgba(255,214,0,.04)}
.btn{font-family:var(--display);font-size:14px;font-weight:700;letter-spacing:3px;text-transform:uppercase;padding:11px 22px;cursor:pointer;border-radius:2px;border:1px solid;transition:all .2s;display:inline-block}
.btn-c{border-color:var(--cyan);color:var(--cyan);background:rgba(0,229,255,.05)}
.btn-c:hover{background:var(--cyan);color:var(--bg);box-shadow:0 0 24px rgba(0,229,255,.3)}
.btn-c:disabled{opacity:.3;cursor:not-allowed;pointer-events:none}
.btn-block{width:100%;text-align:center}
.btn-sm{font-size:10px;letter-spacing:2px;padding:7px 14px;border-color:var(--border2);color:var(--muted);background:transparent}
.btn-sm:hover{border-color:var(--blue2);color:var(--blue2);background:rgba(0,144,255,.06)}
.btn-del{font-size:9px;padding:4px 10px;letter-spacing:1px;border-color:rgba(255,23,68,.3);color:var(--red2);background:transparent}
.btn-del:hover{background:rgba(255,23,68,.1)}
.tbl-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12px}
th{font-size:8px;letter-spacing:3px;text-transform:uppercase;color:var(--muted);padding:8px 10px;text-align:right;border-bottom:1px solid var(--border2)}
th:first-child{text-align:left}
td{padding:7px 10px;text-align:right;border-bottom:1px solid var(--border);font-size:12px;color:var(--text)}
td:first-child{text-align:left;color:var(--muted);font-size:11px}
tr:hover td{background:rgba(255,255,255,.02)}
td.bull{color:var(--green)}td.bear{color:var(--red)}td.neu{color:var(--yellow)}
.ld-box{display:none;text-align:center;padding:60px 20px}.ld-box.show{display:block}
.ld-title{font-size:11px;letter-spacing:4px;text-transform:uppercase;color:var(--cyan);margin-bottom:18px}
.ld-bar{height:2px;background:var(--border2);border-radius:1px;overflow:hidden;margin-bottom:18px}
.ld-fill{height:100%;width:30%;background:linear-gradient(90deg,var(--blue),var(--cyan),var(--green));animation:ld 1.6s ease-in-out infinite;border-radius:1px}
@keyframes ld{0%{margin-left:-30%}100%{margin-left:130%}}
.ld-steps{display:flex;flex-direction:column;gap:5px;max-width:360px;margin:0 auto;text-align:left}
.lst{font-size:10px;color:var(--muted);opacity:.3;transition:opacity .3s;display:flex;gap:8px}
.lst.on{opacity:1;color:var(--yellow)}.lst.done{opacity:1;color:var(--green)}
.res-wrap{display:none}.res-wrap.show{display:block}
.verdict{display:flex;align-items:center;justify-content:space-between;border:1px solid;border-radius:3px;padding:18px 22px;margin-bottom:14px}
.verdict.bull{border-color:rgba(0,230,118,.4);background:rgba(0,230,118,.03)}
.verdict.bear{border-color:rgba(255,23,68,.4);background:rgba(255,23,68,.03)}
.verdict.neu{border-color:rgba(255,214,0,.3);background:rgba(255,214,0,.03)}
.vd-lbl{font-size:9px;letter-spacing:3px;text-transform:uppercase;color:var(--muted);margin-bottom:4px}
.vd-val{font-family:var(--display);font-size:30px;font-weight:700;letter-spacing:3px}
.verdict.bull .vd-val{color:var(--green)}.verdict.bear .vd-val{color:var(--red)}.verdict.neu .vd-val{color:var(--yellow)}
.vd-r{text-align:right;font-size:10px;color:var(--muted);line-height:2}.vd-r span{color:var(--text)}
.prob-row{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}
.prob-card{background:var(--s1);border:1px solid var(--border2);border-radius:3px;padding:26px 22px;position:relative;overflow:hidden}
.prob-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px}
.prob-card.bull::before{background:var(--green);box-shadow:0 0 12px var(--green)}
.prob-card.bear::before{background:var(--red);box-shadow:0 0 12px var(--red)}
.pc-lbl{font-size:9px;letter-spacing:3px;text-transform:uppercase;margin-bottom:10px}
.prob-card.bull .pc-lbl{color:var(--green)}.prob-card.bear .pc-lbl{color:var(--red)}
.pc-num{font-family:var(--display);font-size:76px;font-weight:700;line-height:1;margin-bottom:6px}
.prob-card.bull .pc-num{color:var(--green);text-shadow:0 0 40px rgba(0,230,118,.2)}
.prob-card.bear .pc-num{color:var(--red);text-shadow:0 0 40px rgba(255,23,68,.2)}
.pc-sub{font-size:10px;color:var(--muted)}.pc-ci{font-size:10px;color:var(--muted);margin-top:6px}.pc-ci span{color:var(--text)}
.zdiff-card{background:var(--s1);border:1px solid var(--border2);border-radius:3px;padding:18px 22px;margin-bottom:14px}
.zdiff-lbl{font-size:9px;letter-spacing:4px;text-transform:uppercase;color:var(--purple);margin-bottom:14px}
.zdiff-gauge{position:relative;height:10px;border-radius:5px;margin-bottom:10px;background:linear-gradient(90deg,var(--red) 0%,var(--yellow) 33%,var(--yellow) 67%,var(--green) 100%)}
.zdiff-needle{position:absolute;top:-5px;width:4px;height:20px;background:white;border-radius:2px;transform:translateX(-50%);box-shadow:0 0 8px white;transition:left 1.2s cubic-bezier(.16,1,.3,1);left:50%}
.zdiff-ticks{display:flex;justify-content:space-between;font-size:9px;color:var(--muted);margin-bottom:12px}
.zdiff-inner{display:grid;grid-template-columns:1fr 200px;gap:20px;align-items:start}
.zdiff-num{font-family:var(--display);font-size:48px;font-weight:700;text-align:right;line-height:1}
.zdiff-state{font-size:10px;letter-spacing:3px;text-transform:uppercase;text-align:right;margin-top:4px}
.mini4{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px}
.mini{background:var(--s1);border:1px solid var(--border);border-radius:3px;padding:14px}
.mi-lbl{font-size:8px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:6px}
.mi-val{font-family:var(--display);font-size:22px;font-weight:600}.mi-sub{font-size:9px;color:var(--muted);margin-top:2px}
.chart-wrap{background:var(--s1);border:1px solid var(--border2);border-radius:3px;padding:18px 20px;margin-bottom:14px}
.ch-lbl{font-size:9px;letter-spacing:4px;text-transform:uppercase;color:var(--orange);margin-bottom:12px}
canvas{display:block;width:100%;border-radius:2px}
.ord-box{background:var(--s1);border:1px solid var(--border2);border-radius:3px;padding:22px;margin-bottom:14px}
.ord-hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;flex-wrap:wrap;gap:8px}
.ord-title{font-family:var(--display);font-size:18px;font-weight:700;letter-spacing:3px;color:var(--yellow)}
.ord-meta{font-size:10px;color:var(--muted);line-height:1.8}.ord-meta span{color:var(--yellow)}
.lot-calc{display:flex;gap:10px;align-items:flex-end;flex-wrap:wrap;padding:14px 0 16px;border-bottom:1px solid var(--border);margin-bottom:14px}
.lot-field{display:flex;flex-direction:column;gap:5px}
.lot-field label{font-size:8px;letter-spacing:2px;text-transform:uppercase;color:var(--muted)}
.lot-field input,.lot-field select{background:var(--s0);border:1px solid var(--border2);color:var(--text);font-family:var(--mono);font-size:13px;padding:7px 10px;border-radius:2px;outline:none}
.lot-result{display:flex;flex-direction:column;gap:3px;padding-bottom:2px}
.lot-result .lv{font-family:var(--display);font-size:20px;font-weight:700;color:var(--cyan)}
.lot-result .ls{font-size:10px;color:var(--muted)}
.no-trade{border:1px solid rgba(255,214,0,.35);background:rgba(255,214,0,.04);border-radius:3px;padding:22px 24px}
.nt-title{font-family:var(--display);font-size:26px;font-weight:700;color:var(--yellow);letter-spacing:3px;margin-bottom:8px}
.nt-body{font-size:12px;color:var(--muted);line-height:1.9}
.ord-line{border:1px solid;border-radius:3px;padding:18px 20px;display:grid;grid-template-columns:110px 1fr 1fr 1fr 90px;gap:12px;align-items:center}
.ord-line.buy{border-color:rgba(0,230,118,.25);background:rgba(0,230,118,.03)}
.ord-line.sell{border-color:rgba(255,23,68,.25);background:rgba(255,23,68,.03)}
.ol-badge{font-family:var(--display);font-size:15px;font-weight:700;letter-spacing:2px;padding:6px 10px;border-radius:2px;text-align:center}
.ol-badge.buy{border:1px solid rgba(0,230,118,.4);background:rgba(0,230,118,.1);color:var(--green)}
.ol-badge.sell{border:1px solid rgba(255,23,68,.4);background:rgba(255,23,68,.1);color:var(--red)}
.ol-entry{font-family:var(--display);font-size:22px;font-weight:700}
.ol-entry .sub{font-size:9px;color:var(--muted);display:block;margin-top:2px;font-family:var(--mono);font-weight:400}
.ol-levels{font-size:11px;line-height:1.9;color:var(--muted)}
.ol-note{font-size:10px;color:var(--muted);line-height:1.6}
.ol-prob{font-family:var(--display);font-size:28px;font-weight:700;text-align:right}
.ord-line.buy .ol-prob{color:var(--green)}.ord-line.sell .ol-prob{color:var(--red)}
.ctx-panel{background:var(--s1);border:1px solid var(--border);border-radius:3px;padding:18px 20px;margin-bottom:14px}
.ctx-cards{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:14px}
.ctx-card{background:var(--s0);border:1px solid var(--border2);border-radius:3px;padding:12px 14px}
.ctx-card-lbl{font-size:8px;letter-spacing:3px;text-transform:uppercase;color:var(--muted);margin-bottom:6px}
.ctx-card-val{font-family:var(--display);font-size:22px;font-weight:700;margin-bottom:4px}
.ctx-card-why{font-size:9px;color:var(--muted);line-height:1.5}
.ctx-summary{background:var(--s0);border:1px solid var(--border);border-left:2px solid var(--cyan);border-radius:3px;padding:12px 14px;margin-top:10px;font-size:12px;line-height:1.7;color:var(--text);display:none}
.ai-panel{background:var(--s0);border:1px solid var(--border2);border-left:3px solid var(--blue);border-radius:3px;padding:20px;margin-bottom:14px}
.ai-badge{font-size:8px;letter-spacing:3px;text-transform:uppercase;color:var(--blue2);background:rgba(0,144,255,.1);border:1px solid rgba(0,144,255,.25);padding:3px 10px;border-radius:2px;margin-bottom:12px;display:inline-block}
.ai-body{font-size:13px;line-height:1.8;color:var(--text)}
.disc{font-size:9px;letter-spacing:1px;color:var(--muted);line-height:1.7;border:1px dashed var(--border2);padding:14px;border-radius:3px;text-align:center;margin-top:28px}
@media(max-width:700px){
  .g2,.g3,.g4,.mini4,.prob-row,.ctx-cards{grid-template-columns:1fr 1fr}
  .pc-num{font-size:56px}
  .ord-line{grid-template-columns:90px 1fr 1fr;grid-template-rows:auto auto}
}
</style>
</head>
<body>
<div class="wrap">

<div class="hdr">
  <div class="logo">ORDER<span>FLOW</span> PRO <sub>SWING 3D</sub></div>
  <div class="hdr-r">
    <div class="clk" id="clk">--:-- CET</div>
    <div class="live"><div class="dot"></div>MOTOR ACTIVO</div>
  </div>
</div>

<div class="tabs">
  <div class="tab active" onclick="goTab('input')">① DATOS DE MERCADO</div>
  <div class="tab" onclick="goTab('results')" id="tab-res" style="opacity:.35;pointer-events:none">② ANÁLISIS &amp; ORDEN</div>
</div>

<!-- ═══ TAB INPUT ═══ -->
<div class="tab-panel active" id="panel-input">

  <div class="sec">activos frecuentes</div>
  <div class="pills">
    <button class="pill active" onclick="selectAsset('EURUSD=X','forex',this)">EUR/USD</button>
    <button class="pill"        onclick="selectAsset('GBPUSD=X','forex',this)">GBP/USD</button>
    <button class="pill"        onclick="selectAsset('USDJPY=X','forex',this)">USD/JPY</button>
    <button class="pill gold"   onclick="selectAsset('GC=F','commodity',this)">XAU/USD 🥇</button>
    <button class="pill idx"    onclick="selectAsset('%5EGSPC','index',this)">S&amp;P 500</button>
    <button class="pill idx"    onclick="selectAsset('%5EGDAXI','index',this)">DAX 40</button>
    <button class="pill idx"    onclick="selectAsset('%5EIXIC','index',this)">NASDAQ</button>
  </div>

  <div class="sec">activo &amp; configuración</div>
  <div class="card">
    <div class="g4">
      <div class="field">
        <label>Símbolo Yahoo Finance</label>
        <input id="ticker" value="EURUSD=X" placeholder="EURUSD=X, GC=F, ^GSPC..."/>
      </div>
      <div class="field">
        <label>Precio actual</label>
        <input id="price" type="number" step="0.00001" placeholder="Se carga con las velas"/>
        <div id="price-src" style="font-size:9px;color:var(--green);display:none;margin-top:2px"></div>
      </div>
      <div class="field">
        <label>Tipo de activo</label>
        <select id="asset-type">
          <option value="forex" selected>Forex</option>
          <option value="index">Índice (SP500, DAX...)</option>
          <option value="commodity">Materia prima (XAU...)</option>
          <option value="stock">Acciones</option>
          <option value="crypto">Crypto</option>
        </select>
      </div>
      <div class="field">
        <label>Horizonte operación</label>
        <select id="horizon">
          <option value="1">Intradía (hoy)</option>
          <option value="3" selected>Swing 3 días (GTC)</option>
          <option value="5">Swing 5 días (GTC)</option>
        </select>
      </div>
    </div>
  </div>

  <div class="sec">velas H1 reales — yahoo finance directo (sin api key)</div>
  <div class="card">
    <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-bottom:14px">
      <div>
        <div style="font-size:11px;color:var(--text);margin-bottom:3px">Descarga las últimas 30 velas H1 directamente de Yahoo Finance via proxy público.</div>
        <div style="font-size:10px;color:var(--muted)">
          Forex: <code style="color:var(--cyan)">EURUSD=X</code> &nbsp;·&nbsp;
          XAU/USD: <code style="color:var(--yellow)">GC=F</code> &nbsp;·&nbsp;
          SP500: <code style="color:var(--orange)">%5EGSPC</code> &nbsp;·&nbsp;
          DAX: <code style="color:var(--orange)">%5EGDAXI</code>
        </div>
      </div>
      <button class="btn btn-c" onclick="loadYahooCandles()" id="yahoo-btn" style="font-size:12px;padding:9px 20px">
        📡 CARGAR VELAS H1
      </button>
    </div>

    <div id="yahoo-status" class="sbar" style="display:none">⟳ Cargando...</div>

    <div id="d1-bar" style="display:none;margin-bottom:14px">
      <div class="sec" style="margin-bottom:8px">tendencia D1 — últimas 5 velas diarias (contexto swing)</div>
      <div id="d1-summary" style="font-size:11px;line-height:1.9;color:var(--muted);background:var(--s0);border:1px solid var(--border2);border-left:2px solid var(--orange);border-radius:3px;padding:10px 14px"></div>
    </div>

    <div class="tbl-wrap">
      <table>
        <thead>
          <tr><th>Vela</th><th>Fecha/Hora</th><th>High</th><th>Low</th><th>Close</th><th>Volumen</th><th>TP</th><th></th></tr>
        </thead>
        <tbody id="candle-body"></tbody>
      </table>
    </div>
    <div style="display:flex;gap:10px;margin-top:12px">
      <button class="btn btn-sm" onclick="addRow()">+ AÑADIR MANUAL</button>
    </div>
  </div>

  <div class="sec">contexto swing — búsqueda web automática (sesgo D1 · 3-5 días)</div>
  <div class="ctx-panel">
    <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px">
      <div>
        <div style="font-size:11px;color:var(--text);margin-bottom:3px">Busca noticias, calendario económico y sesgo institucional para los próximos días.</div>
        <div style="font-size:10px;color:var(--muted)">Incluye eventos Fed, BCE, NFP, CPI y geopolítica que afecten el swing.</div>
      </div>
      <div style="display:flex;gap:10px;align-items:center">
        <div class="sbar" id="ctx-status" style="margin-bottom:0;font-size:9px">⬡ SIN CONTEXTO</div>
        <button class="btn btn-c" onclick="fetchContext()" id="ctx-btn" style="font-size:12px;padding:8px 18px">🌐 OBTENER CONTEXTO</button>
      </div>
    </div>
    <div id="ctx-loading" style="display:none;margin-top:12px">
      <div class="ld-bar"><div class="ld-fill"></div></div>
      <div style="font-size:9px;letter-spacing:2px;color:var(--yellow);text-transform:uppercase" id="ctx-msg">Analizando calendario económico...</div>
    </div>
    <div id="ctx-cards-wrap" style="display:none">
      <div class="ctx-cards">
        <div class="ctx-card"><div class="ctx-card-lbl">sesgo macro (3-5d)</div><div class="ctx-card-val" id="ctx-macro-val">—</div><div class="ctx-card-why" id="ctx-macro-why">—</div></div>
        <div class="ctx-card"><div class="ctx-card-lbl">eventos esta semana</div><div class="ctx-card-val" id="ctx-news-val">—</div><div class="ctx-card-why" id="ctx-news-why">—</div></div>
        <div class="ctx-card"><div class="ctx-card-lbl">volatilidad esperada</div><div class="ctx-card-val" id="ctx-vol-val">—</div><div class="ctx-card-why" id="ctx-vol-why">—</div></div>
      </div>
      <div class="ctx-summary" id="ctx-summary-box">
        <div style="font-size:8px;letter-spacing:3px;text-transform:uppercase;color:var(--cyan);margin-bottom:6px">// resumen swing</div>
        <div id="ctx-summary-txt" style="font-size:12px;line-height:1.7"></div>
      </div>
    </div>
    <input type="hidden" id="ctx-macro" value="0"/>
    <input type="hidden" id="ctx-news" value="0"/>
    <input type="hidden" id="ctx-vol" value="normal"/>
    <input type="hidden" id="ctx-summary-val" value=""/>
  </div>

  <div class="sec">parámetros del modelo</div>
  <div class="card">
    <div class="g3">
      <div class="field"><label>Simulaciones Monte Carlo</label>
        <select id="sims"><option value="2000">2,000 (rápido)</option><option value="5000" selected>5,000 (estándar)</option><option value="10000">10,000 (preciso)</option></select>
      </div>
      <div class="field"><label>Periodo Z-Diff (velas H1)</label>
        <input id="zperiod" type="number" value="20" min="10" max="60"/>
      </div>
      <div class="field"><label>Umbral mínimo probabilidad</label>
        <select id="threshold"><option value="60">60% (permisivo)</option><option value="65" selected>65% (recomendado)</option><option value="70">70% (estricto)</option></select>
      </div>
    </div>
  </div>

  <button class="btn btn-c btn-block" onclick="runAnalysis()">▶ EJECUTAR MODELO COMPLETO</button>
</div>

<!-- ═══ TAB RESULTS ═══ -->
<div class="tab-panel" id="panel-results">

  <div class="ld-box" id="ld-box">
    <div class="ld-title">Ejecutando motor cuantitativo — Swing Multi-Step</div>
    <div class="ld-bar"><div class="ld-fill"></div></div>
    <div class="ld-steps">
      <div class="lst" id="ls0">▸ Calculando Typical Price &amp; Raw MF (H1)...</div>
      <div class="lst" id="ls1">▸ Acumulando RMF — ventana deslizante...</div>
      <div class="lst" id="ls2">▸ Normalizando Z-Score (Z-Diff)...</div>
      <div class="lst" id="ls3">▸ Monte Carlo multi-step (72 pasos H1 × 3 días)...</div>
      <div class="lst" id="ls4">▸ Proyectando distribución — 3 días vista...</div>
      <div class="lst" id="ls5">▸ Calculando niveles GTC desde histograma MC...</div>
      <div class="lst" id="ls6">▸ Generando análisis swing con IA...</div>
    </div>
  </div>

  <div class="res-wrap" id="res-wrap">

    <div class="verdict" id="verdict">
      <div>
        <div class="vd-lbl">Veredicto swing — horizonte <span id="v-horizon">3</span> días</div>
        <div class="vd-val" id="v-val">—</div>
      </div>
      <div class="vd-r">
        <div>MC: <span id="v-sims">—</span> sims · <span id="v-steps">—</span> pasos H1</div>
        <div>Z-Diff: <span id="v-z">—</span> · Confianza: <span id="v-conf">—</span></div>
        <div>GTC expira: <span id="v-exp">—</span></div>
      </div>
    </div>

    <div class="prob-row">
      <div class="prob-card bull">
        <div class="pc-lbl">▲ Positivo en <span id="bh">3</span> días</div>
        <div class="pc-num" id="bull-pct">—</div>
        <div class="pc-sub">probabilidad MC multi-step</div>
        <div class="pc-ci">IC 95%: [<span id="bull-lo">—</span>, <span id="bull-hi">—</span>]</div>
      </div>
      <div class="prob-card bear">
        <div class="pc-lbl">▼ Negativo en <span id="bh2">3</span> días</div>
        <div class="pc-num" id="bear-pct">—</div>
        <div class="pc-sub">probabilidad MC multi-step</div>
        <div class="pc-ci">IC 95%: [<span id="bear-lo">—</span>, <span id="bear-hi">—</span>]</div>
      </div>
    </div>

    <div class="zdiff-card">
      <div class="zdiff-lbl">// Z-Diff Order Flow H1 — diagnóstico de subasta institucional</div>
      <div class="zdiff-gauge"><div class="zdiff-needle" id="z-needle"></div></div>
      <div class="zdiff-ticks"><span>VENTA &lt;-1.5</span><span>-0.75</span><span>NEUTRAL</span><span>+0.75</span><span>COMPRA &gt;+1.5</span></div>
      <div class="zdiff-inner">
        <div id="z-detail" style="font-size:11px;line-height:1.9;color:var(--muted)">—</div>
        <div>
          <div class="zdiff-num" id="z-num">—</div>
          <div class="zdiff-state" id="z-state">—</div>
          <div style="font-size:9px;color:var(--muted);text-align:right;margin-top:6px" id="z-desc">—</div>
        </div>
      </div>
    </div>

    <div class="mini4">
      <div class="mini"><div class="mi-lbl">RMF Acumulado</div><div class="mi-val" id="rmf-val" style="font-size:18px;color:var(--cyan)">—</div><div class="mi-sub">flujo monetario H1</div></div>
      <div class="mini"><div class="mi-lbl">Precio Esperado</div><div class="mi-val" id="mc-mean">—</div><div class="mi-sub">media MC (días)</div></div>
      <div class="mini"><div class="mi-lbl">Volatilidad σ H1</div><div class="mi-val" id="sigma-v" style="color:var(--orange)">—</div><div class="mi-sub">desv. estándar log-ret.</div></div>
      <div class="mini"><div class="mi-lbl">ATR H1 real</div><div class="mi-val" id="atr-val" style="color:var(--yellow)">—</div><div class="mi-sub">media High-Low 14v</div></div>
    </div>

    <div class="chart-wrap">
      <div class="ch-lbl" id="ch-lbl">// distribución Monte Carlo — precios proyectados a 3 días</div>
      <canvas id="mc-canvas" height="200"></canvas>
    </div>

    <div class="ord-box">
      <div class="ord-hdr">
        <div class="ord-title">📋 ORDEN GTC — SWING</div>
        <div class="ord-meta">Tipo: <span>GTC</span> · Expira: <span id="exp-date">—</span> · Umbral: <span id="thr-show">65</span>%</div>
      </div>
      <div class="lot-calc">
        <div class="lot-field">
          <label>Capital cuenta ($)</label>
          <input id="account-size" type="number" value="10000" min="100" step="500" style="width:120px" oninput="recalcLots()"/>
        </div>
        <div class="lot-field">
          <label>Riesgo por op. (%)</label>
          <input id="risk-pct" type="number" value="2" min="0.5" max="10" step="0.5" style="width:90px" oninput="recalcLots()"/>
        </div>
        <div class="lot-field">
          <label>Instrumento</label>
          <select id="instr-type" style="width:140px" onchange="recalcLots()">
            <option value="forex_std">Forex std (100k)</option>
            <option value="forex_mini">Forex mini (10k)</option>
            <option value="xauusd">XAU/USD</option>
            <option value="index_cfd">Índice CFD</option>
          </select>
        </div>
        <div class="lot-result" id="lot-result">
          <div class="lv" style="color:var(--muted)">— introduce capital</div>
        </div>
      </div>
      <div id="order-content">—</div>
    </div>

    <div class="ai-panel">
      <div class="ai-badge">⬡ ANÁLISIS INSTITUCIONAL SWING — CLAUDE</div>
      <div class="ai-body" id="ai-body">—</div>
    </div>

    <div class="sec" style="margin-top:20px">tabla order flow H1</div>
    <div class="card">
      <div class="tbl-wrap">
        <table>
          <thead><tr><th>#</th><th>TP</th><th>Raw MF</th><th>RMF Acum.</th><th>Z-Diff</th><th>Estado</th></tr></thead>
          <tbody id="of-tbody"></tbody>
        </table>
      </div>
    </div>

    <div style="text-align:center;margin-top:14px">
      <button class="btn btn-sm" onclick="goTab('input')">← MODIFICAR DATOS</button>
    </div>
    <div class="disc">⚠️ Modelo educativo-cuantitativo. No constituye asesoramiento financiero.<br>Monte Carlo multi-step asume GBM log-normal. Datos Yahoo Finance pueden tener retrasos. Opera siempre con gestión de riesgo.</div>
  </div>
</div>

</div>
<script>
// CLOCK
(function tick(){
  const o={timeZone:'Europe/Madrid',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false};
  document.getElementById('clk').textContent=new Date().toLocaleTimeString('es-ES',o)+' CET';
  setTimeout(tick,1000);
})();

// TABS
function goTab(t){
  ['input','results'].forEach((id,i)=>{
    document.getElementById('panel-'+id).classList.toggle('active',id===t);
    document.querySelectorAll('.tab')[i].classList.toggle('active',id===t);
  });
}

// ASSET PILLS
function selectAsset(symbol,type,el){
  document.querySelectorAll('.pill').forEach(p=>p.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('ticker').value=symbol;
  document.getElementById('asset-type').value=type;
}

// ── VELAS H1 VÍA IA + WEB SEARCH ────────────────────────────────────────────
let rowId=0;
let _msgInterval=null;

async function loadYahooCandles(){
  const sym = document.getElementById('ticker').value.trim();
  const at  = document.getElementById('asset-type').value;
  if(!sym){ alert('Introduce un símbolo primero.'); return; }

  const btn=document.getElementById('yahoo-btn');
  const st =document.getElementById('yahoo-status');
  btn.disabled=true;
  st.className='sbar loading'; st.style.display='flex';

  const msgs=['⟳ Buscando velas H1 en tiempo real...','⟳ Consultando datos OHLCV...','⟳ Extrayendo historial H1...','⟳ Procesando datos de mercado...'];
  let mi=0; st.textContent=msgs[0];
  if(_msgInterval) clearInterval(_msgInterval);
  _msgInterval=setInterval(()=>{ st.textContent=msgs[mi++%msgs.length]; },2500);

  const today=new Date().toLocaleDateString('es-ES',{weekday:'long',day:'2-digit',month:'long',year:'numeric'});
  const time =new Date().toLocaleTimeString('es-ES',{hour:'2-digit',minute:'2-digit'});

  const prompt=`Hoy es ${today}, hora ${time} CET. Busca en web los datos OHLCV reales de las últimas 20 velas H1 para ${sym} (${at}).

Fuentes: Yahoo Finance, Investing.com, TradingView, Forex Factory, o cualquier fuente con datos OHLCV horarios.

Responde SOLO con JSON, sin texto adicional, sin backticks:
{"ticker":"${sym}","price":0,"candles":[{"dt":"22/03 14:00","h":0,"l":0,"c":0,"v":0}]}

Reglas:
- 15-25 velas H1 reales, orden cronológico ascendente (más antigua primero)
- price: último precio actual del mercado
- dt: apertura de vela en formato DD/MM HH:MM
- Precios reales coherentes con mercado actual (forex 5 decimales, XAU/oro 2 decimales, índices 2 decimales)
- v: volumen real o 10000 si no disponible`;

  try{
    const r=await fetch("https://api.anthropic.com/v1/messages",{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        model:'claude-sonnet-4-20250514',max_tokens:3000,
        tools:[{type:"web_search_20250305",name:"web_search"}],
        messages:[{role:'user',content:prompt}]
      })
    });
    const data=await r.json();
    let raw='';
    if(data.content) for(const b of data.content) if(b.type==='text') raw+=b.text;

    const s=raw.indexOf('{'),e=raw.lastIndexOf('}');
    if(s===-1||e===-1) throw new Error('No se encontraron datos estructurados');
    const j=JSON.parse(raw.slice(s,e+1));
    if(!j.candles||!Array.isArray(j.candles)||j.candles.length<5)
      throw new Error('Datos insuficientes — intenta de nuevo');

    document.getElementById('candle-body').innerHTML=''; rowId=0;
    j.candles.forEach(c=>addRow(c.h,c.l,c.c,c.v||10000,c.dt||''));

    const lastPrice=j.price||j.candles.at(-1).c;
    document.getElementById('price').value=lastPrice;
    const psrc=document.getElementById('price-src');
    psrc.textContent=`✓ Precio: ${lastPrice} · ${j.candles.length} velas H1 cargadas`;
    psrc.style.display='block';

    renderD1fromH1(j.candles);

    clearInterval(_msgInterval);
    st.className='sbar ok';
    st.textContent=`✓ ${j.candles.length} velas H1 cargadas · ${sym} · ${time}h`;

  }catch(e){
    clearInterval(_msgInterval);
    st.className='sbar err';
    st.textContent=`⚠ ${e.message} — Pulsa de nuevo o añade velas manualmente.`;
    console.error(e);
  }
  btn.disabled=false;
}

function renderD1fromH1(candles){
  const days={};
  candles.forEach(c=>{
    const day=c.dt?c.dt.split(' ')[0]:'?';
    if(!days[day]) days[day]={h:c.h,l:c.l,c:c.c};
    else{ days[day].h=Math.max(days[day].h,c.h); days[day].l=Math.min(days[day].l,c.l); days[day].c=c.c; }
  });
  const arr=Object.entries(days);
  if(arr.length<2) return;
  const trend=arr.at(-1)[1].c>arr[0][1].c?'📈 ALCISTA':'📉 BAJISTA';
  const tc=arr.at(-1)[1].c>arr[0][1].c?'var(--green)':'var(--red)';
  let html=`<span style="color:${tc};margin-right:16px;font-size:10px;letter-spacing:1px">Tendencia D1 (desde H1): ${trend}</span> `;
  arr.forEach(([day,d],i)=>{
    if(i===0) return;
    const chg=((d.c/arr[i-1][1].c-1)*100).toFixed(2);
    const col=+chg>0?'var(--green)':+chg<0?'var(--red)':'var(--muted)';
    html+=`<span style="margin-right:14px">${day}: <span style="color:${col}">${+chg>0?'+':''}${chg}%</span></span>`;
  });
  document.getElementById('d1-summary').innerHTML=html;
  document.getElementById('d1-bar').style.display='block';
  const d1Dir=arr.at(-1)[1].c>arr[0][1].c?1:-1;
  if((parseInt(document.getElementById('ctx-macro').value)||0)===0)
    document.getElementById('ctx-macro').value=d1Dir;
}
// CANDLE TABLE
function addRow(h='',l='',c='',v='',lbl=''){
  rowId++;
  const id=rowId;
  const is='background:var(--s0);border:1px solid var(--border2);color:var(--text);font-family:var(--mono);font-size:12px;padding:5px 7px;border-radius:2px;outline:none';
  const tr=document.createElement('tr');
  tr.id='r'+id;
  tr.innerHTML=`
    <td>V${id}</td>
    <td style="color:var(--muted);font-size:10px">${lbl||'—'}</td>
    <td><input type="number" step="0.00001" value="${h}" style="${is};width:90px" onchange="recalcTP(${id})"/></td>
    <td><input type="number" step="0.00001" value="${l}" style="${is};width:90px" onchange="recalcTP(${id})"/></td>
    <td><input type="number" step="0.00001" value="${c}" style="${is};width:90px" onchange="recalcTP(${id})"/></td>
    <td><input type="number" value="${v}" style="${is};width:80px"/></td>
    <td class="tp${id}" style="color:var(--muted)">—</td>
    <td><button class="btn btn-del" onclick="document.getElementById('r${id}').remove()">✕</button></td>`;
  document.getElementById('candle-body').appendChild(tr);
  if(h&&l&&c) recalcTP(id);
}

function getRow(id){
  const r=document.getElementById('r'+id); if(!r) return null;
  const ins=r.querySelectorAll('input');
  return{h:+ins[0].value,l:+ins[1].value,c:+ins[2].value,v:+ins[3].value};
}
function recalcTP(id){
  const d=getRow(id); if(!d||isNaN(d.h)) return;
  document.querySelector('.tp'+id).textContent=((d.h+d.l+d.c)/3).toFixed(6);
}
function allCandles(){
  return[...document.querySelectorAll('#candle-body tr')]
    .map(r=>getRow(r.id.slice(1)))
    .filter(d=>d&&!isNaN(d.h)&&!isNaN(d.l)&&!isNaN(d.c)&&!isNaN(d.v)&&d.h>0);
}

// CONTEXT
async function fetchContext(){
  const ticker=document.getElementById('ticker').value.trim().toUpperCase();
  const at=document.getElementById('asset-type').value;
  const horizon=document.getElementById('horizon').value;
  const today=new Date().toLocaleDateString('es-ES',{weekday:'long',day:'2-digit',month:'long',year:'numeric'});

  document.getElementById('ctx-btn').disabled=true;
  document.getElementById('ctx-loading').style.display='block';
  document.getElementById('ctx-status').textContent='◌ BUSCANDO...';
  document.getElementById('ctx-cards-wrap').style.display='none';
  document.getElementById('ctx-summary-box').style.display='none';

  const msgs=['Analizando calendario económico...','Evaluando sesgo institucional...','Buscando eventos de riesgo...','Sintetizando sesgo swing...'];
  let mi=0;
  const mInt=setInterval(()=>document.getElementById('ctx-msg').textContent=msgs[mi++%msgs.length],2000);

  const prompt=`Hoy es ${today}. Eres un analista swing trader.

Busca en la web el contexto de mercado para los próximos ${horizon} días para ${ticker} (${at}). Considera:
- Calendario económico esta semana (Fed, BCE, NFP, CPI, PMI, resultados)
- Tendencia macro semanal/diaria actual
- Eventos de riesgo próximos ${horizon} días
- Posicionamiento institucional

Responde ÚNICAMENTE con JSON puro sin backticks:
{"macro":0,"macro_label":"Neutral","macro_why":"1 frase","news":0,"news_label":"Neutros","news_why":"1 frase con eventos clave","vol":"normal","vol_label":"Normal","vol_why":"1 frase","summary":"2-3 frases sesgo swing ${horizon}d de ${ticker}"}

macro y news = entero -2 a 2. vol = low/normal/high.`;

  try{
    const r=await fetch("https://api.anthropic.com/v1/messages",{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({model:'claude-sonnet-4-20250514',max_tokens:800,
        tools:[{type:"web_search_20250305",name:"web_search"}],
        messages:[{role:'user',content:prompt}]})});
    const data=await r.json();
    let raw=''; if(data.content) for(const b of data.content) if(b.type==='text') raw+=b.text;
    const m=raw.match(/\{[\s\S]*?\}/); if(!m) throw new Error('no json');
    const j=JSON.parse(m[0]);
    document.getElementById('ctx-macro').value=j.macro??0;
    document.getElementById('ctx-news').value=j.news??0;
    document.getElementById('ctx-vol').value=j.vol??'normal';
    document.getElementById('ctx-summary-val').value=j.summary??'';
    const sc=v=>v>0?'var(--green)':v<0?'var(--red)':'var(--yellow)';
    const vc=v=>v==='high'?'var(--orange)':v==='low'?'var(--cyan)':'var(--text)';
    const mv=document.getElementById('ctx-macro-val'); mv.textContent=j.macro_label; mv.style.color=sc(j.macro);
    document.getElementById('ctx-macro-why').textContent=j.macro_why||'—';
    const nv=document.getElementById('ctx-news-val'); nv.textContent=j.news_label; nv.style.color=sc(j.news);
    document.getElementById('ctx-news-why').textContent=j.news_why||'—';
    const vv=document.getElementById('ctx-vol-val'); vv.textContent=j.vol_label; vv.style.color=vc(j.vol);
    document.getElementById('ctx-vol-why').textContent=j.vol_why||'—';
    document.getElementById('ctx-summary-txt').textContent=j.summary||'—';
    document.getElementById('ctx-cards-wrap').style.display='block';
    document.getElementById('ctx-summary-box').style.display='block';
    document.getElementById('ctx-status').className='sbar ok';
    document.getElementById('ctx-status').textContent='✓ CONTEXTO SWING LISTO';
  }catch(e){
    document.getElementById('ctx-macro').value='0'; document.getElementById('ctx-news').value='0'; document.getElementById('ctx-vol').value='normal';
    ['ctx-macro-val','ctx-news-val','ctx-vol-val'].forEach((id,i)=>{ const el=document.getElementById(id); el.textContent=['Neutral','Neutros','Normal'][i]; el.style.color='var(--yellow)'; });
    ['ctx-macro-why','ctx-news-why','ctx-vol-why'].forEach(id=>document.getElementById(id).textContent='No disponible');
    document.getElementById('ctx-summary-txt').textContent='No se pudo obtener contexto. Valores neutros.';
    document.getElementById('ctx-cards-wrap').style.display='block'; document.getElementById('ctx-summary-box').style.display='block';
    document.getElementById('ctx-status').className='sbar err'; document.getElementById('ctx-status').textContent='⚠ ERROR — VALORES NEUTROS';
  }
  clearInterval(mInt);
  document.getElementById('ctx-loading').style.display='none';
  document.getElementById('ctx-btn').disabled=false;
}

// MATH
function mean(a){return a.reduce((s,x)=>s+x,0)/a.length}
function std(a){const m=mean(a);return Math.sqrt(a.reduce((s,x)=>s+(x-m)**2,0)/a.length)}
function randn(){let u=0,v=0;while(!u)u=Math.random();while(!v)v=Math.random();return Math.sqrt(-2*Math.log(u))*Math.cos(2*Math.PI*v);}

// ORDER FLOW
function calcOF(candles,period){
  const tps=candles.map(c=>(c.h+c.l+c.c)/3);
  const rawMF=candles.map((c,i)=>{if(i===0)return 0;const d=tps[i]-tps[i-1];return d>0?tps[i]*c.v:d<0?-(tps[i]*c.v):0;});
  const rmf=rawMF.map((_,i)=>{const s=Math.max(0,i-period+1);return rawMF.slice(s,i+1).reduce((a,b)=>a+b,0);});
  const zDiff=rmf.map((_,i)=>{const s=Math.max(0,i-period+1);const sl=rmf.slice(s,i+1);const sg=std(sl);return sg===0?0:(rmf[i]-mean(sl))/sg;});
  return{tps,rawMF,rmf,zDiff};
}

// MONTE CARLO MULTI-STEP
function mcMultiStep(price,rets,sims,steps,zAdj,vm){
  const mu=mean(rets),sg=std(rets)*vm,drift=mu+zAdj*sg*0.15;
  const fp=[];
  for(let i=0;i<sims;i++){
    let p=price;
    for(let t=0;t<steps;t++) p*=Math.exp((drift-0.5*sg*sg)+sg*randn());
    fp.push(p);
  }
  return{fp,mu,sg,drift};
}

// EXPIRATION DATE (skip weekends)
function getExpDate(days){
  const d=new Date(); let added=0;
  while(added<days){d.setDate(d.getDate()+1);if(d.getDay()!==0&&d.getDay()!==6)added++;}
  return d.toLocaleDateString('es-ES',{weekday:'short',day:'2-digit',month:'short',year:'numeric'})+' 23:59h';
}

function markStep(id){
  ['ls0','ls1','ls2','ls3','ls4','ls5','ls6'].forEach(s=>{
    const el=document.getElementById(s);
    if(el.id===id) el.className='lst on'; else if(el.className==='lst on') el.className='lst done';
  });
}
function allDone(){['ls0','ls1','ls2','ls3','ls4','ls5','ls6'].forEach(s=>document.getElementById(s).className='lst done');}

function assetDec(p){return p>1000?1:p>100?2:p>1?4:5}
function fmt(n,d){return(+n).toFixed(d)}
function fmtBig(n){return(+n).toLocaleString('es-ES',{maximumFractionDigits:0})}

// MAIN
async function runAnalysis(){
  const candles=allCandles();
  if(candles.length<10){alert('Necesitas al menos 10 velas H1. Pulsa "Cargar Velas H1" primero.');return;}

  goTab('results');
  document.getElementById('ld-box').classList.add('show');
  document.getElementById('res-wrap').classList.remove('show');

  const ticker=document.getElementById('ticker').value.toUpperCase();
  const price=parseFloat(document.getElementById('price').value)||candles.at(-1).c;
  const sims=parseInt(document.getElementById('sims').value);
  const zperiod=parseInt(document.getElementById('zperiod').value);
  const at=document.getElementById('asset-type').value;
  const horizon=parseInt(document.getElementById('horizon').value);
  const threshold=parseInt(document.getElementById('threshold').value);
  const macro=parseInt(document.getElementById('ctx-macro').value)||0;
  const newsCtx=parseInt(document.getElementById('ctx-news').value)||0;
  const volCtx=document.getElementById('ctx-vol').value||'normal';
  const ctxSum=document.getElementById('ctx-summary-val').value||'';
  const dec=assetDec(price);

  const step=(id,ms)=>new Promise(r=>{setTimeout(()=>{markStep(id);r();},ms);});

  await step('ls0',400);
  const of=calcOF(candles,zperiod);

  await step('ls1',450);
  const lastRMF=of.rmf.at(-1), lastZ=of.zDiff.at(-1);

  await step('ls2',450);
  const closes=candles.map(c=>c.c);
  const rets=closes.slice(1).map((c,i)=>Math.log(c/closes[i]));
  if(rets.length<5){alert('Necesitas más velas.');return;}

  await step('ls3',800);
  const vm=volCtx==='low'?.7:volCtx==='high'?1.5:1.0;
  const zAdj=Math.max(-2,Math.min(2,lastZ));
  // H1 steps: trading hours ≈ 16h/day for forex/indices, 24h for crypto
  const hrsPerDay=at==='crypto'?24:at==='forex'?24:16;
  const mcSteps=horizon*hrsPerDay;
  const mc=mcMultiStep(price,rets,sims,mcSteps,zAdj,vm);

  await step('ls4',600);
  const sorted=[...mc.fp].sort((a,b)=>a-b);
  const bullN=mc.fp.filter(p=>p>price).length;
  const rawBull=bullN/sims*100;
  const ctxBoost=(macro+newsCtx)/4*8;
  const adjBull=Math.max(10,Math.min(90,rawBull+ctxBoost));
  const adjBear=100-adjBull;
  const mcMean=mean(mc.fp);
  const p5=sorted[Math.floor(sims*.05)], p95=sorted[Math.floor(sims*.95)];

  const atrWin=candles.slice(-14);
  const atr=atrWin.reduce((s,c)=>s+(c.h-c.l),0)/atrWin.length;

  await step('ls5',500);
  const pct=p=>sorted[Math.min(sims-1,Math.floor(sims*p/100))];
  const primBull=adjBull>adjBear;

  // STOP: ruptura del rango H1 reciente
  const last3=candles.slice(-3);
  const recHigh=Math.max(...last3.map(c=>c.h));
  const recLow=Math.min(...last3.map(c=>c.l));
  const buf=atr*0.08;
  const eStop=primBull?recHigh+buf:recLow-buf;

  // LIMIT: percentil 38/62 del MC (zona de pullback)
  const eLim=primBull?pct(38):pct(62);

  // SL y TP desde distribución MC
  const sl=primBull?pct(8):pct(92);
  const tp=primBull?pct(80):pct(20);

  // Elegir tipo de orden según Z-Diff
  const useStop=primBull?lastZ>0.8:lastZ<-0.8;
  const entry=useStop?eStop:eLim;
  const oType=useStop?'STOP':'LIMIT';
  const expDate=getExpDate(horizon);

  await step('ls6',400);
  let aiText='';
  try{aiText=await callAI(ticker,price,lastZ,lastRMF,adjBull,adjBear,mc,mcMean,macro,newsCtx,atr,at,horizon,candles.length,ctxSum,dec);}
  catch(e){aiText=fallback(ticker,lastZ,adjBull,mcMean,price,horizon);}

  allDone();
  await new Promise(r=>setTimeout(r,250));

  window._lastOrder={entry,sl,tp,bull:primBull,prob:primBull?adjBull:adjBear,D:dec,z:lastZ};

  render({ticker,price,of,lastRMF,lastZ,adjBull,adjBear,p5,p95,mc,mcMean,sims,mcSteps,
    atr,zAdj,macro,newsCtx,primBull,threshold,useStop,oType,entry,sl,tp,expDate,
    adjBull,adjBear,aiText,candles,horizon,dec});
}

function render(d){
  document.getElementById('ld-box').classList.remove('show');
  document.getElementById('res-wrap').classList.add('show');
  document.getElementById('tab-res').style.opacity='1';
  document.getElementById('tab-res').style.pointerEvents='auto';

  // Verdict
  const vEl=document.getElementById('verdict'), vv=document.getElementById('v-val');
  if(d.adjBull>=60){vEl.className='verdict bull';vv.textContent='SESGO ALCISTA ▲';}
  else if(d.adjBull<=40){vEl.className='verdict bear';vv.textContent='SESGO BAJISTA ▼';}
  else{vEl.className='verdict neu';vv.textContent='SESGO NEUTRAL ➡';}
  document.getElementById('v-horizon').textContent=d.horizon;
  document.getElementById('v-sims').textContent=d.sims.toLocaleString();
  document.getElementById('v-steps').textContent=d.mcSteps;
  document.getElementById('v-z').textContent=d.lastZ.toFixed(3);
  const conf=d.adjBull>65||d.adjBull<35?'Alta':d.adjBull>58||d.adjBull<42?'Media':'Baja';
  document.getElementById('v-conf').textContent=conf;
  document.getElementById('v-exp').textContent=d.expDate;
  document.getElementById('exp-date').textContent=d.expDate;
  document.getElementById('thr-show').textContent=d.threshold;
  ['bh','bh2'].forEach(id=>document.getElementById(id).textContent=d.horizon);

  // Probs
  document.getElementById('bull-pct').textContent=d.adjBull.toFixed(1)+'%';
  document.getElementById('bear-pct').textContent=d.adjBear.toFixed(1)+'%';
  document.getElementById('bull-lo').textContent=fmt(d.p5,d.dec);
  document.getElementById('bull-hi').textContent=fmt(d.p95,d.dec);
  document.getElementById('bear-lo').textContent=fmt(d.p5,d.dec);
  document.getElementById('bear-hi').textContent=fmt(d.p95,d.dec);

  // Z-Diff
  const z=d.lastZ;
  setTimeout(()=>document.getElementById('z-needle').style.left=Math.max(2,Math.min(98,(z+3)/6*100))+'%',80);
  let zc,zs,zdsc;
  if(z>1.5){zc='var(--green)';zs='COMPRA';zdsc='Iniciativa alcista agresiva. Smart Money barriendo oferta.';}
  else if(z>0.5){zc='var(--green2)';zs='SESGO LARGO';zdsc='Flujo positivo moderado. Presión compradora activa.';}
  else if(z>-0.5){zc='var(--yellow)';zs='NEUTRAL';zdsc='Balance de subasta. Sin mano fuerte dominante.';}
  else if(z>-1.5){zc='var(--red2)';zs='SESGO CORTO';zdsc='Flujo negativo moderado. Presión vendedora creciente.';}
  else{zc='var(--red)';zs='VENTA';zdsc='Distribución institucional. Smart Money liquidando.';}
  const zn=document.getElementById('z-num'); zn.textContent=z.toFixed(3); zn.style.color=zc;
  const zsEl=document.getElementById('z-state'); zsEl.textContent=zs; zsEl.style.color=zc;
  document.getElementById('z-desc').textContent=zdsc;
  document.getElementById('z-detail').innerHTML=`
    RMF acum.: <span style="color:var(--cyan)">${fmtBig(d.lastRMF)}</span><br>
    Periodo Z: <span style="color:var(--text)">${document.getElementById('zperiod').value} velas H1</span><br>
    Drift adj.: <span style="color:${d.zAdj>0?'var(--green)':d.zAdj<0?'var(--red)':'var(--yellow)'}">${d.zAdj>=0?'+':''}${d.zAdj.toFixed(2)}</span><br>
    D1 sesgo: <span style="color:${d.macro>0?'var(--green)':d.macro<0?'var(--red)':'var(--yellow)'}">${['Muy bajista','Bajista','Neutral','Alcista','Muy alcista'][d.macro+2]}</span>`;

  // Mini
  document.getElementById('rmf-val').textContent=fmtBig(d.lastRMF);
  document.getElementById('mc-mean').textContent=fmt(d.mcMean,d.dec);
  document.getElementById('sigma-v').textContent=(d.mc.sg*100).toFixed(3)+'%';
  document.getElementById('atr-val').textContent=fmt(d.atr,d.dec);
  document.getElementById('ch-lbl').textContent=`// distribución Monte Carlo — precios proyectados a ${d.horizon} días (${d.mcSteps} pasos H1)`;

  // Chart
  drawChart(d.mc.fp,d.price,d.dec,{bull:d.primBull,entry:d.entry,sl:d.sl,tp:d.tp});

  // Order
  renderOrder(d);

  // AI
  document.getElementById('ai-body').textContent=d.aiText;

  // OF table
  const tb=document.getElementById('of-tbody'); tb.innerHTML='';
  d.candles.forEach((c,i)=>{
    const z=d.of.zDiff[i],cls=z>1.5?'bull':z<-1.5?'bear':'neu',st=z>1.5?'COMPRA':z<-1.5?'VENTA':'NEUTRAL';
    const mf=d.of.rawMF[i];
    const tr=document.createElement('tr');
    tr.innerHTML=`<td>V${i+1}</td><td>${d.of.tps[i].toFixed(d.dec)}</td><td class="${mf>=0?'bull':'bear'}">${mf>=0?'+':''}${fmtBig(mf)}</td><td>${fmtBig(d.of.rmf[i])}</td><td class="${cls}">${z.toFixed(3)}</td><td class="${cls}">${st}</td>`;
    tb.appendChild(tr);
  });

  recalcLots();
}

function renderOrder(d){
  const prob=d.primBull?d.adjBull:d.adjBear;
  if(prob<d.threshold){
    document.getElementById('order-content').innerHTML=`
      <div class="no-trade">
        <div class="nt-title">⚠ NO OPERAR — CONVICCIÓN INSUFICIENTE</div>
        <div class="nt-body">
          Probabilidad del modelo: <span style="color:var(--yellow)">${prob.toFixed(1)}%</span> — por debajo del umbral de <span style="color:var(--text)">${d.threshold}%</span><br>
          Z-Diff H1: <span style="color:var(--text)">${d.lastZ.toFixed(3)}</span> — ${Math.abs(d.lastZ)<0.5?'sin direccionalidad institucional clara':'señal débil, espera confirmación'}<br>
          <span style="color:var(--yellow);display:block;margin-top:8px">💡 Preservar capital también es una posición válida. Espera alineación de Z-Diff + MC + D1.</span>
        </div>
      </div>`;
    window._lastOrder=null; recalcLots(); return;
  }

  const side=d.primBull?'BUY':'SELL';
  const simCov=(d.mc.fp.filter(p=>d.primBull?(p>=d.entry&&p<=d.tp):(p<=d.entry&&p>=d.tp)).length/d.mc.fp.length*100).toFixed(0);
  const zReason=d.useStop
    ?`Z-Diff ${d.lastZ.toFixed(2)} — ruptura ${d.primBull?'alcista':'bajista'} confirmada`
    :`Z-Diff ${d.lastZ.toFixed(2)} moderado — pullback al percentil ${d.primBull?38:62} MC`;
  const rr=Math.abs(d.tp-d.entry)/Math.abs(d.entry-d.sl);

  document.getElementById('order-content').innerHTML=`
    <div class="ord-line ${side.toLowerCase()}">
      <div class="ol-badge ${side.toLowerCase()}">${side}<br><span style="font-size:11px">${d.oType}</span></div>
      <div class="ol-entry">${fmt(d.entry,d.dec)}<span class="sub">GTC · exp. ${d.expDate}</span></div>
      <div class="ol-levels">
        SL: <span style="color:var(--red);font-weight:500">${fmt(d.sl,d.dec)}</span><br>
        TP: <span style="color:var(--green);font-weight:500">${fmt(d.tp,d.dec)}</span><br>
        RR: <span style="color:var(--text)">1:${rr.toFixed(1)}</span>
      </div>
      <div class="ol-note">${zReason}.<br>${simCov}% simulaciones MC entre entrada y TP (p80).</div>
      <div class="ol-prob">${prob.toFixed(1)}%</div>
    </div>`;
}

// CHART
function drawChart(prices,ref,dec,levels){
  const cv=document.getElementById('mc-canvas'),ctx=cv.getContext('2d');
  const W=cv.offsetWidth||820,H=200; cv.width=W; cv.height=H;
  const bins=60,mn=Math.min(...prices),mx=Math.max(...prices),bw=(mx-mn)/bins;
  const hist=new Array(bins).fill(0);
  prices.forEach(p=>hist[Math.min(bins-1,Math.floor((p-mn)/bw))]++);
  const maxH=Math.max(...hist);
  const pad={t:14,r:10,b:38,l:10},cw=W-20,ch=H-52;
  ctx.clearRect(0,0,W,H);

  // Shade TP zone
  if(levels){
    const shade=(lo,hi,col)=>{
      if(hi<mn||lo>mx)return;
      const x1=pad.l+((Math.max(mn,lo)-mn)/(mx-mn))*cw;
      const x2=pad.l+((Math.min(mx,hi)-mn)/(mx-mn))*cw;
      ctx.fillStyle=col; ctx.fillRect(x1,pad.t,x2-x1,ch);
    };
    levels.bull?shade(levels.entry,levels.tp,'rgba(0,230,118,.09)'):shade(levels.tp,levels.entry,'rgba(255,23,68,.09)');
  }

  // Bars
  hist.forEach((cnt,i)=>{
    const x=pad.l+(i/bins)*cw,bh=(cnt/maxH)*ch,y=pad.t+ch-bh,bc=mn+(i+.5)*bw;
    const g=ctx.createLinearGradient(0,y,0,y+bh);
    if(bc>ref){g.addColorStop(0,'rgba(0,230,118,.85)');g.addColorStop(1,'rgba(0,230,118,.08)');}
    else{g.addColorStop(0,'rgba(255,23,68,.85)');g.addColorStop(1,'rgba(255,23,68,.08)');}
    ctx.fillStyle=g; ctx.fillRect(x,y,cw/bins-1,bh);
  });

  // Lines
  const vLine=(p,col,lbl,yo=0)=>{
    if(p<mn||p>mx)return;
    const x=pad.l+((p-mn)/(mx-mn))*cw;
    ctx.strokeStyle=col;ctx.lineWidth=1.5;ctx.setLineDash([3,3]);
    ctx.beginPath();ctx.moveTo(x,pad.t);ctx.lineTo(x,pad.t+ch);ctx.stroke();ctx.setLineDash([]);
    ctx.fillStyle=col;ctx.font='9px JetBrains Mono';ctx.textAlign='center';
    ctx.fillText(lbl,x,pad.t+ch+14+yo);
  };
  if(levels){
    vLine(levels.sl,'rgba(255,23,68,.9)','SL');
    vLine(levels.entry,levels.bull?'rgba(0,230,118,1)':'rgba(255,23,68,1)','ENTRADA');
    vLine(levels.tp,levels.bull?'rgba(0,230,118,.7)':'rgba(255,23,68,.7)','TP p80');
  }
  const rx=pad.l+((ref-mn)/(mx-mn))*cw;
  ctx.strokeStyle='rgba(255,255,255,.8)';ctx.lineWidth=2;ctx.setLineDash([5,3]);
  ctx.beginPath();ctx.moveTo(rx,pad.t);ctx.lineTo(rx,pad.t+ch);ctx.stroke();ctx.setLineDash([]);
  ctx.fillStyle='rgba(255,255,255,.5)';ctx.font='9px JetBrains Mono';ctx.textAlign='center';
  ctx.fillText('PRECIO',rx,H-4);
  ctx.textAlign='left';ctx.fillStyle='rgba(255,23,68,.7)';ctx.fillText(mn.toFixed(dec),pad.l,H-4);
  ctx.textAlign='right';ctx.fillStyle='rgba(0,230,118,.7)';ctx.fillText(mx.toFixed(dec),W-pad.r,H-4);
}

// LOT CALC
function recalcLots(){
  const o=window._lastOrder,el=document.getElementById('lot-result');
  if(!o){el.innerHTML='<div class="lv" style="color:var(--muted)">— sin orden activa</div>';return;}
  const account=parseFloat(document.getElementById('account-size').value)||10000;
  const riskPct=parseFloat(document.getElementById('risk-pct').value)||2;
  const instr=document.getElementById('instr-type').value;
  const riskUSD=account*(riskPct/100);
  const slDist=Math.abs(o.entry-o.sl);
  if(slDist===0){el.innerHTML='<div class="lv" style="color:var(--muted)">— SL no calculado</div>';return;}
  let lots=0,lotLabel='';
  if(instr==='forex_std'){const p=slDist/0.0001;lots=riskUSD/(p*10);lotLabel=`${lots.toFixed(2)} lotes std (${(lots*100000).toFixed(0)} u.)`;}
  else if(instr==='forex_mini'){const p=slDist/0.0001;lots=riskUSD/(p*1);lotLabel=`${lots.toFixed(2)} mini lotes`;}
  else if(instr==='xauusd'){lots=riskUSD/(slDist*100);lotLabel=`${lots.toFixed(3)} lotes XAU (${(lots*100).toFixed(1)} oz)`;}
  else{lots=riskUSD/slDist;lotLabel=`${lots.toFixed(2)} contratos CFD`;}
  const rr=Math.abs(o.tp-o.entry)/slDist;
  el.innerHTML=`<div class="lv">${lotLabel}</div>
    <div class="ls">Riesgo: <span style="color:var(--red)">$${riskUSD.toFixed(0)}</span> &nbsp;·&nbsp; Beneficio potencial: <span style="color:var(--green)">$${(riskUSD*rr).toFixed(0)}</span> &nbsp;·&nbsp; R:R <span style="color:var(--text)">1:${rr.toFixed(1)}</span></div>`;
}

// AI
async function callAI(ticker,price,z,rmf,bull,bear,mc,mcMean,macro,news,atr,at,horizon,n,ctxSum,dec){
  const mL=['muy bajista','bajista','neutral','alcista','muy alcista'][macro+2];
  const nL=['muy negativos','negativos','neutros','positivos','muy positivos'][news+2];
  const ctx=ctxSum?`\nContexto swing web: ${ctxSum}`:'';
  const prompt=`Eres un trader institucional swing. Análisis técnico directo en español (4-5 frases). Sin asteriscos ni markdown.

Activo: ${ticker} (${at}) | Horizonte: ${horizon} días
Precio: ${price} | Media MC ${horizon}d: ${mcMean.toFixed(dec)}
Z-Diff H1: ${z.toFixed(3)} — ${z>1.5?'COMPRA':z<-1.5?'VENTA':'NEUTRAL'}
RMF: ${fmtBig(rmf)} | P(alcista): ${bull.toFixed(1)}% | σ H1: ${(mc.sg*100).toFixed(3)}%
ATR H1 real: ${atr.toFixed(dec)} | Macro ${horizon}d: ${mL} | Eventos: ${nL}${ctx}

Valida si Z-Diff H1 confirma el sesgo MC multi-step, describe el contexto institucional swing, y justifica Stop vs Limit para GTC de ${horizon} días.`;
  const r=await fetch("https://api.anthropic.com/v1/messages",{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({model:'claude-sonnet-4-20250514',max_tokens:900,messages:[{role:'user',content:prompt}]})});
  const data=await r.json();
  return data.content?.[0]?.text||'';
}

function fallback(ticker,z,bull,mcMean,price,horizon){
  const d=z>1.5?'alcista agresiva':z<-1.5?'bajista institucional':'equilibrada';
  return`El Z-Diff de ${z.toFixed(3)} indica una iniciativa ${d} en el Order Flow H1 de ${ticker}. Monte Carlo multi-step proyecta el precio esperado ${mcMean>price?'por encima':'por debajo'} del nivel actual en ${horizon} días, con probabilidad alcista del ${bull.toFixed(1)}%. La orden GTC queda activa hasta el ${horizon}º día hábil con SL en percentil 8 y TP en percentil 80 de la distribución simulada.`;
}
</script>
</body>
</html>
            body { background-color: #04070d !important; color: #cdd9e5; margin: 0; padding: 0; }
        </style>
    </head>
    <body>
        <h1 style="color: #00e5ff; font-family: sans-serif; padding: 20px;">MOTOR ACTIVO - ESPERANDO DATOS</h1>
    </body>
    </html>
    """

# EJECUCIÓN: Aquí es donde evitamos la pantalla negra
# El 'height' debe ser suficiente, prueba con 1000 o 1200
components.html(get_html(), height=1200, scrolling=True)
