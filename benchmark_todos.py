import time
import sys
import glob
import pandas as pd

# Adiciona a pasta src no path
sys.path.insert(0, "src")

from config import UFS

def run_benchmark_todos():
    print("🚀 Iniciando Estimativa/Benchmark para TODOS OS ESTADOS (54 execuções: 27 UFs x 2 anos)\\n")
    
    # Busca os parquets que o pipeline em background já gerou
    arquivos_prontos = glob.glob("data/cache_pni_2025/uf_*.parquet") + glob.glob("data/cache_pni_2026/uf_*.parquet")
    qtd_prontos = len(arquivos_prontos)
    
    if qtd_prontos == 0:
        print("Nenhum cache encontrado ainda. O pipeline ainda está inicializando.")
        return
        
    print(f"⏳ [1/2] Lendo {qtd_prontos} estados que já estão no cache local...")
    
    start_parquet = time.time()
    dfs = [pd.read_parquet(arq) for arq in arquivos_prontos]
    df_full = pd.concat(dfs, ignore_index=True)
    time_parquet = time.time() - start_parquet
    
    linhas = len(df_full)
    media_parquet_por_uf = time_parquet / qtd_prontos
    tempo_estimado_parquet_54 = media_parquet_por_uf * 54
    
    print(f"✅ Concluído! Tempo Parquet para {qtd_prontos} UFs: {time_parquet:.4f} segundos")
    print(f"   Linhas carregadas: {linhas:,}\\n")
    
    print("⏳ [2/2] Estimando o tempo do S3 para 54 partições (com base na média anterior de ~65s por estado)...")
    media_s3_por_uf = 65.8  # valor cravado do nosso benchmark anterior no AC
    tempo_estimado_s3_54 = media_s3_por_uf * 54
    
    print(f"✅ Concluído! O S3 demoraria aproximadamente {tempo_estimado_s3_54:.2f} segundos ({(tempo_estimado_s3_54/60):.2f} minutos).\\n")
    
    print("=========================================")
    print("🏆 ESTIMATIVA FINAL (TODOS OS ESTADOS - 2025 E 2026)")
    print("=========================================")
    print(f"Desempenho Parquet Local : ~ {tempo_estimado_parquet_54:.4f} segundos (Menos de 1 segundo!)")
    print(f"Desempenho S3 na Nuvem   : ~ {tempo_estimado_s3_54:.1f} segundos (Cerca de 59 Minutos!)")
    print("-----------------------------------------")
    
    melhoria = tempo_estimado_s3_54 / tempo_estimado_parquet_54
    print(f"🚀 Ao carregar TODOS os estados, o cache local é {melhoria:.1f} vezes mais RÁPIDO!")
    print("=========================================")

if __name__ == '__main__':
    run_benchmark_todos()
