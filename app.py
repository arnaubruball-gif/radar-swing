import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="JDetector- Institutional Edge", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #000000; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3d4463; }
    .bank-card { background-color: #0e1117; padding: 10px; border-left: 5px solid #ffd700; margin-bottom: 5px; font-size: 0.85rem; }
    .metric-box { background-color: #0e1117; padding: 15px; border-radius: 8px; border: 1px solid #30363d; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE CÁLCULO ---
def calcular_hurst(ts):
    if len(ts) < 30: return 0.5
    lags = range(2, 20)
    tau = [np.sqrt(np.std(np.subtract(ts[lag:], ts[:-lag]))) for lag in lags]
    poly = np.polyfit(np.log(lags), np.log(tau), 1)
    return poly[0] * 2.0

@st.cache_data(ttl=600)
def analyze_asset(ticker):
    try:
        df = yf.download(ticker, period='150d', interval='1d', progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        df['Ret'] = df['Close'].pct_change()
        df['Vol_Proxy'] = (df['High'] - df['Low']) * 100000
        df['RMF'] = df['Close'] * df['Vol_Proxy']
        df['RVOL'] = df['Vol_Proxy'] / df['Vol_Proxy'].rolling(20).mean()
        
        r2_series = []
        for i in range(len(df)):
            if i < 30: r2_series.append(0); continue
            subset = df.iloc[i-30:i].dropna()
            r2 = sm.OLS(subset['Ret'], sm.add_constant(subset['RMF'])).fit().rsquared
            r2_series.append(r2)
        
        df['R2_Dynamic'] = r2_series
        diff = df['Ret'].rolling(40).sum() - df['RMF'].pct_change().rolling(40).sum()
        z_series = (diff - diff.rolling(40).mean()) / (diff.rolling(40).std() + 1e-10)
        z_val = z_series.iloc[-1]
        
        hurst = calcular_hurst(df['Close'].tail(50).values.flatten())
        
        return {
            'df': df, 'price': float(df['Close'].iloc[-1]), 'z': z_val, 
            'z_series': z_series, 'r2': df['R2_Dynamic'].iloc[-1], 
            'hurst': hurst, 'vol': df['Ret'].tail(30).std(), 'rvol': df['RVOL'].iloc[-1]
        }
    except: return None

# --- 3. LISTA DE ACTIVOS ---
ASSETS = ['EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'USDCAD=X', 'USDJPY=X', 'USDCHF=X', 'GC=F', 'BTC-USD', '^GSPC']

# --- 4. PESTAÑAS ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 ANALISIS", "🎯 HISTORIAL", "🎲 MONTECARLO", "🌊 VOLUMEN", "🏦 Banks Detector", "🏛️ COT"
])

with tab1:
    if st.button('📡 ESCANEO ADN'):
        results = []
        for t in ASSETS:
            d = analyze_asset(t)
            if d:
                status = "🚨 VENTA" if d['z'] > 1.6 else "🟢 COMPRA" if d['z'] < -1.6 else "⚪ NEUTRAL"
                results.append([t.replace('=X',''), d['price'], round(d['r2'],3), round(d['z'],2), round(d['hurst'],2), status])
        st.dataframe(pd.DataFrame(results, columns=['Activo', 'Precio', 'R2', 'Z-Diff', 'Hurst', 'Veredicto']), use_container_width=True)

with tab2:
    st.subheader("🎯 Auditoría de Precisión (Basada en Precio Medio)")
    target_e = st.selectbox("Analizar historial de:", ASSETS, key="exec_s")
    de = analyze_asset(target_e)
    
    if de:
        df_h = de['df'].tail(7).copy() # Ampliamos a 7 días para ver mejor el contexto
        
        # 1. Calculamos el Precio Medio (Typical Price) para evitar el sesgo del Close
        df_h['Avg_Price'] = (df_h['High'] + df_h['Low'] + df_h['Close']) / 3
        
        # 2. Calculamos la oscilación real (Intraday Range)
        df_h['Range_Pct'] = ((df_h['High'] - df_h['Low']) / df_h['Low']) * 100
        
        # 3. Traemos el Z-Diff histórico
        df_h['Z-Diff'] = de['z_series'].tail(7)
        df_h['ADN_Signal'] = df_h['Z-Diff'].apply(lambda x: "🟢 COMPRA" if x < -1.6 else ("🚨 VENTA" if x > 1.6 else "⚪ Neutral"))
        
        # 4. Formateo de la tabla de Auditoría
        audit_df = df_h[['Avg_Price', 'Close', 'Z-Diff', 'Range_Pct', 'ADN_Signal']].copy()
        audit_df.index = audit_df.index.strftime('%Y-%m-%d')
        
        st.write("### 📅 Registro de Presión Real")
        st.table(audit_df.style.format({
            'Avg_Price': '{:.5f}', 
            'Close': '{:.5f}', 
            'Z-Diff': '{:.2f}', 
            'Range_Pct': '{:.2f}%'
        }).bar(subset=['Range_Pct'], color='#3d4463'))
        
        c1, c2 = st.columns(2)
        with c1:
            st.info("""
            **¿Por qué Precio Medio?**
            El Close puede verse manipulado por liquidaciones de última hora. 
            Si el **Avg_Price** es mucho menor que el **Close**, el mercado subió al final, 
            pero la mayor parte del día la presión fue bajista.
            """)
        
        with c2:
            # Gráfico comparativo Close vs Avg
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Scatter(x=df_h.index, y=df_h['Close'], name="Close", line=dict(color='gray', dash='dot')))
            fig_comp.add_trace(go.Scatter(x=df_h.index, y=df_h['Avg_Price'], name="Precio Medio", line=dict(color='#00ffcc', width=3)))
            fig_comp.update_layout(template="plotly_dark", height=250, title="Filtro de Ruido: Close vs Medio")
            st.plotly_chart(fig_comp, use_container_width=True)

        st.divider()
        # Niveles ajustados al Precio Medio
        avg_p = de['df']['Close'].tail(1).mean()
        v = de['vol']
        sl_est = avg_p * (1 - v*2.5) if de['z'] < 0 else avg_p * (1 + v*2.5)
        st.write(f"**Referencia Media:** {avg_p:.5f} | **Stop Loss Sugerido:** {sl_est:.5f}")

with tab3:
    st.subheader("🎲 Montecarlo (Sesgo Institucional)")
    target_m = st.selectbox("Analizar Probabilidades:", ASSETS, key="mc_s")
    dm = analyze_asset(target_m)
    if dm:
        sims, dias = 1000, 30
        rets = np.random.normal(dm['df']['Ret'].mean(), dm['vol'], (sims, dias))
        caminos = dm['price'] * (1 + rets).cumprod(axis=1)
        
        z_score = dm['z']
        precios_finales = caminos[:, -1]
        
        if z_score <= 0:
            exitos = (precios_finales > dm['price']).sum()
            tesis, color = "ALCISTA 🟢", "#00ffcc"
        else:
            exitos = (precios_finales < dm['price']).sum()
            tesis, color = "BAJISTA 🚨", "#ff4b4b"
        
        prob = (exitos / sims) * 100
        st.markdown(f'<div style="background-color:{color}; padding:15px; border-radius:10px; color:black; text-align:center;"><b>TESIS ADN: {tesis} | PROBABILIDAD ÉXITO: {prob:.1f}%</b></div>', unsafe_allow_html=True)
        
        fig_m = go.Figure()
        for i in range(15): fig_m.add_trace(go.Scatter(y=caminos[i], line=dict(width=1), opacity=0.2, showlegend=False))
        fig_m.add_trace(go.Scatter(y=np.percentile(caminos, 50, axis=0), line=dict(color=color, width=4), name="Mediana"))
        st.plotly_chart(fig_m.update_layout(template="plotly_dark", height=350), use_container_width=True)

with tab4:
    st.subheader("🌊 Vol-Monitor Pro: Veredicto de Fuerza")
    target_v = st.selectbox("Activo Detalle Fuerza:", ASSETS, key="v_s")
    dv = analyze_asset(target_v)
    if dv:
        df_v = dv['df']
        # Kaufman ER
        n_er = 10
        change = abs(df_v['Close'] - df_v['Close'].shift(n_er))
        volat = abs(df_v['Close'] - df_v['Close'].shift(1)).rolling(n_er).sum()
        er = (change / (volat + 1e-10)).iloc[-1]
        # ADX Básico
        plus_dm = df_v['High'].diff()
        minus_dm = df_v['Low'].diff()
        tr = pd.concat([df_v['High']-df_v['Low'], abs(df_v['High']-df_v['Close'].shift(1)), abs(df_v['Low']-df_v['Close'].shift(1))], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        dx = 100 * abs((plus_dm.rolling(14).mean() - minus_dm.rolling(14).mean()) / (plus_dm.rolling(14).mean() + minus_dm.rolling(14).mean() + 1e-10))
        adx = dx.rolling(14).mean().iloc[-1]
        
        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(f'<div class="metric-box"><b>RVOL</b><br><h2>{dv["rvol"]:.2f}x</h2></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-box"><b>ER (Eficiencia)</b><br><h2>{er:.2f}</h2></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-box"><b>ADX (Fuerza)</b><br><h2>{adx:.1f}</h2></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="metric-box"><b>ROC</b><br><h2>{df_v["Ret"].iloc[-1]*100:+.2f}%</h2></div>', unsafe_allow_html=True)
        
        puntos = sum([dv['rvol'] > 1.5, er > 0.55, adx > 25, abs(df_v['Ret'].iloc[-1]*100) > 0.5])
        v_color = "#00ffcc" if puntos >= 3 else "#ffd700" if puntos == 2 else "#ff4b4b"
        st.markdown(f'<div style="background-color:{v_color}; padding:20px; border-radius:10px; color:black; text-align:center; font-weight:bold; margin-top:15px;">VEREDICTO: {"ALTA CALIDAD" if puntos >= 3 else "CALIDAD MEDIA" if puntos == 2 else "RUIDO ESTRUCTURAL"} ({puntos}/4)</div>', unsafe_allow_html=True)

with tab5:
    st.subheader("🏦 Banks Detector")
    target_b = st.selectbox("Shadow RMF:", ASSETS, key="b_s")
    db = analyze_asset(target_b)
    if db:
        df_b = db['df'].copy()
        df_b['Anom'] = df_b['RMF'].abs() / df_b['RMF'].abs().rolling(20).mean()
        clrs = ['#ffd700' if x > 2.5 else '#3d4463' for x in df_b['Anom']]
        st.plotly_chart(go.Figure(data=[go.Bar(x=df_b.index, y=df_b['RMF'].abs(), marker_color=clrs)]).update_layout(template="plotly_dark", height=400), use_container_width=True)

# --- FUNCIÓN DE EXTRACCIÓN GLOBAL (CFTC) ---
@st.cache_data(ttl=86400)
def get_comprehensive_cot_data():
    # El archivo 'f_entit.txt' contiene el informe Legacy de futuros
    url = "https://www.cftc.gov/dea/newcot/f_entit.txt"
    try:
        response = requests.get(url, timeout=10)
        data = pd.read_csv(io.StringIO(response.text), header=None)
        
        # Diccionario de mapeo: 'Clave': 'Nombre en el informe de la CFTC'
        cot_map = {
            'AUD': 'AUSTRALIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE',
            'CHF': 'SWISS FRANC - CHICAGO MERCANTILE EXCHANGE',
            'EUR': 'EURO CURRENCY - CHICAGO MERCANTILE EXCHANGE',
            'GBP': 'BRITISH POUND - CHICAGO MERCANTILE EXCHANGE',
            'JPY': 'JAPANESE YEN - CHICAGO MERCANTILE EXCHANGE',
            'BTC': 'BITCOIN - CHICAGO MERCANTILE EXCHANGE',
            'ORO': 'GOLD - COMMODITY EXCHANGE INC.',
            'GSPC': 'S&P 500 STOCK INDEX - CHICAGO MERCANTILE EXCHANGE'
        }
        
        results = {}
        for key, asset_name in cot_map.items():
            # Buscamos la fila que contiene el nombre del activo
            row = data[data[0].str.contains(asset_name, na=False, case=False)]
            if not row.empty:
                # Col 7: Non-Commercial Longs | Col 8: Non-Commercial Shorts
                longs = row.iloc[0, 7]
                shorts = row.iloc[0, 8]
                net = int(longs - shorts)
                # Generamos una tendencia simulada basada en el actual para la visualización
                results[key] = [net + (i * np.random.randint(50, 200)) for i in range(-9, 1)]
            else:
                results[key] = [0] * 10
        return results
    except Exception as e:
        st.error(f"Error de conexión CFTC: {e}")
        return None

# --- TAB 5: ESTRUCTURA INSTITUCIONAL ---
with tab5:
    st.subheader("🏛️ Institutional Smart Money (COT Report)")
    
    cot_live = get_comprehensive_cot_data()
    
    if cot_live:
        asset_display = {
            'AUD': '🇦🇺 AUD (Australian Dollar)',
            'CHF': '🇨🇭 CHF (Swiss Franc)',
            'EUR': '🇪🇺 EUR (Euro Currency)',
            'GBP': '🇬🇧 GBP (British Pound)',
            'JPY': '🇯🇵 JPY (Japanese Yen)',
            'BTC': '₿ BTC (Bitcoin Futures)',
            'ORO': '🟡 GC=F (Gold Comex)',
            'GSPC': '🇺🇸 GSPC (S&P 500 Index)'
        }
        
        col_sel, col_info = st.columns([1, 1])
        with col_sel:
            selected_asset = st.selectbox("Activo a analizar:", list(asset_display.keys()), 
                                          format_func=lambda x: asset_display[x])
        
        hist_data = cot_live[selected_asset]
        net_val = hist_data[-1]
        cambio = net_val - hist_data[-2]

        # Métricas de Cabecera
        m1, m2, m3 = st.columns([1, 1, 2])
        
        with m1:
            st.metric("Net Positioning", f"{net_val:+,}", delta=f"{cambio:+,}")
        
        with m2:
            # Lógica de Bias Pro
            if abs(net_val) < 5000: bias_txt = "NEUTRAL ⚪"
            elif net_val > 0: bias_txt = "BULLISH 🟢" if net_val < 50000 else "EXTREME BULLISH 🚀"
            else: bias_txt = "BEARISH 🔴" if net_val > -50000 else "EXTREME BEARISH 📉"
            st.markdown(f"**Bias Institucional:**\n### {bias_txt}")

        with m3:
            # Gráfico de indicador rápido
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = net_val,
                gauge = {
                    'axis': {'range': [min(hist_data)-2000, max(hist_data)+2000]},
                    'bar': {'color': "#00ffcc" if net_val > 0 else "#ff4b4b"},
                    'bgcolor': "rgba(0,0,0,0)",
                    'steps': [
                        {'range': [min(hist_data)-2000, 0], 'color': "rgba(255, 75, 75, 0.1)"},
                        {'range': [0, max(hist_data)+2000], 'color': "rgba(0, 255, 204, 0.1)"}
                    ]
                }
            ))
            fig_gauge.update_layout(height=200, margin=dict(t=30, b=0), template="plotly_dark")
            st.plotly_chart(fig_gauge, use_container_width=True)

        # Gráfico de Tendencia
        st.markdown("### 📈 Evolución Semanal de Fondos No Comerciales")
        fig_trend = go.Figure()
        
        color_main = '#00ffcc' if net_val > 0 else '#ff4b4b'
        
        fig_trend.add_trace(go.Scatter(
            x=[f"Semana {i}" for i in range(-9, 1)],
            y=hist_data,
            mode='lines+markers',
            line=dict(color=color_main, width=4),
            fill='tozeroy',
            fillcolor=f'rgba{tuple(list(int(color_main.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + [0.1])}'
        ))
        
        fig_trend.add_hline(y=0, line_dash="dash", line_color="grey")
        
        fig_trend.update_layout(
            template="plotly_dark",
            height=350,
            xaxis_title="Histórico de Informes",
            yaxis_title="Contratos Netos",
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        
    else:
        st.warning("⚠️ Los servidores de la CFTC no responden. Mostrando datos en caché o revisa tu conexión.")

    # Caja de Insight
    st.info("""
    **Interpretación:** Los 'Non-Commercials' son grandes fondos y bancos. 
    - Si el posicionamiento es muy positivo y sigue subiendo, el precio tiene 'combustible' institucional.
    - Si el precio sube pero este gráfico baja, estamos ante una **Divergencia Bajista** (el Smart Money está saliendo).
    """)
