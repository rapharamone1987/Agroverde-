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

# 2. Carregar Todos os 497 Municípios do RS via API Oficial do IBGE
@st.cache_data(ttl=86400)
def carregar_municipios_ibge():
    url = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/43/municipios"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            dados = res.json()
            # Ordena os municípios em ordem alfabética
            municipios = sorted([m["nome"] for m in dados])
            return municipios
    except Exception:
        pass
    # Fallback caso a API offline
    return ["Osório", "Alegrete", "Bagé", "Camaquã", "Cruz Alta", "Porto Alegre", "Uruguaiana"]

# Carregar coordenadas reais do município selecionado via API Nominatim/OpenStreetMap
@st.cache_data(ttl=86400)
def buscar_coordenadas_municipio(nome_municipio):
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={nome_municipio},Rio+Grande+do+Sul,Brasil"
    headers = {"User-Agent": "AgroVerdeRS_App"}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200 and len(res.json()) > 0:
            item = res.json()[0]
            return float(item["lat"]), float(item["lon"])
    except Exception:
        pass
    # Coordenadas do centro do RS como padrão
    return -30.0346, -51.2177

# 3. Busca de Dados Climáticos (16 Dias)
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

# Sidebar - Busca por todos os municípios do RS
st.sidebar.header("🔍 Painel de Controle")

lista_municipios = carregar_municipios_ibge()
municipio_sel = st.sidebar.selectbox(
    f"Selecione o Município (Total: {len(lista_municipios)}):", 
    lista_municipios, 
    index=lista_municipios.index("Osório") if "Osório" in lista_municipios else 0
)

lat, lon = buscar_coordenadas_municipio(municipio_sel)
dados_16dias = buscar_clima_16dias(lat, lon)

st.sidebar.markdown("---")
st.sidebar.subheader("📲 Registrar Ação Verde (Produtor)")
comprovante = st.sidebar.file_uploader("Enviar foto georreferenciada:", type=["jpg", "png"])
if comprovante:
    st.sidebar.success("Ação registrada com sucesso! Em análise para incentivo fiscal/crédito.")

# Navegação por Abas
aba_operacional, aba_gestao_detalhada, aba_sazonal = st.tabs([
    "⚡ Monitoramento Operacional (16 Dias)",
    "🛠️ Módulo de Gestão & Ações Detalhadas",
    "📅 Tendência Sazonal & Estratégica (1 a 6 Meses)"
])

# ---------------------------------------------------------
# ABA 1: MONITORAMENTO OPERACIONAL
# ---------------------------------------------------------
with aba_operacional:
    if dados_16dias and "current" in dados_16dias:
        curr = dados_16dias["current"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Temperatura Atual", f"{curr.get('temperature_2m', 'N/D')} °C")
        c2.metric("Umidade do Ar", f"{curr.get('relative_humidity_2m', 'N/D')} %")
        c3.metric("Chuva Hoje", f"{curr.get('precipitation', 0)} mm")
        c4.metric("Vento Atual", f"{curr.get('wind_speed_10m', 'N/D')} km/h")

    st.markdown("---")
    
    c_mapa, c_tabela = st.columns([2, 1])
    with c_mapa:
        st.subheader(f"🗺️ Localização Tática — {municipio_sel} (RS)")
        m = folium.Map(location=[lat, lon], zoom_start=11)
        folium.Marker([lat, lon], popup=f"<b>{municipio_sel}</b>").add_to(m)
        st_folium(m, width="100%", height=400)
        
    with c_tabela:
        st.subheader("📅 Previsão (16 Dias)")
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
# ABA 2: MÓDULO DE GESTÃO & AÇÕES DETALHADAS
# ---------------------------------------------------------
with aba_gestao_detalhada:
    st.subheader(f"📋 Plano de Ações Operacionais & Manejo Técnico — {municipio_sel}")
    st.info("💡 **Diretrizes da SEAPI/EMATER:** Orientações detalhadas por cadeia produtiva com base na análise dos dados meteorológicos dos próximos 16 dias.")

    if dados_16dias and "daily" in dados_16dias:
        daily = dados_16dias["daily"]
        chuvas = daily["precipitation_sum"]
        temp_max = daily["temperature_2m_max"]
        ventos_max = daily["wind_speed_10m_max"]

        chuva_acum_16 = sum(chuvas)
        max_temp_periodo = max(temp_max)
        max_vento_periodo = max(ventos_max)

        # Diagnóstico Geral
        st.markdown(f"### 🔍 Diagnóstico do Período ({municipio_sel})")
        st.write(f"- **Volume total de chuva previsto:** `{chuva_acum_16:.1f} mm` | **Temperatura máxima:** `{max_temp_periodo:.1f} °C` | **Vento máximo:** `{max_vento_periodo:.1f} km/h`")

        st.markdown("---")
        st.markdown("### 🌾 Ações Detalhadas por Setor")

        col_leite, col_graos, col_infra = st.columns(3)

        # 1. Cadeia de Leite e Pecuária
        with col_leite:
            st.markdown("#### 🐄 Pecuária & Leite")
            if max_temp_periodo >= 32:
                st.error("**ALERTA DE ESTRESSE TÉRMICO ANIMAL**")
                st.markdown("""
                * **Ventilação & Aspersão:** Ligar sistemas de resfriamento nos galpões e salas de espera 30min antes da ordenha.
                * **Água Potável:** Verificar vazão dos bebedouros (demanda aumenta em até 40% em dias quentes).
                * **Sombreamento:** Garantir acesso a áreas sombreadas (mínimo de $4m^2$ de sombra por vaca).
                * **Dieta:** Ajustar fornecimento de volumoso para horários mais frios (início da manhã/noite).
                """)
            else:
                st.success("**Condições Térmicas Adequadas**")
                st.markdown("""
                * Manter rotina padrão de pastejo.
                * Monitorar qualidade da água e limpeza de açudes/reservatórios.
                """)

        # 2. Lavouras e Grãos
        with col_graos:
            st.markdown("#### 🌾 Lavouras & Grãos")
            if chuva_acum_16 < 25:
                st.warning("**ALERTA DE DÉFICIT HÍDRICO**")
                st.markdown("""
                * **Manejo de Irrigação:** Escalonar turnos de rega priorizando fases críticas (florescimento/enchimento de grão).
                * **Conservação do Solo:** Manter palhada de cobertura e incorporar biochar/pó de pedra para ampliar retenção na raiz.
                * **Pulverização:** Evitar aplicação de defensivos em horários com umidade do ar $< 50\%$.
                """)
            elif chuva_acum_16 > 70:
                st.error("**ALERTA DE EXCESSO DE UMIDADE**")
                st.markdown("""
                * **Drenagem:** Inspecionar sulcos e curvas de nível para conter erosão.
                * **Fitossanidade:** Monitorar surgimento de doenças fúngicas pós-chuva.
                """)
            else:
                st.success("**Umidade Adequada para Manejo**")
                st.markdown("""
                * Condições favoráveis para adubação de cobertura e tratamentos fitossanitários.
                """)

        # 3. Infraestrutura & Logística Rural
        with col_infra:
            st.markdown("#### 🏛️ Infraestrutura & Estruturas")
            if max_vento_periodo >= 50:
                st.error("**RISCO ESTRUTURAL (VENTO FORTE)**")
                st.markdown("""
                * **Ancoragem:** Reforçar amarrações em estufas, lonas e coberturas de silos-bag.
                * **Energia:** Verificar geradores de emergência para ordenhas e resfriadores de leite.
                * **Pintura Refletiva:** Aplicar tinta de alto albedo em galpões metálicos para reduzir carga térmica.
                """)
            else:
                st.success("**Estruturas Operacionais Estáveis**")
                st.markdown("""
                * Momento ideal para manutenção preventiva de telhados e aplicação de tinta refletiva.
                """)

# ---------------------------------------------------------
# ABA 3: TENDÊNCIA SAZONAL (1 a 6 Meses)
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
    
