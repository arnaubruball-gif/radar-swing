import streamlit as st
import streamlit.components.v1 as components

# 1. Configuración de la interfaz de Streamlit
st.set_page_config(
    page_title="ORDER FLOW PRO",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Definición del código HTML (Aquí es donde "vive" tu herramienta)
# Usamos comillas triples """ para que Python guarde todo como un bloque de texto
html_template = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <style>
        :root{--bg:#04070d;--s0:#070c14;--s1:#0b111c;--b1:#162030;--b2:#1e2e42;--green:#00e676;--red:#ff1744;--yellow:#ffd600;--cyan:#00e5ff;--orange:#ff9100;--blue:#0090ff;--purple:#d500f9;--text:#cdd9e5;--muted:#4a6080;--mono:'JetBrains Mono',monospace;--display:'Rajdhani',sans-serif}
        *{margin:0;padding:0;box-sizing:border-box}
        body{background:var(--bg);color:var(--text);font-family:var(--mono);min-height:100vh;overflow-x:hidden}
        /* ... El resto de tu CSS ... */
    </style>
</head>
<body>
    <div class="w">
        </div>

    <script>
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ORDER FLOW PRO</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Rajdhani:wght@500;600;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#04070d;--s0:#070c14;--s1:#0b111c;--b1:#162030;--b2:#1e2e42;--green:#00e676;--red:#ff1744;--yellow:#ffd600;--cyan:#00e5ff;--orange:#ff9100;--blue:#0090ff;--purple:#d500f9;--text:#cdd9e5;--muted:#4a6080;--mono:'JetBrains Mono',monospace;--display:'Rajdhani',sans-serif}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:var(--mono);min-height:100vh;overflow-x:hidden}
body::after{content:'';position:fixed;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,.06) 2px,rgba(0,0,0,.06) 4px);pointer-events:none;z-index:9999}
.w{max-width:1100px;margin:0 auto;padding:20px 16px 80px;position:relative;z-index:1}

/* HDR */
.hdr{display:flex;align-items:center;justify-content:space-between;padding-bottom:18px;border-bottom:1px solid var(--b2);margin-bottom:24px}
.logo{font-family:var(--display);font-size:26px;font-weight:700;letter-spacing:4px;color:var(--cyan);text-shadow:0 0 20px rgba(0,229,255,.3)}
.logo b{color:var(--yellow)}
.hdr-r{display:flex;gap:14px;align-items:center}
.clk{font-size:11px;color:var(--yellow);background:rgba(255,214,0,.07);border:1px solid rgba(255,214,0,.2);padding:5px 12px;border-radius:2px}
.live{display:flex;align-items:center;gap:6px;font-size:9px;letter-spacing:3px;color:var(--green);text-transform:uppercase}
.dot{width:7px;height:7px;border-radius:50%;background:var(--green);animation:blink 1.4s infinite}
@keyframes blink{0%,100%{box-shadow:0 0 6px var(--green)}50%{opacity:.3;box-shadow:none}}

/* WIZARD */
.wiz{display:flex;margin-bottom:28px;position:relative}
.wiz::before{content:'';position:absolute;top:18px;left:0;right:0;height:1px;background:var(--b2);z-index:0}
.ws{flex:1;display:flex;flex-direction:column;align-items:center;gap:5px;z-index:1;cursor:pointer}
.wc{width:36px;height:36px;border-radius:50%;border:1px solid var(--b2);background:var(--s0);display:flex;align-items:center;justify-content:center;font-family:var(--display);font-size:16px;font-weight:700;color:var(--muted);transition:all .3s}
.wl{font-size:8px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);transition:color .3s;text-align:center}
.ws.active .wc{border-color:var(--cyan);color:var(--cyan);box-shadow:0 0 12px rgba(0,229,255,.3);background:rgba(0,229,255,.07)}
.ws.active .wl{color:var(--cyan)}
.ws.done .wc{border-color:var(--green);color:var(--green);background:rgba(0,230,118,.07)}
.ws.done .wl{color:var(--green)}

/* CARD / FIELD */
.card{background:var(--s1);border:1px solid var(--b1);border-radius:3px;padding:18px 20px}
.f{display:flex;flex-direction:column;gap:6px}
.f label{font-size:9px;letter-spacing:3px;text-transform:uppercase;color:var(--muted)}
.f input,.f select{background:var(--s0);border:1px solid var(--b2);color:var(--text);font-family:var(--mono);font-size:13px;padding:9px 12px;border-radius:2px;outline:none;width:100%;transition:border-color .15s}
.f input:focus,.f select:focus{border-color:var(--blue)}
.f select option{background:var(--s1)}
.sl{font-size:9px;letter-spacing:4px;text-transform:uppercase;color:#40b4ff;margin-bottom:12px}
.sl::before{content:'// ';color:var(--muted)}
.g3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-bottom:14px}
.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px}

/* BUTTONS */
.btn{font-family:var(--display);font-size:14px;font-weight:700;letter-spacing:3px;text-transform:uppercase;padding:11px 22px;cursor:pointer;border-radius:2px;border:1px solid;transition:all .2s;display:inline-block;text-align:center}
.btn-p{border-color:var(--cyan);color:var(--cyan);background:rgba(0,229,255,.05)}
.btn-p:hover:not(:disabled){background:var(--cyan);color:var(--bg);box-shadow:0 0 22px rgba(0,229,255,.3)}
.btn-p:disabled{opacity:.3;cursor:not-allowed;pointer-events:none}
.btn-w{width:100%}
.btn-s{font-size:11px;letter-spacing:2px;padding:7px 14px;border-color:var(--b2);color:var(--muted);background:transparent}
.btn-s:hover{border-color:#40b4ff;color:#40b4ff;background:rgba(0,144,255,.06)}
.btn-d{font-size:10px;padding:4px 9px;border-color:rgba(255,23,68,.3);color:#ff6b6b;background:transparent}
.btn-d:hover{background:rgba(255,23,68,.1)}

/* TABLE */
.tw{overflow-x:auto;margin-bottom:12px}
table{width:100%;border-collapse:collapse;font-size:12px}
th{font-size:8px;letter-spacing:3px;text-transform:uppercase;color:var(--muted);padding:8px 10px;text-align:right;border-bottom:1px solid var(--b2)}
th:first-child{text-align:left}
td{padding:7px 10px;text-align:right;border-bottom:1px solid var(--b1);font-size:12px}
td:first-child{text-align:left;color:var(--muted);font-size:11px}
tr:hover td{background:rgba(255,255,255,.015)}
td.bull{color:var(--green)}td.bear{color:var(--red)}td.neu{color:var(--yellow)}

/* CTX */
.cxm{background:var(--s0);border:1px solid var(--b2);border-radius:3px;padding:13px}
.cxl{font-size:8px;letter-spacing:3px;text-transform:uppercase;color:var(--muted);margin-bottom:5px}
.cxv{font-family:var(--display);font-size:20px;font-weight:700;line-height:1;margin-bottom:3px}
.cxw{font-size:9px;color:var(--muted);line-height:1.5}

/* LOADING */
.ldbox{display:none;text-align:center;padding:60px 20px}
.ldbox.on{display:block}
.ldt{font-size:10px;color:var(--cyan);letter-spacing:4px;text-transform:uppercase;margin-bottom:20px}
.ldb{height:2px;background:var(--b2);border-radius:1px;overflow:hidden;margin-bottom:20px}
.ldf{height:100%;width:30%;background:linear-gradient(90deg,var(--blue),var(--cyan),var(--green));animation:la 1.6s ease-in-out infinite}
@keyframes la{0%{margin-left:-30%}100%{margin-left:130%}}
.lss{display:flex;flex-direction:column;gap:5px;max-width:360px;margin:0 auto;text-align:left}
.ls{font-size:10px;color:var(--muted);opacity:.3;transition:opacity .3s;display:flex;gap:8px;align-items:center}
.ls.on{opacity:1;color:var(--yellow)}.ls.done{opacity:1;color:var(--green)}

/* RESULTS */
.rw{display:none}.rw.on{display:block}

/* PROB */
.prow{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}
.pcard{background:var(--s1);border:1px solid var(--b2);border-radius:3px;padding:26px 22px;position:relative;overflow:hidden}
.pcard::before{content:'';position:absolute;top:0;left:0;right:0;height:2px}
.pcard.bull::before{background:var(--green);box-shadow:0 0 12px var(--green)}
.pcard.bear::before{background:var(--red);box-shadow:0 0 12px var(--red)}
.pcard .lb{font-size:9px;letter-spacing:3px;text-transform:uppercase;margin-bottom:10px}
.pcard.bull .lb{color:var(--green)}.pcard.bear .lb{color:var(--red)}
.pn{font-family:var(--display);font-size:76px;font-weight:700;line-height:1;margin-bottom:6px}
.pcard.bull .pn{color:var(--green);text-shadow:0 0 36px rgba(0,230,118,.2)}
.pcard.bear .pn{color:var(--red);text-shadow:0 0 36px rgba(255,23,68,.2)}
.ps{font-size:10px;color:var(--muted)}.pci{font-size:11px;color:var(--muted);margin-top:6px}.pci span{color:var(--text)}

/* ZDIFF */
.zc{background:var(--s1);border:1px solid var(--b2);border-radius:3px;padding:20px 22px;margin-bottom:14px}
.zl{font-size:9px;letter-spacing:3px;text-transform:uppercase;color:var(--purple);margin-bottom:13px}
.zg{position:relative;height:10px;border-radius:5px;margin-bottom:11px;background:linear-gradient(90deg,var(--red) 0%,var(--yellow) 33%,var(--yellow) 67%,var(--green) 100%)}
.zn{position:absolute;top:-5px;width:4px;height:20px;background:white;border-radius:2px;transform:translateX(-50%);box-shadow:0 0 8px white;transition:left 1.2s cubic-bezier(.16,1,.3,1);left:50%}
.zt{display:flex;justify-content:space-between;font-size:9px;color:var(--muted)}
.zv{font-family:var(--display);font-size:46px;font-weight:700;text-align:right}
.zst{font-size:10px;letter-spacing:3px;text-transform:uppercase;text-align:right}

/* MINI */
.mc4{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px}
.mc{background:var(--s1);border:1px solid var(--b1);border-radius:3px;padding:13px}
.mcl{font-size:8px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:5px}
.mcv{font-family:var(--display);font-size:22px;font-weight:600}
.mcs{font-size:9px;color:var(--muted);margin-top:2px}

/* CHART */
.chw{background:var(--s1);border:1px solid var(--b2);border-radius:3px;padding:20px;margin-bottom:14px}
.chl{font-size:9px;letter-spacing:3px;text-transform:uppercase;color:var(--orange);margin-bottom:12px}
canvas{display:block;width:100%}

/* ORDERS */
.ob{background:var(--s1);border:1px solid var(--b2);border-radius:3px;padding:22px;margin-bottom:14px}
.obh{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;flex-wrap:wrap;gap:8px}
.obt{font-family:var(--display);font-size:17px;font-weight:700;letter-spacing:3px;color:var(--yellow)}
.obt2{font-size:10px;color:var(--muted)}.obt2 span{color:var(--yellow)}
.ol{display:grid;grid-template-columns:110px 1fr 1fr 1fr 80px;gap:10px;align-items:center;padding:13px 0;border-bottom:1px solid var(--b1)}
.ol:last-child{border-bottom:none}
.ot{font-family:var(--display);font-size:13px;font-weight:700;letter-spacing:1px;padding:5px 8px;border-radius:2px;text-align:center;line-height:1.4}
.ot.buy{background:rgba(0,230,118,.12);color:var(--green);border:1px solid rgba(0,230,118,.3)}
.ot.sell{background:rgba(255,23,68,.12);color:var(--red);border:1px solid rgba(255,23,68,.3)}
.op{font-size:15px;font-weight:500}.op .sub{font-size:9px;color:var(--muted);display:block;margin-top:2px}
.oi{font-size:11px;color:var(--muted);line-height:1.7}
.opr{font-family:var(--display);font-size:20px;text-align:right}
.opr.bull{color:var(--green)}.opr.bear{color:var(--red)}

/* AI */
.ai{background:var(--s0);border:1px solid var(--b2);border-left:3px solid var(--blue);border-radius:3px;padding:20px;margin-bottom:14px}
.aih{display:flex;gap:10px;align-items:center;margin-bottom:13px}
.aib{font-size:8px;letter-spacing:3px;text-transform:uppercase;color:#40b4ff;background:rgba(0,144,255,.1);border:1px solid rgba(0,144,255,.25);padding:3px 10px;border-radius:2px}
.ait{font-size:13px;line-height:1.75}

/* VERDICT */
.vb{display:flex;align-items:center;justify-content:space-between;border:1px solid;border-radius:3px;padding:18px 22px;margin-bottom:14px;flex-wrap:wrap;gap:10px}
.vb.bull{border-color:rgba(0,230,118,.4);background:rgba(0,230,118,.04)}
.vb.bear{border-color:rgba(255,23,68,.4);background:rgba(255,23,68,.04)}
.vb.neu{border-color:rgba(255,214,0,.3);background:rgba(255,214,0,.04)}
.vl{font-size:9px;letter-spacing:3px;text-transform:uppercase;color:var(--muted);margin-bottom:5px}
.vv{font-family:var(--display);font-size:30px;font-weight:700;letter-spacing:3px}
.vb.bull .vv{color:var(--green)}.vb.bear .vv{color:var(--red)}.vb.neu .vv{color:var(--yellow)}
.vr{text-align:right}.vm{font-size:10px;color:var(--muted)}.vm span{color:var(--text)}

/* CHIPS */
.chips{display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap}
.chip{font-size:10px;padding:5px 12px;border-radius:2px;border:1px solid var(--b2);background:var(--s1);display:flex;align-items:center;gap:6px}
.d2{width:6px;height:6px;border-radius:50%}

.disc{font-size:9px;color:var(--muted);line-height:1.7;border:1px dashed var(--b2);padding:13px;border-radius:3px;text-align:center;margin-top:26px}
@media(max-width:680px){
  .g3,.mc4,.prow{grid-template-columns:1fr 1fr}
  .ol{grid-template-columns:90px 1fr 1fr;grid-template-rows:auto auto}
  .pn{font-size:56px}.wl{display:none}
}
.btn-xs{font-family:var(--display);font-size:10px;font-weight:600;letter-spacing:2px;padding:4px 10px;border:1px solid var(--border2);border-radius:2px;color:var(--cyan);background:rgba(0,229,255,.05);cursor:pointer;transition:all .15s}
.btn-xs:hover{background:rgba(0,229,255,.12);border-color:var(--cyan)}
</style>
</head>
<body>
<div class="w">

<div class="hdr">
  <div class="logo">ORDER<b>FLOW</b> PRO</div>
  <div class="hdr-r">
    <div class="clk" id="clk">--:-- CET</div>
    <div class="live"><div class="dot"></div>MOTOR ACTIVO</div>
  </div>
</div>

<!-- WIZARD NAV -->
<div class="wiz">
  <div class="ws active" id="ws0"><div class="wc">1</div><div class="wl">Activo</div></div>
  <div class="ws" id="ws1"><div class="wc">2</div><div class="wl">Velas</div></div>
  <div class="ws" id="ws2"><div class="wc">3</div><div class="wl">Contexto IA</div></div>
  <div class="ws" id="ws3"><div class="wc">4</div><div class="wl">Análisis</div></div>
</div>

<!-- PASO 0 -->
<div id="p0">
  <div class="sl">activo &amp; parámetros del modelo</div>
  <div class="card" style="margin-bottom:14px">
    <div class="g3" style="margin-bottom:14px">
      <div class="f"><label>Ticker</label><input id="ticker" onchange="fetchLivePrice()" value="EURUSD"/></div>
      <div class="f">
        <label style="display:flex;align-items:center;justify-content:space-between">
          <span>Precio actual</span>
          <span id="price-source" style="display:none;font-size:9px;color:var(--green);letter-spacing:1px"></span>
        </label>
        <div id="price-wrap" style="position:relative;transition:border-color .3s">
          <input id="price" type="number" step="0.0001" placeholder="Buscando precio en vivo..." style="width:100%"/>
        </div>
        <div style="display:flex;gap:6px;margin-top:4px">
          <button class="btn-xs" onclick="fetchLivePrice()" title="Actualizar precio en vivo">⟳ PRECIO LIVE</button>
        </div>
      </div>
      <div class="f"><label>Tipo de activo</label>
        <select id="at" onchange="fillDemo()">
          <option value="forex">Forex (EUR/USD, GBP/USD…)</option>
          <option value="xauusd">XAU/USD — Oro</option>
          <option value="index">Índices (SP500, DAX, Nasdaq…)</option>
          <option value="stock">Acciones</option>
          <option value="crypto">Crypto</option>
        </select>
      </div>
    </div>
    <div class="g3">
      <div class="f"><label>Simulaciones Monte Carlo</label>
        <select id="sims"><option value="1000">1,000 (rápido)</option><option value="5000" selected>5,000 (estándar)</option><option value="10000">10,000 (preciso)</option></select>
      </div>
      <div class="f"><label>Periodo Z-Diff (velas)</label><input id="zp" type="number" value="14" min="5" max="50"/></div>
    </div>
  </div>
  <div style="text-align:right"><button class="btn btn-p" onclick="goStep(1)">SIGUIENTE: VELAS →</button></div>
</div>

<!-- PASO 1 -->
<div id="p1" style="display:none">
  <div class="sl">historial de velas — order flow (mín. 5, recomendado 14+)</div>
  <div class="card" style="margin-bottom:14px">
    <div class="tw">
      <table>
        <thead><tr><th>#</th><th>High</th><th>Low</th><th>Close</th><th>Volumen</th><th>TP calc.</th><th>Raw MF</th><th></th></tr></thead>
        <tbody id="tb"></tbody>
      </table>
    </div>
    <div style="display:flex;gap:10px;margin-top:10px">
      <button class="btn btn-s" onclick="addRow()">+ AÑADIR VELA</button>
      <button class="btn btn-s" onclick="fillDemo()">↺ RECARGAR DEMO</button>
    </div>
  </div>
  <div style="display:flex;justify-content:space-between">
    <button class="btn btn-s" onclick="goStep(0)">← ATRÁS</button>
    <button class="btn btn-p" onclick="goStep(2)">SIGUIENTE: CONTEXTO IA →</button>
  </div>
</div>

<!-- PASO 2 -->
<div id="p2" style="display:none">
  <div class="sl">contexto de mercado — búsqueda web automática con ia</div>
  <div class="card" style="margin-bottom:14px">
    <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-bottom:18px">
      <div>
        <div style="font-size:13px;line-height:1.7;margin-bottom:6px">
          La IA buscará en tiempo real: <span style="color:var(--cyan)">noticias del día, datos macro, eventos del calendario económico y sentimiento institucional</span> para tu activo.<br>
          <span style="font-size:10px;color:var(--muted)">Ajusta el drift de Monte Carlo automáticamente. No tienes que saber nada de contexto.</span>
        </div>
      </div>
      <button class="btn btn-p" onclick="fetchCtx()" id="ctx-btn" style="white-space:nowrap;font-size:13px;padding:10px 22px;flex-shrink:0">🌐 BUSCAR CONTEXTO</button>
    </div>
    <div id="ctx-ld" style="display:none;margin-bottom:10px">
      <div style="font-size:9px;color:var(--cyan);letter-spacing:3px;text-transform:uppercase;margin-bottom:8px">Buscando en tiempo real…</div>
      <div class="ldb"><div class="ldf"></div></div>
    </div>
    <div id="ctx-res" style="display:none">
      <div class="g3" style="margin-bottom:12px">
        <div class="cxm"><div class="cxl">Tendencia macro</div><div class="cxv" id="ctx-mv">—</div><div class="cxw" id="ctx-mw">—</div></div>
        <div class="cxm"><div class="cxl">Noticias hoy</div><div class="cxv" id="ctx-nv">—</div><div class="cxw" id="ctx-nw">—</div></div>
        <div class="cxm"><div class="cxl">Volatilidad esperada</div><div class="cxv" id="ctx-vv">—</div><div class="cxw" id="ctx-vw">—</div></div>
      </div>
      <div style="background:var(--s0);border:1px solid var(--b1);border-left:2px solid var(--cyan);border-radius:3px;padding:13px">
        <div style="font-size:8px;letter-spacing:3px;text-transform:uppercase;color:var(--cyan);margin-bottom:7px">Resumen del contexto detectado</div>
        <div id="ctx-sum" style="font-size:12px;line-height:1.75">—</div>
      </div>
      <div style="margin-top:10px;text-align:right"><button class="btn btn-s" onclick="fetchCtx()">↺ ACTUALIZAR</button></div>
    </div>
    <div style="margin-top:12px;font-size:10px;color:var(--muted)">💡 Puedes continuar sin contexto — el modelo usará valores neutros.</div>
  </div>
  <div style="display:flex;justify-content:space-between">
    <button class="btn btn-s" onclick="goStep(1)">← ATRÁS</button>
    <button class="btn btn-p" onclick="runAnalysis()">▶ EJECUTAR ANÁLISIS COMPLETO</button>
  </div>
</div>

<!-- PASO 3 -->
<div id="p3" style="display:none">
  <div class="ldbox" id="ldbox">
    <div class="ldt">Ejecutando motor cuantitativo</div>
    <div class="ldb"><div class="ldf"></div></div>
    <div class="lss">
      <div class="ls" id="ls0">▸ Calculando Typical Price &amp; Raw MF…</div>
      <div class="ls" id="ls1">▸ Acumulando RMF (ventana deslizante)…</div>
      <div class="ls" id="ls2">▸ Normalizando Z-Score (Z-Diff)…</div>
      <div class="ls" id="ls3">▸ Ejecutando Monte Carlo GBM…</div>
      <div class="ls" id="ls4">▸ Proyectando distribución de precios…</div>
      <div class="ls" id="ls5">▸ Calculando niveles 22:00h CET…</div>
      <div class="ls" id="ls6">▸ Generando análisis institucional con IA…</div>
    </div>
  </div>

  <div class="rw" id="rw">
    <div class="chips" id="chips"></div>

    <div class="vb" id="vb">
      <div><div class="vl">Veredicto del modelo</div><div class="vv" id="vv">—</div></div>
      <div class="vr">
        <div class="vm">Monte Carlo: <span id="mcn">—</span> simulaciones</div>
        <div class="vm">Confianza estadística: <span id="conf">—</span></div>
      </div>
    </div>

    <div class="prow">
      <div class="pcard bull">
        <div class="lb">▲ Cierre en POSITIVO</div>
        <div class="pn" id="bull-p">—</div>
        <div class="ps">probabilidad Monte Carlo</div>
        <div class="pci">IC 95%: [<span id="ci-lo">—</span> · <span id="ci-hi">—</span>]</div>
      </div>
      <div class="pcard bear">
        <div class="lb">▼ Cierre en NEGATIVO</div>
        <div class="pn" id="bear-p">—</div>
        <div class="ps">probabilidad Monte Carlo</div>
        <div class="pci">Precio esperado MC: <span id="mcm">—</span></div>
      </div>
    </div>

    <div class="zc">
      <div class="zl">// Z-Diff Order Flow — Diagnóstico de Subasta Institucional</div>
      <div style="display:grid;grid-template-columns:1fr 200px;gap:20px;align-items:center">
        <div>
          <div class="zg"><div class="zn" id="zn"></div></div>
          <div class="zt"><span>VENTA &lt;-1.5</span><span>-0.75</span><span>NEUTRAL</span><span>+0.75</span><span>COMPRA &gt;+1.5</span></div>
        </div>
        <div>
          <div class="zv" id="zv">—</div>
          <div class="zst" id="zst">—</div>
          <div style="font-size:9px;color:var(--muted);text-align:right;margin-top:5px" id="zd">—</div>
        </div>
      </div>
    </div>

    <div class="mc4">
      <div class="mc"><div class="mcl">RMF Acumulado</div><div class="mcv" id="rmf" style="color:var(--cyan)">—</div><div class="mcs">flujo monetario</div></div>
      <div class="mc"><div class="mcl">Volatilidad σ diaria</div><div class="mcv" id="sig" style="color:var(--orange)">—</div><div class="mcs">desv. estándar</div></div>
      <div class="mc"><div class="mcl">Drift ajustado</div><div class="mcv" id="dri">—</div><div class="mcs">Z-Diff + contexto</div></div>
      <div class="mc"><div class="mcl">ATR estimado</div><div class="mcv" id="atrv">—</div><div class="mcs">rango proyectado</div></div>
    </div>

    <div class="chw">
      <div class="chl">// distribución Monte Carlo — histograma de precios de cierre simulados</div>
      <canvas id="cv" height="180"></canvas>
    </div>

    <div class="ob">
      <div class="obh">
        <div class="obt">📋 ÓRDENES PARA LAS 22:00h CET</div>
        <div class="obt2">Entrada: <span>22:00 CET</span> · Exp: <span>23:59 CET</span> · Tipo: <span>STOP / LIMIT</span></div>
      </div>
      <div id="ords">—</div>
    </div>

    <div class="ai">
      <div class="aih"><div class="aib">⬡ ANÁLISIS INSTITUCIONAL — CLAUDE + WEB SEARCH</div></div>
      <div class="ait" id="ait">—</div>
    </div>

    <div class="sl" style="margin-top:20px">tabla order flow calculada</div>
    <div class="card" style="margin-bottom:14px">
      <div class="tw">
        <table>
          <thead><tr><th>#</th><th>TP</th><th>Raw MF</th><th>RMF Acum.</th><th>Z-Diff</th><th>Estado</th></tr></thead>
          <tbody id="oftb"></tbody>
        </table>
      </div>
    </div>

    <div style="text-align:center;margin-top:14px">
      <button class="btn btn-s" onclick="goStep(0)">← NUEVO ANÁLISIS</button>
    </div>
    <div class="disc">⚠️ Modelo educativo-cuantitativo. No constituye asesoramiento financiero ni recomendación de inversión.<br>Monte Carlo asume rendimientos log-normales (GBM). Z-Diff basado en Money Flow institucional normalizado.<br>El contexto web es una estimación IA — verifica con fuentes oficiales antes de operar.</div>
  </div>
</div>

</div>
<script>
// CLOCK
function tick(){const o={timeZone:'Europe/Madrid',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false};document.getElementById('clk').textContent=new Date().toLocaleTimeString('es-ES',o)+' CET';}
setInterval(tick,1000);tick();

// WIZARD
function goStep(n){
  [0,1,2,3].forEach(i=>{
    document.getElementById('p'+i).style.display=i===n?'block':'none';
    const ws=document.getElementById('ws'+i);
    ws.classList.remove('active','done');
    if(i<n)ws.classList.add('done');else if(i===n)ws.classList.add('active');
  });
  window.scrollTo({top:0,behavior:'smooth'});
}

// CANDLE TABLE
let rc=0;
function addRow(h='',l='',c='',v=''){
  rc++;const id=rc;
  const tr=document.createElement('tr');tr.id='r'+id;
  const inp=(val,ph,stp)=>`<input type="number" step="${stp}" value="${val}" placeholder="${ph}" style="width:80px;background:var(--s0);border:1px solid var(--b2);color:var(--text);font-family:var(--mono);font-size:12px;padding:5px 8px;border-radius:2px;outline:none" onchange="rcRow(${id})"/>`;
  tr.innerHTML=`<td>V${id}</td><td>${inp(h,'High','0.0001')}</td><td>${inp(l,'Low','0.0001')}</td><td>${inp(c,'Close','0.0001')}</td><td>${inp(v,'Vol','1')}</td><td class="tp${id}" style="color:var(--muted)">—</td><td class="mf${id}" style="color:var(--muted)">—</td><td><button class="btn btn-d" onclick="del(${id})">✕</button></td>`;
  document.getElementById('tb').appendChild(tr);
  if(h&&l&&c&&v)rcRow(id);
}
function del(id){const e=document.getElementById('r'+id);if(e)e.remove();}
function grd(id){const r=document.getElementById('r'+id);if(!r)return null;const i=r.querySelectorAll('input');return{h:parseFloat(i[0].value),l:parseFloat(i[1].value),c:parseFloat(i[2].value),v:parseFloat(i[3].value)};}
function rcRow(id){const d=grd(id);if(!d||isNaN(d.h))return;document.querySelector('.tp'+id).textContent=((d.h+d.l+d.c)/3).toFixed(5);}
function getC(){const rows=document.querySelectorAll('#tb tr');const out=[];rows.forEach(r=>{const id=r.id.replace('r','');const d=grd(id);if(d&&!isNaN(d.h)&&!isNaN(d.l)&&!isNaN(d.c)&&!isNaN(d.v))out.push(d);});return out;}

// DEMO
const DM={
  forex:[[1.0890,1.0855,1.0872,18500],[1.0878,1.0841,1.0860,22100],[1.0868,1.0832,1.0850,19800],[1.0860,1.0820,1.0845,25600],[1.0855,1.0815,1.0838,17300],[1.0848,1.0808,1.0841,20400],[1.0858,1.0825,1.0854,23700],[1.0870,1.0838,1.0865,28900],[1.0880,1.0848,1.0876,31200],[1.0888,1.0855,1.0883,29800],[1.0896,1.0862,1.0890,26500],[1.0902,1.0868,1.0895,33400],[1.0910,1.0875,1.0905,38700],[1.0918,1.0882,1.0912,42100]],
  xauusd:[[3015.4,3008.2,3012.1,14200],[3014.8,3005.6,3009.3,16700],[3011.5,3002.4,3006.8,18300],[3009.2,2999.1,3004.5,22100],[3006.8,2996.3,3001.2,19500],[3004.1,2994.8,2999.7,17200],[3008.5,2998.2,3005.4,24300],[3012.3,3002.6,3009.8,28900],[3018.7,3008.4,3015.3,32100],[3022.1,3012.8,3019.6,29700],[3026.5,3016.3,3023.9,26400],[3030.8,3020.7,3028.2,33800],[3034.3,3024.6,3031.8,39200],[3038.9,3028.4,3036.5,44600]],
  index:[[5785,5762,5778,1850000],[5780,5755,5768,2210000],[5772,5748,5760,1980000],[5765,5741,5752,2560000],[5758,5734,5746,1730000],[5752,5728,5740,2040000],[5762,5738,5754,2370000],[5774,5750,5768,2890000],[5782,5758,5776,3120000],[5790,5765,5783,2980000],[5798,5773,5790,2650000],[5806,5781,5798,3340000],[5815,5790,5808,3870000],[5824,5799,5817,4210000]]
};
const META={forex:['EURUSD',''],xauusd:['XAUUSD',''],index:['SP500',''],stock:['SP500',''],crypto:['BTCUSD','']};

function fillDemo(){
  document.getElementById('tb').innerHTML='';rc=0;
  const t=document.getElementById('at').value;
  const key=t==='xauusd'?'xauusd':t==='index'||t==='stock'?'index':'forex';
  DM[key].forEach(d=>addRow(d[0],d[1],d[2],d[3]));
  const m=META[t]||META.forex;
  document.getElementById('ticker').value=m[0];
  // Fetch real price after loading demo candles
  fetchLivePrice();
}

// ─── LIVE PRICE FETCH ────────────────────────────────────────────────────────
async function fetchLivePrice(){
  const ticker = document.getElementById('ticker').value.trim().toUpperCase();
  if(!ticker) return;

  const priceEl = document.getElementById('price');
  const priceWrap = document.getElementById('price-wrap');
  priceEl.value = '';
  priceEl.placeholder = 'Buscando precio...';
  if(priceWrap) priceWrap.style.borderColor = 'var(--yellow)';

  const today = new Date().toLocaleDateString('es-ES',{day:'2-digit',month:'long',year:'numeric'});

  const prompt = `Hoy es ${today}. Busca el precio de mercado ACTUAL (en tiempo real o más reciente disponible) para el activo ${ticker}.

Responde ÚNICAMENTE con un JSON (sin backticks, sin texto extra):
{"price": 1.1572, "source": "nombre fuente"}

El precio debe ser un número decimal. Para forex 5 decimales, para XAU/USD 2 decimales, para índices 2 decimales.`;

  try {
    const r = await fetch("https://api.anthropic.com/v1/messages",{
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        model:'claude-sonnet-4-20250514', max_tokens:200,
        tools:[{type:"web_search_20250305",name:"web_search"}],
        messages:[{role:'user',content:prompt}]
      })
    });
    const data = await r.json();
    let raw = '';
    if(data.content) for(const b of data.content) if(b.type==='text') raw += b.text;
    const match = raw.match(/\{[\s\S]*?\}/);
    if(!match) throw new Error('no json');
    const j = JSON.parse(match[0]);
    if(j.price && !isNaN(j.price)){
      priceEl.value = j.price;
      priceEl.placeholder = '1.08500';
      if(priceWrap){ priceWrap.style.borderColor='var(--green)'; setTimeout(()=>priceWrap.style.borderColor='',2000); }
      // Show source tooltip
      const src = document.getElementById('price-source');
      if(src){ src.textContent = '✓ '+j.source; src.style.display='block'; }
    } else throw new Error('invalid price');
  } catch(e){
    priceEl.placeholder = 'Introduce precio manualmente';
    if(priceWrap) priceWrap.style.borderColor = 'var(--red2)';
    const src = document.getElementById('price-source');
    if(src){ src.textContent = '⚠ No se pudo obtener. Introduce manualmente.'; src.style.display='block'; src.style.color='var(--red2)'; }
  }
}

// CONTEXT
let CTX={macro:0,news:0,vol:'normal',summary:'',fetched:false,macroLabel:'Neutral',newsLabel:'Neutros',volLabel:'Normal'};
async function fetchCtx(){
  const ticker=document.getElementById('ticker').value.trim().toUpperCase()||'EURUSD';
  const at=document.getElementById('at').value;
  document.getElementById('ctx-btn').disabled=true;
  document.getElementById('ctx-ld').style.display='block';
  document.getElementById('ctx-res').style.display='none';
  const today=new Date().toLocaleDateString('es-ES',{weekday:'long',day:'2-digit',month:'long',year:'numeric'});
  const prompt=`Hoy es ${today}. Analiza el contexto ACTUAL de mercado para ${ticker} (${at}). Usa web search para buscar noticias de hoy, macro y calendario económico.

Responde SOLO con JSON válido (sin backticks ni texto extra):
{"macro":-1,"macro_label":"Bajista","macro_why":"1 frase","news":0,"news_label":"Neutros","news_why":"1 frase","vol":"normal","vol_label":"Normal","vol_why":"1 frase","summary":"2-3 frases contexto completo de ${ticker} hoy"}

macro y news: enteros de -2 a 2. vol: low, normal o high.`;
  try{
    const r=await fetch("https://api.anthropic.com/v1/messages",{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({model:'claude-sonnet-4-20250514',max_tokens:800,tools:[{type:"web_search_20250305",name:"web_search"}],messages:[{role:'user',content:prompt}]})});
    const data=await r.json();
    let raw='';if(data.content)for(const b of data.content)if(b.type==='text')raw+=b.text;
    const s=raw.indexOf('{'),e=raw.lastIndexOf('}');
    const j=JSON.parse(raw.slice(s,e+1));
    CTX={macro:j.macro??0,news:j.news??0,vol:j.vol??'normal',summary:j.summary||'',fetched:true,
      macroLabel:j.macro_label||'Neutral',newsLabel:j.news_label||'Neutros',volLabel:j.vol_label||'Normal',
      macroWhy:j.macro_why||'—',newsWhy:j.news_why||'—',volWhy:j.vol_why||'—'};
    const sc=v=>v>0?'var(--green)':v<0?'var(--red)':'var(--yellow)';
    const vc=v=>v==='high'?'var(--orange)':v==='low'?'var(--cyan)':'var(--text)';
    const mv=document.getElementById('ctx-mv');mv.textContent=j.macro_label;mv.style.color=sc(j.macro);
    document.getElementById('ctx-mw').textContent=j.macro_why||'—';
    const nv=document.getElementById('ctx-nv');nv.textContent=j.news_label;nv.style.color=sc(j.news);
    document.getElementById('ctx-nw').textContent=j.news_why||'—';
    const vv=document.getElementById('ctx-vv');vv.textContent=j.vol_label;vv.style.color=vc(j.vol);
    document.getElementById('ctx-vw').textContent=j.vol_why||'—';
    document.getElementById('ctx-sum').textContent=j.summary||'—';
  }catch(e){
    CTX={macro:0,news:0,vol:'normal',summary:'',fetched:false,macroLabel:'Neutral',newsLabel:'Neutros',volLabel:'Normal'};
    ['ctx-mv','ctx-nv','ctx-vv'].forEach((id,i)=>document.getElementById(id).textContent=['Neutral','Neutros','Normal'][i]);
    ['ctx-mw','ctx-nw','ctx-vw'].forEach(id=>document.getElementById(id).textContent='No disponible');
    document.getElementById('ctx-sum').textContent='No se pudo obtener contexto. Se usarán valores neutros.';
  }
  document.getElementById('ctx-ld').style.display='none';
  document.getElementById('ctx-res').style.display='block';
  document.getElementById('ctx-btn').disabled=false;
}

// ORDER FLOW
function calcOF(candles,period){
  const tps=candles.map(c=>(c.h+c.l+c.c)/3);
  const rawMF=candles.map((c,i)=>{if(i===0)return 0;const tp=tps[i],p=tps[i-1];return tp>p?tp*c.v:tp<p?-(tp*c.v):0;});
  const rmf=rawMF.map((_,i)=>{const s=Math.max(0,i-period+1);return rawMF.slice(s,i+1).reduce((a,b)=>a+b,0);});
  const zd=rmf.map((_,i)=>{const s=Math.max(0,i-period+1);const sl=rmf.slice(s,i+1);const mu=mean(sl),sg=std(sl);return sg===0?0:(rmf[i]-mu)/sg;});
  return{tps,rawMF,rmf,zd};
}
function mean(a){return a.reduce((x,y)=>x+y,0)/a.length}
function std(a){const m=mean(a);return Math.sqrt(a.reduce((x,y)=>x+(y-m)**2,0)/a.length)}

// MONTE CARLO GBM
function mcSim(price,rets,sims,zAdj,vm){
  const mu=mean(rets),sg=std(rets)*vm,drift=mu+zAdj*sg*0.15;
  const fp=[];
  for(let i=0;i<sims;i++){const z=bm();fp.push(price*Math.exp((drift-0.5*sg*sg)+sg*z));}
  return{fp,mu,sg,drift};
}
function bm(){let u=0,v=0;while(!u)u=Math.random();while(!v)v=Math.random();return Math.sqrt(-2*Math.log(u))*Math.cos(2*Math.PI*v);}

// UTILS
function dd(p){return p>500?1:p>100?2:p>1?4:5}
function fmt(n,d){return n.toFixed(d)}
function big(n){return n.toLocaleString('es-ES',{maximumFractionDigits:2})}

// MAIN
async function runAnalysis(){
  const candles=getC();if(candles.length<5){alert('Necesitas al menos 5 velas.');return;}
  goStep(3);
  document.getElementById('ldbox').classList.add('on');
  document.getElementById('rw').classList.remove('on');

  const ticker=document.getElementById('ticker').value.toUpperCase();
  const price=parseFloat(document.getElementById('price').value)||candles[candles.length-1].c;
  const sims=parseInt(document.getElementById('sims').value);
  const zp=parseInt(document.getElementById('zp').value);
  const at=document.getElementById('at').value;
  const macro=CTX.macro,news=CTX.news,vol=CTX.vol;

  const step=(id,ms)=>new Promise(res=>{setTimeout(()=>{stpLd(id);res();},ms);});

  await step('ls0',400);const of=calcOF(candles,zp);
  await step('ls1',450);const lastRMF=of.rmf[of.rmf.length-1],lastZ=of.zd[of.zd.length-1];
  await step('ls2',450);const closes=candles.map(c=>c.c);const rets=closes.slice(1).map((c,i)=>Math.log(c/closes[i]));
  await step('ls3',600);
  const vm=vol==='low'?0.7:vol==='high'?1.5:1.0;
  const ctxSc=(macro+news)/4;
  const zAdj=Math.max(-2,Math.min(2,lastZ+ctxSc*0.5));
  const res=mcSim(price,rets,sims,zAdj,vm);
  await step('ls4',600);
  const bullN=res.fp.filter(p=>p>price).length;
  const adjBull=Math.max(12,Math.min(88,(bullN/sims*100)+ctxSc*6));
  const adjBear=100-adjBull;
  const mcMean=mean(res.fp);
  const sorted=[...res.fp].sort((a,b)=>a-b);
  const p5=sorted[Math.floor(sims*0.05)],p95=sorted[Math.floor(sims*0.95)];
  // ── NIVELES DESDE DISTRIBUCIÓN MONTE CARLO ────────────────────────────────
  // ATR real H1 (para referencia y SL mínimo)
  const atrWin = candles.slice(-14);
  const atr    = atrWin.reduce((s,c)=>s+(c.h-c.l),0) / atrWin.length;

  await step('ls5',500);
  const primBull = adjBull > adjBear;

  // Distribución MC ordenada — extraemos percentiles clave
  const fp  = res.fp;
  const N   = fp.length;
  const pct = (p) => sorted[Math.min(N-1, Math.floor(N * p / 100))];

  // Percentiles direccionales
  const p10  = pct(10),  p15 = pct(15),  p20 = pct(20);
  const p35  = pct(35),  p40 = pct(40),  p45 = pct(45);
  const p55  = pct(55),  p60 = pct(60),  p65 = pct(65);
  const p80  = pct(80),  p85 = pct(85),  p90 = pct(90);

  // STOP — entrada en zona de alta densidad en dirección favorable
  // Bull: entrada sobre el percentil 62 (donde la masa de sims está en positivo)
  // Bear: entrada bajo el percentil 38
  const eStop  = primBull ? pct(62) : pct(38);
  // SL: fuera del 90% de la distribución (escenario adverso extremo)
  const slStop = primBull ? pct(8) : pct(92);
  // TP: zona de alta concentración favorable (percentil 85/15)
  const tpStop = primBull ? pct(85) : pct(15);

  // LIMIT — pullback al percentil 40/60, zona de valor con densidad alta
  const eLim   = primBull ? pct(38) : pct(62);
  // SL: más allá del 10%/90%
  const slLim  = primBull ? pct(8) : pct(92);
  // TP: misma zona objetivo que el stop
  const tpLim  = primBull ? pct(85) : pct(15);
  await step('ls6',400);
  let aiText='';
  try{aiText=await callAI(ticker,price,lastZ,lastRMF,adjBull,adjBear,res,mcMean,macro,news,atr,at,candles.length,CTX.summary);}
  catch(e){aiText=fallback(ticker,lastZ,adjBull,mcMean,price);}
  setLDone();await new Promise(r=>setTimeout(r,250));

  render({ticker,price,of,lastRMF,lastZ,adjBull,adjBear,p5,p95,res,mcMean,sims,atr,zAdj,ctxSc,primBull,eStop,slStop,tpStop,eLim,slLim,tpLim,aiText,candles,at,macro,news,vol});
}

function stpLd(id){const ids=['ls0','ls1','ls2','ls3','ls4','ls5','ls6'];let f=false;ids.forEach(s=>{const el=document.getElementById(s);if(f)return;if(el.id===id){el.className='ls on';f=true;}else{el.className='ls done';}});}
function setLDone(){['ls0','ls1','ls2','ls3','ls4','ls5','ls6'].forEach(s=>document.getElementById(s).className='ls done');}

function render(d){
  document.getElementById('ldbox').classList.remove('on');
  document.getElementById('rw').classList.add('on');
  const D=dd(d.price);
  const sc=v=>v>0?'var(--green)':v<0?'var(--red)':'var(--yellow)';
  const vc=v=>v==='high'?'var(--orange)':v==='low'?'var(--cyan)':'var(--text)';

  // Chips
  document.getElementById('chips').innerHTML=`
    <div class="chip"><span class="d2" style="background:${sc(d.macro)}"></span>Macro: ${CTX.macroLabel}</div>
    <div class="chip"><span class="d2" style="background:${sc(d.news)}"></span>Noticias: ${CTX.newsLabel}</div>
    <div class="chip"><span class="d2" style="background:${vc(d.vol)}"></span>Vol: ${CTX.volLabel}</div>
    ${CTX.fetched?'<div class="chip" style="color:var(--cyan);border-color:rgba(0,229,255,.3)">🌐 Contexto web activo</div>':'<div class="chip" style="color:var(--muted)">⚙️ Sin contexto (neutro)</div>'}`;

  // Verdict
  const vb=document.getElementById('vb'),vv=document.getElementById('vv');
  if(d.adjBull>=60){vb.className='vb bull';vv.textContent='SESGO ALCISTA ▲';}
  else if(d.adjBull<=40){vb.className='vb bear';vv.textContent='SESGO BAJISTA ▼';}
  else{vb.className='vb neu';vv.textContent='SESGO NEUTRAL ➡';}
  document.getElementById('mcn').textContent=d.sims.toLocaleString();
  document.getElementById('conf').textContent=d.adjBull>65||d.adjBull<35?'Alta':d.adjBull>58||d.adjBull<42?'Media':'Baja';

  // Probs
  document.getElementById('bull-p').textContent=d.adjBull.toFixed(1)+'%';
  document.getElementById('bear-p').textContent=d.adjBear.toFixed(1)+'%';
  document.getElementById('ci-lo').textContent=fmt(d.p5,D);
  document.getElementById('ci-hi').textContent=fmt(d.p95,D);
  document.getElementById('mcm').textContent=fmt(d.mcMean,D);

  // Z-Diff
  const z=d.lastZ;
  setTimeout(()=>{document.getElementById('zn').style.left=Math.max(2,Math.min(98,(z+3)/6*100))+'%';},120);
  const ze=document.getElementById('zv');ze.textContent=z.toFixed(3);
  let zs,zdsc,zc;
  if(z>1.5){zs='COMPRA';zdsc='Iniciativa alcista agresiva. Smart Money barriendo oferta.';zc='var(--green)';}
  else if(z>0.5){zs='SESGO LARGO';zdsc='Flujo positivo moderado. Presión compradora activa.';zc='#69f0ae';}
  else if(z>-0.5){zs='NEUTRAL';zdsc='Balance de subasta. Sin mano fuerte dominando.';zc='var(--yellow)';}
  else if(z>-1.5){zs='SESGO CORTO';zdsc='Flujo negativo moderado. Presión vendedora creciente.';zc='#ff6b6b';}
  else{zs='VENTA';zdsc='Distribución institucional. Smart Money liquidando.';zc='var(--red)';}
  ze.style.color=zc;
  document.getElementById('zst').textContent=zs;document.getElementById('zst').style.color=zc;
  document.getElementById('zd').textContent=zdsc;

  // Mini
  document.getElementById('rmf').textContent=big(d.lastRMF);
  document.getElementById('sig').textContent=(d.res.sg*100).toFixed(3)+'%';
  const dr=document.getElementById('dri');dr.textContent=(d.zAdj>=0?'+':'')+d.zAdj.toFixed(2);
  dr.style.color=d.zAdj>0.3?'var(--green)':d.zAdj<-0.3?'var(--red)':'var(--yellow)';
  document.getElementById('atrv').textContent=fmt(d.atr,D);

  // Chart
  drawChart(d.res.fp,d.price,D,{bull:d.primBull,eStop:d.eStop,slStop:d.slStop,tpStop:d.tpStop,eLim:d.eLim,tpLim:d.tpLim});

  // Orders
  const bull=d.primBull;
  // Calcular qué % de simulaciones MC quedan entre entrada y TP
  const bullSimsPct = (lo,hi) => (d.res.fp.filter(p=>p>=lo&&p<=hi).length/d.res.fp.length*100).toFixed(0);
  const pStopCoverage = bull
    ? bullSimsPct(d.eStop, d.tpStop)
    : bullSimsPct(d.tpStop, d.eStop);
  const pLimCoverage = bull
    ? bullSimsPct(d.eLim, d.tpLim)
    : bullSimsPct(d.tpLim, d.eLim);

  document.getElementById('ords').innerHTML=
    oLine(bull?'BUY':'SELL','STOP',d.eStop,d.slStop,d.tpStop,bull?d.adjBull:d.adjBear,D,
      `Percentil MC ${bull?62:38}. ${pStopCoverage}% de simulaciones entre entrada y TP. ${bull?'Z-Diff confirma si >+0.5':'Z-Diff confirma si <−0.5'}.`)+
    oLine(bull?'BUY':'SELL','LIMIT',d.eLim,d.slLim,d.tpLim,(bull?d.adjBull:d.adjBear)*0.85,D,
      `Percentil MC ${bull?38:62} — zona de valor. ${pLimCoverage}% de simulaciones entre entrada y TP. Mayor R:R esperado.`);

  // AI
  document.getElementById('ait').textContent=d.aiText;

  // OF table
  const tb=document.getElementById('oftb');tb.innerHTML='';
  d.candles.forEach((c,i)=>{
    const z=d.of.zd[i];
    const cls=z>1.5?'bull':z<-1.5?'bear':'neu';
    const es=z>1.5?'COMPRA':z<-1.5?'VENTA':'NEUTRAL';
    const mf=d.of.rawMF[i];
    const tr=document.createElement('tr');
    tr.innerHTML=`<td>V${i+1}</td><td>${d.of.tps[i].toFixed(D)}</td><td class="${mf>=0?'bull':'bear'}">${mf>=0?'+':''}${big(mf)}</td><td>${big(d.of.rmf[i])}</td><td class="${cls}">${z.toFixed(3)}</td><td class="${cls}">${es}</td>`;
    tb.appendChild(tr);
  });
}

function oLine(side,type,entry,sl,tp,prob,D,note){
  const buy=side==='BUY';const rr=Math.abs(tp-entry)/Math.abs(entry-sl);
  return`<div class="ol">
    <div class="ot ${buy?'buy':'sell'}">${side}<br/>${type}</div>
    <div class="op"><strong>${entry.toFixed(D)}</strong><span class="sub">entrada 22:00h CET</span></div>
    <div class="oi">SL: <span style="color:var(--red)">${sl.toFixed(D)}</span><br>TP: <span style="color:var(--green)">${tp.toFixed(D)}</span><br>RR: 1:${rr.toFixed(1)}</div>
    <div class="oi" style="font-size:10px;color:var(--muted)">${note}</div>
    <div class="opr ${buy?'bull':'bear'}">${prob.toFixed(1)}%</div>
  </div>`;
}

function drawChart(prices,ref,D,orderLevels){
  const cv=document.getElementById('cv');const ctx=cv.getContext('2d');
  const W=cv.offsetWidth||820,H=200;cv.width=W;cv.height=H;
  const bins=60,mn=Math.min(...prices),mx=Math.max(...prices),bw=(mx-mn)/bins;
  const hist=new Array(bins).fill(0);
  prices.forEach(p=>{const b=Math.min(bins-1,Math.floor((p-mn)/bw));hist[b]++;});
  const maxH=Math.max(...hist);
  const pad={t:14,r:10,b:38,l:10},cw=W-20,ch=H-52;
  ctx.clearRect(0,0,W,H);

  // Shaded TP zone
  if(orderLevels){
    const shade=(lo,hi,col)=>{
      const x1=pad.l+((Math.max(mn,lo)-mn)/(mx-mn))*cw;
      const x2=pad.l+((Math.min(mx,hi)-mn)/(mx-mn))*cw;
      ctx.fillStyle=col;ctx.fillRect(x1,pad.t,x2-x1,ch);
    };
    if(orderLevels.bull){
      shade(orderLevels.eStop,orderLevels.tpStop,'rgba(0,230,118,.08)');
      shade(orderLevels.eLim,orderLevels.tpLim,'rgba(0,230,118,.05)');
    } else {
      shade(orderLevels.tpStop,orderLevels.eStop,'rgba(255,23,68,.08)');
      shade(orderLevels.tpLim,orderLevels.eLim,'rgba(255,23,68,.05)');
    }
  }

  hist.forEach((cnt,i)=>{
    const x=pad.l+(i/bins)*cw;const bh=(cnt/maxH)*ch;const y=pad.t+ch-bh;
    const bc=mn+(i+.5)*bw;const isBull=bc>ref;
    const g=ctx.createLinearGradient(0,y,0,y+bh);
    if(isBull){g.addColorStop(0,'rgba(0,230,118,.85)');g.addColorStop(1,'rgba(0,230,118,.08)');}
    else{g.addColorStop(0,'rgba(255,23,68,.85)');g.addColorStop(1,'rgba(255,23,68,.08)');}
    ctx.fillStyle=g;ctx.fillRect(x,y,cw/bins-1,bh);
  });

  // Helper: draw vertical line with label
  const vLine=(price,color,label,yOff=0)=>{
    if(price<mn||price>mx)return;
    const x=pad.l+((price-mn)/(mx-mn))*cw;
    ctx.strokeStyle=color;ctx.lineWidth=1.5;ctx.setLineDash([3,3]);
    ctx.beginPath();ctx.moveTo(x,pad.t);ctx.lineTo(x,pad.t+ch);ctx.stroke();ctx.setLineDash([]);
    ctx.fillStyle=color;ctx.font='9px JetBrains Mono';ctx.textAlign='center';
    ctx.fillText(label,x,pad.t+ch+14+yOff);
  };

  // Order level lines
  if(orderLevels){
    vLine(orderLevels.slStop, 'rgba(255,23,68,.9)',  'SL');
    vLine(orderLevels.eStop,  orderLevels.bull?'rgba(0,230,118,1)':'rgba(255,23,68,1)', 'STOP');
    vLine(orderLevels.eLim,   orderLevels.bull?'rgba(105,240,174,.9)':'rgba(255,107,107,.9)', 'LIM');
    vLine(orderLevels.tpStop, orderLevels.bull?'rgba(0,230,118,.7)':'rgba(255,23,68,.7)', 'TP');
  }

  // Current price line
  const rx=pad.l+((ref-mn)/(mx-mn))*cw;
  ctx.strokeStyle='rgba(255,255,255,.8)';ctx.lineWidth=2;ctx.setLineDash([5,3]);
  ctx.beginPath();ctx.moveTo(rx,pad.t);ctx.lineTo(rx,pad.t+ch);ctx.stroke();ctx.setLineDash([]);
  ctx.font='10px JetBrains Mono';ctx.textAlign='center';ctx.fillStyle='rgba(255,255,255,.5)';
  ctx.fillText('PRECIO ACTUAL',rx,H-4);
  ctx.textAlign='left';ctx.fillStyle='rgba(255,23,68,.7)';ctx.fillText(mn.toFixed(D),pad.l,H-4);
  ctx.textAlign='right';ctx.fillStyle='rgba(0,230,118,.7)';ctx.fillText(mx.toFixed(D),W-pad.r,H-4);
}

// AI
async function callAI(ticker,price,z,rmf,bull,bear,res,mcMean,macro,news,atr,at,nC,ctxSum){
  const macroTxt=['muy bajista','bajista','neutral','alcista','muy alcista'][macro+2];
  const newsTxt=['muy negativos','negativos','neutros','positivos','muy positivos'][news+2];
  const ctxL=ctxSum&&ctxSum.length>5?`\nContexto web: ${ctxSum}`:'';
  const prompt=`Eres un trader institucional cuantitativo especializado en ${at}. Análisis en español, técnico y directo (4-5 oraciones). Sin asteriscos ni markdown.

Activo: ${ticker} | Precio: ${price} | MC esperado: ${mcMean.toFixed(5)}
Z-Diff: ${z.toFixed(3)} (${z>1.5?'COMPRA INSTITUCIONAL':z<-1.5?'VENTA INSTITUCIONAL':'NEUTRAL'})
RMF: ${big(rmf)} | P(alcista MC): ${bull.toFixed(1)}% | σ: ${(res.sg*100).toFixed(3)}% | ATR(H1): ${atr.toFixed(dd(price))}
Macro: ${macroTxt} | Noticias: ${newsTxt}${ctxL} | Velas: ${nC}

Explica: (1) si Z-Diff confirma el sesgo de Monte Carlo, (2) qué indica el Order Flow sobre presencia institucional, (3) si priorizar STOP o LIMIT a las 22:00h CET y por qué.`;
  const r=await fetch("https://api.anthropic.com/v1/messages",{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({model:'claude-sonnet-4-20250514',max_tokens:1000,messages:[{role:'user',content:prompt}]})});
  const data=await r.json();
  let text='';if(data.content)for(const b of data.content)if(b.type==='text')text+=b.text;
  return text||'';
}
function fallback(ticker,z,bull,mcMean,price){
  const dir=z>1.5?'alcista institucional':z<-1.5?'bajista institucional':'equilibrada';
  return`El Z-Diff de ${z.toFixed(3)} señala una iniciativa ${dir} en el Order Flow de ${ticker}. Monte Carlo proyecta el precio esperado ${mcMean>price?'por encima':'por debajo'} del nivel actual con ${bull.toFixed(1)}% de probabilidad alcista. Para las 22:00h CET se recomienda priorizar la orden ${z>0?'Buy Stop':'Sell Stop'} y ajustar el stop al ATR calculado respetando la gestión de riesgo.`;
}

fillDemo();
</script>
</body>
</html>
    </script>
</body>
</html>
"""

# 3. Ejecución del componente en Streamlit
# Ajustamos el height a 2500 para evitar el doble scroll
components.html(html_template, height=2500, scrolling=False)
