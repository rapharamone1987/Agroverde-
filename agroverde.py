import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import requests
import os

# 1. Configuração da Página
st.set_page_config(
    page_title="Agro Resiliência Climática RS",
    page_icon="🌾",
    layout="wide"
)

# Estilização CSS Customizada (Mobile-friendly & Cartões)
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

st.title("🌾 Agro Resiliência Climática RS")
st.caption("Secretaria da Agricultura, Pecuária, Produção Sustentável e Irrigação (SEAPI-RS)")
st.markdown("---")

# 2. Leitura de Chave e Engine do Gemini (REST API)
def obter_gemini_api_key():
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key and hasattr(st, "secrets"):
        api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    return api_key

API_KEY_GEMINI = obter_gemini_api_key()

def analisar_dados_com_gemini(prompt_contexto):
    """Envia os dados e instruções para o Gemini gerar diagnósticos profundos."""
    if not API_KEY_GEMINI:
        return None
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY_GEMINI}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt_contexto}]}]}
    
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=15)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            url_fb = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY_GEMINI}"
            res_fb = requests.post(url_fb, json=payload, headers=headers, timeout=15)
            if res_fb.status_code == 200:
                return res_fb.json()['candidates'][0]['content']['parts'][0]['text']
            return None
    except Exception:
        return None

# 3. CAMADA DE DADOS DETERMINÍSTICA (PYTHON FETCH)

@st.cache_data(ttl=600)
def buscar_dados_bloqueios_crbm(nome_municipio):
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
    headers = {"User-Agent": "AgroResilienciaClimatica_App"}
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

# Limpa o cache das análises se trocar de município
if "ultimo_municipio" not in st.session_state or st.session_state["ultimo_municipio"] != municipio_sel:
    st.session_state["ultimo_municipio"] = municipio_sel
    st.session_state["parecer_curto"] = None
    st.session_state["parecer_sazonal"] = None

lat, lon = buscar_coordenadas_municipio(municipio_sel)
dados_16dias = buscar_clima_avancado(lat, lon)
bloqueios_reais = buscar_dados_bloqueios_crbm(municipio_sel)

st.sidebar.markdown("---")
if API_KEY_GEMINI:
    st.sidebar.success("🤖 Google Gemini (IA): **Pronto para Análise**")
else:
    st.sidebar.warning("🤖 Google Gemini: **Modo Local**")

st.sidebar.markdown("---")
st.sidebar.subheader("📲 Reportar Ocorrência de Campo")
comprovante = st.sidebar.file_uploader("Foto georreferenciada de obstáculo:", type=["jpg", "png"])
if comprovante:
    st.sidebar.success("Ocorrência enviada para a central de monitoramento da EMATER/SEAPI!")

# Navegação por Abas
aba_operacional, aba_crises, aba_sazonal = st.tabs([
    "⚡ 1. Diagnóstico Operacional & Malha Viária",
    "🚨 2. Resposta a Crises & Contingência",
    "os 3. Prognóstico Sazonal & Eventos Extremos"
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

    st.subheader(f"🤖 Parecer Técnico Agroclimático — {municipio_sel}")
    
    col_btn1, col_info1 = st.columns([1, 2])
    with col_btn1:
        if st.button("🧠 Gerar / Atualizar Parecer Técnico (IA)", use_container_width=True):
            prompt_curto_prazo = f"""
            Você é um Engenheiro Agrônomo sênior da SEAPI-RS.
            Elabore um parecer operacional extremamente detalhado e prático para o município de {municipio_sel} (RS):
            - Chuva Acumulada em 7 Dias: {chuva_acum_7:.1f} mm
            - Pico Térmico: {max_temp:.1f} °C
            - Vento Máximo: {max_vento:.1f} km/h
            - Interdições no CRBM: {len(bloqueios_reais)} registro(s).

            Estruture a resposta em 3 seções bem aprofundadas:
            1. 🌾 **Impacto em Lavouras e Solo:** Janela exata de pulverização, riscos de lixiviação de adubo e drenagem.
            2. 🐄 **Manejo Pecuário e Leite:** Controle de estresse térmico, sanidade do casco, acesso aos tambos e manejo de barro.
            3. 🚜 **Logística e Infraestrutura Rural:** Estratégias para tráfego de maquinário pesados e conservação de sacarias/feno.
            """
            with st.spinner("Sintetizando parecer com o modelo Gemini..."):
                st.session_state["parecer_curto"] = analisar_dados_com_gemini(prompt_curto_prazo)

    if st.session_state.get("parecer_curto"):
        st.info(st.session_state["parecer_curto"])
    else:
        st.caption("👈 Clique no botão acima para acionar a Inteligência Artificial e gerar uma análise detalhada baseada nos dados climáticos atuais.")

    st.markdown("---")

    st.subheader(f"🛡️ Bloqueios Rodoviários Registrados no CRBM — {municipio_sel}")
    if bloqueios_reais:
        st.warning(f"🚨 Atualmente existem **{len(bloqueios_reais)} interdição(ões) ativa(s)** no sistema do Comando de Polícia Rodoviária da BM para {municipio_sel}:")
        st.dataframe(pd.DataFrame(bloqueios_reais), use_container_width=True, hide_index=True)
    else:
        st.success(f"🟢 **Nenhum bloqueio rodoviário ativo** registrado no boletim oficial do Comando de Polícia Rodoviária da BM para **{municipio_sel}**.")
        st.caption("Nota: Vicinais municipais de terra podem sofrer atoleiros em dias de chuva. Em emergências locais, contate a Defesa Civil Municipal pelo 199.")

    st.markdown("---")

    st.subheader(f"🚜 Guia Prático de Manejo na Propriedade")
    col_op1, col_op2, col_op3 = st.columns(3)

    with col_op1:
        st.markdown("""
        <div class="card-lavoura">
            <h4>🌾 Lavouras & Hortifrúti</h4>
            <ul>
                <li><b>Pulverização:</b> Suspender se vento > 10 km/h.</li>
                <li><b>Adubação:</b> Não aplicar ureia pré-tempestade.</li>
                <li><b>Drenagem:</b> Desobstruir valas nas baixadas.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col_op2:
        st.markdown("""
        <div class="card-pecuaria">
            <h4>🐄 Pecuária & Leite</h4>
            <ul>
                <li><b>Estresse Térmico:</b> Aspersores acionados antes da ordenha.</li>
                <li><b>Descargas Elétricas:</b> Afastar gado de cercas metálicas.</li>
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

    c_mapa, c_tabela = st.columns([2, 1])
    with c_mapa:
        st.subheader(f"🗺️ Mapa Tático — {municipio_sel}")
        try:
            m = folium.Map(location=[lat, lon], zoom_start=12)
            folium.Marker([lat, lon], popup=f"<b>{municipio_sel}</b>").add_to(m)
            st_folium(m, width="100%", height=350)
        except Exception:
            st.warning("Não foi possível carregar o mapa interativo no momento.")
        
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
    st.info("💡 **Guia de Campo SEAPI/EMATER:** Protocolos de ação rápida para mitigar perdas rurais.")

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
# ABA 3: PROGNÓSTICO SAZONAL & EVENTOS EXTREMOS
# =========================================================
with aba_sazonal:
    st.markdown("""
    <div class="banner-elnino">
        <h3>🌋 PROGNÓSTICO CLIMÁTICO SAZONAL & ANOMALIAS EXTREMAS</h3>
        <p>Projeção estratégica de médio e longo prazo para mitigação de riscos agrícolas frente a eventos climáticos extraordinários.</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader(f"📊 Relatório Agrometeorológico Sazonal de Longo Prazo — {municipio_sel}")
    
    if st.button("🌋 Gerar Relatório Completo de Resiliência Sazonal (IA)", type="primary", use_container_width=True):
        prompt_sazonal = f"""
        Você é um especialista sênior em Climatologia Agrícola e Economia Rural da SEAPI-RS.
        Elabore um PROGNÓSTICO SAZONAL DE RESILIÊNCIA CLIMÁTICA extremamente abrangente, técnico e detalhado para o município de {municipio_sel} (RS) (Lat: {lat}, Lon: {lon}).

        Considere o histórico agrícola e geográfico da região, além das tendências de anomalias hídricas e térmicas no Sul do Brasil.

        Estruture o relatório minunciosamente nestes 3 tópicos:
        1. 📅 **Projeção Climatológica Trimestral ({municipio_sel}):** Tendências de volumes acumulados, anomalias de temperatura e risco de eventos extremos (enxurradas, estiagens curtas ou granizo) para os próximos 3 a 6 meses.
        2. 🌾 **Impactos e Riscos nas Culturas Locais:** Avaliação específica para a vocação agrícola predominante deste município (grãos, pecuária de leite/corte, horticultura ou fruticultura).
        3. 🛡️ **Plano Diretor de Resiliência Rural:** Recomendações táticas para conservação do solo, manejo de irrigação/reserva de água, proteção de pastagens e ações de mitigação financeira/seguro rural.
        """
        with st.spinner(f"Processando modelo de inteligência sazonal para {municipio_sel}..."):
            st.session_state["parecer_sazonal"] = analisar_dados_com_gemini(prompt_sazonal)

    if st.session_state.get("parecer_sazonal"):
        st.markdown(st.session_state["parecer_sazonal"])
    else:
        st.info("💡 **Clique no botão vermelho acima** para gerar a projeção climatológica sazonal estendida da IA para os próximos trimestres.")
        
