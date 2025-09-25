import pandas as pd
from sqlalchemy import create_engine, text
import urllib.parse
from datetime import datetime
import locale
import os

# --- Configuração do Banco de Dados ---
MYSQL_HOST = '10.51.109.226'
MYSQL_USER = 'root'
MYSQL_PASSWORD = urllib.parse.quote_plus('88538012')
MYSQL_DATABASE = "sandbox"

db_connection_str = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}?charset=utf8mb4"
)
engine = create_engine(db_connection_str,pool_recycle=3600 )


def fetch_kpi_data():
    """
    Busca os dados agregados para os cards de KPI.
    Para Água e Esgoto, calcula a diferença entre o 1º e 2º lugar do ranking.
    """
    kpis = {'total_agua': 0, 'total_esgoto': 0, 'nla': 0, 'nle': 0, 'total_nla_nle': 0}
    try:
        # --- KPI Incrementos Água: Diferença entre 1º e 2º lugar ---
        print("[INFO] Calculando KPI de diferença para Incrementos Água...")
        
        ranking_agua_top2 = fetch_ranking_data('tb_agua','total_jan__atual_2025', limit=2)
        
        if len(ranking_agua_top2) >= 2:
            
            primeiro_lugar_agua = ranking_agua_top2.iloc[0]['total']
            segundo_lugar_agua = ranking_agua_top2.iloc[1]['total']
            # O valor do KPI agora é a diferença
            kpis['total_agua'] = primeiro_lugar_agua - segundo_lugar_agua
        
        else:
            # Se houver menos de 2 superintendências, a diferença é 0.
            kpis['total_agua'] = 0
        # --- KPI Incrementos Esgoto: Diferença entre 1º e 2º lugar ---
        print("[INFO] Calculando KPI de diferença para Incrementos Esgoto...")
        
        ranking_esgoto_top2 = fetch_ranking_data('tb_esgoto','total_jan__atual_2025', limit=2)
        
        if len(ranking_esgoto_top2) >= 2:
            
            primeiro_lugar_esgoto = ranking_esgoto_top2.iloc[0]['total']
            segundo_lugar_esgoto = ranking_esgoto_top2.iloc[1]['total']
            # O valor do KPI agora é a diferença
            kpis['total_esgoto'] = primeiro_lugar_esgoto - segundo_lugar_esgoto
        
        else:
            kpis['total_esgoto'] = 0

        #RESULTADO DO INCREMENTOS ESTÃO CORRETOs, AGORA VAMOS TRABALAHAR O NLA NLE
        ranking_nla_nle = fetch_ranking_nla_nle()

        if not ranking_nla_nle.empty:
            primeiro_lugar_nla = ranking_nla_nle['total_agua'].iloc[0]
            segundo_lugar_nla = ranking_nla_nle['total_agua'].iloc[1]
            kpis['nla'] = primeiro_lugar_nla - segundo_lugar_nla

            primeiro_lugar_nle = ranking_nla_nle['total_esgoto'].iloc[0]
            segundo_lugar_nle = ranking_nla_nle['total_esgoto'].iloc[1]
            kpis['nle'] = primeiro_lugar_nle - segundo_lugar_nle
            kpis['total_nla_nle'] = kpis['nla'] + kpis['nle']
        else:
            kpis['nla'] = 0
            kpis['nle'] = 0
        return kpis
    except Exception as e:
        print(f"[ERRO] Falha ao buscar dados de KPI: {e}")
        return kpis
    
def fetch_ranking_data(table_name, value_col, limit=10):

    """Busca dados para as tabelas de ranking de Água e Esgoto."""
    # value_col já deve ser 'total_jan__atual_2025' agora
    query = text(f"SELECT sup, SUM(`{value_col}`) as total FROM {table_name} GROUP BY sup ORDER BY total DESC LIMIT {limit}")
    try:
        return pd.read_sql(query, engine)
    except Exception as e:
        print(f"[ERRO] Falha ao buscar dados de ranking para '{table_name}': {e}")
        return pd.DataFrame(columns=['sup', 'total'])

def fetch_ranking_nla_nle(limit=10):
    """
    Busca os dados de Novas Ligações, somando a coluna `quantidade`,
    e gera o ranking geral, ignorando superintendências vazias.
    """
    query = text(f"""
        SELECT
            ds_cd_superintendencia,
            SUM(CASE WHEN tipo_ligacao = 'Ligação Nova Água' THEN quantidade ELSE 0 END) AS total_agua,
            SUM(CASE WHEN tipo_ligacao = 'Ligação Nova Esgoto' THEN quantidade ELSE 0 END) AS total_esgoto,
            SUM(quantidade) AS total_geral
        FROM
            tb_nla_nle
        WHERE
            ds_cd_superintendencia IS NOT NULL AND ds_cd_superintendencia != ''
        GROUP BY
            ds_cd_superintendencia
        ORDER BY
            total_geral DESC
        LIMIT {limit}
    """)
    try:
        print("[INFO] Buscando dados para o ranking de Novas Ligações (tb_nla_nle)...")
        ranking_df = pd.read_sql(query, engine)
        if not ranking_df.empty:
            ranking_df[['total_agua', 'total_esgoto', 'total_geral']] = ranking_df[['total_agua', 'total_esgoto', 'total_geral']].astype(int)
            ranking_df = ranking_df.rename(columns={'ds_cd_superintendencia': 'superintendencia'})
        #print(ranking_df.head())
        return ranking_df
    except Exception as e:
        print(f"[ERRO] Falha ao criar ranking geral a partir de 'tb_nla_nle': {e}")
        print("[AVISO] Verifique se as colunas 'ds_cd_superintendencia', 'tipo_ligacao' e 'quantidade' existem na tabela.")
        return pd.DataFrame()
    
def fetch_dados_graficos():
    """
    Busca dados para os gráficos usando CTE para calcular realizado acumulado e inclui as metas.
    Combina dados de realizado (sandbox.tb_dados_realizados) com metas da tabela tb_meta_2025.
    Só inclui superintendências que têm metas definidas.
    """
    # Query para buscar as metas da tabela
    query_metas = text("""
        SELECT 
            sup,
            meta_formal_agua,
            meta_informal_agua,
            meta_formal_esgoto,
            meta_informal_esgoto
        FROM tb_meta_2025
        WHERE sup IS NOT NULL
    """)
    
    # Query para buscar o realizado acumulado (mantém a CTE original)
    query_realizado = text("""
        WITH RealizadoAcumulado AS (
            SELECT
                superintendencia,
                grafico,
                mes_ano,
                SUM(calculo) OVER (PARTITION BY superintendencia, grafico ORDER BY mes_ano) AS realizado_2025_acumulado
            FROM
                sandbox.tb_dados_realizados
            WHERE
                mes_ano LIKE '%2025%'
        ),
        RankingMeses AS (
            SELECT
                superintendencia,
                grafico,
                realizado_2025_acumulado,
                ROW_NUMBER() OVER (PARTITION BY superintendencia, grafico ORDER BY mes_ano DESC) as rn
            FROM
                RealizadoAcumulado
        )
        SELECT
            superintendencia,
            grafico,
            realizado_2025_acumulado
        FROM
            RankingMeses
        WHERE
            rn = 1
        ORDER BY
            superintendencia,
            grafico
    """)
    
    try:
        print("[INFO] Buscando dados para os gráficos (metas + realizado acumulado)...")
        
        # Buscar metas da tabela
        df_metas = pd.read_sql(query_metas, engine)
        print(f"[INFO] {len(df_metas)} registros de metas encontrados")
        
        # Buscar realizado acumulado
        df_realizado = pd.read_sql(query_realizado, engine)
        print(f"[INFO] {len(df_realizado)} registros de realizado encontrados")
        
        if df_metas.empty:
            print("[AVISO] Nenhuma meta encontrada na tabela tb_meta_2025.")
            return {}
        
        # Organizar os dados no formato esperado pelos gráficos
        dados_finais = {}
        
        # Processar apenas superintendências que têm metas definidas
        for _, row in df_metas.iterrows():
            sup_nome = row['sup']
            dados_finais[sup_nome] = {
                'AGUA_FORMAL': {'meta': int(row.get('meta_formal_agua', 0)), 'realizado': 0},
                'AGUA_INFORMAL': {'meta': int(row.get('meta_informal_agua', 0)), 'realizado': 0},
                'ESGOTO_FORMAL': {'meta': int(row.get('meta_formal_esgoto', 0)), 'realizado': 0},
                'ESGOTO_INFORMAL': {'meta': int(row.get('meta_informal_esgoto', 0)), 'realizado': 0}
            }
        
        # Processar realizado acumulado apenas para superintendências que têm metas
        for _, row in df_realizado.iterrows():
            sup_nome = row['superintendencia']
            grafico = row['grafico']
            realizado = int(row['realizado_2025_acumulado'])
            
            # Só adicionar realizado se a superintendência tem metas definidas
            if sup_nome in dados_finais:
                # Mapear o tipo de gráfico para a chave correta
                if grafico == 'Incremento de Água - Urbano':
                    dados_finais[sup_nome]['AGUA_FORMAL']['realizado'] = realizado
                elif grafico == 'Incremento de Água - Rural + Informal':
                    dados_finais[sup_nome]['AGUA_INFORMAL']['realizado'] = realizado
                elif grafico == 'Incremento de Esgoto - Urbano':
                    dados_finais[sup_nome]['ESGOTO_FORMAL']['realizado'] = realizado
                elif grafico == 'Incremento de Esgoto Rural + Informal':
                    dados_finais[sup_nome]['ESGOTO_INFORMAL']['realizado'] = realizado
        
        # Calcular ranking de desempenho e ordenar as superintendências
        ranking_sups = []
        for sup_nome, dados_sup in dados_finais.items():
            percentuais = []
            for categoria, dados in dados_sup.items():
                meta = dados['meta']
                realizado = dados['realizado']
                if meta > 0:
                    percentual = (realizado / meta) * 100
                    percentuais.append(percentual)
            
            # Calcular percentual médio de todas as metas
            if percentuais:
                percentual_medio = sum(percentuais) / len(percentuais)
                ranking_sups.append((sup_nome, percentual_medio, dados_sup))
        
        # Ordenar por percentual médio (do melhor para o pior)
        ranking_sups.sort(key=lambda x: x[1], reverse=True)
        
        # Reconstruir o dicionário ordenado
        dados_finais_ordenados = {}
        for sup_nome, percentual_medio, dados_sup in ranking_sups:
            dados_finais_ordenados[sup_nome] = dados_sup
        
        print(f"[SUCESSO] Dados para gráficos processados. {len(dados_finais_ordenados)} superintendências com metas encontradas.")
        print(f"[INFO] Ranking de desempenho: {[f'{sup} ({percentual:.1f}%)' for sup, percentual, _ in ranking_sups]}")
        return dados_finais_ordenados
        
    except Exception as e:
        print(f"[ERRO] Falha ao buscar dados para os gráficos: {e}")
        return {}

def fetch_update_dates_separately():
    """
    Busca a data de extração mais recente de cada tabela e retorna
    como três variáveis separadas.
    """
    # A ordem nesta lista determinará a ordem do retorno
    tabelas = [
        ('NLA NLE', 'tb_nla_nle'),
        ('ÁGUA', 'tb_agua'),
        ('ESGOTO', 'tb_esgoto')
    ]
    
    datas_extracao = []

    try:
        with engine.connect() as connection:
            for nome_display, nome_tabela in tabelas:
                query = text(f"SELECT MAX(data_extracao_etl) as ultima_data FROM sandbox.{nome_tabela};")
                resultado = connection.execute(query).fetchone()
                
                if resultado and resultado.ultima_data:
                    data_formatada = resultado.ultima_data.strftime('%d/%m/%Y %H:%M:%S')
                    datas_extracao.append(data_formatada)
                else:
                    datas_extracao.append("Data não disponível")
        
        # Retorna os três valores na ordem definida
        return datas_extracao[0], datas_extracao[1], datas_extracao[2]

    except Exception as e:
        print(f"Erro ao buscar datas de atualização: {e}")
        return "Erro na consulta", "Erro na consulta", "Erro na consulta"




if __name__ == "__main__":
    # Teste rápido das funções gráfico

    grafico_data = fetch_dados_graficos()
    print("[GRAFICO DATA]", grafico_data)