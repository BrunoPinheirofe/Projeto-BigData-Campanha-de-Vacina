import time
import sys
import pandas as pd

# Adiciona a pasta src no path para poder importar os módulos
sys.path.insert(0, "src")

from ingest import load_pni_ufs
from transform import prepara_pni_completo

def run_benchmark():
    uf = "AC"
    ano = "2025"
    
    print(f"🚀 Iniciando Benchmark de Performance: S3 (Remoto) vs Parquet (Local Cache)")
    print(f"📍 Alvo: Estado do {uf} - Ano {ano}\\n")
    
    # --- Teste 1: Leitura do Cache Local (Parquet) ---
    print("⏳ [1/2] Lendo do Cache Local (Parquet)...")
    start_parquet = time.time()
    df_parquet = pd.read_parquet(f"data/cache_pni_{ano}/uf_{uf}.parquet")
    time_parquet = time.time() - start_parquet
    print(f"✅ Concluído! Tempo Parquet: {time_parquet:.4f} segundos")
    print(f"   Linhas carregadas: {len(df_parquet):,}\\n")
    
    # --- Teste 2: Download Direto do S3 ---
    print("⏳ [2/2] Baixando do DataLake S3 e processando dados (como era antes)...")
    start_s3 = time.time()
    # Estamos pegando apenas 1 ano para ser mais rápido o teste (antes pegava 2025 e 2026 juntos)
    t_pni = load_pni_ufs([uf], anos=[ano])
    df_s3 = prepara_pni_completo(t_pni)
    time_s3 = time.time() - start_s3
    print(f"✅ Concluído! Tempo S3: {time_s3:.4f} segundos")
    print(f"   Linhas carregadas: {len(df_s3):,}\\n")
    
    # --- Resultados Finais ---
    print("=========================================")
    print("🏆 RESULTADOS DO BENCHMARK")
    print("=========================================")
    print(f"Desempenho Parquet Local : {time_parquet:.4f} s")
    print(f"Desempenho S3 na Nuvem   : {time_s3:.4f} s")
    print("-----------------------------------------")
    
    if time_parquet > 0:
        melhoria = time_s3 / time_parquet
        print(f"🚀 O novo método (Parquet) é {melhoria:.1f} vezes mais RÁPIDO!")
    print("=========================================")

if __name__ == '__main__':
    run_benchmark()
