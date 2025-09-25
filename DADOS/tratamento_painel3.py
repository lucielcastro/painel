import pandas as pd
from datetime import datetime
import re
from sistema_log import log_print
def processar_dados_painel3(caminho_do_arquivo):
    """
    Processa os dados do painel 3, calculando incrementos e realizado 2025.
    
    Args:
        caminho_do_arquivo (str): Caminho para o arquivo CSV
        
    Returns:
        tuple: (DataFrame processado, DataFrame com realizado 2025)
    """
    
    # Dicionário para traduzir os meses
    meses_map = {
        'janeiro': 'January', 'fevereiro': 'February', 'março': 'March', 'abril': 'April',
        'maio': 'May', 'junho': 'June', 'julho': 'July', 'agosto': 'August',
        'setembro': 'September', 'outubro': 'October', 'novembro': 'November', 'dezembro': 'December'
    }
    
    try:
        # --- 1. LEITURA DO ARQUIVO ---
        try:
            df = pd.read_csv(caminho_do_arquivo, sep=';', encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(caminho_do_arquivo, sep=';', encoding='latin1')

        # --- 2. LIMPEZA E PREPARAÇÃO DOS DADOS ---
        df = df.rename(columns={
            'Superintendencia': 'Superintendencia',
            'Gráfico': 'Grafico',
            'Mês_Ano': 'Mes_Ano',
            'Incremento Água Urbano': 'dados_extraidos_painel_3',
        })
        df.dropna(subset=['Mes_Ano'], inplace=True)

        # ⭐ CORREÇÃO: Converte para numérico e depois para inteiro para evitar floats.
        df['dados_extraidos_painel_3'] = pd.to_numeric(df['dados_extraidos_painel_3'].str.replace('.', '', regex=False), errors='coerce')
        df['dados_extraidos_painel_3'] = df['dados_extraidos_painel_3'].fillna(0)
        df['dados_extraidos_painel_3'] = df['dados_extraidos_painel_3'].astype(int)
        
        # Transformar para formato "março 2025"
        temp_mes_ano = df['Mes_Ano'].str.lower()
        for pt, en in meses_map.items():
            temp_mes_ano = temp_mes_ano.str.replace(pt, en)
        
        # Converter para datetime primeiro
        df['Mes_Ano'] = pd.to_datetime(temp_mes_ano, format='%B de %Y')
        
        # Agora converter de volta para o formato desejado "março 2025"
        df['Mes_Ano'] = df['Mes_Ano'].dt.strftime('%B %Y')
        
        # Traduzir de volta para português
        meses_map_reverso = {v: k for k, v in meses_map.items()}
        for en, pt in meses_map_reverso.items():
            df['Mes_Ano'] = df['Mes_Ano'].str.replace(en, pt, case=False)
        
        # --- 3. CÁLCULO SIMPLES ---
        # Criar coluna CALCULO: último valor - valor anterior
        df['CALCULO'] = df.groupby('Grafico')['dados_extraidos_painel_3'].diff()
        
        # --- 4. CÁLCULO REALIZADO 2025 ---
        # Filtrar apenas dados de 2025
        df_2025 = df[df['Mes_Ano'].str.contains('2025')].copy()
        
        # Calcular soma acumulada da coluna CALCULO de janeiro até o mês atual para cada Superintendencia e Grafico
        df_2025['REALIZADO_2025'] = df_2025.groupby(['Superintendencia', 'Grafico'])['CALCULO'].cumsum()
        
        # Adiciona colunas de metadados
        df['TIPO'] = 'PAINEL_3'
        df['DATA DE EXTRAÇÃO'] = datetime.now().strftime('%d/%m/%Y %H:%M')
        df['ORIGEM DE DADOS'] = 'PAINEL 3'
        
        # --- 5. SALVAMENTO DO ARQUIVO ---
        try:
            nome_arquivo = "resultado_com_calculos.xlsx"
            df.to_excel(nome_arquivo, index=False)
            print(f"\n✅ Arquivo '{nome_arquivo}' salvo com sucesso!")
            log_print(f"\n✅ Arquivo '{nome_arquivo}' salvo com sucesso!")
        except Exception as e:
            print(f"[ERRO] Falha ao salvar o arquivo: {e}")
            log_print(f"[ERRO] Falha ao salvar o arquivo: {e}")
        
        return df, df_2025
        
    except FileNotFoundError:
        print(f"[ERRO] O arquivo não foi encontrado no caminho especificado: {caminho_do_arquivo}")
        log_print(f"[ERRO] O arquivo não foi encontrado no caminho especificado: {caminho_do_arquivo}")
        return None, None
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro durante o processo: {e}")
        log_print(f"[ERRO] Ocorreu um erro durante o processo: {e}")
         # Retorna None para ambos os DataFrames em caso de erro
        return None, None

def exibir_realizado_2025(df_2025):
    """
    Exibe o resultado do realizado 2025 em formato de tabela.
    
    Args:
        df_2025 (DataFrame): DataFrame com os dados de 2025
    """
    if df_2025 is None or df_2025.empty:
        print("[ERRO] Não há dados de 2025 para exibir.")
        log_print("[ERRO] Não há dados de 2025 para exibir.")
         # Retorna para evitar erro
        return
    
    # Mostrar o resultado do realizado 2025
    print("\n📊 REALIZADO 2025 (Soma da coluna CALCULO de janeiro até o mês atual):")
    
    print("=" * 80)
    
    # Agrupar por Superintendencia e Grafico para mostrar o último valor (mês mais recente)
    realizado_2025 = df_2025.groupby(['Superintendencia', 'Grafico'])['REALIZADO_2025'].last().reset_index()
    
    # Ordenar por Superintendencia e Grafico para melhor visualização
    realizado_2025 = realizado_2025.sort_values(['Superintendencia', 'Grafico'])
    
    # Exibir o resultado formatado
    for _, row in realizado_2025.iterrows():
        print(f"{row['Superintendencia']:<35} | {row['Grafico']:<40} | {row['REALIZADO_2025']:>10,.0f}")
    
    print("=" * 80)

# Execução principal
if __name__ == "__main__":
    # Caminho para o seu arquivo CSV
    caminho_do_arquivo = r'C:\Users\lcastro.eficien\Desktop\PAINEL ACOMPANHAMENTO\DADOS\Export Painel 3\dados_extraidos.csv'
    
    # Processar os dados
    df, df_2025 = processar_dados_painel3(caminho_do_arquivo)
    
    if df is not None:
        # Exibir o realizado 2025
        exibir_realizado_2025(df_2025)
        
        print("\n✅ Sucesso! Dados processados com sucesso.")
    else:
        print("[ERRO] Falha no processamento dos dados.")