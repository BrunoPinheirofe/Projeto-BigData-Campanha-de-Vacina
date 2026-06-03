import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob

# Configuração de estilo
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = [12, 8]

# Mapeamento de Regiões
REGIOES = {
    'Norte': ['AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO'],
    'Nordeste': ['AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'],
    'Centro-Oeste': ['DF', 'GO', 'MT', 'MS'],
    'Sudeste': ['ES', 'MG', 'RJ', 'SP'],
    'Sul': ['PR', 'RS', 'SC']
}
uf_to_regiao = {uf: reg for reg, ufs in REGIOES.items() for uf in ufs}

def processar_arquivos_2025():
    path_pattern = "src/vacinação/vacinacao_*_2025_gripe*.csv"
    arquivos = glob.glob(path_pattern)
    arquivos.sort()
    
    resumos_mensais = []
    resumos_uf = []
    resumos_sexo = []
    resumos_grupo = []
    dados_idade_uf = []

    colunas_interesse = [
        'sg_uf_paciente', 
        'tp_sexo_paciente', 
        'nu_idade_paciente', 
        'dt_vacina', 
        'ds_vacina_grupo_atendimento'
    ]

    print(f"Encontrados {len(arquivos)} arquivos para processamento.")

    for arquivo in arquivos:
        nome_arquivo = os.path.basename(arquivo)
        print(f"Processando: {nome_arquivo}...")
        
        try:
            chunk_iter = pd.read_csv(arquivo, sep=';', encoding='latin1', 
                                    usecols=colunas_interesse, low_memory=False, chunksize=500000)
            
            for df in chunk_iter:
                df = df.copy() # Evitar SettingWithCopyWarning
                df['dt_vacina'] = pd.to_datetime(df['dt_vacina'], errors='coerce')
                df['mes_referencia'] = df['dt_vacina'].dt.strftime('%Y-%m')
                
                # Agregações
                resumos_mensais.append(df['mes_referencia'].value_counts().reset_index())
                resumos_uf.append(df['sg_uf_paciente'].value_counts().reset_index())
                resumos_sexo.append(df['tp_sexo_paciente'].value_counts().reset_index())
                resumos_grupo.append(df['ds_vacina_grupo_atendimento'].value_counts().reset_index())
                
                # Amostragem para análise de distribuição (Big Data sample)
                sample = df[['sg_uf_paciente', 'nu_idade_paciente']].sample(frac=0.02).copy()
                sample['regiao'] = sample['sg_uf_paciente'].map(uf_to_regiao)
                dados_idade_uf.append(sample)
            
        except Exception as e:
            print(f"Erro ao processar {nome_arquivo}: {e}")

    print("Consolidando dados...")
    
    def consolidar(lista_resumos, col_id):
        df_temp = pd.concat(lista_resumos, ignore_index=True)
        # Identificar a coluna de contagem
        count_col = [c for c in df_temp.columns if c != col_id][0]
        return df_temp.groupby(col_id)[count_col].sum().reset_index().rename(columns={count_col: 'total'})

    df_mensal = consolidar(resumos_mensais, 'mes_referencia').sort_values('mes_referencia')
    df_uf = consolidar(resumos_uf, 'sg_uf_paciente').sort_values('total', ascending=False)
    df_sexo = consolidar(resumos_sexo, 'tp_sexo_paciente')
    df_grupo = consolidar(resumos_grupo, 'ds_vacina_grupo_atendimento').sort_values('total', ascending=False)
    df_amostra_idade = pd.concat(dados_idade_uf, ignore_index=True)

    # Agregação por região
    df_uf['regiao'] = df_uf['sg_uf_paciente'].map(uf_to_regiao)
    df_regiao = df_uf.groupby('regiao')['total'].sum().reset_index().sort_values('total', ascending=False)

    return df_mensal, df_uf, df_sexo, df_grupo, df_amostra_idade, df_regiao

def gerar_graficos_avancados(df_mensal, df_uf, df_sexo, df_grupo, df_amostra_idade, df_regiao):
    output_dir = "src/vacinação/graficos"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Gerando gráficos avançados em {output_dir}...")

    # 1. Tendência Temporal
    plt.figure()
    sns.lineplot(data=df_mensal, x='mes_referencia', y='total', marker='o', color='teal')
    plt.title('Tendência Temporal de Vacinação (2025)', fontsize=15)
    plt.xticks(rotation=45)
    plt.ylabel('Doses')
    plt.tight_layout()
    plt.savefig(f"{output_dir}/2025_01_tendencia_temporal.png")
    
    # 2. Cobertura por Região
    plt.figure()
    sns.barplot(data=df_regiao, x='total', y='regiao', palette='rocket', hue='regiao', legend=False)
    plt.title('Distribuição de Vacinas por Região', fontsize=15)
    plt.xlabel('Total de Doses')
    plt.savefig(f"{output_dir}/2025_02_cobertura_regiao.png")

    # 3. Densidade Etária (KDE)
    plt.figure()
    sns.kdeplot(data=df_amostra_idade, x='nu_idade_paciente', fill=True, color='purple', bw_adjust=0.5)
    plt.title('Perfil de Densidade Etária (Amostra Analítica)', fontsize=15)
    plt.xlabel('Idade')
    plt.ylabel('Densidade')
    plt.savefig(f"{output_dir}/2025_03_densidade_etaria.png")

    # 4. Box Plot de Idade por Região
    plt.figure()
    sns.boxplot(data=df_amostra_idade, x='nu_idade_paciente', y='regiao', palette='Set2', hue='regiao', legend=False)
    plt.title('Variabilidade Etária por Região (Outliers e Dispersão)', fontsize=15)
    plt.xlabel('Idade')
    plt.savefig(f"{output_dir}/2025_04_boxplot_regioes.png")

    # 5. Top 10 Grupos
    plt.figure()
    sns.barplot(data=df_grupo.head(10), x='total', y='ds_vacina_grupo_atendimento', palette='mako', hue='ds_vacina_grupo_atendimento', legend=False)
    plt.title('Top 10 Grupos Prioritários Impactados', fontsize=15)
    plt.xlabel('Doses')
    plt.tight_layout()
    plt.savefig(f"{output_dir}/2025_05_grupos_prioritarios.png")

if __name__ == "__main__":
    try:
        dados = processar_arquivos_2025()
        gerar_graficos_avancados(*dados)
        print("\nSucesso: Gráficos de Big Data atualizados e corrigidos!")
    except Exception as e:
        print(f"Erro: {e}")
