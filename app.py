with tab5:
    st.subheader("🌊 Vol-Monitor Pro: Confluencia de Fuerza")
    target_v = st.selectbox("Activo Detalle Fuerza:", ASSETS, key="v_s")
    dv = analyze_asset(target_v)
    if dv:
        # Fila de métricas
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown('<div class="metric-box"><b>RVOL (Interés)</b><br><h2>{:.2f}x</h2></div>'.format(dv['rvol']), unsafe_allow_html=True)
        with m2:
            color_er = "#00ffcc" if dv['er'] > 0.5 else "#ff4b4b"
            st.markdown('<div class="metric-box"><b>Eficiencia (ER)</b><br><h2 style="color:{};">{:.2f}</h2></div>'.format(color_er, dv['er']), unsafe_allow_html=True)
        with m3:
            color_adx = "#ffd700" if dv['adx'] > 25 else "#8b949e"
            st.markdown('<div class="metric-box"><b>Tendencia (ADX)</b><br><h2 style="color:{};">{:.1f}</h2></div>'.format(color_adx, dv['adx']), unsafe_allow_html=True)
        with m4:
            st.markdown('<div class="metric-box"><b>Velocidad (ROC)</b><br><h2>{:+.2f}%</h2></div>'.format(dv['roc']), unsafe_allow_html=True)

        # --- LÓGICA DEL VEREDICTO DE FUERZA ---
        st.write("---")
        puntos = 0
        if dv['rvol'] > 1.5: puntos += 1
        if dv['er'] > 0.55: puntos += 1
        if dv['adx'] > 25: puntos += 1
        if abs(dv['roc']) > 0.5: puntos += 1

        if puntos >= 3:
            v_color = "#00ffcc"
            v_text = "🚀 ALTA CALIDAD: Movimiento Institucional Limpio y Fuerte"
            v_note = "El volumen y la eficiencia confirman que el Smart Money tiene el control."
        elif puntos == 2:
            v_color = "#ffd700"
            v_text = "⚠️ CALIDAD MEDIA: Fuerza en desarrollo"
            v_note = "Hay interés, pero el movimiento aún tiene algo de ruido. Vigilar roturas."
        else:
            v_color = "#ff4b4b"
            v_text = "🚫 RUIDO ESTRUCTURAL: Evitar operativa"
            v_note = "El mercado está lateral o el volumen no está generando un movimiento eficiente."

        st.markdown(f"""
        <div style="background-color:{v_color}; padding:20px; border-radius:10px; color:black; text-align:center;">
            <h2 style="margin:0;">{v_text}</h2>
            <p style="margin:5px 0 0 0; font-weight:bold;">{v_note}</p>
        </div>
        """, unsafe_allow_html=True)

        # Gráfico visual de eficiencia vs volumen
        st.write("### 📈 Visualización Eficiencia/RVOL")
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Scatter(x=dv['df'].index[-30:], y=dv['df']['ER'].tail(30), name="Eficiencia (ER)", line=dict(color="#00ffcc")))
        fig_vol.add_trace(go.Bar(x=dv['df'].index[-30:], y=dv['df']['RVOL'].tail(30)/5, name="RVOL (Escalado)", opacity=0.3, marker_color="#ffd700"))
        st.plotly_chart(fig_vol.update_layout(template="plotly_dark", height=300, margin=dict(l=0,r=0,t=20,b=0)), use_container_width=True)
