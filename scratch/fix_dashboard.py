import sys

with open("src/dashboard.py", "r") as f:
    content = f.read()

# 1. Fix warnings
content = content.replace("use_container_width=True", 'width="stretch"')

# 2. Fix OOM by using LazyFrames
content = content.replace("pl.read_parquet", "pl.scan_parquet")

# Remove is_empty() checks which don't work on LazyFrames. We'll replace `dados_pni.is_empty()` with `dados_pni is None`
# First, change carregar_dados_pni to return None if no data
old_return = """            if dfs:
                return pl.concat(dfs, how="vertical_relaxed")
            else:
                return pl.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar PNI: {e}")
        return pl.DataFrame()"""
new_return = """            if dfs:
                return pl.concat(dfs, how="vertical_relaxed")
            else:
                return None
    except Exception as e:
        st.error(f"Erro ao carregar PNI: {e}")
        return None"""
content = content.replace(old_return, new_return)

# Replace all `not dados_pni.is_empty():` with `dados_pni is not None:`
content = content.replace("not dados_pni.is_empty():", "dados_pni is not None:")

# Replace `not df_a.is_empty():` with `df_a is not None:`? Wait, df_a is a LazyFrame, so it's never None.
# If we filter a LazyFrame, it doesn't execute. So we can't check is_empty.
# Instead of `if not df_a.is_empty():`, we can just execute the query and check if the result is empty!
# But since we only pass aggregated data to Plotly, if the aggregation is empty, Plotly handles it or we can check the pandas df.
# Let's manually fix the lazy frame collections using Python string replacements.

content = content.replace(".to_pandas()", ".collect().to_pandas()")

with open("src/dashboard.py", "w") as f:
    f.write(content)

