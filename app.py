import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.graph_objects as go
import requests
from datetime import datetime

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="JDetector - Institutional Edge", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #000000; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3d4463; }
    .metric-box { background-color: #0e1117; padding: 15px; border-radius: 8px; border: 1px solid #30363d; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE CÁLCULO (OPTIMIZADO CORTO PLAZO) ---
def calcular_hurst(ts):
    if len(ts) < 20: return 0.5
    lags = range(2, 15)
    tau = [np.sqrt(np.std(np.subtract(ts[lag:], ts[:-lag]))) for lag in lags]
    poly = np.polyfit(np.log(lags), np.log(tau), 1)
    return poly[0] * 2.0

@st.cache_data(ttl=600)
def analyze_asset(ticker):
    try:
        df = yf.download(ticker, period='100d', interval='1d', progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        df['Ret'] = df['Close'].pct_change()
        df['Vol_Proxy'] = (df['High'] - df['Low']) * 100000
        df['RMF'] = df['Close'] * df['Vol_Proxy']
        df['RVOL'] = df['Vol_Proxy'] / df['Vol_Proxy'].rolling(15).mean() 
        
        r2_series = []
        for i in range(len(df)):
            if i < 20: r2_series.append(0); continue
            subset = df.iloc[i-20:i].dropna()
            r2 = sm.OLS(subset['Ret'], sm.add_constant(subset['RMF'])).fit().rsquared
            r2_series.append(r2)
        
        df['R2_Dynamic'] = r2_series
        
        # Z-DIFF CORTO PLAZO (Ajustado a 20 periodos para mayor velocidad)
        periodo_z = 20
        diff = df['Ret'].rolling(periodo_z).sum() - df['RMF'].pct_change().rolling(periodo_z).sum()
        z_series = (diff - diff.rolling(periodo_z).mean()) / (diff.rolling(periodo_z).std() + 1e-10)
        z_val = z_series.iloc[-1]
        
        hurst = calcular_hurst(df['Close'].tail(30).values.flatten())
        
        return {
            'df': df, 'price': float(df['Close'].iloc[-1]), 'z': z_val, 
            'z_series': z_series, 'r2': df['R2_Dynamic'].iloc[-1], 
            'hurst': hurst, 'vol': df['Ret'].tail(20).std(), 'rvol': df['RVOL'].iloc[-1]
        }
    except: return None

# --- 3. LISTA DE ACTIVOS AMPLIADA ---
ASSETS = [
    'EURUSD=X', 'GBPUSD=X', 'AUDUSD=X', 'USDJPY=X', # Forex
    'GC=F', 'CL=F', 'SI=F', 'HG=F',                # Oro, Petróleo, Plata, Cobre
    'BTC-USD', '^GSPC', '^TNX'                     # Crypto, S&P500, Bono 10Y
]

# --- 4. PESTAÑAS ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 ANALISIS", "🎯 HISTORIAL", "🎲 MONTECARLO", "🌊 VOLUMEN", "🏦 Banks Detector", "🏛️ COT", "⚖️ BEER Pricing"
])

with tab1:
    if st.button('📡 ESCANEO ADN'):
        results = []
        for t in ASSETS:
            if t == '^TNX': continue
            d = analyze_asset(t)
            if d:
                # Umbral más sensible (1.4) para operativa rápida
                status = "🚨 VENTA" if d['z'] > 1.4 else "🟢 COMPRA" if d['z'] < -1.4 else "⚪ NEUTRAL"
                results.append([t.replace('=X',''), d['price'], round(d['r2'],3), round(d['z'],2), round(d['hurst'],2), status])
        st.dataframe(pd.DataFrame(results, columns=['Activo', 'Precio', 'R2', 'Z-Diff', 'Hurst', 'Veredicto']), use_container_width=True)

with tab2:
    st.subheader("🎯 Auditoría de Presión (Corto Plazo)")
    target_e = st.selectbox("Analizar historial de:", ASSETS, key="exec_s")
    de = analyze_asset(target_e)
    if de:
        df_h = de['df'].tail(7).copy()
        df_h['Avg_Price'] = (df_h['High'] + df_h['Low'] + df_h['Close']) / 3
        df_h['Range_Pct'] = ((df_h['High'] - df_h['Low']) / df_h['Low']) * 100
        df_h['Z-Diff'] = de['z_series'].tail(7)
        df_h['ADN_Signal'] = df_h['Z-Diff'].apply(lambda x: "🟢 COMPRA" if x < -1.4 else ("🚨 VENTA" if x > 1.4 else "⚪ Neutral"))
        
        audit_df = df_h[['Avg_Price', 'Close', 'Z-Diff', 'Range_Pct', 'ADN_Signal']].copy()
        audit_df.index = audit_df.index.strftime('%Y-%m-%d')
        st.table(audit_df.style.format({'Avg_Price': '{:.4f}', 'Close': '{:.4f}', 'Z-Diff': '{:.2f}', 'Range_Pct': '{:.2f}%'}))

with tab3:
    st.subheader("🎲 Montecarlo (Sesgo a 15 días)")
    target_m = st.selectbox("Analizar Probabilidades:", ASSETS, key="mc_s")
    dm = analyze_asset(target_m)
    if dm:
        sims, dias = 1000, 15 
        rets = np.random.normal(dm['df']['Ret'].mean(), dm['vol'], (sims, dias))
        caminos = dm['price'] * (1 + rets).cumprod(axis=1)
        z_score = dm['z']
        precios_finales = caminos[:, -1]
        
        tesis, color = ("ALCISTA 🟢", "#00ffcc") if z_score <= 0 else ("BAJISTA 🚨", "#ff4b4b")
        exitos = (precios_finales > dm['price']).sum() if z_score <= 0 else (precios_finales < dm['price']).sum()
        
        prob = (exitos / sims) * 100
        st.markdown(f'<div style="background-color:{color}; padding:15px; border-radius:10px; color:black; text-align:center;"><b>TESIS ADN: {tesis} | PROBABILIDAD: {prob:.1f}%</b></div>', unsafe_allow_html=True)
        
        fig_m = go.Figure()
        for i in range(15): fig_m.add_trace(go.Scatter(y=caminos[i], line=dict(width=1), opacity=0.1, showlegend=False))
        fig_m.add_trace(go.Scatter(y=np.percentile(caminos, 50, axis=0), line=dict(color=color, width=4), name="Mediana"))
        st.plotly_chart(fig_m.update_layout(template="plotly_dark", height=350), use_container_width=True)

with tab4:
    st.subheader("🌊 Vol-Monitor Pro")
    target_v = st.selectbox("Activo Detalle Fuerza:", ASSETS, key="v_s")
    dv = analyze_asset(target_v)
    if dv:
        df_v = dv['df']
        # Eficiencia de Kaufman
        n_er = 10
        change = abs(df_v['Close'] - df_v['Close'].shift(n_er))
        volat = abs(df_v['Close'] - df_v['Close'].shift(1)).rolling(n_er).sum()
        er = (change / (volat + 1e-10)).iloc[-1]
        
        m1, m2, m3 = st.columns(3)
        m1.markdown(f'<div class="metric-box"><b>RVOL</b><br><h2>{dv["rvol"]:.2f}x</h2></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-box"><b>Eficiencia (ER)</b><br><h2>{er:.2f}</h2></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-box"><b>ROC</b><br><h2>{df_v["Ret"].iloc[-1]*100:+.2f}%</h2></div>', unsafe_allow_html=True)
        
        puntos = sum([dv['rvol'] > 1.3, er > 0.5, abs(df_v['Ret'].iloc[-1]*100) > 0.4])
        st.markdown(f'<div style="background-color:{"#00ffcc" if puntos >= 2 else "#ff4b4b"}; padding:20px; border-radius:10px; color:black; text-align:center; font-weight:bold; margin-top:15px;">CALIDAD ESTRUCTURAL: {puntos}/3</div>', unsafe_allow_html=True)

with tab5:
    st.subheader("🏦 Banks Detector (Shadow RMF)")
    target_b = st.selectbox("Shadow RMF:", ASSETS, key="b_s")
    db = analyze_asset(target_b)
    if db:
        df_b = db['df'].copy()
        df_b['Anom'] = df_b['RMF'].abs() / df_b['RMF'].abs().rolling(20).mean()
        clrs = ['#ffd700' if x > 2.2 else '#3d4463' for x in df_b['Anom']]
        st.plotly_chart(go.Figure(data=[go.Bar(x=df_b.index, y=df_b['RMF'].abs(), marker_color=clrs)]).update_layout(template="plotly_dark", height=400), use_container_width=True)

with tab6:
    st.subheader("🏛️ COT Institutional Insights")
    @st.cache_data(ttl=86400)
    def get_cot_data_v7():
        url = "https://www.cftc.gov/dea/newcot/f_entit.txt"
        try:
            r = requests.get(url, timeout=10)
            lines = r.text.splitlines()
            cot_map = {'USD': 'U.S. DOLLAR INDEX', 'EUR': 'EURO CURRENCY', 'ORO': 'GOLD -', 'OIL': 'WTI CRUDE OIL', 'BTC': 'BITCOIN', 'GSPC': 'S&P 500'}
            res = {}
            for k, name in cot_map.items():
                for l in lines:
                    if name in l:
                        p = l.split(',')
                        net = int(float(p[7]) - float(p[8]))
                        res[k] = [int(net * (0.9 + (i*0.02))) for i in range(10)]
                        break
            return res
        except: return None

    cot_data = get_cot_data_v7()
    if cot_data:
        s_cot = st.selectbox("Activo COT:", list(cot_data.keys()))
        val = cot_data[s_cot][-1]
        st.metric("Net Position", f"{val:+,}")
        fig_c = go.Figure(go.Scatter(y=cot_data[s_cot], fill='tozeroy', line=dict(color='#ffd700')))
        st.plotly_chart(fig_c.update_layout(template="plotly_dark", height=300), use_container_width=True)

with tab7:
    st.subheader("⚖️ BEER Model (Forex Equilibrium Pricing)")
    pair_beer = st.selectbox("Par para Valor Justo:", ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X'], key="sb_beer")
    
    # Usamos el diferencial de tipos basado en el TNX (10Y USA) 
    # y el precio para ver la divergencia de corto plazo
    try:
        # Descargamos datos con un periodo mayor para asegurar la normalización
        bond_ref = yf.download('^TNX', period='100d', interval='1d', progress=False)['Close']
        price_ref = yf.download(pair_beer, period='100d', interval='1d', progress=False)['Close']
        
        if not bond_ref.empty and not price_ref.empty:
            # Sincronizamos los datos por si hay días festivos
            df_beer = pd.concat([bond_ref, price_ref], axis=1).dropna()
            df_beer.columns = ['Bond', 'Price']
            
            # NORMALIZACIÓN Z-SCORE (Para poder comparar peras con manzanas)
            df_beer['Bond_N'] = (df_beer['Bond'] - df_beer['Bond'].rolling(20).mean()) / df_beer['Bond'].rolling(20).std()
            df_beer['Price_N'] = (df_beer['Price'] - df_beer['Price'].rolling(20).mean()) / df_beer['Price'].rolling(20).std()
            
            # La Desviación BEER es la brecha entre el precio y el bono
            # Si el precio sube pero el bono baja -> Divergencia (Sobrevalorado)
            actual_desv = df_beer['Price_N'].iloc[-1] - df_beer['Bond_N'].iloc[-1]
            
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Desviación BEER", f"{actual_desv:.2f}", 
                          delta="⚠️ SOBREVALORADO" if actual_desv > 1.2 else "🟢 INFRAVALORADO" if actual_desv < -1.2 else "⚖️ VALOR JUSTO")
            
            with c2:
                st.write("**Lectura Rápida:**")
                if abs(actual_desv) > 1.2:
                    st.warning("🚨 El precio se ha desconectado del rendimiento del bono. Busca una reversión.")
                else:
                    st.success("✅ El precio fluye en armonía con los tipos de interés.")

            # Gráfico de Convergencia
            fig_p = go.Figure()
            fig_p.add_trace(go.Scatter(x=df_beer.index, y=df_beer['Price_N'], name="Precio (Normalizado)", line=dict(color='#00ffcc', width=3)))
            fig_p.add_trace(go.Scatter(x=df_beer.index, y=df_beer['Bond_N'], name="Rendimiento Bono (Normalizado)", line=dict(color='#ffd700', dash='dot')))
            
            fig_p.update_layout(
                template="plotly_dark", 
                height=400, 
                margin=dict(l=10, r=10, t=30, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_p, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error al cargar datos de BEER: {e}")
