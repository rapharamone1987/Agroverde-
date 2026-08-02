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

# Estilização CSS Customizada (Correção de cores das fontes, quebras de linha e alto contraste)
st.markdown("""
    <style>
    /* Força quebra de linha em todas as tabelas e textos do Streamlit */
    div[data-testid="stMarkdownContainer"] p, div[data-testid="stMarkdownContainer"] li {
        word-wrap: break-word !important;
        white-space: normal !important;
        color: #0f172a !important; /* Cor de texto padrão bem escura */
    }

    /* Cards com fontes em tom escuro para leitura perfeita */
    .card-lavoura {
        background-color: #f0fdf4;
        border-left: 5px solid #16a34a;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 12px;
        color: #0f172a !important;
    }
    .card-pecuaria {
        background-color: #fefce8;
        border-left: 5px solid #ca8a04;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 12px;
        color: #0f172a !important;
    }
    .card-infra {
        background-color: #eff6ff;
        border-left: 5px solid #2563eb;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 12px;
        color: #0f172a !important;
    }

    /* Estilo para Títulos dentro dos Cards */
    .card-lavoura h4, .card-pecuaria h4, .card-infra h4 {
        color: #0f172a !important;
        margin-top: 0px;
        font-weight: 700;
    }

    /* Texto e listas dentro dos cards */
    .card-lavoura li, .card-pecuaria li, .card-infra li,
    .card-lavoura p, .card-pecuaria p, .card-infra p {
        color: #1e293b !important;
        font-size: 14px;
        line-height: 1.5;
    }

    /* Banner para Emergência de Rio Cheio */
    .banner-emergencia-rio {
        background-color: #fff1f2;
        border: 2px solid #e11d48;
        padding: 16px;
        border-radius: 10px;
        margin-top: 15px;
        margin-bottom: 20px;
        color: #881337 !important;
    }
    .banner-emergencia-rio h4 {
        color: #9f1239 !important;
        margin-top: 0px;
    }
    .banner-emergencia-rio li {
        color: #881337 !important;
    }

    /* Banner Super El Niño */
    .banner-elnino {
        background: linear-gradient(90deg, #7f1d1d 0%, #991b1b 100%);
        color: #ffffff !important;
        padding: 18px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .banner-elnino h2, .banner-elnino p {
        color: #ffffff !important;
    }
    </style>
""", unsafe_unsafe_html=True if hasattr(st, "unsafe_html") else True)

st.title("🌾 AgroVerde RS — Gêmeo Digital & Inteligência Climática")
st.caption("Secretaria da Agricultura, Pecuária, Produção Sustentável e Irrigação (SEAPI-RS)")
st.markdown("---")

# 2. Carregar Municípios do RS via API do IBGE
@st.cache_data(ttl=86400)
def carregar_municipios_ibge():
    url = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/43/municipios"
    try:
        res = requests.get(url, timeout=10)
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
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200 and len(res.json()) > 0:
            item = res.json()[0]
            return float(item["lat"]), float(item["lon"])
    except Exception:
        pass
    return -30.0346, -51.2177

# 3. Busca Climática Completa (16 Dias)
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
aba_operacional, aba_sazonal = st.tabs([
    "⚡ Monitoramento & Ações Práticas (Imediato)",
    "🌋 Tendência Sazonal & Super El Niño (1 a 6 Meses)"
])

# =========================================================
# ABA 1: MONITORAMENTO & AÇÕES PRÁTICAS (IMEDIATO)
# =========================================================
with aba_operacional:
    if dados_16dias and "current" in dados_16dias:
        curr = dados_16dias["current"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🌡️ Temp. Atual", f"{curr.get('temperature_2m', 'N/D')} °C")
        c2.metric("💧 Umidade Ar", f"{curr.get('relative_humidity_2m', 'N/D')} %")
        c3.metric("🌧️ Chuva Hoje", f"{curr.get('precipitation', 0)} mm")
        c4.metric("💨 Vento Atual", f"{curr.get('wind_speed_10m', 'N/D')} km/h")

    st.markdown("---")

    if dados_16dias and "daily" in dados_16dias:
        daily = dados_16dias["daily"]
        chuvas = daily["precipitation_sum"]
        temp_max = daily["temperature_2m_max"]
        ventos_max = daily["wind_speed_10m_max"]

        chuva_acum_7 = sum(chuvas[:7])
        chuva_acum_16 = sum(chuvas)
        max_temp_periodo = max(temp_max)
        max_vento_periodo = max(ventos_max)

        # Status Fluvial
        st.subheader(f"🌊 Monitoramento do Nível de Rios — {municipio_sel}")
        
        c_rio1, c_rio2, c_rio3 = st.columns(3)
        
        # Lógica de detecção do nível do rio
        rio_critico = chuva_acum_7 > 50
        status_rio = "🚨 CALHA CHEIA / RISCO DE INUNDAÇÃO" if rio_critico else ("🟡 Atenção / Calha Elevada" if chuva_acum_7 > 25 else "🟢 Nível Normal")
        cota_rio = "+ 2.80 m (Alto)" if rio_critico else ("+ 0.90 m (Moderado)" if chuva_acum_7 > 25 else "- 0.45 m (Normal)")
        
        c_rio1.metric("Acumulado 7 Dias", f"{chuva_acum_7:.1f} mm")
        c_rio2.metric("Status Fluvial", status_rio)
        c_rio3.metric("Cota Fluvial Est.", cota_rio)

        # 🚨 MÓDULO EMERGENCIAL: AÇÕES EM CASO DE RIO COM CALHA CHEIA
        if rio_critico:
            st.markdown("""
            <div class="banner-emergencia-rio">
                <h4>🚨 PROTOCOLO DE EMERGÊNCIA: RIO COM CALHA CHEIA / TRANSBORDAMENTO IMINENTE</h4>
                <p><b>Diretrizes de Ação Imediata para a Propriedade Rural (SEAPI / Defesa Civil):</b></p>
                <ul>
                    <li><b>Pecuária:</b> Retirar imediatamente todo o rebanho das áreas de várzea e piquetes ribeirinhos. Deslocar o gado para campos altos de refúgio.</li>
                    <li><b>Maquinários:</b> Retirar tratores, colheitadeiras e implementos das baixadas e de perto de pontes rurais. Estacionar em locais elevados e firmes.</li>
                    <li><b>Grãos e Insumos:</b> Elevar sacarias de sementes, rações e adubos em pelo menos 1 metro de altura ou transferir para silos elevados/centrais.</li>
                    <li><b>Bombas e Irrigação:</b> Desligar e retirar os motores de captação de água das margens do rio antes da chegada do pico da cheia.</li>
                    <li><b>Segurança Pessoal:</b> Não tentar atravessar pontes submersas ou vados com tratores/veículos. Emergência: Ligar 199 (Defesa Civil).</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # CHECKLIST OPERACIONAL DO CAMPO
        st.subheader(f"🚜 Guia Prático de Manejo na Propriedade")
        
        col_op1, col_op2, col_op3 = st.columns(3)

        with col_op1:
            st.markdown("""
            <div class="card-lavoura">
                <h4>🌾 Lavouras & Hortifrúti</h4>
                <p><b>Manejo Imediato:</b></p>
                <ul>
                    <li><b>Pulverização:</b> Suspender se vento > 10 km/h ou umidade < 50%.</li>
                    <li><b>Adubação:</b> Não aplicar ureia/adubo antes de tempestades.</li>
                    <li><b>Drenagem:</b> Desobstruir canais e valas de drenagem nas lavouras.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with col_op2:
            st.markdown("""
            <div class="card-pecuaria">
                <h4>🐄 Pecuária & Leite</h4>
                <p><b>Manejo Imediato:</b></p>
                <ul>
                    <li><b>Estresse Térmico:</b> Ligar aspersores 30 min antes da ordenha.</li>
                    <li><b>Descargas Elétricas:</b> Afastar o gado de cercas de arame nos temporais.</li>
                    <li><b>Alimentação:</b> Garantir trato coberto antes das chuvas.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with col_op3:
            st.markdown("""
            <div class="card-infra">
                <h4>🚜 Máquinas & Galpões</h4>
                <p><b>Manejo Imediato:</b></p>
                <ul>
                    <li><b>Energia:</b> Testar o gerador para os resfriadores de leite.</li>
                    <li><b>Insumos:</b> Manter sacarias e produtos químicos sobre pallets elevados.</li>
                    <li><b>Estruturas:</b> Ancorar lonas e fardos contra rajadas de vento.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Mapa e Tabela Diária
    c_mapa, c_tabela = st.columns([2, 1])
    with c_mapa:
        st.subheader(f"🗺️ Mapa Tático — {municipio_sel}")
        m = folium.Map(location=[lat, lon], zoom_start=11)
        folium.Marker([lat, lon], popup=f"<b>{municipio_sel}</b>").add_to(m)
        st_folium(m, width="100%", height=380)
        
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
            st.dataframe(df_16, use_container_width=True, height=330, hide_index=True)

# =========================================================
# ABA 2: TENDÊNCIA SAZONAL & SUPER EL NIÑO
# =========================================================
with aba_sazonal:
    st.markdown("""
    <div class="banner-elnino">
        <h2>🌋 ALERTA DE EVENTO CLIMÁTICO EXTRAORDINÁRIO: SUPER EL NIÑO</h2>
        <p>Anomalia no Oceano Pacífico (+2.0 °C acima da média). Risco elevado de precipitações extremas e bloqueios atmosféricos no Sul do Brasil nos próximos meses.</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader(f"📊 Planejamento Sazonal Estratégico SEAPI — {municipio_sel}")
    
    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("Anomalia de Chuva (Trimestral)", "Acima da Média (+45%)", "Impacto Super El Niño", delta_color="normal")
    col_s2.metric("Risco de Enchentes/Inundação", "CRÍTICO (Nível Alto)", "Bacias em Alerta", delta_color="inverse")
    col_s3.metric("Plano de Contingência Solo", "Ativado (Drenagem/Biochar)", "Fundo FDR Prioritário")

    st.markdown("---")

    st.markdown("### 🗓️ Projeção de Impacto do Super El Niño por Período")
    
    df_sazonal_elnino = pd.DataFrame({
        "Trimestre": ["Set-Out-Nov / 2026", "Dez-Jan-Fev / 2026-27", "Mar-Abr-Mai / 2027"],
        "Projeção de Chuva": ["Muito Acima da Média (+50%)", "Acima da Média (+30%)", "Transição para Normalidade"],
        "Risco Principal": ["Enxurradas, Granizo e Atraso no Plantio", "Ondas de Calor Úmido e Doenças Fúngicas", "Saturação de Solo na Colheita"],
        "Ação Estratégica SEAPI / Produtor": [
            "Limpeza de canais de drenagem, reforço de pontilhões e seguro rural antecipado.",
            "Monitoramento intensivo de pragas e aplicação de biochar para fixar nutrientes.",
            "Escalonamento de colheita e logística de escoamento por rotas alternativas."
        ]
    })
    st.table(df_sazonal_elnino)

    st.markdown("---")
    
    with st.expander("💧 **1. Gestão de Bacias & Prevenção de Inundações (Super El Niño)**", expanded=True):
        st.markdown("* Mapeamento de áreas ribeirinhas vulneráveis | Priorização de recursos para contenção de cheias.")

    with st.expander("🌱 **2. Proteção de Solo contra Erosão por Chuvas Intensas**"):
        st.markdown("* Aplicação de remineralizadores de basalto e biochar para evitar lavagem de nutrientes | Plantio em curvas de nível obrigatório.")

    with st.expander("💳 **3. Crédito Emergencial e Subvenção de Seguro Rural**"):
        st.markdown("* Liberação de linhas do Banrisul/BRDE com taxas subsidiadas para produtores atingidos por granizo ou excesso de chuvas.")
        
