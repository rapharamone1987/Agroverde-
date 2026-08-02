import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd

# 1. Configuração da Página do Streamlit
st.set_page_config(
    page_title="AgroVerde RS - Gêmeo Digital",
    page_icon="🌾",
    layout="wide"
)

# Cabeçalho Principal
st.title("🌾 AgroVerde RS — Painel Preditivo & Resiliência")
st.caption("Secretaria da Agricultura, Pecuária, Produção Sustentável e Irrigação (SEAPI-RS)")

st.markdown("---")

# 2. Barra Lateral: Filtros e Registro do Produtor
st.sidebar.header("🔍 Painel de Controle & Pesquisa")

municipio = st.sidebar.selectbox(
    "Selecione o Município Prioritário:",
    ["Osório", "Alegrete", "Bagé", "Uruguaiana", "Camaquã", "Cruz Alta"]
)

nivel_risco = st.sidebar.radio(
    "Filtro de Risco Hídrico:",
    ["Todos", "Crítico (Alerta Vermelho)", "Moderado", "Estável"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("📲 Registrar Ação Verde (Produtor)")
comprovante = st.sidebar.file_uploader("Enviar foto georreferenciada da ação:", type=["jpg", "png"])

if comprovante:
    st.sidebar.success("Ação registrada com sucesso! Benefício/Crédito em análise.")

# 3. Métricas Principais (KPIs do Governo)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Microbacias Monitoradas", "1,248", "+12 nesta semana")
col2.metric("Índice de Estresse Hídrico", "68%", "Alerta Moderado", delta_color="inverse")
col3.metric("Ações Verdes Validadas", "3,420 ha", "+450 ha")
col4.metric("CO₂eq Mitigado (Est.)", "12.500 t", "Meta: 80%")

st.markdown("---")

# 4. Mapeamento Interativo e Tabela de Alertas
col_mapa, col_dados = st.columns([2, 1])

with col_mapa:
    st.subheader(f"🗺️ Mapa Preditivo de Risco Hídrico — {municipio}")
    
    # Coordenadas base do RS
    m = folium.Map(location=[-30.0346, -51.2177], zoom_start=7, tiles="OpenStreetMap")

    # Pontos do Mapa
    pontos_risco = [
        {"nome": "Microbacia Alfa (Alegrete)", "loc": [-29.783, -55.791], "status": "Crítico", "cor": "red"},
        {"nome": "Cooperativa Sul (Bagé)", "loc": [-31.331, -54.106], "status": "Moderado", "cor": "orange"},
        {"nome": "Área de Preservação (Osório)", "loc": [-29.886, -50.270], "status": "Estável", "cor": "green"},
    ]

    for p in pontos_risco:
        folium.Marker(
            p["loc"],
            popup=f"<b>{p['nome']}</b><br>Status: {p['status']}",
            icon=folium.Icon(color=p["cor"], icon="info-sign")
        ).add_to(m)

    st_folium(m, width="100%", height=450)

with col_dados:
    st.subheader("📊 Alertas e Ações Prioritárias")
    st.warning("⚠️ **Região Oeste:** Previsão de alta evapotranspiração para os próximos 10 dias. Recomendada ativação de reservatórios.")
    st.info("💡 **Boas Práticas:** Produtores com biochar no solo mantiveram a umidade 30% acima da média regional.")
    
    st.markdown("### Resumo de Prioridades")
    df = pd.DataFrame({
        "Localidade": ["Microbacia 01", "Assentamento B", "Cooperativa C"],
        "Risco": ["Crítico", "Moderado", "Estável"],
        "Recomendação": ["Irrigação / Reservatório", "Plantio de Cobertura", "Monitorar"]
    })
    st.dataframe(df, use_container_width=True)
