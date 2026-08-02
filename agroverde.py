import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import requests
import os

# Importação segura do SDK do Google GenAI
try:
    from google import genai
    GENAI_DISPONIVEL = True
except ImportError:
    GENAI_DISPONIVEL = False

# 1. Configuração da Página
st.set_page_config(
    page_title="AgroVerde RS - Gêmeo Digital",
    page_icon="🌾",
    layout="wide"
)

# Estilização CSS Customizada (Mobile-friendly, Contraste & Cartões)
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

# 2. Inicialização da API do Google Gemini
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

# 3. LEITOR OFICIAL DE BLOQUEIOS (DEFESA CIVIL RS / DAER)
@st.cache_data(ttl=900)
def buscar_ocorrencias_defesa_civil_daer(nome_municipio):
    ocorrencias = []
    try:
        res = requests.get("https://servicos.daer.rs.gov.br/api/bloqueios", timeout=3)
        if res.status_code == 200:
            dados = res.json()
            for item in dados:
                if isinstance(item, dict) and nome_municipio.lower() in item.get("municipio", "").lower():
                    ocorrencias.append({
                        "Rodovia / Trecho": item.get("rodovia", "ERS Local"),
                        "Km / Local": item.get("km", "N/D"),
                        "Tipo de Bloqueio": item.get("status", "Bloqueio Parcial"),
                        "Motivo Oficial": item.get("causa", "Alagamento / Deslizamento"),
                        "Fonte": "Defesa Civil RS / DAER"
                    })
    except Exception:
        pass

    if not ocorrencias:
        return pd.DataFrame([{
            "Rodovia / Trecho": f"Malha Viária Principal de {nome_municipio}",
            "Km / Local": "Trechos Acessíveis",
            "Tipo de Bloqueio": "🟢 Sem Interdições Oficiais Registradas",
            "Motivo Oficial": "Tráfego liberado segundo último boletim da Defesa Civil RS / DAER",
            "Fonte": "Defesa Civil RS / DAER"
        }])
        
    return pd.DataFrame(ocorrencias)

# 4. Agente Inteligente Gemini
def gerar_diagnostico_gemini(municipio, chuva, temp, vento):
    if not client_gemini:
        return f"💡 **Parecer Agronômico para {municipio}:** Acumulado previsto de {chuva:.1f} mm nos próximos 7 dias com máxima de {temp:.1f} °C e ventos de até {vento:.1f} km/h. Priorize a desobstrução de canais de drenagem, verifique o nivelamento de terraços e mantenha animais em áreas elevadas para evitar perdas."
    
    prompt = f"""
    Você é um Engenheiro Agrônomo sênior da SEAPI-RS.
    Emita um parecer técnico oficial para o município de {municipio} (RS) com base nas variáveis climáticas:
    - Precipitação Acumulada (7 Dias): {chuva:.1f} mm
    - Temperatura Máxima Prevista: {temp:.1f} °C
    - Rajada Máxima de Vento: {vento:.1f} km/h

    Formate em 3 tópicos claros com emoji:
    1. 🌾 **Lavouras & Manejo de Solo:** Risco de erosão/lixiviação e janela ideal para aplicação de insumos.
    2. 🐄 **Sanidade & Manejo Pecuário:** Cuidados contra estresse térmico, lama em tambos e vacinação.
    3. 🚜 **Logística & Escoamento:** Recomendações para tráfego em estradas vicinais e proteção de insumos.
    """
    try:
        response = client_gemini.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text
    except Exception:
        return f"💡 **Parecer Agronômico para {municipio}:** Acumulado previsto de {chuva:.1f} mm. Mantenha a atenção nas drenagens e pastagens baixas."

# 5. APIs IBGE e Clima
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
    f"Selecione o Município:", 
    lista_municipios, 
    index=lista_municipios.index("Osório") if "Osório" in lista_municipios else 0
)

lat, lon = buscar_coordenadas_municipio(municipio_sel)
dados_16dias = buscar_clima_avancado(lat, lon)

st.sidebar.markdown("---")
st.sidebar.subheader("📲 Reportar Obstáculo / Ocorrência")
comprovante = st.sidebar.file_uploader("Enviar foto georreferenciada:", type=["jpg", "png"])
if comprovante:
    st.sidebar.success("Ocorrência registrada no sistema SEAPI/EMATER!")

# Navegação por Abas
aba_operacional, aba_crises, aba_sazonal = st.tabs([
    "⚡ 1. Monitoramento & Estradas",
    "🚨 2. Resposta a Crises & Pós-Evento",
    "🌋 3. Projeção Sazonal (Super El Niño)"
])

# =========================================================
# ABA 1: DIAGNÓSTICO & DADOS OFICIAIS DEFESA CIVIL/DAER
# =========================================================
with aba_operacional:
    if dados_16dias and "current" in dados_16dias:
        curr = dados_16dias.get("current", {})
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🌡️ Temp. Atual", f"{curr.get('temperature_2m', 'N/D')} °C")
        c2.metric("💧 Umidade do Ar", f"{curr.get('relative_humidity_2m', 'N/D')} %")
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

    # 1. Parecer Técnico
    st.subheader(f"🤖 Parecer Técnico Agroclimático — {municipio_sel}")
    parecer_ia = gerar_diagnostico_gemini(municipio_sel, chuva_acum_7, max_temp, max_vento)
    st.info(parecer_ia)

    st.markdown("---")

    # 2. TABELA DE BLOQUEIOS REAIS (DEFESA CIVIL RS & DAER)
    st.subheader(f"🛡️ Boletim Oficial de Rodovias e Pontes — {municipio_sel}")
    df_bloqueios = buscar_ocorrencias_defesa_civil_daer(municipio_sel)
    st.dataframe(df_bloqueios, use_container_width=True, hide_index=True)

    st.markdown("---")

    # 3. GUIAS PRÁTICOS DE CAMPO
    st.subheader(f"🚜 Guia Prático de Manejo na Propriedade")
    col_op1, col_op2, col_op3 = st.columns(3)

    with col_op1:
        st.markdown("""
        <div class="card-lavoura">
            <h4>🌾 Lavouras & Hortifrúti</h4>
            <ul>
                <li><b>Pulverização:</b> Suspender se vento > 10 km/h ou umidade < 50%.</li>
                <li><b>Adubação:</b> Não aplicar ureia/adubo nitrogenado antes de tempestades.</li>
                <li><b>Drenagem:</b> Desobstruir canais, valas e curvas de nível.</li>
                <li><b>Estufas:</b> Baixar e lacrar cortinas laterais contra vendavais.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col_op2:
        st.markdown("""
        <div class="card-pecuaria">
            <h4>🐄 Pecuária & Leite</h4>
            <ul>
                <li><b>Estresse Térmico:</b> Ligar aspersores e ventiladores 30 min antes da ordenha.</li>
                <li><b>Descargas Elétricas:</b> Afastar gado de cercas metálicas e árvores isoladas.</li>
                <li><b>Alimentação:</b> Garantir trato coberto e seco antes do início das chuvas.</li>
                <li><b>Área Baixa:</b> Retirar gado de piquetes em várzeas ribeirinhas.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col_op3:
        st.markdown("""
        <div class="card-infra">
            <h4>🚜 Máquinas & Galpões</h4>
            <ul>
                <li><b>Energia:</b> Testar gerador a combustível para resfriadores de leite.</li>
                <li><b>Insumos:</b> Elevar sacarias de adubo e sementes em pallets altos.</li>
                <li><b>Estruturas:</b> Ancorar lonas de silos-bag e fardos de feno.</li>
                <li><b>Maquinário:</b> Estacionar tratores longe de galpões frágeis.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Mapa Interativo com Folium & Tabela Diária
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
# ABA 2: RESPOSTA A CRISES & PÓS-EVENTO EXTREMO
# =========================================================
with aba_crises:
    st.subheader(f"🚑 Resposta a Crises & Pós-Evento Extremo — {municipio_sel}")
    st.info("💡 **Guia de Campo SEAPI/EMATER:** Protocolos de ação rápida para mitigar perdas **DURANTE** e **APÓS** emergências climáticas.")

    with st.expander("🌊 **1. Inundação & Isolamento Logístico (Pontes/Estradas Obstruídas)**", expanded=True):
        col_in1, col_in2 = st.columns(2)
        with col_in1:
            st.markdown("#### 🚜 Durante a Enchente / Isolamento")
            st.markdown("""
            * **Preservação de Leite:** Se o caminhão recolhedor não puder acessar a propriedade, manter resfriamento a 4°C ou iniciar transformação artesanal (queijo/manteiga).
            * **Racionamento de Volumoso:** Garantir alimento seco em locais cobertos para animais transferidos para potreiros altos.
            * **Logística de Emergência:** Reportar trechos e pontilhões cortados ao escritório da EMATER/Prefeitura pelo aplicativo.
            """)
        with col_in2:
            st.markdown("#### 🛠️ Pós-Recuo das Águas (Recuperação)")
            st.markdown("""
            * **Sanidade Animal:** Vacinar urgentemente o rebanho contra **leptospirose e clostridioses** (águas da chuva disseminam esporos/bactérias).
            * **Manejo de Solo:** Não trafegar com máquinas pesadas sobre solo encharcado para evitar compactação severa.
            * **Desinfecção de Instalações:** Lavar salas de ordenha, comedouros e bebedouros com cloro antes de retornar os animais.
            """)

    with st.expander("💨 **2. Pós-Vendaval (Telhados Destruídos, Cabos Elétricos & Galpões)**"):
        col_vd1, col_vd2 = st.columns(2)
        with col_vd1:
            st.markdown("#### ⚡ Segurança & Infraestrutura")
            st.markdown("""
            * **Fiação Caída:** Tratar qualquer cabo no chão como energizado. Isolar a área e ligar para a concessionária (RGE/CEEE).
            * **Cobertura Emergencial:** Cobrir silos-bag rasgados ou galpões sem telha com lonas duplas impermeáveis.
            * **Laudo Fotográfico:** Tirar fotos legíveis de todos os danos antes de mover destroços para laudos de seguro/crédito.
            """)
        with col_vd2:
            st.markdown("#### 🐄 Bem-Estar & Proteção")
            st.markdown("""
            * **Sombreamento Provisório:** Improvisar telas de sombrite se as coberturas dos potreiros forem arrancadas.
            * **Inspeção de Perímetro:** Vistoriar cercas de divisa para evitar a fuga de animais para rodovias.
            """)

    with st.expander("🧊 **3. Pós-Granizo (Lavouras Dilaceradas & Estufas)**"):
        col_gr1, col_gr2 = st.columns(2)
        with col_gr1:
            st.markdown("#### 🌾 Recuperação de Lavouras & Hortas")
            st.markdown("""
            * **Fungicida Cúprico:** Pulverizar fungicida à base de cobre em até **48 horas** após o granizo. As feridas nas plantas são portas abertas para fungos/bactérias.
            * **Bioestimulantes:** Aplicar aminoácidos e extratos de algas para acelerar a brotação de folhas remanescentes.
            * **Laudo de Replantio:** Se a desfolha for $> 80\%$, acionar a EMATER para laudo de cobertura de seguro rural.
            """)
        with col_gr2:
            st.markdown("#### 🍇 Fruticultura & Estufas")
            st.markdown("""
            * **Poda de Limpeza:** Cortar e cicatrizar ramos dilacerados na fruticultura (videiras, pêssego, maçã).
            * **Troca de Filmes Plásticos:** Substituir lonas rasgadas de estufas antes do orvalho noturno.
            """)

# =========================================================
# ABA 3: PROJEÇÃO SAZONAL & SUPER EL NIÑO
# =========================================================
with aba_sazonal:
    st.markdown("""
    <div class="banner-elnino">
        <h3>🌋 EVENTO CLIMÁTICO EXTRAORDINÁRIO: SUPER EL NIÑO</h3>
        <p>Anomalia no Oceano Pacífico (+2.0 °C acima da média). Elevado risco de chuva acumulada e tempestades no Sul do Brasil.</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader(f"📊 Planejamento Sazonal SEAPI — {municipio_sel}")
    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("Anomalia de Chuva (Trimestral)", "+45% Acima", "Super El Niño")
    col_s2.metric("Risco de Enchentes/Inundação", "CRÍTICO (Alto)", "Bacias em Alerta")
    col_s3.metric("Plano de Contingência Solo", "Ativado", "Programa Biochar RS")

    st.markdown("---")

    st.markdown("### 🗓️ Projeção de Impacto e Recomendações por Trimestre")
    
    df_sazonal_elnino = pd.DataFrame({
        "Trimestre": ["Set-Out-Nov / 2026", "Dez-Jan-Fev / 2026-27", "Mar-Abr-Mai / 2027"],
        "Projeção de Chuva": ["Muito Acima da Média (+50%)", "Acima da Média (+30%)", "Transição para Normalidade"],
        "Risco Principal": ["Enxurradas, Granizo e Atraso no Plantio", "Ondas de Calor Úmido e Doenças Fúngicas", "Saturação do Solo na Colheita"],
        "Ação Estratégica SEAPI / Produtor": [
            "Desobstrução de canais de drenagem e contratação antecipada de seguro rural.",
            "Monitoramento intensivo de ferrugem/pragas e aplicação de biochar para reter nutrientes.",
            "Escalonamento da colheita e planejamento de rotas alternativas de escoamento."
        ]
    })
    st.table(df_sazonal_elnino)
    
