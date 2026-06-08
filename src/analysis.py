import pandas as pd
import numpy as np
from scipy.stats import pearsonr

from config import REGIACOES


POPULACAO_BRASIL_2025 = 212_600_000
POPULACAO_60_MAIS = 35_000_000


def cobertura_por_uf(doses_agg: pd.DataFrame) -> pd.DataFrame:
    pop_uf = {
        "SP": 46_000_000, "MG": 21_300_000, "RJ": 17_400_000,
        "BA": 14_900_000, "PR": 11_600_000, "RS": 11_500_000,
        "PE": 9_600_000, "CE": 9_200_000, "PA": 8_800_000,
        "SC": 8_200_000, "GO": 7_300_000, "MA": 7_200_000,
        "ES": 4_100_000, "DF": 3_300_000, "MS": 2_900_000,
        "MT": 2_800_000, "PB": 4_100_000, "RN": 3_600_000,
        "PI": 3_300_000, "AL": 3_400_000, "SE": 2_400_000,
        "RO": 1_800_000, "TO": 1_600_000, "AC": 900_000,
        "AP": 900_000, "RR": 650_000,
    }
    col_uf = "sg_uf_paciente" if "sg_uf_paciente" in doses_agg.columns else "sg_uf"
    doses_uf = doses_agg.groupby(col_uf)["total_doses"].sum().reset_index()
    doses_uf["populacao"] = doses_uf[col_uf].map(pop_uf)
    doses_uf["cobertura_100k"] = (doses_uf["total_doses"] / doses_uf["populacao"]) * 100_000
    doses_uf["cobertura_pct"] = (doses_uf["total_doses"] / doses_uf["populacao"]) * 100
    return doses_uf.sort_values("cobertura_100k", ascending=False).reset_index(drop=True)


def cobertura_por_regiao(doses_agg: pd.DataFrame) -> pd.DataFrame:
    col_uf = "sg_uf_paciente" if "sg_uf_paciente" in doses_agg.columns else "sg_uf"
    uf_to_regiao = {uf: reg for reg, ufs in REGIACOES.items() for uf in ufs}
    doses_agg["regiao"] = doses_agg[col_uf].map(uf_to_regiao)
    return doses_agg.groupby("regiao")["total_doses"].sum().reset_index().sort_values("total_doses", ascending=False)


def cobertura_por_faixa_etaria(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("faixa_etaria")
        .size()
        .reset_index(name="total_doses")
        .sort_values("faixa_etaria")
    )


def cobertura_por_sexo(df: pd.DataFrame) -> pd.DataFrame:
    col_sexo = "tp_sexo_paciente" if "tp_sexo_paciente" in df.columns else "co_sexo"
    return (
        df.groupby(col_sexo)
        .size()
        .reset_index(name="total_doses")
    )


def cobertura_por_raca(df: pd.DataFrame) -> pd.DataFrame:
    col_raca = "co_raca_cor_paciente" if "co_raca_cor_paciente" in df.columns else "co_raca_cor"
    mapa_raca = {
        "1": "Branca", "2": "Preta", "3": "Amarela",
        "4": "Parda", "5": "Indígena",
    }
    df["raca_desc"] = df[col_raca].map(mapa_raca).fillna("Sem informação")
    return (
        df.groupby("raca_desc")
        .size()
        .reset_index(name="total_doses")
        .sort_values("total_doses", ascending=False)
    )


def correlacao_cobertura_desfecho(
    df: pd.DataFrame,
    col_cobertura: str = "total_doses",
    col_desfecho: str = "internacoes",
) -> dict:
    df_clean = df[[col_cobertura, col_desfecho]].dropna()
    if len(df_clean) < 3:
        return {"r": np.nan, "p": np.nan}
    r, p = pearsonr(df_clean[col_cobertura], df_clean[col_desfecho])
    return {"r": r, "p": p}


def gap_score(
    doses_uf: pd.DataFrame,
    internacoes_uf: pd.DataFrame | None = None,
    col_doses: str = "total_doses",
    col_internacoes: str = "total_internacoes",
) -> pd.DataFrame:
    if internacoes_uf is not None:
        col_uf = "sg_uf_paciente" if "sg_uf_paciente" in doses_uf.columns else "sg_uf"
        merged = doses_uf.merge(
            internacoes_uf[[col_uf, col_internacoes]],
            on=col_uf, how="left",
        ).fillna(0)
        max_doses = merged[col_doses].max()
        max_internacoes = merged[col_internacoes].max()
        if max_doses > 0 and max_internacoes > 0:
            merged["doses_norm"] = merged[col_doses] / max_doses
            merged["internacoes_norm"] = merged[col_internacoes] / max_internacoes
            merged["gap_score"] = (1 - merged["doses_norm"]) * merged["internacoes_norm"]
            return merged.sort_values("gap_score", ascending=False).reset_index(drop=True)
    doses_uf["gap_score"] = 0
    return doses_uf


def ranking_municipios_criticos(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    col_mun = "co_municipio_paciente" if "co_municipio_paciente" in df.columns else "co_municipio_ibge"
    col_uf = "sg_uf_paciente" if "sg_uf_paciente" in df.columns else "sg_uf"
    agg = (
        df.groupby([col_mun, col_uf])
        .size()
        .reset_index(name="total_doses")
        .sort_values("total_doses", ascending=True)
        .head(top_n)
    )
    return agg


def serie_temporal_mensal(df: pd.DataFrame) -> pd.DataFrame:
    col_ano = "ano_vacina" if "ano_vacina" in df.columns else "ano"
    return (
        df.groupby([col_ano, "mes"])
        .size()
        .reset_index(name="total_doses")
        .sort_values([col_ano, "mes"])
    )


def resumo_metricas(df: pd.DataFrame, doses_agg: pd.DataFrame) -> dict:
    col_uf = "sg_uf_paciente" if "sg_uf_paciente" in df.columns else "sg_uf"
    col_mun = "co_municipio_paciente" if "co_municipio_paciente" in df.columns else "co_municipio_ibge"
    col_sexo = "tp_sexo_paciente" if "tp_sexo_paciente" in df.columns else "co_sexo"
    return {
        "total_doses": int(len(df)),
        "media_diaria": round(len(df) / 395, 0),
        "ufs_atendidas": int(df[col_uf].nunique()),
        "municipios_atendidos": int(df[col_mun].nunique()),
        "media_idade": round(df["nu_idade_paciente"].mean(), 1),
        "pct_feminino": round((df[col_sexo] == "F").mean() * 100, 1),
        "pct_masculino": round((df[col_sexo] == "M").mean() * 100, 1),
    }
