# ===================================================================
# ARQUIVO: main.py
# DESCRIÇÃO: Orquestra todo o processo de ETL.
# 1. Processa os arquivos de dados extraídos.
# 2. Enriquece os dados com metadados.
# 3. Sobe os DataFrames para o banco de dados MySQL.
# 4. Salva o resultado final em um arquivo Excel consolidado.
# ===================================================================

import os
import pandas as pd
import warnings
from datetime import datetime

# --- IMPORTAÇÃO DAS FUNÇÕES ---
# Certifique-se de que o arquivo ferramentas_dados.py está na pasta DADOS
# e que ele contém as funções de processamento e a nova função de upload.
# A importação da função de upload foi atualizada para o nome novo e mais claro.
from DADOS.ferramentas_dados import (
#from ferramentas_dados import (
    processar_arquivos_incremento, 
    processar_arquivos_nla_nle,
    processar_dados_graficos,
    subir_multiplos_dfs_para_mysql # Nome da nova função robusta
)

# Ignora avisos que podem poluir a saída do console
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

def executar_processamento_dados(data_atualizacao_painel):
    """
    Função principal que orquestra todo o processo de ETL de dados.

    Args:
        data_atualizacao_painel (str): A data/hora de atualização extraída
                                       do painel Power BI pelo Selenium.
    """
    print("=============================================")
    print("=== INICIANDO PROCESSAMENTO DE DADOS (ETL) ===")
    print("=============================================")

    # --- 1. Definição de Caminhos ---
    base_path = r"C:\Users\lcastro.eficien\Desktop\PAINEL ACOMPANHAMENTO"
    caminho_painel_1 = os.path.join(base_path, "DADOS", "Export Painel 1", "DADOS PAINEL 1.xlsx")
    caminho_agua = os.path.join(base_path, "DADOS", "Export Painel 2", "AGUA")
    caminho_esgoto = os.path.join(base_path, "DADOS", "Export Painel 2", "ESGOTO")
    caminho_graficos = os.path.join(base_path, "DADOS", "Export Painel 3", "dados_extraidos.csv")
    arquivo_saida = os.path.join(base_path, 'PAINEL ACOMPANHAMENTO.xlsx')

    # --- CAPTURA DE METADADOS ---
    data_extracao_geral = datetime.now()
    data_atualizacao_painel = datetime.now()
    print(f"Data de Extração (Timestamp do Robô): {data_extracao_geral.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Data de Atualização (Vinda do Painel): {data_atualizacao_painel}")


    # --- 2. Processamento e Enriquecimento dos Dados ---
    print("\nProcessando arquivos de ESGOTO...")
    df_esgoto = processar_arquivos_incremento(caminho_esgoto, 'ESGOTO', origem_dados="Power BI - Incremento Esgoto")
    if not df_esgoto.empty:
        df_esgoto['data_extracao_etl'] = data_extracao_geral
        df_esgoto['data_atualizacao_painel'] = pd.to_datetime(data_atualizacao_painel)

    print("\nProcessando arquivos de ÁGUA...")
    df_agua = processar_arquivos_incremento(caminho_agua, 'ÁGUA', origem_dados="Power BI - Incremento Água")
    if not df_agua.empty:
        df_agua['data_extracao_etl'] = data_extracao_geral
        df_agua['data_atualizacao_painel'] = pd.to_datetime(data_atualizacao_painel)

    print("\nProcessando arquivos de NLA/NLE...")
    df_nla_nle = processar_arquivos_nla_nle(caminho_painel_1, origem_dados="Power BI - Novas Ligações")
    if not df_nla_nle.empty:
        df_nla_nle['data_extracao_etl'] = data_extracao_geral
        df_nla_nle['data_atualizacao_painel'] = pd.to_datetime(data_atualizacao_painel)


    print("\nProcessando arquivos de GRÁFICOS (Painel 3)...")
    df_graficos = processar_dados_graficos(caminho_graficos)
    
    if not df_graficos.empty:
        df_graficos['data_extracao_etl'] = data_extracao_geral
        df_graficos['data_atualizacao_painel'] = pd.to_datetime(data_atualizacao_painel)


    # Cria o dicionário com os dataframes já enriquecidos
    datasets = {
        "agua": df_agua,
        "esgoto": df_esgoto,
        "nla_nle": df_nla_nle,
        "dados_realizados": df_graficos
    }

    # --- 3. Upload para o Banco de Dados ---
    # Esta etapa agora acontece ANTES da escrita do Excel.
    # Chamando a função correta e robusta que criamos.
    subir_multiplos_dfs_para_mysql(datasets, tabela_prefixo="tb_", database="sandbox")
    
    # --- 4. Salvamento dos Resultados em Excel ---
    # COMENTADO TEMPORARIAMENTE - Atualização das abas desabilitada
    # print(f"\nAtualizando abas no arquivo Excel: {arquivo_saida}")
    # mode = 'a' if os.path.exists(arquivo_saida) else 'w'
    # extra_params = {'if_sheet_exists': 'replace'} if mode == 'a' else {}

    # try:
    #     with pd.ExcelWriter(arquivo_saida, engine='openpyxl', mode=mode, **extra_params) as writer:
    #         total = len(datasets)
    #         print("Iniciando a escrita no arquivo Excel...")
    #         for i, (sheet_name, df) in enumerate(datasets.items(), 1):
    #             percent = int((i / total) * 100)
    #             bar = '█' * (percent // 10) + '-' * (10 - percent // 10)
    #             print(f"[{bar}] {percent}% - Processando aba '{sheet_name}'")
    #             
    #             if df is not None and not df.empty:
    #                 df.to_excel(writer, sheet_name=sheet_name, index=False)
    #                 print(f" -> Aba '{sheet_name}' salva com sucesso.")
    #             else:
    #                 print(f" -> Nenhum dado para a aba '{sheet_name}'. Pulando.")
    
    # except Exception as e:
    #     print(f"[ERRO] Falha ao salvar o arquivo Excel: {e}")
    
    print("📝 Salvamento em Excel temporariamente desabilitado.")

    print("\n=============================================")
    print("===      PROCESSAMENTO FINALIZADO         ===")
    print("=============================================")


if __name__ == "__main__":
    
    print("\n--- INICIANDO ORQUESTRADOR PRINCIPAL ---")
    
    # Exemplo de como você chamaria esta função a partir do seu script de scraping.
    # O valor '2025-07-28 10:00:00' deve ser a string que o Selenium extraiu do painel.
    data_extraida_do_painel = "2025-07-28 10:00:00" # Exemplo
    
    executar_processamento_dados(data_atualizacao_painel=data_extraida_do_painel)
    
    print("\n--- PROCESSO FINALIZADO ---")
