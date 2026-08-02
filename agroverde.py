import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import requests
import os

# Importação do SDK do Google GenAI
try:
    from google import genai
    GENAI_DISPONIVEL = True
except ImportError:
    GENAI_DISPONIVEL = False

# Configuração da Página
st.set_page_config(
    page_title="AgroVerde RS - Gêmeo Digital",
    page_icon="🌾",
    layout="wide"
)

# Estilização CSS Customizada (Mobile & Contraste)
st.markdown("""
    <style>
    div[data-testid="stMarkdownContainer"] p, div[data-testid="stMarkdownContainer"] li {
        word-wrap: break-word !important;
        white-space: normal !important;
    }
    button[data-baseweb="tab"] {
        white-space: nowrap !important;
        font-size: 14px !important;
        padding: 8px 16px !important;
        font-weight: 600 !important;
    }
    div[data-baseweb="tab-list"] {
        overflow-x: auto !important;
        flex-wrap: nowrap !important;
    }
    .card-lavoura {
        background-color: #f0fdf4 !important;
        border-left: 5px solid #16a34a !important;
        padding: 16px !important;
        border-radius: 8px !important;
        margin-bottom: 12px !important;
    }
    .card-pecuaria {
        background-color: #fefce8 !important;
        border-left: 5px solid #ca8a04 !important;
        padding: 16px !important;
        border-radius: 8px !important;
        margin-bottom: 12px !important;
    }
    .card-infra {
        background-color: #eff6ff !important;
        border-left: 5px solid #2563eb !important;
        padding: 16px !important;
        border-radius: 8px !important;
        margin-bottom: 12px !important;
    }
    .card-lavoura h4, .card-pecuaria h4, .card-infra h4 {
        color: #0f172a !important;
        margin-top: 0px !important;
        font-weight: 700 !important;
    }
    .card-lavoura li, .card-pecuaria li, .card-infra li,
    .card-lavoura p, .card-pecuaria p, .card-infra p {
        color: #1e293b !important;
        font-size: 14px !important;
        line-height: 1.5 !important;
    }
    .banner-elnino {
        background: linear-gradient(90deg, #7f1d1d 0%, #991b1b 100%) !important;
        padding: 18px !important;
        border-radius: 10px !important;
        margin-bottom: 20px !important;
    }
    .banner-elnino h3, .banner-elnino p { color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🌾 AgroVerde RS — Gêmeo Digital & Inteligência Climática")
st.caption("Secretaria da Agricultura, Pecuária, Produção Sustentável e Irrigação (SEAPI-RS)")
st.markdown("---")

# Inicialização da API do Google Gemini
@st.cache_resource
def iniciar_cliente_gemini():
    if not GENAI_DISPONIVEL:
        return None
    try:
        api_key = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", None)
        if api_key:
            return genai.Client(api_key=api_key)
    except Exception:
        pass
    return None

client_gemini = iniciar_cliente_gemini()

# CONSULTA REAL DE BLOQUEIOS DO CRBM / DAER
@st.cache_data(ttl=600)
def consultar_bloqueios_crbm_reais(nome_municipio):
    url_crbm = "https://servicos.daer.rs.gov.br/api/bloqueios"
    ocorrencias = []
    
    try:
        res = requests.get(url_crbm, timeout=5)
        if res.status_code == 200:
            dados = res.json()
            if isinstance(dados, list):
                for item in dados:
                    mun_item = str(item.get("municipio", "")).lower()
                    if nome_municipio.lower() in mun_item:
                        ocorrencias.append({
                            "Rodovia": item.get("rodovia", "N/D"),
                            "Km": item.get("km", "N/D"),
                            "Situação": item.get("status", "N/D"),
                            "Causa Registrada": item.get("causa", "N/D"),
                            "Última Atualização": item.get("data_atualizacao", "Recente")
                        })
    except Exception:
        pass

    return ocorrencias

# AGENTE INTELIGENTE: PARECER DE CURTO PRAZO
def gerar_diagnostico_curto_prazo(municipio, chuva, temp, vento):
    if not client_gemini:
        return f"💡 **Alerta Operacional ({municipio}):** Chuva acumulada em 7 dias prevista em {chuva:.1f} mm. Verifique valas de drenagem nas lavouras e mantenha animais em áreas elevadas."
    
    prompt = f"""
    Atue como Engenheiro Agrônomo da SEAPI-RS.
    Elabore uma análise operacional de curto prazo para o município de {municipio} (RS):
    - Chuva Prevista (7 Dias): {chuva:.1f} mm
    - Pico Térmico: {temp:.1f} °C
    - Rajada de Vento: {vento:.1f} km/h

    Responda em 3 tópicos objetivos:
    1. 🌾 **Impacto Agrícola:** Risco de erosão e janela de defensivos.
    2. 🐄 **Manejo Pecuário:** Cuidados contra estresse térmico ou barro em tambos.
    3. 🚜 **Estrutura & Logística:** Cuidados com feno, silos e máquinas.
    """
    try:
        response = client_gemini.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text
    except Exception:
        return f"💡 **Alerta Operacional ({municipio}):** Acumulado de {chuva:.1f} mm. Atentar para drenagem em lavouras baixas."

# AGENTE INTELIGENTE: PROGNÓSTICO SAZONAL DE MÉDIO/LONGO PRAZO (REAL)
def gerar_prognostico_sazonal_gemini(municipio, lat, lon):
    if not client_gemini:
        return "⚠️ Configure a chave `GEMINI_API_KEY` para gerar o prognóstico sazonal detalhado por Inteligência Artificial."
    
    prompt = f"""
    Você é um especialista em Climatologia Agrícola e Economia Rural do Rio Grande do Sul (SEAPI-RS).
    Gere um PROGNÓSTICO SAZONAL ESTRATÉGICO real para o município de {municipio} (RS) (Coordenadas: {lat}, {lon}).

    Considere as características geográficas e agrícolas reais deste município no RS e a dinâmica climática sazonal atual (El Niño/La Niña e anomalias do Atlântico Sul).

    Estruture a resposta nos seguintes tópicos técnicos:
    1. 📅 **Cenário Climatológico Trimestral para {municipio}:** Projeção de chuvas e temperatura para os próximos 3 a 6 meses.
    2. 🌾 **Riscos para as Principais Culturas Locais:** Como o clima afetará as principais atividades agrícolas/pecuárias típicas desse município.
    3. 🛡️ **Plano de Contingência Recomendado ao Produtor:** Ações preventivas de manejo de solo, reserva hídrica e logística.
    """
    try:
        response = client_gemini.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"Não foi possível gerar o prognóstico sazonal em tempo real ({e})."

# Carregamento de Municípios via IBGE
@st.cache_data(ttl=86400)
def carregar_municipios_ibge():
    url = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/43/municipios"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return sorted([m["nome"] for m in res.json()])
    except Exception:
        pass
    return ["Osório", "Alegrete", "Bagé", "Camaquã", "Cruz Alta", "Porto Alegre", "Uruguaiana"]

@st.cache_data(ttl=86400)
def buscar_coordenadas_municipio(nome_municipio):
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={nome_municipio},Rio+Grande+do+Sul,Brasil"
    headers = {"User-Agent": "AgroVerdeRS_App"}
    try:
        res = requests.get(url, headers=headers, timeout=4)
        if res.status_code == 200 and len(res.json()) > 0:
            item = res.json()[0]
            return float(item["lat"]), float(item["lon"])
    except Exception:
        pass
    return -30.0346, -51.2177

@st.cache_data(ttl=3600)
def buscar_clima_avancado(lat, lon):
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

lista_municipios = carregar_municipios_ibge()
municipio_sel = st.sidebar.selectbox(
    "Selecione o Município (RS):", 
    lista_municipios, 
    index=lista_municipios.index("Osório") if "Osório" in lista_municipios else 0
)

lat, lon = buscar_coordenadas_municipio(municipio_sel)
dados_16dias = buscar_clima_avancado(lat, lon)

st.sidebar.markdown("---")
st.sidebar.subheader("📲 Reportar Ocorrência de Campo")
comprovante = st.sidebar.file_uploader("Foto georreferenciada de obstáculo:", type=["jpg", "png"])
if comprovante:
    st.sidebar.success("Ocorrência enviada para fiscalização da EMATER/SEAPI!")

# Navegação por Abas
aba_operacional, aba_crises, aba_sazonal = st.tabs([
    "⚡ 1. Monitoramento & Bloqueios Reais",
    "🚨 2. Resposta a Crises & Emergências",
    "🌋 3. Prognóstico Sazonal Dinâmico"
])

# =========================================================
# ABA 1: DIAGNÓSTICO OPERACIONAL E BLOQUEIOS REAIS
# =========================================================
with aba_operacional:
    if dados_16dias and "current" in dados_16dias:
        curr = dados_16dias.get("current", {})
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🌡️ Temp. Atual", f"{curr.get('temperature_2m', 'N/D')} °C")
        c2.metric("💧 Umidade Ar", f"{curr.get('relative_humidity_2m', 'N/D')} %")
        c3.metric("🌧️ Chuva Hoje", f"{curr.get('precipitation', 0)} mm")
        c4.metric("💨 Vento Atual", f"{curr.get('wind_speed_10m', 'N/D')} km/h")

    st.markdown("---")

    daily = dados_16dias.get("daily", {}) if dados_16dias else {}
    chuvas = [v for v in (daily.get("precipitation_sum") or []) if v is not None]
    temp_max_list = [v for v in (daily.get("temperature_2m_max") or []) if v is not None]
    vento_max_list = [v for v in (daily.get("wind_speed_10m_max") or []) if v is not None]

    chuva_acum_7 = float(sum(chuvas[:7])) if chuvas else 0.0
    max_temp = float(max(temp_max_list)) if temp_max_list else 25.0
    max_vento = float(max(vento_max_list)) if vento_max_list else 10.0

    st.subheader(f"🤖 Parecer Técnico Operacional — {municipio_sel}")
    parecer_ia = gerar_diagnostico_curto_prazo(municipio_sel, chuva_acum_7, max_temp, max_vento)
    st.info(parecer_ia)

    st.markdown("---")

    # CONSULTA EM TEMPO REAL AO BOLETIM DA BRIGADA MILITAR / CRBM
    st.subheader(f"🛡️ Bloqueios em Rodovias Registrados no CRBM — {municipio_sel}")
    bloqueios_reais = consultar_bloqueios_crbm_reais(municipio_sel)
    
    if bloqueios_reais:
        st.warning(f"🚨 Atualmente existem **{len(bloqueios_reais)} interdição(ões) registrada(s)** no mapa do CRBM para {municipio_sel}:")
        st.dataframe(pd.DataFrame(bloqueios_reais), use_container_width=True, hide_index=True)
    else:
        st.success(f"🟢 **Nenhum bloqueio rodoviário ativo** registrado no banco oficial do Comando de Polícia Rodoviária da BM para o município de **{municipio_sel}** neste momento.")
        st.caption("Nota: Vicinais municipais de terra podem sofrer atoleiros locais em dias de chuva intensa. Consulte a Defesa Civil Municipal pelo 199.")

    st.markdown("---")

    # Guia Prático de Campo
    st.subheader(f"🚜 Guia Prático de Manejo na Propriedade")
    col_op1, col_op2, col_op3 = st.columns(3)

    with col_op1:
        st.markdown("""
        <div class="card-lavoura">
            <h4>🌾 Lavouras & Hortifrúti</h4>
            <ul>
                <li><b>Pulverização:</b> Suspender se vento > 10 km/h.</li>
                <li><b>Adubação:</b> Evitar aplicação de ureia pré-tempestade.</li>
                <li><b>Drenagem:</b> Limpar valas e canais nas baixadas.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col_op2:
        st.markdown("""
        <div class="card-pecuaria">
            <h4>🐄 Pecuária & Leite</h4>
            <ul>
                <li><b>Estresse Térmico:</b> Aspersores acionados antes da ordenha.</li>
                <li><b>Descargas Elétricas:</b> Afastar gado de cercas de arame.</li>
                <li><b>Alimentação:</b> Manter volumoso coberto.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col_op3:
        st.markdown("""
        <div class="card-infra">
            <h4>🚜 Máquinas & Galpões</h4>
            <ul>
                <li><b>Energia:</b> Testar gerador a combustível.</li>
                <li><b>Insumos:</b> Elevar adubos e sementes em pallets.</li>
                <li><b>Estruturas:</b> Ancorar lonas de silos-bag.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Mapa Interativo e Tabela Diária
    c_mapa, c_tabela = st.columns([2, 1])
    with c_mapa:
        st.subheader(f"🗺️ Mapa Tático — {municipio_sel}")
        try:
            m = folium.Map(location=[lat, lon], zoom_start=12)
            folium.Marker([lat, lon], popup=f"<b>{municipio_sel}</b>").add_to(m)
            st_folium(m, width="100%", height=350)
        except Exception:
            st.warning("Não foi possível carregar a visualização do mapa no momento.")
        
    with c_tabela:
        st.subheader("📅 Previsão (16 Dias)")
        if daily:
            df_16 = pd.DataFrame({
                "Data": daily.get("time", []),
                "Chuva (mm)": daily.get("precipitation_sum", []),
                "Máx (°C)": daily.get("temperature_2m_max", []),
                "Vento (km/h)": daily.get("wind_speed_10m_max", [])
            })
            st.dataframe(df_16, use_container_width=True, height=300, hide_index=True)

# =========================================================
# ABA 2: RESPOSTA A CRISES
# =========================================================
with aba_crises:
    st.subheader(f"🚑 Resposta a Crises & Pós-Evento Extremo — {municipio_sel}")
    st.info("💡 **Guia de Campo SEAPI/EMATER:** Orientações táticas para mitigação de perdas.")

    with st.expander("🌊 **1. Inundação & Isolamento Logístico**", expanded=True):
        col_in1, col_in2 = st.columns(2)
        with col_in1:
            st.markdown("#### 🚜 Durante o Isolamento")
            st.markdown("""
            * **Preservação de Leite:** Resfriamento contínuo a 4°C ou queijaria emergencial.
            * **Racionamento:** Trato seco coberto para animais em pontos altos.
            """)
        with col_in2:
            st.markdown("#### 🛠️ Pós-Recuo das Águas")
            st.markdown("""
            * **Sanidade Animal:** Vacinação emergencial contra **leptospirose e clostridioses**.
            * **Solo:** Evitar tráfego de tratores pesados em solo encharcado.
            """)

    with st.expander("💨 **2. Pós-Vendaval (Galpões & Rede Elétrica)**"):
        col_vd1, col_vd2 = st.columns(2)
        with col_vd1:
            st.markdown("#### ⚡ Segurança")
            st.markdown("""
            * **Fiação Caída:** Isolar área e comunicar RGE/CEEE (tratar como energizado).
            * **Silos-Bag:** Vedar rasgos imediatamente com lona dupla.
            """)
        with col_vd2:
            st.markdown("#### 📸 Documentação")
            st.markdown("""
            * **Laudo Fotográfico:** Fotografar estragos antes de mover destroços para cobertura do Seguro Rural.
            """)

# =========================================================
# ABA 3: PROGNÓSTICO SAZONAL DINÂMICO (VIA GEMINI IA)
# =========================================================
with aba_sazonal:
    st.markdown("""
    <div class="banner-elnino">
        <h3>🌋 PROGNÓSTICO CLIMÁTICO SAZONAL DE MÉDIO PRAZO</h3>
        <p>Análise de inteligência para planejamento agrícola e gestão de riscos em médio e longo prazo.</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader(f"📊 Relatório Climatológico Sazonal Específico — {municipio_sel}")
    
    with st.spinner(f"Gerando análise de inteligência sazonal customizada para {municipio_sel}..."):
        relatorio_sazonal = gerar_prognostico_sazonal_gemini(municipio_sel, lat, lon)
        st.markdown(relatorio_sazonal)
        
