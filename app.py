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
.card{background:var(--s1);border:1px solid var(--border);border-radius:3px;padding:18px 20px;margin-bottom:14px}
.field{display:flex;flex-direction:column;gap:6px}
.field label{font-size:9px;letter-spacing:3px;text-transform:uppercase;color:var(--muted)}
.field input,.field select{background:var(--s0);border:1px solid var(--border2);color:var(--text);font-family:var(--mono);font-size:13px;padding:9px 12px;border-radius:2px;outline:none;width:100%}
.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.pills{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}
.pill{font-family:var(--display);font-size:13px;font-weight:600;letter-spacing:2px;padding:7px 16px;border:1px solid var(--border2);border-radius:2px;cursor:pointer;color:var(--muted);background:transparent;transition:all .15s}
.pill.active{color:var(--cyan);border-color:var(--cyan);background:rgba(0,229,255,.06)}
.sbar{display:flex;align-items:center;gap:10px;padding:9px 14px;border-radius:2px;font-size:10px;letter-spacing:2px;text-transform:uppercase;margin-bottom:10px;border:1px solid var(--border2);color:var(--muted);background:var(--s0)}
.sbar.ok{border-color:rgba(0,230,118,.3);color:var(--green);background:rgba(0,230,118,.04)}
.btn{font-family:var(--display);font-size:14px;font-weight:700;letter-spacing:3px;text-transform:uppercase;padding:11px 22px;cursor:pointer;border-radius:2px;border:1px solid;transition:all .2s}
.btn-c{border-color:var(--cyan);color:var(--cyan);background:rgba(0,229,255,.05);width:100%}
.btn-c:hover{background:var(--cyan);color:var(--bg);box-shadow:0 0 24px rgba(0,229,255,.3)}
.tbl-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12px}
th{font-size:8px;letter-spacing:3px;text-transform:uppercase;color:var(--muted);padding:8px 10px;text-align:right;border-bottom:1px solid var(--border2)}
td{padding:7px 10px;text-align:right;border-bottom:1px solid var(--border)}
.res-wrap{display:none}.res-wrap.show{display:block}
.verdict{border:1px solid;border-radius:3px;padding:18px 22px;margin-bottom:14px;display:flex;justify-content:space-between;align-items:center}
.verdict.bull{border-color:var(--green);background:rgba(0,230,118,.05)}
.verdict.bear{border-color:var(--red);background:rgba(255,23,68,.05)}
.vd-val{font-family:var(--display);font-size:30px;font-weight:700;letter-spacing:2px}
.prob-card{background:var(--s1);border:1px solid var(--border2);padding:20px;text-align:center}
.pc-num{font-family:var(--display);font-size:60px;font-weight:700}
.zdiff-gauge{position:relative;height:10px;background:#333;border-radius:5px;margin:20px 0}
.zdiff-needle{position:absolute;top:-5px;width:4px;height:20px;background:#fff;left:50%;transition:all 1s}
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
        <div class="tab active" onclick="goTab('input')">① ENTRADA DE DATOS</div>
        <div class="tab" onclick="goTab('results')" id="tab-res" style="opacity:0.5">② RESULTADOS</div>
    </div>

    <div class="tab-panel active" id="panel-input">
        <div class="pills">
            <button class="pill" onclick="selectAsset('EURUSD=X','forex',this)">EUR/USD</button>
            <button class="pill" onclick="selectAsset('GC=F','commodity',this)">XAU/USD 🥇</button>
            <button class="pill" onclick="selectAsset('%5EGSPC','index',this)">S&P 500</button>
            <button class="pill" onclick="selectAsset('BTC-USD','crypto',this)">BITCOIN</button>
        </div>

        <div class="card">
            <div class="g4">
                <div class="field"><label>Ticker</label><input id="ticker" value="EURUSD=X"></div>
                <div class="field"><label>Precio actual</label><input id="price" type="number" step="0.00001"></div>
                <div class="field"><label>Activo</label><select id="asset-type"><option value="forex">Forex</option><option value="commodity">XAU/USD</option></select></div>
                <div class="field"><label>Días</label><input id="horizon" type="number" value="3"></div>
            </div>
        </div>

        <div id="yahoo-status" class="sbar" style="display:none">📡 SINCRONIZANDO...</div>

        <div class="card">
            <div class="tbl-wrap">
                <table>
                    <thead><tr><th>VELA</th><th>HIGH</th><th>LOW</th><th>CLOSE</th><th>VOL</th><th>TP</th></tr></thead>
                    <tbody id="candle-body"></tbody>
                </table>
            </div>
        </div>

        <div id="ctx-status" class="sbar" style="display:none">◌ IA ANALIZANDO...</div>

        <button class="btn btn-c" onclick="runAnalysis()">▶ EJECUTAR ANÁLISIS COMPLETO</button>
    </div>

    <div class="tab-panel" id="panel-results">
        <div class="res-wrap" id="res-wrap">
            <div class="verdict" id="verdict">
                <div><div class="vd-val" id="v-val">ANALIZANDO...</div></div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
                <div class="prob-card"><div class="pc-num" id="bull-pct">0%</div><div>PROB. ALCISTA</div></div>
                <div class="prob-card"><div class="pc-num" id="bear-pct">0%</div><div>PROB. BAJISTA</div></div>
            </div>
            <div class="card">
                <div class="zdiff-gauge"><div class="zdiff-needle" id="z-needle"></div></div>
                <div style="text-align:center;font-size:20px" id="z-num">0.00</div>
            </div>
            <div class="ai-panel" style="background:#001529;padding:20px;border-left:4px solid #0090ff">
                <div id="ai-body">Esperando respuesta de la IA...</div>
            </div>
        </div>
    </div>
</div>

<script>
// --- MOTOR DE AUTOCARGA ---
async function selectAsset(symbol, type, el) {
    document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
    el.classList.add('active');
    document.getElementById('ticker').value = symbol;
    document.getElementById('asset-type').value = type;
    
    // Disparo automático
    await loadYahooCandles();
    await fetchContext();
}

async function loadYahooCandles() {
    const sym = document.getElementById('ticker').value;
    const st = document.getElementById('yahoo-status');
    st.style.display = 'flex';
    st.textContent = '📡 CARGANDO VELAS REALES H1...';

    const prompt = `Devuelve las últimas 20 velas H1 reales para ${sym}. Solo JSON sin texto: {"price":0,"candles":[{"h":0,"l":0,"c":0,"v":0}]}`;

    try {
        const r = await fetch("https://api.anthropic.com/v1/messages", {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: 'claude-sonnet-4-20250514', max_tokens: 2000,
                tools: [{ type: "web_search_20250305", name: "web_search" }],
                messages: [{ role: 'user', content: prompt }]
            })
        });
        const data = await r.json();
        const j = JSON.parse(data.content[0].text);

        document.getElementById('candle-body').innerHTML = '';
        j.candles.forEach((c, i) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td>V${i}</td><td>${c.h}</td><td>${c.l}</td><td>${c.c}</td><td>${c.v}</td><td>${((c.h+c.l+c.c)/3).toFixed(5)}</td>`;
            document.getElementById('candle-body').appendChild(tr);
        });
        document.getElementById('price').value = j.price || j.candles.at(-1).c;
        st.textContent = '✓ VELAS SINCRONIZADAS';
    } catch (e) { st.textContent = '⚠ ERROR DE CARGA'; }
}

async function fetchContext() {
    const ticker = document.getElementById('ticker').value;
    const st = document.getElementById('ctx-status');
    st.style.display = 'flex';
    st.textContent = '◌ IA ANALIZANDO NOTICIAS...';

    try {
        const r = await fetch("https://api.anthropic.com/v1/messages", {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: 'claude-sonnet-4-20250514', max_tokens: 800,
                tools: [{ type: "web_search_20250305", name: "web_search" }],
                messages: [{ role: 'user', content: `Analiza noticias swing para ${ticker}. Solo JSON: {"bias":1,"summary":"..."}` }]
            })
        });
        const data = await r.json();
        const j = JSON.parse(data.content[0].text);
        window._macroBias = j.bias;
        st.textContent = '✓ IA: SESGO LISTO';
    } catch (e) { st.textContent = '⚠ ERROR IA'; }
}

// --- LÓGICA DE CÁLCULO ---
function goTab(t) {
    document.getElementById('panel-input').classList.toggle('active', t==='input');
    document.getElementById('panel-results').classList.toggle('active', t==='results');
}

function runAnalysis() {
    goTab('results');
    document.getElementById('res-wrap').classList.add('show');
    
    // Simulación de cálculo Order Flow
    const z = (Math.random() * 4 - 2).toFixed(2);
    document.getElementById('z-num').textContent = z;
    document.getElementById('z-needle').style.left = `${((parseFloat(z)+3)/6)*100}%`;
    
    const bull = (Math.random() * 40 + 30 + (window._macroBias || 0) * 10).toFixed(1);
    document.getElementById('bull-pct').textContent = bull + '%';
    document.getElementById('bear-pct').textContent = (100 - bull).toFixed(1) + '%';
    
    const v = document.getElementById('verdict');
    if(bull > 55) { v.className = 'verdict bull'; document.getElementById('v-val').textContent = 'COMPRA'; }
    else { v.className = 'verdict bear'; document.getElementById('v-val').textContent = 'VENTA'; }
}

setInterval(() => {
    document.getElementById('clk').textContent = new Date().toLocaleTimeString();
}, 1000);
</script>
</body>
</html>
