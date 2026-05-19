import pyarrow.dataset as pds
import pyarrow.fs as fs
import pyarrow.compute as pc

from config import (
    S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY, S3_REGION, S3_BUCKET,
    ANOS, UFS, COLUNAS_PNI,
)

PYSUS_DISPONIVEL = False
try:
    from pysus.online_data.SIH import download as _download_sih
    from pysus.online_data.SIM import download as _download_sim
    PYSUS_DISPONIVEL = True
except ImportError:
    pass


def get_s3_filesystem() -> fs.S3FileSystem:
    return fs.S3FileSystem(
        endpoint_override=S3_ENDPOINT,
        access_key=S3_ACCESS_KEY,
        secret_key=S3_SECRET_KEY,
        region=S3_REGION,
    )


def load_pni_table(filtro_uf: list[str] | None = None):
    s3 = get_s3_filesystem()
    dataset = pds.dataset(
        S3_BUCKET,
        filesystem=s3,
        format="parquet",
        partitioning="hive",
    )
    conditions = [pc.field("ano").isin(ANOS)]
    if filtro_uf:
        conditions.append(pc.field("uf").isin(filtro_uf))
    filtro = conditions[0] if len(conditions) == 1 else pc.and_(*conditions)
    return dataset.to_table(filter=filtro, columns=COLUNAS_PNI)


def download_sih(uf: str, ano: int):
    if not PYSUS_DISPONIVEL:
        raise RuntimeError("PySUS não instalado. Use Python <3.14 ou instale manualmente.")
    return _download_sih(uf, ano)


def download_sim(uf: str, ano: int):
    if not PYSUS_DISPONIVEL:
        raise RuntimeError("PySUS não instalado. Use Python <3.14 ou instale manualmente.")
    return _download_sim(uf, ano)


def download_todas_sih(anos: list[int] | None = None) -> dict:
    if anos is None:
        anos = [2025, 2026]
    resultados = {}
    for uf in UFS:
        for ano in anos:
            print(f"Baixando SIH {uf}/{ano}...")
            resultados[(uf, ano)] = download_sih(uf, ano)
    return resultados


def download_todas_sim(anos: list[int] | None = None) -> dict:
    if anos is None:
        anos = [2025, 2026]
    resultados = {}
    for uf in UFS:
        for ano in anos:
            print(f"Baixando SIM {uf}/{ano}...")
            resultados[(uf, ano)] = download_sim(uf, ano)
    return resultados
