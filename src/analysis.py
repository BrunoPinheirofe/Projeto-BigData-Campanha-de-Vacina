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
    doses_uf = doses_agg.groupby("sg_uf")["total_doses"].sum().reset_index()
    doses_uf["populacao"] = doses_uf["sg_uf"].map(pop_uf)
    doses_uf["cobertura_100k"] = (doses_uf["total_doses"] / doses_uf["populacao"]) * 100_000
    doses_uf["cobertura_pct"] = (doses_uf["total_doses"] / doses_uf["populacao"]) * 100
    return doses_uf.sort_values("cobertura_100k", ascending=False).reset_index(drop=True)


def cobertura_por_regiao(doses_agg: pd.DataFrame) -> pd.DataFrame:
    uf_to_regiao = {uf: reg for reg, ufs in REGIACOES.items() for uf in ufs}
    doses_agg["regiao"] = doses_agg["sg_uf"].map(uf_to_regiao)
    return doses_agg.groupby("regiao")["total_doses"].sum().reset_index().sort_values("total_doses", ascending=False)


def cobertura_por_faixa_etaria(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("faixa_etaria")
        .size()
        .reset_index(name="total_doses")
        .sort_values("faixa_etaria")
    )


def cobertura_por_sexo(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("co_sexo")
        .size()
        .reset_index(name="total_doses")
    )


def cobertura_por_raca(df: pd.DataFrame) -> pd.DataFrame:
    mapa_raca = {
        "1": "Branca", "2": "Preta", "3": "Amarela",
        "4": "Parda", "5": "Indígena",
    }
    df["raca_desc"] = df["co_raca_cor"].map(mapa_raca).fillna("Sem informação")
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
        merged = doses_uf.merge(
            internacoes_uf[["sg_uf", col_internacoes]],
            on="sg_uf", how="left",
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
    agg = (
        df.groupby(["co_municipio_ibge", "sg_uf"])
        .size()
        .reset_index(name="total_doses")
        .sort_values("total_doses", ascending=True)
        .head(top_n)
    )
    return agg


def serie_temporal_mensal(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["ano", "mes"])
        .size()
        .reset_index(name="total_doses")
        .sort_values(["ano", "mes"])
    )


def resumo_metricas(df: pd.DataFrame, doses_agg: pd.DataFrame) -> dict:
    return {
        "total_doses": int(len(df)),
        "media_diaria": round(len(df) / (365 + 30), 0),
        "ufs_atendidas": int(df["sg_uf"].nunique()),
        "municipios_atendidos": int(df["co_municipio_ibge"].nunique()),
        "media_idade": round(df["idade"].mean(), 1),
        "pct_feminino": round((df["co_sexo"] == "F").mean() * 100, 1),
        "pct_masculino": round((df["co_sexo"] == "M").mean() * 100, 1),
    }
