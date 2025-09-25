# ===================================================================
# ARQUIVO: ferramentas_dados.py
# Contém todas as funções para processamento e limpeza dos dados.
# ===================================================================
import pandas as pd
import unicodedata
import os
import locale
import re
from datetime import datetime
from sqlalchemy import create_engine, text , inspect
import urllib.parse
from DADOS.sistema_log    import log_print

# --- Configuração de Localidade ---
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    print("Aviso: Localidade 'pt_BR.UTF-8' não encontrada. Usando a localidade padrão.")
    log_print("Aviso: Localidade 'pt_BR.UTF-8' não encontrada. Usando a localidade padrão.")


# ===================================================================
# FUNÇÃO AUXILIAR (Mantida como está)
# ===================================================================
def clean_column_name(col_name):
    """Limpa e formata nomes de colunas para serem compatíveis com MySQL."""
    col_name = unicodedata.normalize('NFKD', str(col_name)).encode('ASCII', 'ignore').decode('utf-8')
    col_name = re.sub(r'\s+', '_', col_name.strip().lower())
    col_name = col_name.replace('/', '_').replace('\\', '_')
    col_name = ''.join(e for e in col_name if e.isalnum() or e == '_')
    return col_name

def get_mysql_type_from_pandas(dtype):
    """
    Converte um tipo de dado do Pandas para um tipo de dado compatível com MySQL.
    Esta é uma nova função auxiliar para a criação dinâmica de colunas.
    """
    if pd.api.types.is_integer_dtype(dtype):
        return 'BIGINT'
    elif pd.api.types.is_float_dtype(dtype):
        return 'DOUBLE'
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return 'DATETIME'
    elif pd.api.types.is_bool_dtype(dtype):
        return 'TINYINT(1)'
    # Para strings ou tipos não reconhecidos, TEXT é uma opção segura.
    else:
        return 'TEXT'


def _processar_pasta(folder_path, tipo_dado):
    """
    Função auxiliar genérica para ler todos os arquivos .xlsx de uma pasta.
    """
    all_data_frames = []
    if not os.path.exists(folder_path):
        print(f"[AVISO] O diretório não existe: {folder_path}")
        log_print(f"[AVISO] O diretório não existe: {folder_path}")
        return all_data_frames
        
    for filename in os.listdir(folder_path):
        if filename.endswith('.xlsx') and not filename.startswith('~'):
            file_path = os.path.join(folder_path, filename)
            df = pd.read_excel(file_path, header=0)
            df['NOME ARQUIVO'] = filename
            all_data_frames.append(df)
    
    if not all_data_frames:
        print(f"AVISO: Nenhum arquivo do tipo '{tipo_dado}' encontrado em {folder_path}.")
        log_print(f"AVISO: Nenhum arquivo do tipo '{tipo_dado}' encontrado em {folder_path}.")
        
    return all_data_frames

# ===================================================================
# FUNÇÃO DE PROCESSAMENTO DE INCREMENTO (COM LÓGICA DINÂMICA)
# ===================================================================
def processar_arquivos_incremento(folder_path, tipo, origem_dados=None):
    """
    Função genérica para processar arquivos de ÁGUA ou ESGOTO com ordenação de colunas dinâmica.
    """
    all_data_frames = _processar_pasta(folder_path, tipo)
    if not all_data_frames:
        return pd.DataFrame()

    df_final = pd.concat(all_data_frames, ignore_index=True)
    
    if 'Mês_Ano' not in df_final.columns:
        print(f"[ERRO] Coluna 'Mês_Ano' não encontrada nos arquivos de {tipo}. Pulando processamento.")
        log_print(f"[ERRO] Coluna 'Mês_Ano' não encontrada nos arquivos de {tipo}. Pulando processamento.")
        return pd.DataFrame()
        
    df_final = df_final[df_final['Mês_Ano'] != 'MUNICIPIO'].copy()

    # Renomeia as colunas de data para um formato padronizado (ex: 'jan/2025')
    rename_mapping = {'Mês_Ano': 'MUNICIPIO'}
    for col in df_final.columns:
        try:
            # Tenta converter o nome da coluna para data.
            # A biblioteca 'dateutil' do pandas é poderosa para inferir formatos.
            data_obj = pd.to_datetime(col, errors='coerce')
            if pd.notna(data_obj):
                # Formata para 'MêsAbreviado/Ano' em minúsculas (ex: 'jan/2025')
                novo_nome = data_obj.strftime('%b/%Y').lower()
                rename_mapping[col] = novo_nome
        except (ValueError, TypeError):
            continue
    df_final.rename(columns=rename_mapping, inplace=True)

    # Converte colunas de meses para tipo numérico (inteiro)
    cols_to_convert = [col for col in df_final.columns if '/' in str(col)]
    for col in cols_to_convert:
        df_final[col] = pd.to_numeric(df_final[col], errors='coerce')
        df_final[col] = df_final[col].fillna(0)
        df_final[col] = df_final[col].astype(int)

    # Calcula o total para o ano corrente de forma dinâmica
    current_year = datetime.now().year
    target_month_cols = [col for col in df_final.columns if f'/{current_year}' in col]
    total_col_name = f'TOTAL (Jan - Atual {current_year})'
    df_final[total_col_name] = df_final[target_month_cols].sum(axis=1, skipna=True) if target_month_cols else 0
    df_final[total_col_name] = df_final[total_col_name].astype(int)

    # Adiciona colunas de metadados
    df_final['TIPO'] = tipo.upper()
    df_final['DATA DE EXTRAÇÃO'] = datetime.now().strftime('%d/%m/%Y %H:%M')
    df_final['ORIGEM DE DADOS'] = origem_dados if origem_dados else f"PAINEL {tipo.upper()}"

    # Extrai a superintendência (SUP) do nome do arquivo
    padrao_regex = fr'{tipo.replace("Á", "A")}\s*[-–]?\s*(.*?)\.xlsx'
    df_final['SUP'] = "SUP " + df_final['NOME ARQUIVO'].str.extract(
        padrao_regex, flags=re.IGNORECASE, expand=False
    ).str.strip().str.upper()

    # ⭐ INÍCIO DA LÓGICA DE ORDENAÇÃO DINÂMICA DE COLUNAS ⭐
    prefix_cols = ["NOME ARQUIVO", "SUP", "TIPO", "MUNICIPIO"]
    suffix_cols = [col for col in df_final.columns if 'TOTAL' in col] + ["DATA DE EXTRAÇÃO", "ORIGEM DE DADOS"]
    date_cols = [col for col in df_final.columns if '/' in str(col)]

    month_map = {
        'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
        'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12
    }

    def sort_key_mes_ano(col_name):
        try:
            month_str, year_str = col_name.split('/')
            return (int(year_str), month_map.get(month_str.lower(), 0))
        except:
            return (9999, 99)

    date_cols.sort(key=sort_key_mes_ano)

    final_column_order = prefix_cols + date_cols + suffix_cols
    existing_cols_in_order = [col for col in final_column_order if col in df_final.columns]
    df_final = df_final[existing_cols_in_order]
    # ⭐ FIM DA LÓGICA DE ORDENAÇÃO DINÂMICA ⭐

    # Limpeza final
    df_final = df_final[df_final['MUNICIPIO'].notna()]
    df_final = df_final[~df_final['MUNICIPIO'].astype(str).str.startswith("Filtros aplicados:", na=False)]
    df_final = df_final[df_final['MUNICIPIO'].astype(str).str.strip().str.upper() != "TOTAL"]
    
    return df_final

def processar_arquivos_nla_nle(file_path, origem_dados=None):
    """
    Lê e processa o arquivo Excel de NLA/NLE a partir de um caminho de arquivo direto.
    Adiciona colunas de metadados: DATA DE EXTRAÇÃO, ORIGEM DE DADOS, ATUALIZADO EM.
    """
    if not os.path.exists(file_path):
        print(f"[AVISO] O arquivo não existe: {file_path}")
        log_print(f"[AVISO] O arquivo não existe: {file_path}")
        return pd.DataFrame()

    df_final = pd.read_excel(file_path)
    
    if 'Ano e Mes' in df_final.columns:
        df_final['Ano e Mes'] = df_final['Ano e Mes'].astype(str).str.strip()
        df_final['Ano e Mes'] = df_final['Ano e Mes'].str.slice(4, 6) + '/' + df_final['Ano e Mes'].str.slice(2, 4)
    
    # Verifica e processa a coluna de tipo de ligação
    if 'TIPO LIGACAO' in df_final.columns:
        df_final.rename(columns={'TIPO LIGACAO': 'TIPO_LIGACAO'}, inplace=True)

    else:
        print("AVISO: Coluna 'Ano e Mes' não encontrada no arquivo NLA/NLE.")
        log_print("AVISO: Coluna 'Ano e Mes' não encontrada no arquivo NLA/NLE.")

    # Adiciona colunas de metadados
    df_final['DATA DE EXTRAÇÃO'] = datetime.now().strftime('%d/%m/%Y %H:%M')
    df_final['ORIGEM DE DADOS'] = origem_dados if origem_dados else "PAINEL NLA/NLE"
    #df_final['ATUALIZADO EM'] = atualizado_em if atualizado_em else ""

    return df_final


def processar_dados_graficos(caminho_do_arquivo):
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
        
        # Remover " de " para converter corretamente
        temp_mes_ano = temp_mes_ano.str.replace(' de ', ' ')
        
        # Converter para datetime usando inferência automática
        df['Mes_Ano'] = pd.to_datetime(temp_mes_ano, format='mixed', dayfirst=False)
        
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
            caminho_salvamento =  r"C:\Users\lcastro.eficien\Desktop\PAINEL ACOMPANHAMENTO\DADOS\Export Painel 3\resultado_com_calculos.xlsx"
            df.to_excel(caminho_salvamento, index=False)
            print(f"\n✅ Arquivo salvo em  '{caminho_salvamento}' salvo com sucesso!")
            log_print(f"\n✅ Arquivo salvo em  '{caminho_salvamento}' salvo com sucesso!")
        except Exception as e:
            print(f"[ERRO] Falha ao salvar o arquivo: {e}")
            log_print(f"[ERRO] Falha ao salvar o arquivo: {e}")
        
        return df
        
    except FileNotFoundError:
        print(f"[ERRO] O arquivo não foi encontrado no caminho especificado: {caminho_do_arquivo}")
        
        return pd.DataFrame()
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro durante o processo: {e}")
        return pd.DataFrame()

def exibir_realizado_2025(df_2025):
    """
    Exibe o resultado do realizado 2025 em formato de tabela.
    
    Args:
        df_2025 (DataFrame): DataFrame com os dados de 2025
    """
    if df_2025 is None or df_2025.empty:
        print("[ERRO] Não há dados de 2025 para exibir.")
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






# ===================================================================
# LÓGICA DE UPLOAD GENÉRICA (LÓGICA PRINCIPAL ATUALIZADA)
# ===================================================================
def upload_df_to_mysql(df_to_upload, mysql_config, date_column, table_name):
    """
    Faz o upload de um DataFrame para uma tabela específica no MySQL.
    Esta função foi ATUALIZADA para lidar com a adição de novas colunas
    em tabelas existentes.
    """
    print(f"\nIniciando o upload do DataFrame para a tabela: `{table_name}`...")

    # Conexão com o banco
    db_connection_str = (
        f"mysql+pymysql://{mysql_config['user']}:{mysql_config['password']}@"
        f"{mysql_config['host']}/{mysql_config['database']}?charset=utf8mb4"
    )
    try:
        engine = create_engine(db_connection_str)
        inspector = inspect(engine)
    except Exception as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        return

    try:
        df = df_to_upload.copy()
        df.columns = [clean_column_name(col) for col in df.columns]
        
        # Adiciona a coluna de data do upload
        if date_column not in df.columns:
            df[date_column] = datetime.now()

        # Se a tabela não existe, cria com PK
        if not inspector.has_table(table_name):
            print(f"  A tabela `{table_name}` não existe. Criando e inserindo dados...")
            df.to_sql(table_name, engine, if_exists='replace', index=False)
            with engine.connect() as connection:
                query = text(f"ALTER TABLE `{table_name}` ADD COLUMN `id` INT AUTO_INCREMENT PRIMARY KEY FIRST;")
                connection.execute(query)
                connection.commit()
            print(f"  Tabela `{table_name}` criada e dados inseridos com sucesso.")

        # Se a tabela já existe
        else:
            print(f"  A tabela `{table_name}` já existe. Verificando esquema...")
            existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
            if 'id' in existing_columns:
                existing_columns.remove('id')
            
            df_columns = df.columns.tolist()

            # ===================================================================
            # INÍCIO DA NOVA LÓGICA DE ATUALIZAÇÃO DE ESQUEMA
            # ===================================================================

            # Verifica se há colunas no DataFrame que não existem na tabela do banco
            colunas_extras_df = set(df_columns) - set(existing_columns)
            
            # Verifica se há colunas na tabela do banco que não existem no DataFrame
            colunas_faltando_df = set(existing_columns) - set(df_columns)

            # Se faltam colunas no DataFrame que são obrigatórias no banco, isso é um erro.
            if colunas_faltando_df:
                print(f"  [ERRO] Esquema incompatível para a tabela `{table_name}`.")
                print(f"  Colunas que existem no banco mas faltam no DataFrame: {colunas_faltando_df}")
                return # Interrompe a execução para esta tabela

            # Se existem colunas novas no DataFrame, vamos adicioná-las à tabela do banco
            if colunas_extras_df:
                print(f"  Detectadas novas colunas no DataFrame: {colunas_extras_df}. Adicionando à tabela...")
                with engine.connect() as connection:
                    for col_name in colunas_extras_df:
                        # Mapeia o tipo do pandas para o tipo do MySQL
                        mysql_type = get_mysql_type_from_pandas(df[col_name].dtype)
                        
                        # Cria e executa a query para adicionar a nova coluna
                        query = text(f"ALTER TABLE `{table_name}` ADD COLUMN `{col_name}` {mysql_type};")
                        connection.execute(query)
                        print(f"    Coluna `{col_name}` (tipo {mysql_type}) adicionada com sucesso.")
                    connection.commit()
            
            # ===================================================================
            # FIM DA NOVA LÓGICA
            # ===================================================================

            print(f"  Esquema verificado/atualizado. Apagando dados antigos (TRUNCATE) e inserindo os novos.")
            with engine.connect() as connection:
                connection.execute(text(f"TRUNCATE TABLE `{table_name}`;"))
                connection.commit()
            
            df.to_sql(table_name, engine, if_exists='append', index=False)
            print(f"  Tabela `{table_name}` atualizada com sucesso.")

    except Exception as e:
        print(f"  [ERRO] Erro inesperado ao processar o DataFrame para a tabela `{table_name}`: {e}")


# ===================================================================
# FUNÇÃO "ORQUESTRADORA" (Versão Refatorada)
# ===================================================================
def subir_multiplos_dfs_para_mysql(df_dict, tabela_prefixo="tb_", database="sandbox", date_column="data_upload"):
    """
    Orquestra o upload de múltiplos DataFrames para o MySQL, chamando a função genérica
    para cada um.
    """
    print("=====================================================")
    print("=== INICIANDO PROCESSO DE UPLOAD DE DATAFRAMES... ===")
    print("=====================================================")

    # Centraliza a configuração do banco
    mysql_config = {
        'host': '10.51.109.226',
        'user': 'root',
        'password': urllib.parse.quote_plus('88538012'),
        'database': database
    }

    # Itera sobre o dicionário de DataFrames
    for nome_base, df in df_dict.items():
        # Limpa o nome para criar um nome de tabela válido
        nome_tabela_limpo = re.sub(r'\s+', '_', nome_base.strip().lower())
        nome_tabela_limpo = ''.join(e for e in nome_tabela_limpo if e.isalnum() or e == '_')
        
        tabela = f"{tabela_prefixo}{nome_tabela_limpo}"
        
        # Chama a função genérica e robusta para fazer o trabalho
        upload_df_to_mysql(
            df_to_upload=df,
            mysql_config=mysql_config,
            date_column=date_column,
            table_name=tabela
        )