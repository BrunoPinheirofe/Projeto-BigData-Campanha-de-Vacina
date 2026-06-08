# AGENTS.md

## Projeto

Análise de dados de vacinação contra Influenza no Brasil (maio/2025 – maio/2026).

**Fonte principal**: healthbr-data (SI-PNI em Parquet via S3 público).
**Fontes auxiliares**: PySUS para SIH (internações) e SIM (óbitos) — filtrar CID J10-J11.
**Infra**: Streamlit dashboard + Jupyter notebooks + scripts.

## Comandos

```bash
uv sync                       # instala dependências (alternativa a pip)
pip install -e ".[dev]"       # instala dependências + dev
streamlit run src/dashboard.py # sobe dashboard
pytest tests/ -v              # roda testes
python src/pipeline_paralelo.py  # pipeline completo (todas UFs, ambos anos)
python src/analise_2025.py       # análise ano 2025 (apenas AC por padrão)
python src/analise_2026.py       # análise ano 2026 (apenas AC por padrão)
ruff check src/               # linter
black src/                    # formatter
```

## Estrutura

```
src/
  config.py              # credenciais S3, CIDs, UFs, período
  ingest.py              # load PNI via PyArrow S3 + SIH/SIM via PySUS
  transform.py           # filtra Influenza, tipa, agrega, merge
  analysis.py            # cobertura, correlação desfecho, ranking gaps
  viz.py                 # gráficos (plotly + matplotlib)
  dashboard.py           # Streamlit app
  pipeline_paralelo.py   # pipeline paralelo (ThreadPoolExecutor, 6 workers)
  analise_2025.py        # script análise 2025 → resultado_cruzamento_2025.csv
  analise_2026.py        # script análise 2026 → resultado_cruzamento_2026.csv
  vacinação/             # LEGADO — análise CSV local (não S3), matplotlib
tests/
  test_ingest.py         # testes de config (UFs, CIDs, S3, colunas)
  test_transform.py      # testes de transform (faixa etária, região, merge)
notebooks/
  01_ingest_explore.ipynb
  02_transform.ipynb
  03_analysis.ipynb
  04_dashboard_proto.ipynb
```

## Regras importantes

- **Testes**: usam `sys.path.insert(0, "src")` — executar da raiz do projeto (`pytest tests/`)
- **Output CSVs** (`resultado_cruzamento_202*.csv`) são ignorados pelo `.gitignore`
- Dados PNI ficam no S3 (não baixar localmente — ler partição específica)
  - Use `load_pni_uf(uf, anos, meses)` — constrói path `ano={ano}/mes={mes}/uf={uf}/`
  - NUNCA tente criar dataset da raiz do bucket (milhões de arquivos, timeout)
  - Esquema real: colunas com sufixo `_paciente` (ex: `sg_uf_paciente`, `tp_sexo_paciente`)
- SIH/SIM exigem download por UF+ano individual via PySUS
  - PySUS NÃO funciona com Python >=3.14 (build do cffi quebra)
  - PySUS é opcional: `PYSUS_DISPONIVEL = False` se não instalado, pipeline segue só com PNI
  - Instalar: `pip install pysus` (ou `pip install -e ".[sih-sim]"`)
- `ds_vacina` para Influenza: filtrar por `'INFLUENZA'` ou `'GRIPE'` (case-insensitive)
  - Nomes reais: `Vacina influenza tetravalente`, `Vacina influenza trivalente`, `Vacina Influenza H1N1`
- CIDs para desfecho: J10-J11 (J09 é aviária, raro)
- População IBGE necessária para taxas por 100k hab (hardcoded em `analysis.py`)
- Usar `polars` para >1M linhas, `pandas` para análise final
- Pipeline validado com AC (Acre) — ~10k registros Influenza/mês
- `src/vacinação/` é LEGADO: analisa CSVs locais baixados manualmente, não conectar ao S3
