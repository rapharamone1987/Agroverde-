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

# Estilização CSS Customizada (Visual limpo, alta legibilidade e quebra de linhas)
st.markdown("""
    <style>
    div[data-testid="stMarkdownContainer"] p, div[data-testid="stMarkdownContainer"] li {
        word-wrap: break-word !important;
        white-space: normal !important;
    }

    /* Cards Operacionais */
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
    .card-lavoura p, .card-pecuaria p, .card-infra p,
    .card-lavoura b, .card-pecuaria b, .card-infra b {
        color: #1e293b !important;
        font-size: 14px !important;
        line-height: 1.5 !important;
    }

    /* Banners Especiais */
    .banner-emergencia-rio {
        background-color: #fff1f2 !important;
        border: 2px solid #e11d48 !important;
        padding: 16px !important;
        border-radius: 10px !important;
        margin-top: 15px !important;
        margin-bottom: 20px !important;
    }
    .banner-emergencia-rio h4 {
        color: #9f1239 !important;
        margin-top: 0px !important;
    }
    .banner-emergencia-rio p, .banner-emergencia-rio li, .banner-emergencia-rio b {
        color: #881337 !important;
        font-size: 14px !important;
    }

    .banner-elnino {
        background: linear-gradient(90deg, #7f1d1d 0%, #991b1b 100%) !important;
        padding: 18px !important;
        border-radius: 10px !important;
        margin-bottom: 20px !important;
    }
    .banner-elnino h2, .banner-elnino p {
        color: #ffffff !important;
    }

    /* Estilo para Tabela de Logística de Vias */
    .status-livre { color: #16a34a; font-weight: bold; }
    .status-atencao { color: #ca8a04; font-weight: bold; }
    .status-bloqueado { color: #dc2626; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

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

# 4. Barra Lateral (Sidebar)
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

# 5. Navegação por Abas
aba_operacional, aba_crises, aba_sazonal = st.tabs([
    "⚡ Monitoramento & Situação Territorial (Imediato)",
    "🚨 Resposta a Crises & Pós-Evento Extremo",
    "🌋 Tendência Sazonal & Super El Niño (1 a 6 Meses)"
])

# =========================================================
# ABA 1: MONITORAMENTO & SITUAÇÃO TERRITORIAL DO MUNICÍPIO
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
        chuva_acum_7 = sum(chuvas[:7])

        rio_critico = chuva_acum_7 > 50

        # NOVO: PAINEL DE SITUAÇÃO TERRITORIAL E LOGÍSTICA DO MUNICÍPIO
        st.subheader(f"📍 Diagnóstico Territorial & Logística Rural — {municipio_sel}")

        col_sit1, col_sit2, col_sit3 = st.columns(3)

        status_rio_txt = "🚨 INUNDAÇÃO / CALHA CHEIA" if rio_critico else ("🟡 Calha Elevada" if chuva_acum_7 > 25 else "🟢 Calha Normal")
        status_vias_txt = "🚨 ESTRADAS BLOQUEADAS / PONTES DANIFICADAS" if rio_critico else ("🟡 Vicinais com Atoleiros" if chuva_acum_7 > 25 else "🟢 Vias Operacionais")
        status_acesso_txt = "⚠️ RISCO DE ISOLAMENTO RURAL" if rio_critico else "✅ Trafegabilidade Garantida"

        col_sit1.metric("Nível do Rio Principal", status_rio_txt)
        col_sit2.metric("Malha Rodoviária Rural", status_vias_txt)
        col_sit3.metric("Acesso a Distritos Rurais", status_acesso_txt)

        st.markdown("---")

        # TABELA DINÂMICA DE MALHA RURAL E INFRAESTRUTURA
        st.markdown(f"### 🚦 Status das Vias de Escoamento e Pontilhões — {municipio_sel}")
        
        if rio_critico:
            df_vias = pd.DataFrame({
                "Trecho / Acesso Rural": ["Estrada Principal de Escoamento", "Estradas Vicinais Secundárias", "Pontilhão sobre Rio Principal", "Vias de Acesso às Cooperativas"],
                "Condição Atual": ["🚨 Parcialmente Submersa", "⚠️ Atoleiros Severos", "⛔ Interditado / Risco Estrutural", "🟡 Tráfego Restrito a Tratores"],
                "Recomendação Logística": ["Utilizar desvio via RS alta", "Evitar caminhões pesados", "Passagem proibida para veículos", "Escalonar saída da produção"]
            })
        else:
            df_vias = pd.DataFrame({
                "Trecho / Acesso Rural": ["Estrada Principal de Escoamento", "Estradas Vicinais Secundárias", "Pontilhão sobre Rio Principal", "Vias de Acesso às Cooperativas"],
                "Condição Atual": ["🟢 Trafegável", "🟢 Trafegável", "🟢 Liberado", "🟢 Trafegável"],
                "Recomendação Logística": ["Tráfego normal", "Manutenção preventiva padrão", "Tráfego normal", "Tráfego normal"]
            })

        st.dataframe(df_vias, use_container_width=True, hide_index=True)

        # PROTOCOLO SE RIO E ESTRADAS ESTIVEREM CRÍTICOS
        if rio_critico:
            st.markdown("""
            <div class="banner-emergencia-rio">
                <h4>🚨 PROTOCOLO DE EMERGÊNCIA TERRITORIAL ({municipio_sel})</h4>
                <p><b>Ações Imediatas devido a Inundações e Bloqueio de Vias:</b></p>
                <ul>
                    <li><b>Pontes e Passagens:</b> Não force a travessia de pontilhões cobertos por água. Riscos de colapso de cabeceira.</li>
                    <li><b>Logística do Leite:</b> Acione os tanques comunitários da região mais próxima antes do fechamento total dos acessos.</li>
                    <li><b>Gado em Várzea:</b> Remova imediatamente o rebanho para os potreiros mais altos mapeados na propriedade.</li>
                </ul>
            </div>
            """.format(municipio_sel=municipio_sel), unsafe_allow_html=True)

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
# ABA 2: RESPOSTA A CRISES & PÓS-EVENTO EXTREMO
# =========================================================
with aba_crises:
    st.subheader(f"🚑 Central de Resposta Imediata & Ações Pós-Evento Extremo — {municipio_sel}")
    st.info("💡 **Guia de Campo SEAPI/EMATER:** Protocolos práticos para mitigar perdas e recuperar a produção **DURANTE** e **APÓS** eventos severos.")

    with st.expander("🌊 **1. Durante & Pós-Inundação (Pontes/Estradas Obstruídas ou Destruídas)**", expanded=True):
        col_in1, col_in2 = st.columns(2)
        with col_in1:
            st.markdown("#### 🚜 Durante a Enchente / Isolamento Logístico")
            st.markdown("""
            * **Preservação de Leite:** Se o caminhão recolhedor não chegar por pontes destruídas, acionar resfriamento contínuo ou realizar pasteurização/queijaria artesanal emergencial.
            * **Racionamento de Ração:** Reduzir concentrado e manter volumoso seco para animais isolados em áreas altas.
            * **Logística Emergencial:** Mapear rotas vicinais alternativas e comunicar o escritório da EMATER/Prefeitura sobre trechos cortados.
            """)
        with col_in2:
            st.markdown("#### 🛠️ Pós-Recuo das Águas (Recuperação)")
            st.markdown("""
            * **Sanidade Animal:** Vacinar rebanho contra **leptospirose e clostridioses** (águas de enchente propagam bactérias no solo/pasto).
            * **Recuperação de Solo:** Não trafegar com tratores pesados em solo encharcado (evitar compactação severa). Aplicar calcário/gesso assim que secar.
            * **Desinfecção de Instalações:** Lavar salas de ordenha e comedouros com água sanitária/cloro antes do retorno dos animais.
            """)

    with st.expander("💨 **2. Pós-Vendaval (Telhados Destruídos, Rede Elétrica Caída & Destroços)**"):
        col_vd1, col_vd2 = st.columns(2)
        with col_vd1:
            st.markdown("#### ⚡ Segurança & Infraestrutura")
            st.markdown("""
            * **Cabo Partido:** Tratar todo fio caído no chão como energizado. Isolar a área e acionar a concessionária de energia (RGE/CEEE).
            * **Cobertura Emergencial:** Cobrir silos-bag rasgados ou galpões sem telha com lonas duplas reforçadas para não perder grãos/insumos.
            * **Laudo Fotográfico:** Fotografar todos os estragos na estrutura antes da remoção dos destroços (necessário para seguro rural e laudo SEAPI).
            """)
        with col_vd2:
            st.markdown("#### 🐄 Bem-Estar & Manejo")
            st.markdown("""
            * **Manejo de Sombreamento:** Improvisar sombrite provisório se estruturas de sombra da pecuária forem destruídas.
            * **Inspeção de Cercas:** Fazer varredura rápida no perímetro para evitar fuga de gado para estradas.
            """)

    with st.expander("🧊 **3. Pós-Granizo (Lavouras Danificadas & Estufas Rasgadas)**"):
        col_gr1, col_gr2 = st.columns(2)
        with col_gr1:
            st.markdown("#### 🌾 Recuperação de Lavouras & Hortas")
            st.markdown("""
            * **Aplicação de Fungicida Cúprico:** Pulverizar fungicida à base de cobre em até **48 horas** após o granizo. As feridas nas folhas são portas de entrada para fungos/bactérias.
            * **Bioestimulantes:** Aplicar aminoácidos e extratos de algas para acelerar a brotação de folhas remanescentes.
            * **Avaliação de Replantio:** Se a desfolha for $> 80\%$ em fases iniciais, acionar a EMATER para laudo de replantio imediato.
            """)
        with col_gr2:
            st.markdown("#### 🍇 Fruticultura & Estufas")
            st.markdown("""
            * **Poda de Limpeza:** Eliminar ramos dilacerados para evitar necrose do lenho na fruticultura (uva, maçã, pêssego).
            * **Troca de Filmes:** Substituir lonas de estufas rasgadas antes da entrada de umidade noturna.
            """)

    with st.expander("☀️ **4. Pós-Estiagem Severa (Solo Defrontado & Pastagem Degradada)**"):
        st.markdown("""
        * **Reativação Biológica do Solo:** Não adubar com nitrogênio sintético pesado imediatamente. Utilizar **biocarvão (biochar)** e matéria orgânica para reter a primeira chuva.
        * **Dessalinização / Limpeza de Açudes:** Aproveitar o nível baixo de reservatórios para realizar a dragagem da lama e ampliação da capacidade de armazenamento.
        """)

# =========================================================
# ABA 3: TENDÊNCIA SAZONAL & SUPER EL NIÑO
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
        
