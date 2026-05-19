import streamlit as st
import pandas as pd
import plotly.express as px

from config import UFS, REGIACOES, PERIODO_INICIO, PERIODO_FIM

st.set_page_config(
    page_title="Análise Vacinação Influenza",
    page_icon="💉",
    layout="wide",
)

st.title("💉 Análise da Vacinação contra Influenza no Brasil")
st.markdown(f"**Período:** {PERIODO_INICIO} a {PERIODO_FIM}")
st.markdown("---")


@st.cache_data
def carregar_dados():
    return pd.DataFrame()


@st.cache_data
def carregar_resultados():
    return {}


dados = carregar_dados()
resultados = carregar_resultados()


st.sidebar.header("Filtros")

uf_selecionadas = st.sidebar.multiselect(
    "Unidades Federativas",
    options=UFS,
    default=[],
    placeholder="Todas as UFs",
)

regiao_selecionada = st.sidebar.selectbox(
    "Região",
    options=["Todas"] + list(REGIACOES.keys()),
    index=0,
)

faixa_etaria_selecionada = st.sidebar.multiselect(
    "Faixa Etária",
    options=["0-4", "5-11", "12-17", "18-29", "30-39", "40-49", "50-59", "60+"],
    default=[],
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Dados:** healthbr-data (S3) + PySUS")
st.sidebar.markdown("[SI-PNI](https://dadosabertos.saude.gov.br) | [PySUS](https://github.com/AlertaDengue/pySUS)")


aba1, aba2, aba3, aba4, aba5 = st.tabs([
    "📊 Panorama", "👥 Demografia", "🏥 Desfecho",
    "⚠️ Gaps", "📋 Relatório",
])

with aba1:
    st.header("Panorama Geral")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Doses (estimado)", "—")
    with col2:
        st.metric("UFs Atendidas", "—")
    with col3:
        st.metric("Cobertura Média", "—")
    with col4:
        st.metric("Municípios", "—")

    col_esq, col_dir = st.columns(2)
    with col_esq:
        st.subheader("Série Temporal")
        st.info("Carregue os dados para visualizar")
    with col_dir:
        st.subheader("Cobertura por UF")
        st.info("Carregue os dados para visualizar")

with aba2:
    st.header("Perfil Demográfico")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Distribuição por Faixa Etária")
        st.info("Carregue os dados para visualizar")
    with c2:
        st.subheader("Distribuição por Sexo")
        st.info("Carregue os dados para visualizar")

    st.subheader("Distribuição por Raça/Cor")
    st.info("Carregue os dados para visualizar")

with aba3:
    st.header("Correlação Cobertura × Desfecho")

    c_esq, c_dir = st.columns(2)
    with c_esq:
        st.subheader("Cobertura × Internações")
        st.info("Carregue os dados de SIH para visualizar")
    with c_dir:
        st.subheader("Cobertura × Óbitos")
        st.info("Carregue os dados de SIM para visualizar")

    st.subheader("Série Dupla: Doses × Desfecho")
    st.info("Carregue os dados para visualizar")

with aba4:
    st.header("Análise de Gaps")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Ranking de UFs Críticas")
        st.info("Carregue os dados para visualizar")
    with c2:
        st.subheader("Gap Score")
        st.info("Carregue os dados para visualizar")

    st.subheader("Municípios com Menor Cobertura")
    st.info("Carregue os dados para visualizar")

with aba5:
    st.header("Relatório")

    st.subheader("Principais Insights")
    st.info("Os insights serão gerados após o carregamento dos dados")

    st.subheader("Dados Agregados")
    if st.button("Exportar Dados (CSV)"):
        st.info("Disponível após carregar os dados")
