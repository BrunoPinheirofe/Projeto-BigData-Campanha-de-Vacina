import sys

with open("src/dashboard.py", "r") as f:
    content = f.read()

# Imports
content = content.replace("import io\n", "import io\nimport polars as pl\n")

# carregar_dados_pni
old_carregar = """@st.cache_data
def carregar_dados_pni(ufs):
    if not ufs:
        return pd.DataFrame()

    try:
        with st.spinner(
            f"⏳ Carregando dados para {len(ufs)} UF(s): {', '.join(ufs)}..."
        ):
            dfs = []
            ufs_restantes = []
            
            # Tentar ler dos caches parquets locais gerados pelo pipeline_paralelo
            for uf in ufs:
                for ano in [2025, 2026]:
                    cache_file = f"data/cache_pni_{ano}/uf_{uf}.parquet"
                    if os.path.exists(cache_file):
                        dfs.append(pd.read_parquet(cache_file))
                    else:
                        ufs_restantes.append(f"{uf} ({ano})")

            if ufs_restantes:
                # Mostra um warning caso falte dados, em vez de baixar e travar o app
                st.warning(f"⚠️ Atenção: Os dados de {len(ufs_restantes)} UFs/Anos ainda não foram gerados pelo pipeline. (Ex: {', '.join(ufs_restantes[:3])}...). Execute o 'pipeline_paralelo.py' para gerar o cache local.")

            if dfs:
                return pd.concat(dfs, ignore_index=True)
            else:
                return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar PNI: {e}")
        return pd.DataFrame()"""

new_carregar = """@st.cache_resource
def carregar_dados_pni(ufs):
    if not ufs:
        return pl.DataFrame()

    try:
        with st.spinner(
            f"⏳ Carregando dados para {len(ufs)} UF(s): {', '.join(ufs)}..."
        ):
            dfs = []
            ufs_restantes = []
            
            # Tentar ler dos caches parquets locais gerados pelo pipeline_paralelo
            for uf in ufs:
                for ano in [2025, 2026]:
                    cache_file = f"data/cache_pni_{ano}/uf_{uf}.parquet"
                    if os.path.exists(cache_file):
                        dfs.append(pl.read_parquet(cache_file))
                    else:
                        ufs_restantes.append(f"{uf} ({ano})")

            if ufs_restantes:
                st.warning(f"⚠️ Atenção: Os dados de {len(ufs_restantes)} UFs/Anos ainda não foram gerados pelo pipeline. (Ex: {', '.join(ufs_restantes[:3])}...). Execute o 'pipeline_paralelo.py' para gerar o cache local.")

            if dfs:
                return pl.concat(dfs, how="vertical_relaxed")
            else:
                return pl.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar PNI: {e}")
        return pl.DataFrame()"""
content = content.replace(old_carregar, new_carregar)

# Filtros e aba2 checks
old_filtros = """# Aplicar filtros
if regiao_selecionada != "Todas" and not dados_pni.empty:
    dados_pni = dados_pni[dados_pni["regiao"] == regiao_selecionada]

if faixa_etaria_selecionada and not dados_pni.empty:
    dados_pni = dados_pni[dados_pni["faixa_etaria"].isin(faixa_etaria_selecionada)]"""

new_filtros = """# Aplicar filtros
if regiao_selecionada != "Todas" and not dados_pni.is_empty():
    dados_pni = dados_pni.filter(pl.col("regiao") == regiao_selecionada)

if faixa_etaria_selecionada and not dados_pni.is_empty():
    dados_pni = dados_pni.filter(pl.col("faixa_etaria").is_in(faixa_etaria_selecionada))"""
content = content.replace(old_filtros, new_filtros)

# Aba2
old_aba2_if = """    if not dados_pni.empty:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Distribuição por Faixa Etária")
            df_fe = (
                dados_pni.groupby("faixa_etaria").size().reset_index(name="total_doses")
            )
            st.plotly_chart(viz.barra_faixa_etaria(df_fe), use_container_width=True)

        with c2:
            st.subheader("Distribuição por Sexo")
            df_sex = (
                dados_pni.groupby("tp_sexo_paciente")
                .size()
                .reset_index(name="total_doses")
            )
            df_sex.rename(columns={"tp_sexo_paciente": "co_sexo"}, inplace=True)
            st.plotly_chart(viz.pizza_sexo(df_sex), use_container_width=True)

        st.subheader("Distribuição por Raça/Cor")
        mapa_raca = {
            "1": "Branca",
            "2": "Preta",
            "3": "Amarela",
            "4": "Parda",
            "5": "Indígena",
            "99": "Sem info",
        }
        df_raca = (
            dados_pni.groupby("co_raca_cor_paciente")
            .size()
            .reset_index(name="total_doses")
        )
        df_raca["raca_desc"] = (
            df_raca["co_raca_cor_paciente"].astype(str).map(mapa_raca).fillna("Outros")
        )
        st.plotly_chart(viz.barra_raca(df_raca), use_container_width=True)"""

new_aba2_if = """    if not dados_pni.is_empty():
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Distribuição por Faixa Etária")
            df_fe = (
                dados_pni.group_by("faixa_etaria").agg(pl.len().alias("total_doses"))
            ).to_pandas()
            st.plotly_chart(viz.barra_faixa_etaria(df_fe), use_container_width=True)

        with c2:
            st.subheader("Distribuição por Sexo")
            df_sex = (
                dados_pni.group_by("tp_sexo_paciente")
                .agg(pl.len().alias("total_doses"))
            ).to_pandas()
            df_sex.rename(columns={"tp_sexo_paciente": "co_sexo"}, inplace=True)
            st.plotly_chart(viz.pizza_sexo(df_sex), use_container_width=True)

        st.subheader("Distribuição por Raça/Cor")
        mapa_raca = {
            "1": "Branca",
            "2": "Preta",
            "3": "Amarela",
            "4": "Parda",
            "5": "Indígena",
            "99": "Sem info",
        }
        df_raca = (
            dados_pni.group_by("co_raca_cor_paciente")
            .agg(pl.len().alias("total_doses"))
        ).to_pandas()
        df_raca["raca_desc"] = (
            df_raca["co_raca_cor_paciente"].astype(str).map(mapa_raca).fillna("Outros")
        )
        st.plotly_chart(viz.barra_raca(df_raca), use_container_width=True)"""
content = content.replace(old_aba2_if, new_aba2_if)

with open("src/dashboard.py", "w") as f:
    f.write(content)

