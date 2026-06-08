import sys
sys.path.insert(0, "src")

from config import UFS, ANOS, REGIACOES, CID_INFLUENZA


def test_ufs_lista_completa():
    assert len(UFS) == 27


def test_ufs_nao_vazia():
    assert all(uf for uf in UFS)


def test_anos_periodo():
    assert "2025" in ANOS
    assert "2026" in ANOS


def test_regioes_cobrem_todas_ufs():
    ufs_nas_regioes = set()
    for ufs in REGIACOES.values():
        ufs_nas_regioes.update(ufs)
    assert ufs_nas_regioes == set(UFS)


def test_cid_influenza():
    assert "J10" in CID_INFLUENZA
    assert "J11" in CID_INFLUENZA
    assert len(CID_INFLUENZA) == 2


def test_s3_config_exists():
    from config import S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY
    assert S3_ENDPOINT.startswith("https://")
    assert len(S3_ACCESS_KEY) > 0
    assert len(S3_SECRET_KEY) > 0


def test_colunas_pni():
    from config import COLUNAS_PNI
    colunas_essenciais = {"dt_vacina", "ds_vacina", "sg_uf_paciente"}
    assert colunas_essenciais.issubset(set(COLUNAS_PNI))
