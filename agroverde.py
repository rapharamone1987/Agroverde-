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
    "📅 Tendência Sazonal & Estratégia de Governo (1 a 6 Meses)"
])

# =========================================================
# ABA 1: MONITORAMENTO & AÇÕES PRÁTICAS (TUDO NA 1ª GUIA)
# =========================================================
with aba_operacional:
    # A. Métricas em Tempo Real & Nível dos Rios
    if dados_16dias and "current" in dados_16dias:
        curr = dados_16dias["current"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Temperatura Atual", f"{curr.get('temperature_2m', 'N/D')} °C")
        c2.metric("Umidade do Ar", f"{curr.get('relative_humidity_2m', 'N/D')} %")
        c3.metric("Chuva Hoje", f"{curr.get('precipitation', 0)} mm")
        c4.metric("Vento Atual", f"{curr.get('wind_speed_10m', 'N/D')} km/h")

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

        # B. Central de Alertas Oficiais & Nível de Rios
        st.subheader(f"🌊 Status da Bacia & Alertas Severos — {municipio_sel}")
        
        c_rio1, c_rio2, c_rio3 = st.columns(3)
        status_rio = "ALERTA DE CHEIA" if chuva_acum_7 > 80 else ("Atenção / Calha Cheia" if chuva_acum_7 > 30 else "Nível Baixo / Estiagem")
        cota_rio = "+ 2.80 m (Alto)" if chuva_acum_7 > 80 else ("+ 0.90 m (Normal)" if chuva_acum_7 > 30 else "- 0.45 m (Baixo)")
        
        c_rio1.metric("Acumulado 7 Dias", f"{chuva_acum_7:.1f} mm")
        c_rio2.metric("Tendência Fluvial", status_rio)
        c_rio3.metric("Cota Estada Fluvial (Est.)", cota_rio)

        # C. Alerta Severo (Exemplo: Tempestade / Alerta Amarelo/Laranja)
        if (20 <= chuva_acum_7 <= 60) or (40 <= max_vento_periodo <= 60):
            st.warning("⚠️ **ALERTA METEOROLÓGICO: PERIGO POTENCIAL DE TEMPESTADE / VENDAVAL** (Inmet / Defesa Civil)")
            with st.expander("🛡️ **Precauções de Segurança Pessoal (Defesa Civil 199)**"):
                st.markdown("* Não se abrigue debaixo de árvores | Evite usar eletrodomésticos na tomada | Emergência: 199 / 193.")

        st.markdown("---")

        # D. PAINEL DE AÇÕES PRÁTICAS OPERACIONAIS (AÇÕES NO CAMPO)
        st.subheader(f"🚜 Checklist de Manejo Operacional na Propriedade")
        
        col_op1, col_op2, col_op3 = st.columns(3)

        with col_op1:
            st.markdown("#### 🌾 Lavouras & Hortifrúti")
            if chuva_acum_16 < 25:
                st.markdown("""
                * **Irrigação:** Priorizar turnos de rega em fases de floração/enchimento.
                * **Pulverização:** **Suspender** se umidade do ar $< 50\%$ ou vento $> 10\text{ km/h}$.
                * **Solo:** Manter palhada e aplicar biochar para conter evaporação.
                """)
            else:
                st.markdown("""
                * **Adubação/Defensivos:** **Suspender** aplicações pré-chuva (risco de lixiviação).
                * **Estufas:** Baixar cortinas laterais contra rajadas de vento.
                * **Drenagem:** Inspecionar valas e canais para conter empoçamento.
                """)

        with col_op2:
            st.markdown("#### 🐄 Pecuária & Leite")
            if max_temp_periodo >= 32:
                st.markdown("""
                * **Estresse Térmico:** Ligar aspersores e ventiladores 30 min antes da ordenha.
                * **Proteção de Raios:** Retirar gado de perto de cercas de arame e árvores isoladas.
                * **Água Potável:** Checar vazão dos bebedouros (demanda sobe em 40%).
                """)
            else:
                st.markdown("""
                * **Remoção de Rebanho:** Tirar animais de áreas baixas sujeitas a alagamento.
                * **Alimentação:** Garantir trato coberto antes do início das chuvas.
                """)

        with col_op3:
            st.markdown("#### 🚜 Máquinas & Infraestrutura")
            st.markdown("""
            * **Energia:** Testar gerador a combustível/tomada do trator para resfriadores de leite.
            * **Insumos:** Proteger sementes, rações e adubos em locais elevados.
            * **Maquinário:** Retirar tratores de perto de árvores antigas ou galpões frágeis.
            """)

    st.markdown("---")

    # E. Mapa Tático e Tabela Diária
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
# ABA 2: TENDÊNCIA SAZONAL & ESTRATÉGIA DE GOVERNO
# =========================================================
with aba_sazonal:
    st.subheader(f"📊 Planejamento Sazonal Estratégico & Políticas Públicas — {municipio_sel}")
    st.info("💡 **Diretrizes de Governo da SEAPI:** Ações de médio e longo prazo por pilar de política pública com base na tendência climática trimestral/semestral.")

    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("Tendência Trimestral (Chuva)", "Abaixo da Média (-18%)", "Alerta de Estiagem", delta_color="inverse")
    col_s2.metric("Anomalia Térmica Prevista", "+2.1 °C vs Histórico", "Onda de Calor no Verão", delta_color="inverse")
    col_s3.metric("Meta de Resiliência de Solo", "85% de Cobertura", "Acionar Programa Biochar")

    st.markdown("---")

    with st.expander("💧 **1. Pilar de Irrigação & Reservas Hídricas (1 a 6 Meses)**", expanded=True):
        st.markdown("* Limpeza de açudes | Priorização do Fundo FDR para irrigação por gotejamento | Rede de caminhões-pipa.")

    with st.expander("🌱 **2. Pilar de Solo, Carbono e Biochar (Manejo Regenerativo)**"):
        st.markdown("* Distribuição do *Kit AgroClima* | Incentive ao plantio de cobertura | Emissão do **Selo RS Carbono Neutro**.")

    with st.expander("🏛️ **3. Pilar de Infraestrutura & Bem-Estar Animal**"):
        st.markdown("* Pintura de alto albedo em galpões metálicos | Linhas para sistemas silvopastoris.")

    with st.expander("💳 **4. Pilar de Crédito Verde, Seguro & Incentivos Fiscais**"):
        st.markdown("* Desconto no ICMS/IPVA agrícola via validação do app | Bonificação no seguro rural do Banrisul/BRDE.")
        
