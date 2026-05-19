# Análise de Vacinação contra Influenza no Brasil

Análise de dados de vacinação contra Influenza no Brasil no período de **maio/2025 a maio/2026**, utilizando dados do SI-PNI (Programa Nacional de Imunizações) e correlação com desfechos de internações (SIH) e óbitos (SIM).

## Fontes de Dados

| Fonte | Dado | Acesso |
|---|---|---|
| [healthbr-data](https://huggingface.co/datasets/SidneyBissoli/sipni-microdados) | Doses aplicadas (SI-PNI) | S3 público (Parquet) |
| [PySUS](https://github.com/AlertaDengue/pySUS) | Internações (SIH) e Óbitos (SIM) | Download por UF+ano |
| IBGE | População residente | Projeções intercensitárias |

## Estrutura

```
src/
  config.py     # Credenciais S3, CIDs, UFs, período
  ingest.py     # Load PNI via PyArrow S3 + SIH/SIM via PySUS
  transform.py  # Filtra Influenza, tipa, agrega, merge
  analysis.py   # Cobertura, correlação desfecho, ranking gaps
  viz.py        # Gráficos (plotly + matplotlib)
  dashboard.py  # Streamlit app
notebooks/      # Notebooks de exploração e análise
tests/          # Testes unitários
```

## Setup

```bash
pip install -e ".[dev]"
```

## Uso

```bash
# Dashboard
streamlit run src/dashboard.py

# Notebooks
jupyter notebook notebooks/

# Testes
pytest tests/ -v
```

## Análises

1. Cobertura vacinal contra influenza por UF, município e grupo demográfico
2. Correlação entre cobertura e desfechos graves (internações/óbitos)
3. Identificação de regiões e públicos com baixa adesão
4. Ranking de municípios críticos para priorização

## Licença

Dados: CC-BY 4.0 (Ministério da Saúde / OpenDATASUS).
Código: MIT.
