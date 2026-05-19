# AGENTS.md

## Projeto

Análise de dados de vacinação contra Influenza no Brasil (maio/2025 – maio/2026).

**Fonte principal**: healthbr-data (SI-PNI em Parquet via S3 público).
**Fontes auxiliares**: PySUS para SIH (internações) e SIM (óbitos) — filtrar CID J10-J11.
**Infra**: Streamlit dashboard + notebooks + scripts.

## Comandos

```bash
pip install -e ".[dev]"        # instala dependências + dev
streamlit run src/dashboard.py # sobe dashboard
pytest tests/                  # roda testes
pytest tests/test_ingest.py -v # teste específico
jupyter notebook notebooks/    # abre notebooks
```

## Estrutura

```
src/
  config.py     # credenciais S3, CIDs, UFs, período
  ingest.py     # load PNI via PyArrow S3 + download SIH/SIM via PySUS
  transform.py  # filtra Influenza, tipa, agrega, merge bases
  analysis.py   # cobertura, correlação desfecho, ranking gaps
  viz.py        # gráficos reutilizáveis (plotly + matplotlib)
  dashboard.py  # Streamlit app
notebooks/      # notebooks de exploração e análise
```

## Regras importantes

- Dados PNI ficam no S3 (não baixar localmente — usar partition pruning)
- SIH/SIM exigem download por UF+ano individual via PySUS
  - PySUS NÃO funciona com Python >=3.14 (build do cffi quebra)
  - Se precisar de SIH/SIM, use Python <3.14 ou ignore e analise só PNI
  - Instalar: `pip install pysus` (ou `pip install -e ".[sih-sim]"`)
- `ds_vacina` para Influenza pode variar; filtrar por `'INFLUENZA'` ou `'GRIPE'` (case-insensitive)
- CIDs para desfecho: J10-J11 (J09 é aviária, raro)
- População IBGE necessária para taxas por 100k hab
- Sempre usar `polars` para agregações grandes (>1M linhas), `pandas` para análise final
