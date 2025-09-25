import os
import shutil
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from DADOS.sistema_log import log_print

DIRETORIO_PERFIL_CHROME = r"C:\Users\lcastro.eficien\Desktop\PAINEL ACOMPANHAMENTO\NAVEGADOR\chrome_session_profile"

def configurar_perfil():
    """Configura as opções do Chrome para usar o perfil de sessão."""
    chrome_options = Options()
    chrome_options.add_argument(f"user-data-dir={os.path.abspath(DIRETORIO_PERFIL_CHROME)}")
    chrome_options.add_argument("--disable-session-crashed-bubble")
    chrome_options.add_argument("--disable-infobars")
    #chrome_options.add_argument("--")
    return chrome_options

def deletar_perfil_sessao():
    """
    Função dedicada e segura para apagar a pasta do perfil de sessão.
    Só deve ser chamada quando houver certeza de que a sessão expirou.
    """
    if os.path.exists(DIRETORIO_PERFIL_CHROME):
        try:
            print(f"[INFO] A sessão é inválida. A apagar perfil antigo de '{DIRETORIO_PERFIL_CHROME}'...")
            log_print(f"[INFO] A sessão é inválida. A apagar perfil antigo de '{DIRETORIO_PERFIL_CHROME}'...")
            shutil.rmtree(DIRETORIO_PERFIL_CHROME)
            print("[SUCESSO] Perfil de sessão antigo foi removido.")
            log_print("[SUCESSO] Perfil de sessão antigo foi removido.")
             # Retorna True para indicar que o perfil foi apagado com sucesso
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao apagar o perfil de sessão: {e}")
            log_print(f"[ERRO] Falha ao apagar o perfil de sessão: {e}")
             # Retorna False para indicar que houve um erro ao apagar o perfil
            return False
    else:
        print("[INFO] Nenhum perfil de sessão para apagar.")
        return True

def iniciar_sessao_existente():
    """Inicia o navegador usando um perfil de sessão existente."""
    if not os.path.exists(DIRETORIO_PERFIL_CHROME):
        print(f"\n[ERRO] Perfil de sessão '{DIRETORIO_PERFIL_CHROME}' não encontrado.")
        log_print(f"\n[ERRO] Perfil de sessão '{DIRETORIO_PERFIL_CHROME}' não encontrado.")
        return None
        
    print("[INFO] A usar perfil de sessão existente para iniciar o navegador...")
    log_print("[INFO] A usar perfil de sessão existente para iniciar o navegador...")
    
    driver = webdriver.Chrome(options=configurar_perfil())
    driver.maximize_window()
    return driver

def criar_nova_sessao_manual(url_inicial):
    """
    Abre o navegador para que o utilizador crie uma nova sessão.
    Esta função agora é NÃO-DESTRUTIVA.
    """
    driver = webdriver.Chrome(options=configurar_perfil())
    driver.maximize_window()
    
    try:
        driver.get(url_inicial)
        print("\n--- AÇÃO NECESSÁRIA ---")
        print(f"Uma janela do navegador foi aberta para si para criar uma nova sessão.")
        print("1. Faça o login COMPLETO na sua conta Microsoft.")
        print("2. Marque a opção 'Permanecer conectado', se disponível.")
        print("3. Aguarde o carregamento completo do painel do Power BI.")
        input("4. Após tudo carregado, pressione Enter aqui para finalizar...")

        print(f"\n[SUCESSO] Sessão de autenticação guardada no perfil '{DIRETORIO_PERFIL_CHROME}'.")
        time.sleep(3)
    finally:
        driver.quit()