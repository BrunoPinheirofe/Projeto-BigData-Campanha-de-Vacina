import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np


FIGW = 12
FIGH = 6
COR_PALETTE = px.colors.qualitative.Set2


def serie_temporal_plotly(df: pd.DataFrame, col_data: str = "mes_ano", col_valor: str = "total_doses") -> go.Figure:
    fig = px.line(
        df, x=col_data, y=col_valor,
        markers=True,
        title="Doses de Influenza Aplicadas por Mês (Brasil)",
        labels={col_data: "Mês", col_valor: "Total de Doses"},
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        hovermode="x unified",
        template="plotly_white",
    )
    return fig


def mapa_cobertura_plotly(df: pd.DataFrame, col_valor: str = "cobertura_100k") -> go.Figure:
    siglas = {
        "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas",
        "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal",
        "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão",
        "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais",
        "PA": "Pará", "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco",
        "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
        "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima",
        "SC": "Santa Catarina", "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins",
    }
    df = df.copy()
    df["estado"] = df["sg_uf"].map(siglas)
    fig = px.choropleth(
        df,
        locations="estado",
        locationmode="country names",
        color=col_valor,
        scope="south america",
        title="Cobertura Vacinal contra Influenza por UF (doses/100k hab)",
        labels={col_valor: "Doses/100k hab"},
        color_continuous_scale="Viridis",
    )
    fig.update_layout(geo=dict(bgcolor="rgba(0,0,0,0)"))
    return fig


def barra_cobertura_uf(df: pd.DataFrame, col_valor: str = "cobertura_100k") -> go.Figure:
    df_sorted = df.sort_values(col_valor, ascending=True)
    fig = px.bar(
        df_sorted,
        x=col_valor,
        y="sg_uf",
        orientation="h",
        title="Cobertura Vacinal por UF (doses/100k hab)",
        labels={col_valor: "Doses/100k hab", "sg_uf": "UF"},
        color=col_valor,
        color_continuous_scale="Viridis",
    )
    fig.update_layout(template="plotly_white")
    return fig


def scatter_cobertura_desfecho(
    df: pd.DataFrame,
    x: str = "cobertura_100k",
    y: str = "taxa_internacoes",
    label_col: str = "sg_uf",
) -> go.Figure:
    fig = px.scatter(
        df, x=x, y=y, text=label_col,
        title="Cobertura × Internações por Influenza (por UF)",
        labels={x: "Cobertura (doses/100k hab)", y: "Taxa de Internações/100k hab"},
        trendline="ols",
    )
    fig.update_traces(textposition="top center")
    fig.update_layout(template="plotly_white")
    return fig


def treemap_gaps(df: pd.DataFrame, nomes: str = "sg_uf", valores: str = "gap_score") -> go.Figure:
    fig = px.treemap(
        df, path=[nomes], values=valores,
        title="Gap Score por UF (baixa cobertura × alta incidência)",
        color=valores,
        color_continuous_scale="RdYlGn_r",
    )
    fig.update_layout(template="plotly_white")
    return fig


def barra_faixa_etaria(df: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        df, x="faixa_etaria", y="total_doses",
        title="Doses Aplicadas por Faixa Etária",
        labels={"faixa_etaria": "Faixa Etária", "total_doses": "Total de Doses"},
        color="total_doses",
        color_continuous_scale="Blues",
    )
    fig.update_layout(template="plotly_white")
    return fig


def pizza_sexo(df: pd.DataFrame) -> go.Figure:
    fig = px.pie(
        df, values="total_doses", names="co_sexo",
        title="Distribuição por Sexo",
        hole=0.4,
    )
    fig.update_layout(template="plotly_white")
    return fig


def barra_raca(df: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        df, x="raca_desc", y="total_doses",
        title="Doses Aplicadas por Raça/Cor",
        labels={"raca_desc": "Raça/Cor", "total_doses": "Total de Doses"},
        color="total_doses",
        color_continuous_scale="Teal",
    )
    fig.update_layout(template="plotly_white")
    return fig


def heatmap_regiao_mes(df: pd.DataFrame) -> go.Figure:
    pivot = df.pivot_table(
        index="regiao", columns="mes", values="total_doses", aggfunc="sum"
    ).fillna(0)
    fig = px.imshow(
        pivot,
        text_auto=".0f",
        title="Doses Aplicadas por Região × Mês",
        labels={"x": "Mês", "y": "Região", "color": "Doses"},
        color_continuous_scale="YlOrRd",
        aspect="auto",
    )
    fig.update_layout(template="plotly_white")
    return fig


def bubble_gap_analysis(df: pd.DataFrame) -> go.Figure:
    fig = px.scatter(
        df,
        x="total_doses", y="gap_score",
        size="gap_score", color="sg_uf",
        hover_name="sg_uf",
        title="Análise de Gaps: Doses Aplicadas × Gap Score",
        labels={
            "total_doses": "Total de Doses",
            "gap_score": "Gap Score (prioridade)",
        },
    )
    fig.update_layout(template="plotly_white")
    return fig


def serie_dupla_plotly(
    df: pd.DataFrame,
    x: str = "mes_ano",
    y1: str = "total_doses",
    y2: str = "total_internacoes",
    nome_y1: str = "Doses Aplicadas",
    nome_y2: str = "Internações",
) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[x], y=df[y1], mode="lines+markers",
        name=nome_y1, yaxis="y",
    ))
    fig.add_trace(go.Scatter(
        x=df[x], y=df[y2], mode="lines+markers",
        name=nome_y2, yaxis="y2",
    ))
    fig.update_layout(
        title="Doses Aplicadas × Internações por Influenza",
        xaxis=dict(title="Mês"),
        yaxis=dict(title=nome_y1, side="left"),
        yaxis2=dict(title=nome_y2, side="right", overlaying="y", tickmode="sync"),
        template="plotly_white",
        hovermode="x unified",
    )
    return fig


def tabela_ranking(df: pd.DataFrame, colunas: list[str], titulo: str = "") -> go.Figure:
    cabecalhos = [c.replace("_", " ").title() for c in colunas]
    fig = go.Figure(data=[go.Table(
        header=dict(values=cabecalhos, fill_color="paleturquoise", align="left"),
        cells=dict(values=[df[c] for c in colunas], align="left"),
    )])
    fig.update_layout(title=titulo, template="plotly_white")
    return fig


def timeline_regiao_plotly(df: pd.DataFrame) -> go.Figure:
    fig = px.line(
        df, x="mes_ano", y="total_doses", color="regiao",
        markers=True,
        title="Doses de Influenza por Região (série temporal)",
        labels={"mes_ano": "Mês", "total_doses": "Doses", "regiao": "Região"},
    )
    fig.update_layout(template="plotly_white", hovermode="x unified")
    return fig
