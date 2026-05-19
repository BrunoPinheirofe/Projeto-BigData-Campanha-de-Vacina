import sys
sys.path.insert(0, "src")

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from transform import (
    filtra_sih_sim_influenza, tipa_pni, faixa_etaria,
    adiciona_regiao, adiciona_mes_ano, agrega_doses,
    prepara_pni_completo,
)


def test_faixa_etaria():
    assert faixa_etaria(3) == "0-4"
    assert faixa_etaria(10) == "5-11"
    assert faixa_etaria(15) == "12-17"
    assert faixa_etaria(25) == "18-29"
    assert faixa_etaria(35) == "30-39"
    assert faixa_etaria(45) == "40-49"
    assert faixa_etaria(55) == "50-59"
    assert faixa_etaria(70) == "60+"


def test_faixa_etaria_limites():
    assert faixa_etaria(0) == "0-4"
    assert faixa_etaria(4) == "0-4"
    assert faixa_etaria(5) == "5-11"
    assert faixa_etaria(59) == "50-59"
    assert faixa_etaria(60) == "60+"


def test_adiciona_regiao():
    df = pd.DataFrame({"sg_uf": ["SP", "BA", "AM"]})
    df = adiciona_regiao(df)
    assert list(df["regiao"]) == ["Sudeste", "Nordeste", "Norte"]


def test_adiciona_mes_ano():
    df = pd.DataFrame({"dt_vacina": [datetime(2025, 5, 15)]})
    df = adiciona_mes_ano(df)
    assert df["mes"].iloc[0] == 5
    assert df["ano"].iloc[0] == 2025


def test_tipa_pni():
    df = pd.DataFrame({
        "dt_vacina": ["2025-05-15"],
        "dt_nascimento": ["2000-01-01"],
    })
    df = tipa_pni(df)
    assert pd.api.types.is_datetime64_any_dtype(df["dt_vacina"])
    assert pd.api.types.is_datetime64_any_dtype(df["dt_nascimento"])
    assert df["idade"].iloc[0] > 20


def test_filtra_sih_sim_influenza():
    df = pd.DataFrame({
        "DIAG_PRINC": ["J101", "A09", "J111", "J189", "J109"],
    })
    result = filtra_sih_sim_influenza(df, "DIAG_PRINC")
    assert len(result) == 3
    assert all(result["DIAG_PRINC"].str.startswith(("J10", "J11")))


def test_filtra_sih_sim_influenza_ampliado():
    df = pd.DataFrame({
        "DIAG_PRINC": ["J101", "J189", "A09"],
    })
    from config import CID_INFLUENZA_AMPLIADO
    result = filtra_sih_sim_influenza(df, "DIAG_PRINC", ampliado=True)
    assert len(result) == 2
