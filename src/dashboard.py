import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io
import polars as pl

from config import UFS, REGIACOES, PERIODO_INICIO, PERIODO_FIM
from ingest import load_pni_ufs
from transform import prepara_pni_completo
import viz

# Estética Premium (Glassmorphism e gradientes)
st.set_page_config(
    page_title="Análise Vacinação Influenza",
    page_icon="💉",
    layout="wide",
)

st.markdown(
    """
<style>
    /* Estilo do Main e Background */
    .stApp {
        background: linear-gradient(135deg, #0e1117 0%, #17202A 100%);
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Cards das Métricas */
    div[data-testid="metric-container"] {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease-in-out;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        border: 1px solid rgba(52, 152, 219, 0.5);
    }
    
    /* Cores das Métricas */
    div[data-testid="metric-container"] > div {
        color: #e0e0e0;
    }
    
    /* Títulos */
    h1, h2, h3 {
        color: #3498db !important;
        font-weight: 700;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #11151c;
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    
    /* Tab headers */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0px 0px;
        padding: 10px 20px;
        background-color: rgba(255, 255, 255, 0.05);
        color: #aaaaaa;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3498db !important;
        color: #ffffff !important;
        font-weight: bold;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.title("💉 Análise da Vacinação contra Influenza no Brasil")
st.markdown(f"**Período:** {PERIODO_INICIO} a {PERIODO_FIM}")
st.markdown("---")


@st.cache_data
def carregar_resultados():
    df_2025 = pd.DataFrame()
    df_2026 = pd.DataFrame()

    try:
        if os.path.exists("resultado_cruzamento_2025.csv"):
            df_2025 = pd.read_csv("resultado_cruzamento_2025.csv")
    except Exception:
        pass

    try:
        if os.path.exists("resultado_cruzamento_2026.csv"):
            df_2026 = pd.read_csv("resultado_cruzamento_2026.csv")
    except Exception:
        pass

    df_resultado = pd.concat([df_2025, df_2026], ignore_index=True)
    if (
        not df_resultado.empty
        and "mes" in df_resultado.columns
        and "ano_vacina" in df_resultado.columns
    ):
        df_resultado["mes_ano"] = (
            df_resultado["ano_vacina"].astype(str)
            + "-"
            + df_resultado["mes"].astype(str).str.zfill(2)
        )

    return df_resultado


@st.cache_resource
def carregar_dados_pni(ufs):
    if not ufs:
        return pl.DataFrame()

    try:
        with st.spinner(
            f"⏳ Carregando dados para {len(ufs)} UF(s): {', '.join(ufs)}..."
        ):
            dfs = []
            ufs_s3 = []

            for uf in ufs:
                for ano in [2025, 2026]:
                    cache_file = f"data/cache_pni_{ano}/uf_{uf}.parquet"
                    if os.path.exists(cache_file):
                        dfs.append(pl.scan_parquet(cache_file))
                    else:
                        ufs_s3.append(uf)

            # Fallback: carrega direto do S3 para UFs sem cache local
            if ufs_s3:
                with st.spinner("🔄 Cache local não encontrado. Carregando do S3..."):
                    table = load_pni_ufs(list(set(ufs_s3)))
                    df_pni = prepara_pni_completo(table)
                    dfs.append(pl.from_pandas(df_pni).lazy())

            if dfs:
                return pl.concat(dfs, how="vertical_relaxed")
            else:
                return None
    except Exception as e:
        st.error(f"Erro ao carregar PNI: {e}")
        return None


# Carregar CSVs combinados
resultados = carregar_resultados()

st.sidebar.header("Filtros")

uf_selecionadas = st.sidebar.multiselect(
    "Unidades Federativas (Filtro Demográfico)",
    options=UFS,
    default=UFS,
    help="Selecione as UFs. Padrão: todas. Limpar seleção desabilita os gráficos demográficos.",
)

regiao_selecionada = st.sidebar.selectbox(
    "Região (Filtro Demográfico)",
    options=["Todas"] + list(REGIACOES.keys()),
    index=0,
)

faixa_etaria_selecionada = st.sidebar.multiselect(
    "Faixa Etária (Filtro Demográfico)",
    options=["0-4", "5-11", "12-17", "18-29", "30-39", "40-49", "50-59", "60+"],
    default=[],
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Dados:** healthbr-data (S3) + PySUS")
st.sidebar.markdown(
    "[SI-PNI](https://dadosabertos.saude.gov.br) | [PySUS](https://github.com/AlertaDengue/pySUS)"
)

# Carregar dados demográficos
dados_pni = carregar_dados_pni(uf_selecionadas)

# Aplicar filtros
if regiao_selecionada != "Todas" and dados_pni is not None:
    dados_pni = dados_pni.filter(pl.col("regiao") == regiao_selecionada)

if faixa_etaria_selecionada and dados_pni is not None:
    dados_pni = dados_pni.filter(pl.col("faixa_etaria").is_in(faixa_etaria_selecionada))


aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs(
    [
        "📊 Panorama",
        "👥 Demografia",
        "🏥 Desfecho",
        "⚠️ Gaps",
        "📊 Comparativo Anual",
        "📅 Campanha",
    ]
)

with aba1:
    st.header("Panorama Geral")

    col1, col2, col3, col4 = st.columns(4)

    total_doses = resultados["total_doses"].sum() if not resultados.empty else 0
    ufs_atendidas = (
        resultados["sg_uf_paciente"].nunique() if not resultados.empty else 0
    )

    with col1:
        st.metric("Total de Doses (Cruzamento)", f"{total_doses:,.0f}")
    with col2:
        st.metric("UFs Atendidas", f"{ufs_atendidas}")
    with col3:
        st.metric(
            "Total de Internações (Gripe)",
            f"{resultados['internacoes'].sum() if 'internacoes' in resultados else 0:,.0f}",
        )
    with col4:
        st.metric(
            "Óbitos (Gripe)",
            f"{resultados['obitos'].sum() if 'obitos' in resultados else 0:,.0f}",
        )

    col_esq, col_dir = st.columns(2)
    with col_esq:
        st.subheader("Série Temporal (Vacinação)")
        if not resultados.empty:
            df_st = resultados.groupby("mes_ano")["total_doses"].sum().reset_index()
            fig = viz.serie_temporal_plotly(df_st)
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Sem dados para série temporal")

    with col_dir:
        st.subheader("Cobertura por UF")
        if not resultados.empty:
            df_uf = (
                resultados.groupby("sg_uf_paciente")["total_doses"].sum().reset_index()
            )
            df_uf.rename(columns={"sg_uf_paciente": "sg_uf"}, inplace=True)
            fig = viz.barra_cobertura_uf(df_uf, col_valor="total_doses")
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Sem dados para cobertura UF")

with aba2:
    st.header("Perfil Demográfico (Baseado em UFs Selecionadas)")

    if dados_pni is not None:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Distribuição por Faixa Etária")
            df_fe = (
                dados_pni.group_by("faixa_etaria").agg(pl.len().alias("total_doses"))
            ).collect().to_pandas()
            st.plotly_chart(viz.barra_faixa_etaria(df_fe), width="stretch")

        with c2:
            st.subheader("Distribuição por Sexo")
            df_sex = (
                dados_pni.group_by("tp_sexo_paciente")
                .agg(pl.len().alias("total_doses"))
            ).collect().to_pandas()
            df_sex.rename(columns={"tp_sexo_paciente": "co_sexo"}, inplace=True)
            st.plotly_chart(viz.pizza_sexo(df_sex), width="stretch")

        st.subheader("Distribuição por Raça/Cor")
        mapa_raca = {
            "1": "Branca",
            "2": "Preta",
            "3": "Amarela",
            "4": "Parda",
            "5": "Indígena",
            "99": "Sem info",
        }
        df_raca = (
            dados_pni.group_by("co_raca_cor_paciente")
            .agg(pl.len().alias("total_doses"))
        ).collect().to_pandas()
        df_raca["raca_desc"] = (
            df_raca["co_raca_cor_paciente"].astype(str).map(mapa_raca).fillna("Outros")
        )
        st.plotly_chart(viz.barra_raca(df_raca), width="stretch")
    else:
        st.info("Carregando ou sem dados para Demografia. Tente ajustar os filtros.")

with aba3:
    st.header("Correlação Cobertura × Desfecho (Vacinas vs Internações/Óbitos)")

    if "internacoes" not in resultados.columns:
        st.warning("⚠️ Módulo PySUS (SIH/SIM) não instalado no ambiente (Incompatível com Python 3.14). Dados de Internações e Óbitos não disponíveis para análise de desfecho.")
    elif not resultados.empty:
        c_esq, c_dir = st.columns(2)
        with c_esq:
            st.subheader("Cobertura × Internações")
            if "internacoes" in resultados.columns:
                df_corr = (
                    resultados.groupby("sg_uf_paciente")[["total_doses", "internacoes"]]
                    .sum()
                    .reset_index()
                )
                df_corr.rename(
                    columns={
                        "sg_uf_paciente": "sg_uf",
                        "internacoes": "taxa_internacoes",
                        "total_doses": "cobertura_100k",
                    },
                    inplace=True,
                )
                st.plotly_chart(
                    viz.scatter_cobertura_desfecho(df_corr), width="stretch"
                )
            else:
                st.info("Sem dados de internações")

        with c_dir:
            st.subheader("Cobertura × Óbitos")
            if "obitos" in resultados.columns:
                df_corr = (
                    resultados.groupby("sg_uf_paciente")[["total_doses", "obitos"]]
                    .sum()
                    .reset_index()
                )
                df_corr.rename(
                    columns={
                        "sg_uf_paciente": "sg_uf",
                        "obitos": "taxa_internacoes",
                        "total_doses": "cobertura_100k",
                    },
                    inplace=True,
                )
                st.plotly_chart(
                    viz.scatter_cobertura_desfecho(df_corr), width="stretch"
                )
            else:
                st.info("Sem dados de óbitos")

        st.subheader("Série Dupla: Doses × Internações")
        if "internacoes" in resultados.columns:
            df_dupla = (
                resultados.groupby("mes_ano")[["total_doses", "internacoes"]]
                .sum()
                .reset_index()
            )
            st.plotly_chart(
                viz.serie_dupla_plotly(df_dupla, y2="internacoes"),
                width="stretch",
            )
    else:
        st.info("Carregue os dados para visualizar")

with aba4:
    st.header("Análise de Gaps (Gap Score)")

    if "internacoes" not in resultados.columns:
        st.warning("⚠️ Módulo PySUS (SIH/SIM) não instalado no ambiente. Impossível calcular o Gap Score sem dados de internação.")
    elif not resultados.empty:
        c1, c2 = st.columns(2)

        # Calcular Gap Score On-The-Fly
        doses_uf = (
            resultados.groupby("sg_uf_paciente")["total_doses"].sum().reset_index()
        )
        internacoes_uf = (
            resultados.groupby("sg_uf_paciente")["internacoes"]
            .sum()
            .reset_index(name="total_internacoes")
        )

        from analysis import gap_score

        gap_df = gap_score(doses_uf, internacoes_uf)
        gap_df.rename(columns={"sg_uf_paciente": "sg_uf"}, inplace=True)

        with c1:
            st.subheader("Gap Score por UF")
            st.plotly_chart(viz.treemap_gaps(gap_df), width="stretch")
        with c2:
            st.subheader("Relação Doses x Gap")
            st.plotly_chart(viz.bubble_gap_analysis(gap_df), width="stretch")

    else:
        st.info("Sem dados suficientes para calcular Gaps.")

with aba5:
    st.header("📊 Comparativo Anual: 2025 vs 2026")

    if not resultados.empty and "ano_vacina" in resultados.columns:
        df_2025 = resultados[resultados["ano_vacina"] == 2025]
        df_2026 = resultados[resultados["ano_vacina"] == 2026]

        def m(d):
            return {
                "doses": int(d["total_doses"].sum()) if not d.empty else 0,
                "ufs": int(d["sg_uf_paciente"].nunique()) if not d.empty else 0,
                "internacoes": (
                    int(d["internacoes"].sum())
                    if not d.empty and "internacoes" in d.columns
                    else 0
                ),
                "obitos": (
                    int(d["obitos"].sum())
                    if not d.empty and "obitos" in d.columns
                    else 0
                ),
            }

        m25, m26 = m(df_2025), m(df_2026)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Doses 2025", f"{m25['doses']:,}")
        c2.metric(
            "Doses 2026", f"{m26['doses']:,}", delta=f"{m26['doses'] - m25['doses']:+}"
        )
        c3.metric("Internações 2025", f"{m25['internacoes']:,}")
        c4.metric(
            "Internações 2026",
            f"{m26['internacoes']:,}",
            delta=f"{m26['internacoes'] - m25['internacoes']:+}",
            delta_color="inverse",
        )

        if m25["obitos"] or m26["obitos"]:
            c1, c2 = st.columns(2)
            c1.metric("Óbitos 2025", f"{m25['obitos']:,}")
            c2.metric(
                "Óbitos 2026",
                f"{m26['obitos']:,}",
                delta=f"{m26['obitos'] - m25['obitos']:+}",
                delta_color="inverse",
            )

        st.markdown("---")
        col_esq, col_dir = st.columns(2)

        with col_esq:
            st.subheader("Doses por UF")
            doses_uf = (
                resultados.groupby(["sg_uf_paciente", "ano_vacina"])["total_doses"]
                .sum()
                .reset_index()
            )
            fig = px.bar(
                doses_uf,
                x="sg_uf_paciente",
                y="total_doses",
                color="ano_vacina",
                barmode="group",
                labels={
                    "sg_uf_paciente": "UF",
                    "total_doses": "Doses",
                    "ano_vacina": "Ano",
                },
            )
            fig.update_layout(template="plotly_white")
            st.plotly_chart(fig, width="stretch")

        with col_dir:
            st.subheader("Série Mensal Comparada")
            serie = (
                resultados.groupby(["mes_ano", "ano_vacina"])["total_doses"]
                .sum()
                .reset_index()
            )
            fig = px.line(
                serie,
                x="mes_ano",
                y="total_doses",
                color="ano_vacina",
                markers=True,
                labels={"mes_ano": "Mês", "total_doses": "Doses", "ano_vacina": "Ano"},
            )
            fig.update_layout(template="plotly_white", hovermode="x unified")
            st.plotly_chart(fig, width="stretch")

        csv_buffer = io.StringIO()
        resultados.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Exportar Dados Consolidados (CSV)",
            data=csv_buffer.getvalue(),
            file_name="relatorio_influenza_cruzado.csv",
            mime="text/csv",
        )
    else:
        st.info("Carregue os dados do pipeline para visualizar o comparativo anual.")

with aba6:
    ano_campanha = st.selectbox("Selecione o ano", ["2025", "2026", "Ambos"], index=0)

    if dados_pni is not None:
        if ano_campanha == "Ambos":
            c_esq, c_dir = st.columns(2)
            with c_esq:
                st.subheader("📈 2025")
                df_a = dados_pni.filter(pl.col("ano_vacina") == 2025)
                if df_a.select(pl.len()).collect().item() > 0:
                    st.plotly_chart(
                        viz.timeline_regiao_plotly(
                            df_a.group_by(["mes_ano", "regiao"])
                            .agg(pl.len().alias("total_doses"))
                            .sort("mes_ano")
                            .collect().to_pandas()
                        ),
                        width="stretch",
                    )
                    st.plotly_chart(
                        viz.barra_cobertura_regiao(
                            df_a.group_by("regiao").agg(pl.len().alias("Total de Doses"))
                            .sort("Total de Doses", descending=True)
                            .rename({"regiao": "Região"}).collect().to_pandas()
                        ), width="stretch"
                    )
                else:
                    st.info("Sem dados para 2025")
            with c_dir:
                st.subheader("📈 2026")
                df_b = dados_pni.filter(pl.col("ano_vacina") == 2026)
                if df_b.select(pl.len()).collect().item() > 0:
                    st.plotly_chart(
                        viz.timeline_regiao_plotly(
                            df_b.group_by(["mes_ano", "regiao"])
                            .agg(pl.len().alias("total_doses"))
                            .sort("mes_ano")
                            .collect().to_pandas()
                        ),
                        width="stretch",
                    )
                    st.plotly_chart(
                        viz.barra_cobertura_regiao(
                            df_b.group_by("regiao").agg(pl.len().alias("Total de Doses"))
                            .sort("Total de Doses", descending=True)
                            .rename({"regiao": "Região"}).collect().to_pandas()
                        ), width="stretch"
                    )
                else:
                    st.info("Sem dados para 2026")
        else:
            ano = int(ano_campanha)
            df_filtrado = dados_pni.filter(pl.col("ano_vacina") == ano)
            if df_filtrado.select(pl.len()).collect().item() > 0:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("📈 Tendência Temporal por Região")
                    st.plotly_chart(
                        viz.timeline_regiao_plotly(
                            df_filtrado.group_by(["mes_ano", "regiao"])
                            .agg(pl.len().alias("total_doses"))
                            .sort("mes_ano")
                            .collect().to_pandas()
                        ),
                        width="stretch",
                    )
                with col2:
                    st.subheader("🗺️ Cobertura por Região")
                    st.plotly_chart(
                        viz.barra_cobertura_regiao(
                            df_filtrado.group_by("regiao").agg(pl.len().alias("Total de Doses"))
                            .sort("Total de Doses", descending=True)
                            .rename({"regiao": "Região"}).collect().to_pandas()
                        ),
                        width="stretch",
                    )

                st.markdown("---")
                col3, col4 = st.columns(2)
                with col3:
                    st.subheader("🧬 Densidade Etária")
                    df_idade = (
                        df_filtrado.group_by("nu_idade_paciente")
                        .agg(pl.len().alias("Quantidade"))
                        .sort("nu_idade_paciente")
                        .collect().to_pandas()
                    )
                    st.plotly_chart(
                        viz.histograma_idade_plotly(df_idade),
                        width="stretch",
                    )
                with col4:
                    st.subheader("📦 Variabilidade Etária (Outliers)")
                    df_stats = (
                        df_filtrado.group_by("regiao").agg(
                            pl.col("nu_idade_paciente").min().alias("min"),
                            pl.col("nu_idade_paciente").quantile(0.25).alias("q1"),
                            pl.col("nu_idade_paciente").median().alias("median"),
                            pl.col("nu_idade_paciente").quantile(0.75).alias("q3"),
                            pl.col("nu_idade_paciente").max().alias("max"),
                        ).collect().to_pandas()
                    )
                    st.plotly_chart(
                        viz.boxplot_regioes_plotly(df_stats),
                        width="stretch",
                    )

                st.markdown("---")
                st.subheader("🔝 Top 10 Grupos Prioritários")
                df_grupos = (
                    df_filtrado.group_by("ds_vacina_grupo_atendimento")
                    .agg(pl.len().alias("Total de Doses"))
                    .sort("Total de Doses", descending=True)
                    .head(10)
                    .rename({"ds_vacina_grupo_atendimento": "Grupo de Atendimento"})
                    .sort("Total de Doses")
                    .collect().to_pandas()
                )
                st.plotly_chart(
                    viz.barra_grupos_prioritarios_plotly(df_grupos),
                    width="stretch",
                )
            else:
                st.info(
                    f"Nenhum dado encontrado para {ano_campanha} com os filtros atuais."
                )
    else:
        st.info("Carregue os dados na barra lateral para visualizar.")
