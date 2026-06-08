import pandas as pd
import concurrent.futures
import traceback
import sys
import os

from config import UFS
from ingest import load_pni_ufs, PYSUS_DISPONIVEL, download_sih, download_sim
from transform import prepara_pni_completo, agrega_doses, filtra_sih_sim_influenza, merge_cobertura_desfecho

def processar_uf(uf, ano):
    """
    Processa uma UF específica para um ano específico.
    """
    try:
        # 1. PNI
        t_pni = load_pni_ufs([uf], anos=[str(ano)])
        df_pni = prepara_pni_completo(t_pni)
        
        # Salva em cache parquet para o dashboard
        cache_dir = f"data/cache_pni_{ano}"
        os.makedirs(cache_dir, exist_ok=True)
        df_pni.to_parquet(f"{cache_dir}/uf_{uf}.parquet", index=False)
        
        doses_agg = agrega_doses(df_pni, granularidade="uf_mes")
        
        sih_agg = None
        sim_agg = None
        
        if PYSUS_DISPONIVEL:
            # 2. SIH
            sih_dfs = []
            try:
                df_sih = download_sih(uf, ano)
                if not df_sih.empty:
                    df_sih["sg_uf_paciente"] = uf
                    sih_dfs.append(df_sih)
            except Exception as e:
                pass
                
            if sih_dfs:
                df_sih_full = pd.concat(sih_dfs, ignore_index=True)
                df_sih_influenza = filtra_sih_sim_influenza(df_sih_full, col_cid="SP_CIDPRI")
                if "SP_DTINTER" in df_sih_influenza.columns:
                    df_sih_influenza["SP_DTINTER"] = pd.to_datetime(df_sih_influenza["SP_DTINTER"], format="%Y%m%d", errors="coerce")
                    df_sih_influenza["ano_vacina"] = df_sih_influenza["SP_DTINTER"].dt.year
                    df_sih_influenza["mes"] = df_sih_influenza["SP_DTINTER"].dt.month
                else:
                    df_sih_influenza["ano_vacina"] = ano
                    df_sih_influenza["mes"] = 1
                sih_agg = df_sih_influenza.groupby(["sg_uf_paciente", "ano_vacina", "mes"]).size().reset_index(name="internacoes")

            # 3. SIM
            sim_dfs = []
            try:
                df_sim = download_sim(uf, ano)
                if not df_sim.empty:
                    df_sim["sg_uf_paciente"] = uf
                    sim_dfs.append(df_sim)
            except Exception as e:
                pass
                
            if sim_dfs:
                df_sim_full = pd.concat(sim_dfs, ignore_index=True)
                df_sim_influenza = filtra_sih_sim_influenza(df_sim_full, col_cid="CAUSABAS")
                if "DTOBITO" in df_sim_influenza.columns:
                    df_sim_influenza["DTOBITO"] = pd.to_datetime(df_sim_influenza["DTOBITO"], format="%d%m%Y", errors="coerce")
                    df_sim_influenza["ano_vacina"] = df_sim_influenza["DTOBITO"].dt.year
                    df_sim_influenza["mes"] = df_sim_influenza["DTOBITO"].dt.month
                else:
                    df_sim_influenza["ano_vacina"] = ano
                    df_sim_influenza["mes"] = 1
                sim_agg = df_sim_influenza.groupby(["sg_uf_paciente", "ano_vacina", "mes"]).size().reset_index(name="obitos")
                
        # Cruzamento Parcial (outer join por mês/uf)
        df_cruzado_uf = merge_cobertura_desfecho(doses_agg.to_pandas(), sih_agg, sim_agg)
        
        print(f"[{ano}] UF {uf} processada com sucesso! Doses: {len(df_pni)}")
        return df_cruzado_uf

    except Exception as e:
        print(f"[{ano}] Erro processando UF {uf}: {e}")
        return None

import gc

def rodar_pipeline_ano(ano):
    print(f"\\n🚀 Iniciando Pipeline Nacional para o ano de {ano}...")
    arquivo_saida = f"resultado_cruzamento_{ano}.csv"
    
    # Se o arquivo já existe, apagamos para começar do zero
    if os.path.exists(arquivo_saida):
        os.remove(arquivo_saida)
        
    first_write = True
    
    # Processamento puramente sequencial para não estourar a memória (PySUS / PyArrow usam muita RAM)
    for uf in UFS:
        try:
            res = processar_uf(uf, ano)
            if res is not None:
                # Salva incrementalmente para não estourar a memória
                res.to_csv(arquivo_saida, mode='a', header=first_write, index=False)
                first_write = False
            
            # Força a limpeza de memória após cada UF processada
            del res
            gc.collect()
        except Exception as e:
            print(f"[{ano}] Exceção crítica na UF {uf}: {e}")
                
    print(f"✅ Arquivo {arquivo_saida} finalizado com sucesso!")

if __name__ == "__main__":
    if not PYSUS_DISPONIVEL:
        print("Aviso: PySUS não disponível. Internações não serão baixadas.")
        
    for ano in [2025, 2026]:
        rodar_pipeline_ano(ano)
    
    print("\\n🎉 PIPELINE COMPLETO FINALIZADO!")
