import polars as pl
import pandas as pd

from config import CID_INFLUENZA, CID_INFLUENZA_AMPLIADO, REGIACOES


def filtra_influenza_pni(table: "pa.Table") -> "pa.Table":
    import pyarrow.compute as pc
    mask = pc.match_substring(pc.upper(table.column("ds_vacina")), "INFLUENZA")
    mask = pc.or_(mask, pc.match_substring(pc.upper(table.column("ds_vacina")), "GRIPE"))
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
    df["dt_nascimento"] = pd.to_datetime(df["dt_nascimento"], errors="coerce")
    df["idade"] = (df["dt_vacina"] - df["dt_nascimento"]).dt.days / 365.25
    df["idade"] = df["idade"].clip(0, 120).astype(int)
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
    df["regiao"] = df["sg_uf"].map(uf_to_regiao)
    return df


def adiciona_mes_ano(df: pd.DataFrame) -> pd.DataFrame:
    df["mes"] = df["dt_vacina"].dt.month
    df["ano"] = df["dt_vacina"].dt.year
    return df


def agrega_doses(df: pd.DataFrame, granularidade: str = "uf_mes") -> pl.DataFrame:
    pl_df = pl.from_pandas(df)
    group_cols = {
        "uf_mes": ["sg_uf", "ano", "mes"],
        "uf": ["sg_uf"],
        "regiao_mes": ["regiao", "ano", "mes"],
        "faixa_etaria": ["faixa_etaria", "sg_uf"],
        "sexo": ["co_sexo", "sg_uf"],
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
        on = ["sg_uf", "ano", "mes"]
    result = doses_agg.copy()
    if sih_agg is not None:
        result = result.merge(sih_agg, on=on, how="left", suffixes=("", "_sih"))
    if sim_agg is not None:
        result = result.merge(sim_agg, on=on, how="left", suffixes=("", "_sim"))
    result = result.fillna(0)
    return result


def prepara_pni_completo(table: "pa.Table") -> pd.DataFrame:
    import pyarrow.compute as pc

    dt_inicio = pc.scalar("2025-05-01", type=pc.timestamp("s"))
    dt_fim = pc.scalar("2026-05-31", type=pc.timestamp("s"))
    dt_vacina = table.column("dt_vacina")

    mask_data = pc.and_(
        pc.greater_equal(dt_vacina, dt_inicio),
        pc.less_equal(dt_vacina, dt_fim),
    )
    table_filtrada = table.filter(mask_data)
    table_influenza = filtra_influenza_pni(table_filtrada)
    df = table_influenza.to_pandas()
    df = tipa_pni(df)
    df["faixa_etaria"] = df["idade"].apply(faixa_etaria)
    df = adiciona_regiao(df)
    df = adiciona_mes_ano(df)
    df["mes_ano"] = df["ano"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2)
    return df
