import streamlit as st  # <--- ESTA LÍNEA DEBE IR PRIMERO
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Halcón 4.0 Pro Terminal", layout="wide", page_icon="🦅")


@st.cache_data(ttl=600)
def fetch_and_calculate(tickers):
    results = []
    for ticker in tickers:
        try:
            # Descargamos un poco más de datos para asegurar el cálculo
            df_hist = yf.download(ticker, period="65d", interval="1d", progress=False)
            
            # Limpieza: Eliminamos Multi-index y valores nulos
            if isinstance(df_hist.columns, pd.MultiIndex):
                df_hist.columns = df_hist.columns.get_level_values(0)
            
            df_hist = df_hist.dropna()

            if len(df_hist) > 41:
                # Convertimos a array plano de numpy y aseguramos que sea float
                prices = df_hist['Close'].values.flatten().astype(float)
                actual_price = prices[-1]
                
                # --- Z-DIFF Y R2 (Últimos 40 días) ---
                window = prices[-40:]
                ma40 = np.mean(window)
                std40 = np.std(window)
                z_diff = (actual_price - ma40) / std40 if std40 != 0 else 0
                
                x = np.arange(40)
                coeffs = np.polyfit(x, window, 1)
                p = np.poly1d(coeffs)
                y_hat = p(x)
                ss_res = np.sum((window - y_hat)**2)
                ss_tot = np.sum((window - np.mean(window))**2)
                r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
                
                # --- AMIHUD (Corregido para evitar desajuste de tamaño) ---
                # Usamos los últimos 21 días para obtener 20 retornos
                prices_ami = prices[-21:]
                # Diferencia absoluta / precio anterior (mismo tamaño: 20)
                returns = np.abs(np.diff(prices_ami)) / prices_ami[:-1]
                amihud = np.mean(returns) * 10**6
                
                if "NZD" in ticker: amihud *= 5
                
                # Volatilidad para Montecarlo
                volatilidad = np.std(returns)

                results.append({
                    'Ticker': ticker,
                    'Precio': round(actual_price, 4),
                    'Z-Diff': round(z_diff, 2),
                    'R2': round(r2, 3),
                    'Amihud': round(amihud, 2),
                    'Volatilidad': volatilidad,
                    'MA40': ma40
                })
        except Exception as e:
            st.warning(f"Error procesando {ticker}: {e}")
            continue
            
    return pd.DataFrame(results)
