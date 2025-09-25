from DADOS.dados import executar_processamento_dados
from DADOS.sistema_log import log_print  # Processa e consolida os dados extraídos dos arquivos Excel
from NAVEGADOR.navegador import main as navegador_main  # Realiza a automação da extração dos dados dos painéis Power BI via Selenium
from NAVEGADOR.atualizar_login import  atualizar_login  # Importa o objeto navegador para uso posterior
from datetime import datetime  # Importa a classe datetime para manipulação de datas

# ===================== ETAPA 1: EXTRAÇÃO DOS DADOS DOS PAINÉIS =====================
# navegador_main() executa a automação web:
# - Abre o navegador Chrome com perfil salvo
# - Realiza login no Power BI (se necessário)
# - Navega até os painéis do Power BI
# - Exporta os dados dos relatórios desepjados para arquivos Excel
# - Salva os arquivos exportados nas pastas corretas para processamento posterior

try:
    #Se navegador_main retornar 'LOGIN_REQUIRED', significa que a sessão expirou e é necessário atualizar o login
    resultado = navegador_main()
    if resultado == 'LOGIN_REQUIRED':
        print("\n[INFO] Sessão expirada. Atualizando login...")
        log_print("\n[INFO] Sessão expirada. Atualizando login...")
        atualizar_login()  # Atualiza o login se necessário
        print("[INFO] Login atualizado com sucesso. Reiniciando a extração dos dados...")
        log_print("[INFO]" 
        " " 
        " " 
        " Login atualizado com sucesso. Reiniciando a extração dos dados...")
        resultado = navegador_main()  # Tenta novamente a extração após atualizar o login

except Exception as e:
    print(f"\n[ERRO] Falha na extração dos dados: {e}")
    log_print(f"\n[ERRO] Falha na extração dos dados: {e}")
    print("--- Tente atualizar o login manualmente ---")
    log_print("--- Tente atualizar o login manualmente ---")
    #atualizar_login()
    exit(1)

# ===================== ETAPA 2: PROCESSAMENTO DOS DADOS EXTRAÍDOS =====================
# executar_processamento_dados() faz o ETL dos dados:
# - Lê os arquivos Excel exportados (ÁGUA, ESGOTO, NLA/NLE)
# - Trata, limpa e transforma os dados
# - Realiza somatórios, renomeia colunas, extrai metadados
# - Consolida tudo em um único arquivo Excel final, com abas específicas para cada tipo de dado
data_atualizacao_painel = datetime.now()
    
executar_processamento_dados(data_atualizacao_painel=data_atualizacao_painel)

# ===================== ETAPA 3: FINALIZAÇÃO =====================
print("\n--- PROCESSO FINALIZADO ---")  # Indica que todo o fluxo foi executado com sucesso
log_print("\n--- PROCESSO FINALIZADO ---")  # Registra a finalização do processo no log