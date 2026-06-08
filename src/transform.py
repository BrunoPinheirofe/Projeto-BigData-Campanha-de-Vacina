import polars as pl
import pandas as pd

from config import CID_INFLUENZA, CID_INFLUENZA_AMPLIADO, REGIACOES


def filtra_influenza_pni(table: "pa.Table") -> "pa.Table":
    import pyarrow.compute as pc
    nome = table.column("ds_vacina")
    mask = pc.match_substring(pc.utf8_upper(nome), "INFLUENZA")
    mask = pc.or_(mask, pc.match_substring(pc.utf8_upper(nome), "GRIPE"))
    return table.filter(mask)


def filtra_sih_sim_influenza(
    df: pd.DataFrame,
    col_cid: str = "DIAG_PRINC",
    ampliado: bool = False,
) -> pd.DataFrame:
    cids = CID_INFLUENZA_AMPLIADO if ampliado else CID_INFLUENZA
    mask = df[col_cid].astype(str).str.startswith(tuple(cids), na=False)
    return df[mask].copy()


def tipa_pni(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["dt_vacina"] = pd.to_datetime(df["dt_vacina"], errors="coerce")
    df["nu_idade_paciente"] = pd.to_numeric(df["nu_idade_paciente"], errors="coerce").fillna(0).astype(int)
    return df


def faixa_etaria(idade: int) -> str:
    if idade < 5:
        return "0-4"
    if idade < 12:
        return "5-11"
    if idade < 18:
        return "12-17"
    if idade < 30:
        return "18-29"
    if idade < 40:
        return "30-39"
    if idade < 50:
        return "40-49"
    if idade < 60:
        return "50-59"
    return "60+"


def adiciona_regiao(df: pd.DataFrame) -> pd.DataFrame:
    uf_to_regiao = {uf: reg for reg, ufs in REGIACOES.items() for uf in ufs}
    col_uf = "sg_uf_paciente" if "sg_uf_paciente" in df.columns else "sg_uf"
    df["regiao"] = df[col_uf].map(uf_to_regiao)
    return df


def adiciona_mes_ano(df: pd.DataFrame) -> pd.DataFrame:
    df["mes"] = df["dt_vacina"].dt.month
    df["ano_vacina"] = df["dt_vacina"].dt.year
    return df


def agrega_doses(df: pd.DataFrame, granularidade: str = "uf_mes") -> pl.DataFrame:
    pl_df = pl.from_pandas(df)
    col_uf = "sg_uf_paciente" if "sg_uf_paciente" in df.columns else "sg_uf"
    group_cols = {
        "uf_mes": [col_uf, "ano_vacina", "mes"],
        "uf": [col_uf],
        "regiao_mes": ["regiao", "ano_vacina", "mes"],
        "faixa_etaria": ["faixa_etaria", col_uf],
        "sexo": ["tp_sexo_paciente", col_uf],
    }
    cols = group_cols.get(granularidade, group_cols["uf_mes"])
    return (
        pl_df.group_by(cols)
        .agg(pl.len().alias("total_doses"))
        .sort(cols)
    )


def merge_cobertura_desfecho(
    doses_agg: pd.DataFrame,
    sih_agg: pd.DataFrame | None = None,
    sim_agg: pd.DataFrame | None = None,
    on: list[str] | None = None,
) -> pd.DataFrame:
    if on is None:
        on = ["sg_uf_paciente", "ano_vacina", "mes"]
    result = doses_agg.copy()
    if sih_agg is not None:
        result = result.merge(sih_agg, on=on, how="left", suffixes=("", "_sih"))
    if sim_agg is not None:
        result = result.merge(sim_agg, on=on, how="left", suffixes=("", "_sim"))
    result = result.fillna(0)
    return result


def prepara_pni_completo(table: "pa.Table") -> pd.DataFrame:
    import pyarrow as pa
    import pyarrow.compute as pc

    dt_vacina = table.column("dt_vacina")
    mask_data = pc.and_(
        pc.greater_equal(dt_vacina, pa.scalar("2025-05-01")),
        pc.less_equal(dt_vacina, pa.scalar("2026-05-31")),
    )
    table_filtrada = table.filter(mask_data)
    table_influenza = filtra_influenza_pni(table_filtrada)
    df = table_influenza.to_pandas()
    df = tipa_pni(df)
    df["faixa_etaria"] = df["nu_idade_paciente"].apply(faixa_etaria)
    df = adiciona_regiao(df)
    df = adiciona_mes_ano(df)
    df["mes_ano"] = df["ano_vacina"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2)
    return df
