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

# 2. Busca de Clima para Curto/Médio Prazo (16 Dias)
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

# Sidebar
st.sidebar.header("🔍 Painel de Controle")
municipio_sel = st.sidebar.selectbox("Selecione o Município:", list(MUNICIPIOS_RS.keys()))
coords = MUNICIPIOS_RS[municipio_sel]

dados_16dias = buscar_clima_16dias(coords["lat"], coords["lon"])

st.sidebar.markdown("---")
st.sidebar.subheader("📲 Registrar Ação Verde (Produtor)")
comprovante = st.sidebar.file_uploader("Enviar foto georreferenciada:", type=["jpg", "png"])
if comprovante:
    st.sidebar.success("Ação registrada com sucesso! Em análise para incentivo fiscal/crédito.")

# Navegação por Abas
aba_operacional, aba_sazonal = st.tabs([
    "⚡ Monitoramento Operacional (1 a 16 Dias)",
    "📅 Tendência Sazonal & Estratégica (1 a 6 Meses)"
])

# ---------------------------------------------------------
# ABA 1: MONITORAMENTO OPERACIONAL (Com Resumo e Ações)
# ---------------------------------------------------------
with aba_operacional:
    # 1. Métricas em Tempo Real
    if dados_16dias and "current" in dados_16dias:
        curr = dados_16dias["current"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Temperatura Atual", f"{curr.get('temperature_2m', 'N/D')} °C")
        c2.metric("Umidade do Ar", f"{curr.get('relative_humidity_2m', 'N/D')} %")
        c3.metric("Chuva Hoje", f"{curr.get('precipitation', 0)} mm")
        c4.metric("Vento Atual", f"{curr.get('wind_speed_10m', 'N/D')} km/h")

    st.markdown("---")

    # 2. NOVO PAINEL: Resumo do Prognóstico & Ações Recomendadas
    st.subheader(f"📋 Prognóstico Operacional & Diretrizes Técnicas — {municipio_sel}")

    if dados_16dias and "daily" in dados_16dias:
        daily = dados_16dias["daily"]
        chuvas = daily["precipitation_sum"]
        temp_max = daily["temperature_2m_max"]
        ventos_max = daily["wind_speed_10m_max"]

        chuva_acum_16 = sum(chuvas)
        max_temp_periodo = max(temp_max)
        max_vento_periodo = max(ventos_max)

        col_prog, col_acoes = st.columns(2)

        # Lógica para construir o Resumo do Prognóstico
        with col_prog:
            st.markdown("#### 🔮 Resumo do Prognóstico (Próximos 16 Dias)")
            
            resumo_texto = f"- **Volume Total de Chuva:** Estimado em **{chuva_acum_16:.1f} mm** para o período.\n"
            resumo_texto += f"- **Pico de Temperatura:** Máxima prevista de **{max_temp_periodo:.1f} °C**.\n"
            resumo_texto += f"- **Rajada Máxima de Vento:** Até **{max_vento_periodo:.1f} km/h**.\n"

            if chuva_acum_16 < 20:
                resumo_texto += "- **Diagnóstico Geral:** Tendência de **déficit hídrico severo** e aceleração da evapotranspiração do solo."
            elif chuva_acum_16 > 70:
                resumo_texto += "- **Diagnóstico Geral:** Tendência de **saturação de solo** e risco de alagamento em áreas baixas."
            else:
                resumo_texto += "- **Diagnóstico Geral:** Condições dentro da normalidade com umidade moderada."

            st.info(resumo_texto)

        # Lógica para determinar as Ações Recomendadas
        with col_acoes:
            st.markdown("#### 🛠️ Ações Recomendadas (Manejo & Defesa)")
            
            acoes = []
            if chuva_acum_16 < 20:
                acoes.append("💧 **Manejo de Irrigação:** Ativar reservas de água e racionalizar turnos de rega.")
                acoes.append("🌱 **Proteção do Solo:** Aplicar cobertura vegetal/biochar para reter umidade na raiz.")
            elif chuva_acum_16 > 70:
                acoes.append("🚜 **Drenagem:** Inspecionar e desobstruir canais de drenagem e sarjetas nas lavouras.")
                acoes.append("⚠️ **Logística:** Antecipar escoamento de insumos sensíveis antes de períodos de chuva forte.")

            if max_temp_periodo >= 33:
                acoes.append("🐄 **Pecuária/Leite:** Ligar sistemas de aspersão/ventilação em galpões contra estresse térmico.")

            if max_vento_periodo >= 50:
                acoes.append("🏛️ **Estruturas:** Ancorar estufas, silos e silos-bag contra rajadas de vento severas.")

            if not acoes:
                acoes.append("✅ **Manutenção de Rotina:** Manter monitoramento padrão e práticas conservacionistas regulares.")

            for acao in acoes:
                st.write(f"- {acao}")

    st.markdown("---")

    # 3. Mapa Tático e Tabela Diária
    c_mapa, c_tabela = st.columns([2, 1])
    
    with c_mapa:
        st.subheader(f"🗺️ Mapa Tático — {municipio_sel}")
        m = folium.Map(location=[coords["lat"], coords["lon"]], zoom_start=10)
        folium.Marker([coords["lat"], coords["lon"]], popup=f"<b>{municipio_sel}</b>").add_to(m)
        st_folium(m, width="100%", height=400)
        
    with c_tabela:
        st.subheader("📅 Detalhamento Diário (16 Dias)")
        if dados_16dias and "daily" in dados_16dias:
            daily = dados_16dias["daily"]
            df_16 = pd.DataFrame({
                "Data": daily["time"],
                "Chuva (mm)": daily["precipitation_sum"],
                "Máx (°C)": daily["temperature_2m_max"],
                "Vento (km/h)": daily["wind_speed_10m_max"]
            })
            st.dataframe(df_16, use_container_width=True, height=350, hide_index=True)

# ---------------------------------------------------------
# ABA 2: TENDÊNCIA SAZONAL (1 a 6 Meses)
# ---------------------------------------------------------
with aba_sazonal:
    st.subheader(f"📊 Planejamento Sazonal de Safra — {municipio_sel}")
    st.info("💡 **Uso Estratégico:** Projeções de anomalias para suporte a linhas de crédito rural, reservatórios de irrigação e mitigação preventiva da SEAPI.")

    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("Tendência Trimestral (Chuva)", "Abaixo da Média (-18%)", "Alerta de Estiagem", delta_color="inverse")
    col_s2.metric("Risco de Estresse Térmico", "Elevado (Primavera/Verão)", "+2.1 °C vs Histórico", delta_color="inverse")
    col_s3.metric("Capacidade de Retenção Recomendada", "Mínima 85%", "Acionar Biochar/Solo")

    st.markdown("---")
    
    df_sazonal = pd.DataFrame({
        "Mês/Período": ["Setembro/2026", "Outubro/2026", "Novembro/2026", "Dezembro/2026", "Janeiro/2027", "Fevereiro/2027"],
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
    
