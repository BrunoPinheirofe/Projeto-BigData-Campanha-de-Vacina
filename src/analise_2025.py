import pandas as pd
from ingest import load_pni_ufs, download_todas_sih, download_todas_sim, PYSUS_DISPONIVEL
from transform import prepara_pni_completo, agrega_doses, filtra_sih_sim_influenza, merge_cobertura_desfecho
from analysis import gap_score

def analisar_2025(apenas_ac=True):
    print("Iniciando carregamento do PNI para o ano de 2025...")
    ufs_alvo = ["AC"] if apenas_ac else None
    
    try:
        t_pni = load_pni_ufs(ufs_alvo if ufs_alvo else ["AC"], anos=["2025"])
        df_pni = prepara_pni_completo(t_pni)
        doses_agg = agrega_doses(df_pni, granularidade="uf_mes")
        
        print(f"\nPNI carregado com sucesso. Total de doses (amostra): {df_pni.shape[0]}")
        
        sih_agg = None
        sim_agg = None
        
        if PYSUS_DISPONIVEL:
            print("\nBaixando dados do SIH e SIM (casos de gripe) para o ano de 2025 via PySUS...")
            from ingest import download_sih, download_sim
            
            sih_dfs = []
            sim_dfs = []
            
            for uf in (ufs_alvo if ufs_alvo else ["AC"]):
                print(f"  Buscando {uf}...")
                try:
                    df_sih = download_sih(uf, 2025)
                    if not df_sih.empty:
                        df_sih["sg_uf_paciente"] = uf
                        sih_dfs.append(df_sih)
                except Exception as e:
                    print(f"  Erro SIH {uf}: {e}")
                    
                try:
                    df_sim = download_sim(uf, 2025)
                    if not df_sim.empty:
                        df_sim["sg_uf_paciente"] = uf
                        sim_dfs.append(df_sim)
                except Exception as e:
                    print(f"  Erro SIM {uf}: {e}")
            
            if sih_dfs:
                df_sih_full = pd.concat(sih_dfs, ignore_index=True)
                df_sih_influenza = filtra_sih_sim_influenza(df_sih_full, col_cid="SP_CIDPRI")
                
                if "SP_DTINTER" in df_sih_influenza.columns:
                    df_sih_influenza["SP_DTINTER"] = pd.to_datetime(df_sih_influenza["SP_DTINTER"], format="%Y%m%d", errors="coerce")
                    df_sih_influenza["ano_vacina"] = df_sih_influenza["SP_DTINTER"].dt.year
                    df_sih_influenza["mes"] = df_sih_influenza["SP_DTINTER"].dt.month
                else:
                    df_sih_influenza["ano_vacina"] = 2025
                    df_sih_influenza["mes"] = 1
                
                sih_agg = df_sih_influenza.groupby(["sg_uf_paciente", "ano_vacina", "mes"]).size().reset_index(name="internacoes")
                
            if sim_dfs:
                df_sim_full = pd.concat(sim_dfs, ignore_index=True)
                df_sim_influenza = filtra_sih_sim_influenza(df_sim_full, col_cid="CAUSABAS")
                
                if "DTOBITO" in df_sim_influenza.columns:
                    df_sim_influenza["DTOBITO"] = pd.to_datetime(df_sim_influenza["DTOBITO"], format="%d%m%Y", errors="coerce")
                    df_sim_influenza["ano_vacina"] = df_sim_influenza["DTOBITO"].dt.year
                    df_sim_influenza["mes"] = df_sim_influenza["DTOBITO"].dt.month
                else:
                    df_sim_influenza["ano_vacina"] = 2025
                    df_sim_influenza["mes"] = 1
                
                sim_agg = df_sim_influenza.groupby(["sg_uf_paciente", "ano_vacina", "mes"]).size().reset_index(name="obitos")
                
        else:
            print("\nAVISO: PySUS não disponível. Não será possível cruzar com SIH/SIM.")
        
        print("\nRealizando o cruzamento (merge) dos dados...")
        df_cruzado = merge_cobertura_desfecho(doses_agg.to_pandas(), sih_agg, sim_agg)
        
        print("\n=== RESULTADO DO CRUZAMENTO (VACINAÇÃO vs CASOS DE GRIPE) ===")
        print(df_cruzado.to_string())
        
        print("\n=== GAP SCORE (Prioridade de intervenção) ===")
        doses_uf = df_pni.groupby("sg_uf_paciente").size().reset_index(name="total_doses")
        internacoes_uf = None
        if sih_agg is not None:
            internacoes_uf = sih_agg.groupby("sg_uf_paciente")["internacoes"].sum().reset_index(name="total_internacoes")
            
        gap_df = gap_score(doses_uf, internacoes_uf)
        print(gap_df.to_string())
        
        print("\nExportando resultado para 'resultado_cruzamento_2025.csv'...")
        df_cruzado.to_csv("resultado_cruzamento_2025.csv", index=False)
        print("Finalizado!")
        
    except Exception as e:
        print(f"\nErro durante a execução: {e}")

if __name__ == "__main__":
    analisar_2025(apenas_ac=True)
