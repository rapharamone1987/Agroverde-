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

st.title("🌾 AgroVerde RS — Gêmeo Digital & Inteligência Climática")
st.caption("Secretaria da Agricultura, Pecuária, Produção Sustentável e Irrigação (SEAPI-RS)")
st.markdown("---")

MUNICIPIOS_RS = {
    "Osório": {"lat": -29.8863, "lon": -50.2697},
    "Alegrete": {"lat": -29.7831, "lon": -55.7919},
    "Bagé": {"lat": -31.3312, "lon": -54.1069},
    "Uruguaiana": {"lat": -29.7547, "lon": -57.0883},
    "Camaquã": {"lat": -30.8511, "lon": -51.8119},
    "Cruz Alta": {"lat": -28.6386, "lon": -53.6064},
}

# 2. API de Clima Curto/Médio Prazo (16 Dias)
@st.cache_data(ttl=3600)
def buscar_clima_16dias(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
        f"&daily=precipitation_sum,temperature_2m_max,temperature_2m_min,wind_speed_10m_max"
        f"&forecast_days=16&timezone=America%2FSao_Paulo"
    )
    try:
        res = requests.get(url, timeout=5)
        return res.json() if res.status_code == 200 else None
    except Exception:
        return None

# 3. API de Projeção Sazonal / Anomalia de Médio-Longo Prazo (Climate API)
@st.cache_data(ttl=86400) # Cache de 24h para dados sazonais
def buscar_tendencia_sazonal(lat, lon):
    url = (
        f"https://climate-api.open-meteo.com/v1/climate?latitude={lat}&longitude={lon}"
        f"&start_date=2026-08-01&end_date=2027-01-31"
        f"&models=ECMWF_SEAS5&daily=precipitation_sum,temperature_2m_max"
    )
    try:
        res = requests.get(url, timeout=5)
        return res.json() if res.status_code == 200 else None
    except Exception:
        return None

# Sidebar
st.sidebar.header("🔍 Painel de Controle")
municipio_sel = st.sidebar.selectbox("Selecione o Município:", list(MUNICIPIOS_RS.keys()))
coords = MUNICIPIOS_RS[municipio_sel]

dados_16dias = buscar_clima_16dias(coords["lat"], coords["lon"])

# Navegação por Abas para Separar Operacional vs. Estratégico
aba_operacional, aba_sazonal = st.tabs([
    "⚡ Monitoramento Operacional (1 a 16 Dias)",
    "📅 Tendência Sazonal & Estratégica (1 a 6 Meses)"
])

# ---------------------------------------------------------
# ABA 1: OPERACIONAL (1 a 16 Dias)
# ---------------------------------------------------------
with aba_operacional:
    col1, col2, col3, col4 = st.columns(4)
    if dados_16dias and "current" in dados_16dias:
        curr = dados_16dias["current"]
        col1.metric("Temperatura Atual", f"{curr.get('temperature_2m', 'N/D')} °C")
        col2.metric("Umidade do Ar", f"{curr.get('relative_humidity_2m', 'N/D')} %")
        col3.metric("Chuva Hoje", f"{curr.get('precipitation', 0)} mm")
        col4.metric("Vento Atual", f"{curr.get('wind_speed_10m', 'N/D')} km/h")
    
    st.markdown("---")
    c_mapa, c_alertas = st.columns([2, 1])
    
    with c_mapa:
        st.subheader(f"🗺️ Localização — {municipio_sel}")
        m = folium.Map(location=[coords["lat"], coords["lon"]], zoom_start=10)
        folium.Marker([coords["lat"], coords["lon"]], popup=municipio_sel).add_to(m)
        st_folium(m, width="100%", height=400)
        
    with c_alertas:
        st.subheader("🚨 Alertas de Curto/Médio Prazo")
        if dados_16dias and "daily" in dados_16dias:
            daily = dados_16dias["daily"]
            df_16 = pd.DataFrame({
                "Data": daily["time"],
                "Chuva (mm)": daily["precipitation_sum"],
                "Máx (°C)": daily["temperature_2m_max"],
                "Vento Máx (km/h)": daily["wind_speed_10m_max"]
            })
            st.dataframe(df_16, use_container_width=True, height=300, hide_index=True)

# ---------------------------------------------------------
# ABA 2: TENDÊNCIA SAZONAL (1 a 6 Meses - Estratégico SEAPI)
# ---------------------------------------------------------
with aba_sazonal:
    st.subheader(f"📊 Planejamento Sazonal de Safra & Resiliência Hídrica — {municipio_sel}")
    st.info("💡 **Uso Estratégico:** Projeções de anomalias para suporte a linhas de crédito rural, reservatórios de irrigação e mitigação preventiva da SEAPI.")

    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("Tendência Trimestral (Chuva)", "Abaixo da Média (-18%)", "Alerta de Estiagem", delta_color="inverse")
    col_s2.metric("Risco de Estresse Térmico", "Elevado (Primavera/Verão)", "+2.1 °C vs Histórico", delta_color="inverse")
    col_s3.metric("Capacidade de Retenção Recomendada", "Mínima 85%", "Acionar Biochar/Solo")

    st.markdown("---")
    
    st.markdown("### 🗓️ Cenário de Anomalias Climáticas para os Próximos Meses")
    
    # Simulação Estruturada de Projeção Sazonal por Mês
    df_sazonal = pd.DataFrame({
        "Mês/Período": ["Agosto/2026", "Setembro/2026", "Outubro/2026", "Novembro/2026", "Dezembro/2026", "Janeiro/2027"],
        "Projeção de Chuva": ["Dentro da Média", "Ligeiramente Abaixo (-10%)", "Abaixo da Média (-25%)", "Crítico (-35%)", "Recuperação Moderada", "Dentro da Média"],
        "Anomalia Térmica": ["+0.5 °C", "+1.2 °C", "+1.8 °C", "+2.5 °C", "+2.0 °C", "+1.0 °C"],
        "Recomendação de Gestão SEAPI": [
            "Manutenção de açudes e reservatórios",
            "Início da aplicação de coberturas de solo (Biochar/Basalto)",
            "Priorizar subvenção de irrigação para pequenos produtores",
            "Ativação de plano de contingência para leite e grãos",
            "Monitoramento contínuo de umidade de solo",
            "Avaliação de impacto de safra"
        ]
    })
    
    st.table(df_sazonal)

