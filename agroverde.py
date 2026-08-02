import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import requests

# 1. Configuração da Página
st.set_page_config(
    page_title="AgroVerde RS - Gêmeo Digital",
    page_icon="🌾",
    layout="wide"
)

st.title("🌾 AgroVerde RS — Gêmeo Digital & Monitoramento Real")
st.caption("Secretaria da Agricultura, Pecuária, Produção Sustentável e Irrigação (SEAPI-RS)")
st.markdown("---")

# Coordenadas Reais de Municípios do RS
MUNICIPIOS_RS = {
    "Osório": {"lat": -29.8863, "lon": -50.2697},
    "Alegrete": {"lat": -29.7831, "lon": -55.7919},
    "Bagé": {"lat": -31.3312, "lon": -54.1069},
    "Uruguaiana": {"lat": -29.7547, "lon": -57.0883},
    "Camaquã": {"lat": -30.8511, "lon": -51.8119},
    "Cruz Alta": {"lat": -28.6386, "lon": -53.6064},
}

# 2. Função para Puxar Clima em Tempo Real (API Open-Meteo)
@st.cache_data(ttl=3600)  # Guarda em cache por 1 hora para economizar chamadas
def buscar_clima_real(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m&daily=precipitation_sum,temperature_2m_max&timezone=America%2FSao_Paulo"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception:
        return None
    return None

# 3. Barra Lateral
st.sidebar.header("🔍 Painel de Controle")
municipio_sel = st.sidebar.selectbox("Selecione o Município:", list(MUNICIPIOS_RS.keys()))
coords = MUNICIPIOS_RS[municipio_sel]

# Chamada da API com dados reais
dados_clima = buscar_clima_real(coords["lat"], coords["lon"])

st.sidebar.markdown("---")
st.sidebar.subheader("📲 Registrar Ação Verde (Produtor)")
comprovante = st.sidebar.file_uploader("Enviar foto georreferenciada:", type=["jpg", "png"])
if comprovante:
    st.sidebar.success("Ação registrada com sucesso! Em análise para incentivo.")

# 4. Métricas Reais na Tela
if dados_clima and "current" in dados_clima:
    atual = dados_clima["current"]
    temp = atual.get("temperature_2m", "N/D")
    umidade = atual.get("relative_humidity_2m", "N/D")
    chuva = atual.get("precipitation", 0)
    vento = atual.get("wind_speed_10m", "N/D")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Temperatura Atual", f"{temp} °C")
    col2.metric("Umidade Relativa do Ar", f"{umidade} %")
    col3.metric("Precipitação Recente", f"{chuva} mm")
    col4.metric("Velocidade do Vento", f"{vento} km/h")
else:
    st.warning("Carregando ou falha na conexão com os dados de meteorologia em tempo real.")

st.markdown("---")

# 5. Mapa Interativo com Posição Real
col_mapa, col_dados = st.columns([2, 1])

with col_mapa:
    st.subheader(f"🗺️ Localização e Alertas — {municipio_sel}")
    
    m = folium.Map(location=[coords["lat"], coords["lon"]], zoom_start=10, tiles="OpenStreetMap")
    
    # Determina cor do marcador com base na umidade real
    if dados_clima and "current" in dados_clima:
        u = dados_clima["current"].get("relative_humidity_2m", 100)
        cor_ponto = "red" if u < 40 else ("orange" if u < 60 else "green")
        status_hídrico = "Crítico (Ar Seco)" if u < 40 else ("Atenção" if u < 60 else "Adequado")
    else:
        cor_ponto = "blue"
        status_hídrico = "Monitorando"

    folium.Marker(
        [coords["lat"], coords["lon"]],
        popup=f"<b>{municipio_sel}</b><br>Status Hídrico: {status_hídrico}",
        icon=folium.Icon(color=cor_ponto, icon="cloud")
    ).add_to(m)

    st_folium(m, width="100%", height=400)

with col_dados:
    st.subheader("📊 Diagnóstico em Tempo Real")
    if dados_clima and "current" in dados_clima:
        u = dados_clima["current"].get("relative_humidity_2m", 100)
        if u < 40:
            st.error(f"🚨 **Alerta de Estresse Hídrico:** A umidade do ar em {municipio_sel} está em {u}%. Risco para pastagens e lavouras.")
        elif u < 60:
            st.warning(f"⚠️ **Atenção:** Umidade moderada ({u}%). Acompanhar necessidade de irrigação.")
        else:
            st.success(f"✅ **Condições Estáveis:** Umidade em {u}%. Favorável para a produção.")
    
    st.info("💡 **Integração:** Conectado à API meteorológica do Open-Meteo sem custos de infraestrutura.")
    
