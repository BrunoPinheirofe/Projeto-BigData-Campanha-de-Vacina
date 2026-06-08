S3_ENDPOINT = "https://5c499208eebced4e34bd98ffa204f2fb.r2.cloudflarestorage.com"
S3_ACCESS_KEY = "28c72d4b3e1140fa468e367ae472b522"
S3_SECRET_KEY = "2937b2106736e2ba64e24e92f2be4e6c312bba3355586e41ce634b14c1482951"
S3_REGION = "auto"
S3_BUCKET = "healthbr-data/sipni/microdados/"

PERIODO_INICIO = "2025-05-01"
PERIODO_FIM = "2026-05-31"
ANOS = ["2025", "2026"]

UFS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO",
    "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
    "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
]

REGIACOES = {
    "Norte": ["AC", "AP", "AM", "PA", "RO", "RR", "TO"],
    "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "Centro-Oeste": ["DF", "GO", "MT", "MS"],
    "Sudeste": ["ES", "MG", "RJ", "SP"],
    "Sul": ["PR", "RS", "SC"],
}

CID_INFLUENZA = ["J10", "J11"]
CID_INFLUENZA_AMPLIADO = ["J09", "J10", "J11", "J12", "J13", "J14", "J15", "J16", "J17", "J18"]

COLUNAS_PNI = [
    "dt_vacina", "ds_vacina", "co_dose_vacina", "ds_dose_vacina",
    "sg_uf_paciente", "co_municipio_paciente", "tp_sexo_paciente",
    "co_raca_cor_paciente", "nu_idade_paciente",
    "co_vacina_categoria_atendimento", "ds_vacina_categoria_atendimento",
    "co_vacina_grupo_atendimento", "ds_vacina_grupo_atendimento",
]

PNEUMONIA_CIDS = ["J12", "J13", "J14", "J15", "J16", "J17", "J18"]
