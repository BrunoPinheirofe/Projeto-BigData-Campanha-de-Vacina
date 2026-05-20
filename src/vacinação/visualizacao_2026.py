import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Configuração de estilo
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = [12, 8]

def carregar_dados():
    # Caminhos dos arquivos
    path_jan = "src/vacinação/vacinacao_jan_2026_filtrado.csv"
    path_fev = "src/vacinação/vacinacao_fev_2026_filtrado.csv"
    
    # Carregando com encoding latin1 (comum em arquivos do governo)
    df_jan = pd.read_csv(path_jan, sep=';', encoding='latin1')
    df_fev = pd.read_csv(path_fev, sep=';', encoding='latin1')
    
    # Adicionando coluna de mês para identificação
    df_jan['mes_referencia'] = 'Janeiro'
    df_fev['mes_referencia'] = 'Fevereiro'
    
    return pd.concat([df_jan, df_fev], ignore_index=True)

def gerar_graficos(df):
    # Pasta para salvar as imagens
    output_dir = "src/vacinação/graficos"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Gerando gráficos em {output_dir}...")

    # 1. Comparativo Mensal (Total de Doses)
    plt.figure()
    sns.countplot(data=df, x='mes_referencia', hue='mes_referencia', palette='viridis', legend=False)
    plt.title('Total de Vacinas Aplicadas (Jan vs Fev 2026)', fontsize=15)
    plt.ylabel('Quantidade de Doses')
    plt.xlabel('Mês')
    plt.savefig(f"{output_dir}/comparativo_mensal.png")
    plt.close()
    print("- Gráfico de comparativo mensal gerado.")

    # 2. Distribuição por Grupo de Atendimento (Top 10)
    plt.figure()
    top_grupos = df['ds_vacina_grupo_atendimento'].value_counts().nlargest(10).index
    df_top_grupos = df[df['ds_vacina_grupo_atendimento'].isin(top_grupos)]
    sns.countplot(data=df_top_grupos, y='ds_vacina_grupo_atendimento', hue='mes_referencia', palette='magma')
    plt.title('Top 10 Grupos de Atendimento por Mês', fontsize=15)
    plt.ylabel('Grupo de Atendimento')
    plt.xlabel('Quantidade de Doses')
    plt.savefig(f"{output_dir}/grupos_atendimento.png")
    plt.close()
    print("- Gráfico de grupos de atendimento gerado.")

    # 3. Perfil Etário (Histograma)
    plt.figure()
    sns.histplot(data=df, x='nu_idade_paciente', bins=20, kde=True, color='skyblue')
    plt.title('Distribuição de Idade dos Vacinados', fontsize=15)
    plt.ylabel('Frequência')
    plt.xlabel('Idade (Anos)')
    plt.savefig(f"{output_dir}/perfil_etario.png")
    plt.close()
    print("- Gráfico de perfil etário gerado.")

    # 4. Distribuição por Sexo
    plt.figure(figsize=(8, 8))
    df['tp_sexo_paciente'].value_counts().plot.pie(autopct='%1.1f%%', colors=['#ff9999','#66b3ff'], startangle=90)
    plt.title('Distribuição por Sexo dos Vacinados', fontsize=15)
    plt.ylabel('')
    plt.savefig(f"{output_dir}/distribuicao_sexo.png")
    plt.close()
    print("- Gráfico de distribuição por sexo gerado.")

if __name__ == "__main__":
    try:
        dados = carregar_dados()
        gerar_graficos(dados)
        print("\nSucesso! Todos os gráficos foram salvos na pasta 'src/vacinação/graficos/'.")
    except Exception as e:
        print(f"Erro ao processar dados: {e}")
