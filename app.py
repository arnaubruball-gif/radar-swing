with tab3:
    st.subheader("🎲 Simulación de Montecarlo & Datos Críticos")
    mc_col1, mc_col2 = st.columns([1, 3])
    
    # 1. Entrada de Ticker específica para esta pestaña
    with mc_col1:
        ticker_mc = st.text_input("Activo a proyectar:", "GBPUSD=X", key="mc_ticker_input")
        dias_sim = st.slider("Días de Proyección", 5, 30, 15)
        
    data_mc = analyze_asset(ticker_mc)
    
    if data_mc:
        # 2. Parámetros de la simulación
        last_price = float(data_mc['price'])
        drift = float(data_mc['drift'])
        vol = float(data_mc['vol'])
        num_sim = 100 
        
        # 3. Creación de trayectorias (Caminata aleatoria)
        simulaciones = np.zeros((dias_sim + 1, num_sim))
        simulaciones[0] = last_price
        for i in range(1, dias_sim + 1):
            # Aplicamos el drift y la volatilidad histórica
            simulaciones[i] = simulaciones[i-1] * (1 + np.random.normal(drift, vol, num_sim))
        
        # 4. Cálculo de bandas de dispersión
        p10 = np.percentile(simulaciones, 10, axis=1)
        p50 = np.percentile(simulaciones, 50, axis=1) # Mediana (Línea central)
        p90 = np.percentile(simulaciones, 90, axis=1)
        
        # 5. Renderizado de Métricas en el lateral
        with mc_col1:
            st.metric("Drift (Inercia)", f"{drift*100:.4f}%")
            st.metric("Z-Diff (Tensión)", round(data_mc['z'], 2))
            st.metric("Hurst (Memoria)", round(data_mc['hurst'], 2))
            st.caption("Nota: Un Hurst < 0.50 sugiere que el precio tenderá a regresar al inicio de la nube.")
            
        # 6. Gráfico de Dispersión
        with mc_col2:
            fig_mc = go.Figure()
            
            # Añadir la Nube de Probabilidad (Sombreado entre p10 y p90)
            fig_mc.add_trace(go.Scatter(
                x=list(range(dias_sim+1)) + list(range(dias_sim+1))[::-1],
                y=list(p90) + list(p10[::-1]),
                fill='toself',
                fillcolor='rgba(0, 255, 204, 0.1)', # Turquesa muy suave
                line=dict(color='rgba(255,255,255,0)'),
                hoverinfo="skip",
                name='Intervalo de Confianza (80%)'
            ))
            
            # Añadir la Línea Central (Drift esperado)
            fig_mc.add_trace(go.Scatter(
                x=list(range(dias_sim+1)), 
                y=p50,
                line=dict(color='#00ffcc', width=4),
                name='Trayectoria Media'
            ))
            
            fig_mc.update_layout(
                template="plotly_dark",
                hovermode="x unified",
                xaxis_title="Días en el futuro",
                yaxis_title="Precio proyectado",
                margin=dict(l=20, r=20, t=40, b=20),
                height=500
            )
            st.plotly_chart(fig_mc, use_container_width=True)
