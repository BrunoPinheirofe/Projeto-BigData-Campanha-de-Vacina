import pyarrow.dataset as pds
import pyarrow.fs as fs
import pyarrow.compute as pc

from config import (
    S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY, S3_REGION, S3_BUCKET,
    ANOS, UFS, COLUNAS_PNI,
)

PYSUS_DISPONIVEL = False
try:
    from pysus.api._impl.databases import sih as _sih_api
    from pysus.api._impl.databases import sim as _sim_api
    
    def _download_sih(uf, ano):
        return _sih_api(state=uf, year=ano, month=list(range(1, 13)))
        
    def _download_sim(uf, ano):
        return _sim_api(state=uf, year=ano)
        
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


def load_pni_uf_mes(
    uf: str,
    ano: str = "2025",
    mes: str = "05",
) -> "pa.Table":
    s3 = get_s3_filesystem()
    path = f"{S3_BUCKET}ano={ano}/mes={mes}/uf={uf}/"
    dataset = pds.dataset(
        path,
        filesystem=s3,
        format="parquet",
        partitioning="hive",
    )
    return dataset.to_table(columns=COLUNAS_PNI)


def load_pni_uf(
    uf: str,
    anos: list[str] | None = None,
    meses: list[str] | None = None,
) -> "pa.Table":
    if anos is None:
        anos = ANOS
    if meses is None:
        meses = [f"{m:02d}" for m in range(5, 13)]
    import pyarrow.compute as pc
    tables = []
    for ano in anos:
        for mes in meses:
            try:
                t = load_pni_uf_mes(uf, ano, mes)
                tables.append(t)
            except Exception:
                continue
    if not tables:
        raise RuntimeError(f"Nenhum dado encontrado para UF={uf}")
    import pyarrow as pa
    return pa.concat_tables(tables)


def load_pni_ufs(
    ufs: list[str],
    anos: list[str] | None = None,
    meses: list[str] | None = None,
) -> "pa.Table":
    if anos is None:
        anos = ANOS
    if meses is None:
        meses = [f"{m:02d}" for m in range(1, 13)]
    import pyarrow as pa
    tables = []
    for uf in ufs:
        try:
            t = load_pni_uf(uf, anos, meses)
            tables.append(t)
            print(f"  {uf}: {t.num_rows:,} registros")
        except RuntimeError as e:
            print(f"  {uf}: {e}")
    if not tables:
        raise RuntimeError("Nenhum dado encontrado para as UFs fornecidas")
    return pa.concat_tables(tables)


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
