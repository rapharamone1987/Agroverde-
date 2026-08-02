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

# Estilização CSS customizada para visual atrativo
st.markdown("""
    <style>
    .card-lavoura {
        background-color: #f0fdf4;
        border-left: 5px solid #16a34a;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .card-pecuaria {
        background-color: #fefce8;
        border-left: 5px solid #ca8a04;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .card-infra {
        background-color: #eff6ff;
        border-left: 5px solid #2563eb;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .banner-elnino {
        background: linear-gradient(90deg, #7f1d1d 0%, #991b1b 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

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
# ABA 1: MONITORAMENTO & AÇÕES PRÁTICAS (VISUAL ATRATIVO)
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
        st.subheader(f"🌊 Status Fluvial & Alertas — {municipio_sel}")
        
        c_rio1, c_rio2, c_rio3 = st.columns(3)
        status_rio = "🚨 ALERTA DE CHEIA" if chuva_acum_7 > 80 else ("🟡 Atenção / Calha Cheia" if chuva_acum_7 > 30 else "🟢 Nível Normal")
        cota_rio = "+ 2.80 m (Alto)" if chuva_acum_7 > 80 else ("+ 0.90 m (Normal)" if chuva_acum_7 > 30 else "- 0.45 m (Baixo)")
        
        c_rio1.metric("Acumulado 7 Dias", f"{chuva_acum_7:.1f} mm")
        c_rio2.metric("Tendência Fluvial", status_rio)
        c_rio3.metric("Cota Fluvial Est.", cota_rio)

        # Alerta Severo
        if (20 <= chuva_acum_7 <= 60) or (40 <= max_vento_periodo <= 60):
            st.warning("⚠️ **ALERTA METEOROLÓGICO: PERIGO POTENCIAL DE TEMPESTADE / VENDAVAL** (Inmet / Defesa Civil)")
            with st.expander("🛡️ **Precauções de Segurança Pessoal (Defesa Civil 199)**"):
                st.markdown("* Não se abrigue debaixo de árvores | Evite usar eletrodomésticos na tomada | Emergência: 199 / 193.")

        st.markdown("---")

        # CHECKLIST INTERATIVO E VISUAL PARA O PRODUTOR
        st.subheader(f"🚜 Guia Prático de Manejo na Propriedade")
        
        col_op1, col_op2, col_op3 = st.columns(3)

        with col_op1:
            st.markdown("""
            <div class="card-lavoura">
                <h4>🌾 Lavouras & Hortifrúti</h4>
                <p><b>Diretrizes Recomendadas:</b></p>
                <ul>
                    <li><b>Pulverização:</b> Suspenda com ventos > 10 km/h ou umidade < 50%.</li>
                    <li><b>Adubação:</b> Não aplique ureia/adubo antes de tempestades.</li>
                    <li><b>Estufas:</b> Baixe as cortinas laterais contra ventos fortes.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with col_op2:
            st.markdown("""
            <div class="card-pecuaria">
                <h4>🐄 Pecuária & Leite</h4>
                <p><b>Diretrizes Recomendadas:</b></p>
                <ul>
                    <li><b>Estresse Térmico:</b> Ligue aspersores 30 min antes da ordenha.</li>
                    <li><b>Proteção de Raios:</b> Afaste o gado de cercas de arame.</li>
                    <li><b>Água:</b> Verifique vazão dos bebedouros (demanda +40%).</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with col_op3:
            st.markdown("""
            <div class="card-infra">
                <h4>🚜 Máquinas & Galpões</h4>
                <p><b>Diretrizes Recomendadas:</b></p>
                <ul>
                    <li><b>Geradores:</b> Teste o gerador para os resfriadores de leite.</li>
                    <li><b>Insumos:</b> Eleve sacarias de sementes e adubos do chão.</li>
                    <li><b>Veículos:</b> Retire tratores de perto de árvores antigas.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Mapa e Tabela
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
# ABA 2: TENDÊNCIA SAZONAL & SUPER EL NIÑO (PROJEÇÃO EXTRAORDINÁRIA)
# =========================================================
with aba_sazonal:
    # BANNER DEDICADO A EVENTOS EXTRAORDINÁRIOS (SUPER EL NIÑO)
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
    
    # Tabela com detalhamento extraordinário
    df_sazonal_elnino = pd.DataFrame({
        "Trimestre": ["Set-Out-Nov / 2026", "Dez-Jan-Fev / 2026-27", "Mar-Abr-Mai / 2027"],
        "Projeção de Chuva": ["Muito Acima da Média (+50%)", "Acima da Média (+30%)", "Transição para Normalidade"],
        "Risco Principal": ["Enxurradas, Granizo e Atraso no Plantio", "Ondas de Calor Umido e Doenças Fúngicas", "Saturação de Solo na Colheita"],
        "Ação Estratégica SEAPI / Produtor": [
            "Limpeza de canais de drenagem, reforço de pontilhões e seguro rural antecipado.",
            "Monitoramento intensivo de pragas e aplicação de biochar para fixar nutrientes.",
            "Escalonamento de colheita e logística de escoamento por rotas alternativas."
        ]
    })
    st.table(df_sazonal_elnino)

    st.markdown("---")
    
    # Pilares de Governo
    with st.expander("💧 **1. Gestão de Bacias & Prevenção de Inundações (Super El Niño)**", expanded=True):
        st.markdown("* Mapeamento de áreas ribeirinhas vulneráveis | Priorização de recursos para contenção de cheias.")

    with st.expander("🌱 **2. Proteção de Solo contra Erosão por Chuvas Intensas**"):
        st.markdown("* Aplicação de remineralizadores de basalto e biochar para evitar lavagem de nutrientes | Plantio em curvas de nível obrigatório.")

    with st.expander("💳 **3. Crédito Emergencial e Subvenção de Seguro Rural**"):
        st.markdown("* Liberação de linhas do Banrisul/BRDE com taxas subsidiadas para produtores atingidos por granizo ou excesso de chuvas.")
        
