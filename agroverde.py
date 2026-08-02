import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import requests

# 1. Configuração Inicial da Página
st.set_page_config(
    page_title="AgroVerde RS - Gêmeo Digital",
    page_icon="🌾",
    layout="wide"
)

# Cabeçalho Principal
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

# 2. Função de Integração com API (Clima Atual + Previsão de 7 Dias)
@st.cache_data(ttl=3600)  # Mantém cache por 1 hora
def buscar_clima_e_previsao(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m&daily=precipitation_sum,temperature_2m_max&forecast_days=7&timezone=America%2FSao_Paulo"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception:
        return None
    return None

# 3. Barra Lateral (Filtros e Envio de Ações)
st.sidebar.header("🔍 Painel de Controle")
municipio_sel = st.sidebar.selectbox("Selecione o Município:", list(MUNICIPIOS_RS.keys()))
coords = MUNICIPIOS_RS[municipio_sel]

# Requisição dos dados climáticos para o município selecionado
dados_clima = buscar_clima_e_previsao(coords["lat"], coords["lon"])

st.sidebar.markdown("---")
st.sidebar.subheader("📲 Registrar Ação Verde (Produtor)")
comprovante = st.sidebar.file_uploader("Enviar foto georreferenciada:", type=["jpg", "png"])
if comprovante:
    st.sidebar.success("Ação registrada com sucesso! Em análise para incentivo fiscal/crédito.")

# 4. Métricas do Tempo Presente (KPIs em Tempo Real)
if dados_clima and "current" in dados_clima:
    atual = dados_clima["current"]
    temp = atual.get("temperature_2m", "N/D")
    umidade = atual.get("relative_humidity_2m", "N/D")
    chuva_hoje = atual.get("precipitation", 0)
    vento = atual.get("wind_speed_10m", "N/D")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Temperatura Atual", f"{temp} °C")
    col2.metric("Umidade do Ar", f"{umidade} %")
    col3.metric("Chuva Hoje", f"{chuva_hoje} mm")
    col4.metric("Velocidade do Vento", f"{vento} km/h")
else:
    st.warning("Aguardando resposta da API meteorológica...")

st.markdown("---")

# 5. Painel Principal: Mapa (Esquerda) e Alertas/Previsão (Direita)
col_mapa, col_dados = st.columns([2, 1])

with col_mapa:
    st.subheader(f"🗺️ Localização e Status — {municipio_sel}")
    
    # Renderização do Mapa com Folium
    m = folium.Map(location=[coords["lat"], coords["lon"]], zoom_start=10, tiles="OpenStreetMap")
    
    # Lógica do Marcador baseada na umidade atual
    if dados_clima and "current" in dados_clima:
        u = dados_clima["current"].get("relative_humidity_2m", 100)
        cor_ponto = "red" if u < 40 else ("orange" if u < 60 else "green")
        status_hidrico = "Crítico (Seco)" if u < 40 else ("Atenção" if u < 60 else "Adequado")
    else:
        cor_ponto = "blue"
        status_hidrico = "Monitorando"

    folium.Marker(
        [coords["lat"], coords["lon"]],
        popup=f"<b>{municipio_sel}</b><br>Status Hídrico: {status_hidrico}",
        icon=folium.Icon(color=cor_ponto, icon="cloud")
    ).add_to(m)

    st_folium(m, width="100%", height=450)

with col_dados:
    st.subheader("🚨 Alertas & Previsão da Semana")
    
    if dados_clima and "daily" in dados_clima:
        dias = dados_clima["daily"]["time"]
        chuvas = dados_clima["daily"]["precipitation_sum"]
        
        # Cálculo da chuva acumulada nos próximos 7 dias
        total_chuva_semana = sum(chuvas)
        
        # Alertas Inteligentes
        if total_chuva_semana > 50:
            st.error(f"🌧️ **ALERTA DE CHUVA INTENSA:** Previsto **{total_chuva_semana:.1f} mm** para os próximos 7 dias em {municipio_sel}. Atenção para baixadas.")
        elif total_chuva_semana > 15:
            st.info(f"🌦️ **Previsão de Chuva Moderada:** Acumulado de **{total_chuva_semana:.1f} mm** previsto para a semana.")
        else:
            st.warning(f"⚠️ **ALERTA DE ESTIAGEM:** Apenas **{total_chuva_semana:.1f} mm** de chuva previstos para os próximos 7 dias.")
            
        # Tabela com a Previsão Diária
        df_previsao = pd.DataFrame({
            "Data": dias,
            "Chuva (mm)": chuvas
        })
        st.markdown("### Previsão Diária")
        st.dataframe(df_previsao, use_container_width=True, hide_index=True)
    else:
        st.warning("Não foi possível carregar os dados previstos para a semana.")
        
