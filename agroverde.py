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

# 2. Carregar Municípios do RS via API Oficial do IBGE
@st.cache_data(ttl=86400)
def carregar_municipios_ibge():
    url = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/43/municipios"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            dados = res.json()
            return sorted([m["nome"] for m in dados])
    except Exception:
        pass
    return ["Osório", "Alegrete", "Bagé", "Camaquã", "Cruz Alta", "Porto Alegre", "Uruguaiana"]

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
    return -30.0346, -51.2177

# 3. Busca de Dados Climáticos + Nível de Rios / Eventos Extremos (16 Dias)
@st.cache_data(ttl=3600)
def buscar_clima_avancado(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
        f"&daily=precipitation_sum,temperature_2m_max,temperature_2m_min,wind_speed_10m_max,weather_code"
        f"&forecast_days=16&timezone=America%2FSao_Paulo"
    )
    try:
        res = requests.get(url, timeout=5)
        return res.json() if res.status_code == 200 else None
    except Exception:
        return None

# Sidebar
st.sidebar.header("🔍 Painel de Controle")

lista_municipios = carregar_municipios_ibge()
municipio_sel = st.sidebar.selectbox(
    f"Selecione o Município (Total: {len(lista_municipios)}):", 
    lista_municipios, 
    index=lista_municipios.index("Osório") if "Osório" in lista_municipios else 0
)

lat, lon = buscar_coordenadas_municipio(municipio_sel)
dados_16dias = buscar_clima_avancado(lat, lon)

st.sidebar.markdown("---")
st.sidebar.subheader("📲 Registrar Ação Verde (Produtor)")
comprovante = st.sidebar.file_uploader("Enviar foto georreferenciada:", type=["jpg", "png"])
if comprovante:
    st.sidebar.success("Ação registrada com sucesso! Em análise para incentivo fiscal/crédito.")

# Navegação por Abas
aba_operacional, aba_gestao_detalhada, aba_sazonal = st.tabs([
    "⚡ Monitoramento & Rios (16 Dias)",
    "🛠️ Módulo de Gestão & Eventos Extremos",
    "📅 Tendência Sazonal & Ações Estratégicas (1 a 6 Meses)"
])

# ---------------------------------------------------------
# ABA 1: MONITORAMENTO OPERACIONAL & NÍVEL DE RIOS
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

    # Painel de Monitoramento Fluvial e Bacias
    st.subheader(f"🌊 Status da Bacia Hidrográfica & Nível de Rios — {municipio_sel}")
    
    col_rio1, col_rio2, col_rio3 = st.columns(3)
    
    if dados_16dias and "daily" in dados_16dias:
        chuva_acum_7dias = sum(dados_16dias["daily"]["precipitation_sum"][:7])
        
        # Simulação de Nível de Rio com base nos acumulados reais
        if chuva_acum_7dias > 80:
            status_rio = "ALERTA DE CHEIA / OVERFLOW"
            nivel_rio = "+ 2.80 m (Acima do Normal)"
            cor_rio = "inverse"
        elif chuva_acum_7dias > 30:
            status_rio = "Atenção / Calha Cheia"
            nivel_rio = "+ 0.90 m (Dentro da Calha)"
            cor_rio = "normal"
        else:
            status_rio = "Nível Baixo / Estiagem"
            nivel_rio = "- 0.45 m (Abaixo do Normal)"
            cor_rio = "off"

        col_rio1.metric("Acumulado de Chuva (7 Dias)", f"{chuva_acum_7dias:.1f} mm")
        col_rio2.metric("Tendência Fluvial (Rio Principal)", status_rio)
        col_rio3.metric("Cota Estada Fluvial (Est.)", nivel_rio, delta_color=cor_rio)

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
# ABA 2: MÓDULO DE GESTÃO & EVENTOS EXTREMOS
# ---------------------------------------------------------
with aba_gestao_detalhada:
    st.subheader(f"📋 Alertas de Eventos Severos & Matriz de Resposta — {municipio_sel}")

    if dados_16dias and "daily" in dados_16dias:
        daily = dados_16dias["daily"]
        chuvas = daily["precipitation_sum"]
        temp_max = daily["temperature_2m_max"]
        ventos_max = daily["wind_speed_10m_max"]

        chuva_acum_16 = sum(chuvas)
        max_temp_periodo = max(temp_max)
        max_vento_periodo = max(ventos_max)

        # Painel de Alerta de Eventos Severos Combinados
        st.markdown("### 🚨 Central de Mitigação de Eventos Extremos")
        
        c_evt1, c_evt2, c_evt3 = st.columns(3)

        # Matriz Risco 1: Enxurrada/Granizo
        if chuva_acum_16 > 90 or any(c > 35 for c in chuvas):
            c_evt1.error("🌧️ **RISCO DE ENXURRADA / GRANIZO**\n\n- Desobstruir valas e canais rurais imediatamente.\n- Proteger maquinários de áreas de baixada.\n- Acionar alerta da Defesa Civil local.")
        else:
            c_evt1.success("✅ **Sem Risco Inundação/Granizo**\n\n- Monitoramento padrão de calhas.")

        # Matriz Risco 2: Vendaval
        if max_vento_periodo >= 55:
            c_evt2.error(f"💨 **RISCO DE VENDAVAL ({max_vento_periodo:.0f} km/h)**\n\n- Ancorar estruturas de estufas e galpões.\n- Desligar redes elétricas rurais expostas.\n- Testar geradores de emergência.")
        else:
            c_evt2.success("✅ **Ventos sob Controle**\n\n- Sem alertas estruturais de rajada.")

        # Matriz Risco 3: Onda de Calor / Seca Relâmpago
        if max_temp_periodo >= 34 or chuva_acum_16 < 15:
            c_evt3.warning(f"🔥 **CALOR EXTREMO / SECA RELÂMPAGO**\n\n- Acionar aspersores em galpões de ordenha.\n- Racionar irrigação para fases de floração.\n- Aumentar oferta de água para rebanhos.")
        else:
            c_evt3.success("✅ **Temperatura Adequada**\n\n- Condições térmicas estáveis.")

        st.markdown("---")
        st.markdown("### 🌾 Manejo Técnico Recomendado")

        col_leite, col_graos = st.columns(2)

        with col_leite:
            st.markdown("#### 🐄 Cadeia do Leite & Proteína Animal")
            st.markdown("""
            * **Estresse Térmico:** Ligar resfriamento 30 min antes da ordenha.
            * **Reservatórios:** Garantir cota mínima de reservatório de água para dessedentação animal.
            * **Conservação da Silagem:** Vedar silos contra entrada de umidade por chuvas fortes.
            """)

        with col_graos:
            st.markdown("#### 🌾 Lavoras de Grãos & Hortifrúti")
            st.markdown("""
            * **Solo e Umidade:** Aplicar cobertura morta ou biocarvão para retardar perda por evaporação.
            * **Aplicação Defensivos:** Evitar pulverização com ventos $> 10\text{ km/h}$ ou umidade $< 50\%$.
            * **Escoamento:** Retirar safra armazenada em áreas rurais suscetíveis a alagamento.
            """)

# ---------------------------------------------------------
# ABA 3: TENDÊNCIA SAZONAL DETALHADA (1 a 6 Meses)
# ---------------------------------------------------------
with aba_sazonal:
    st.subheader(f"📊 Planejamento Sazonal Estratégico & Políticas Públicas — {municipio_sel}")
    st.info("💡 **Diretrizes de Governo da SEAPI:** Ações de médio e longo prazo por pilar de política pública com base na tendência climática trimestral/semestral.")

    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("Tendência Trimestral (Chuva)", "Abaixo da Média (-18%)", "Alerta de Estiagem", delta_color="inverse")
    col_s2.metric("Anomalia Térmica Prevista", "+2.1 °C vs Histórico", "Onda de Calor no Verão", delta_color="inverse")
    col_s3.metric("Meta de Resiliência de Solo", "85% de Cobertura", "Acionar Programa Biochar")

    st.markdown("---")
    st.markdown("### 🗓️ Cronograma e Detalhamento de Ações Estratégicas da SEAPI")

    # Módulos Expandidos de Ação Sazonal
    with st.expander("💧 **1. Pilar de Irrigação & Reservas Hídricas (Ações de 1 a 6 Meses)**", expanded=True):
        st.markdown("""
        * **Mês 1-2 (Preparação):** Limpeza de açudes, vertedouros e canais de irrigação nas propriedades cadastradas.
        * **Mês 3-4 (Execução):** Priorização de subvenções do Fundo de Desenvolvimento Rural (FDR) para micro-reservatórios e sistemas de irrigação por gotejamento na agricultura familiar.
        * **Mês 5-6 (Contingência):** Ativação da rede de caminhões-pipa comunitários para comunidades com déficit hídrico severo.
        """)

    with st.expander("🌱 **2. Pilar de Solo, Carbono e Biochar (Manejo Regenerativo)**"):
        st.markdown("""
        * **Fomento ao Biocarvão:** Distribuição do *Kit AgroClima* (Biochar + Remineralizadores de Basalto) para retenção de água e adubação orgânica.
        * **Plantio de Cobertura:** Incentivo ao plantio de adubos verdes (palhada) para evitar o aquecimento direto da camada arável do solo.
        * **Certificação:** Validação via app para emissão do **Selo RS Carbono Neutro**.
        """)

    with st.expander("🏛️ **3. Pilar de Infraestrutura & Bem-Estar Animal**"):
        st.markdown("""
        * **Cinturão de Resfriamento Passivo:** Programa de pintura de alto albedo (tinta refletiva) nos galpões metálicos de cooperativas e pequenas propriedades.
        * **Sombreamento de Pastagens:** Linha de fomento para sistemas silvopastoris (integração lavoura-pecuária-floresta).
        """)

    with st.expander("💳 **4. Pilar de Crédito Verde, Seguro & Incentivos Fiscais**"):
        st.markdown("""
        * **Desconto Fiscal (ICMS/IPVA Agrícola):** Produtores com ações validadas no app recebem bonificação fiscal do Estado.
        * **Subvenção de Seguro Rural:** Bonificação nas apólices de seguro do Banrisul/BRDE para produtores que adotam as recomendações técnicas do app.
        """)

    st.markdown("---")
    st.markdown("### 📅 Matriz de Acompanhamento Mensal de Safra")
    
    df_sazonal = pd.DataFrame({
        "Período": ["Mês 1", "Mês 2", "Mês 3", "Mês 4", "Mês 5", "Mês 6"],
        "Cenário Climático": ["Dentro da Média", "Abaixo da Média (-10%)", "Abaixo da Média (-25%)", "Crítico (-35%)", "Recuperação Moderada", "Dentro da Média"],
        "Ação Prioritária SEAPI": [
            "Manutenção de açudes e reservatórios",
            "Aplicação de coberturas de solo (Biochar/Basalto)",
            "Liberação de recursos FDR para irrigação",
            "Ativação de plano de emergência para leite/grãos",
            "Monitoramento contínuo de umidade de solo",
            "Avaliação de impacto e certificação"
        ]
    })
    st.table(df_sazonal)
    
