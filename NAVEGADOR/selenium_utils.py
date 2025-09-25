# ===================================================================
# ARQUIVO: selenium_utils.py (MODIFICADO)
# Nossa caixa de ferramentas para interações com o Selenium.
# ===================================================================
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
import shutil


######################################################################################
#                           --- FUNÇÃO UNIVERSAL  ---                                #
######################################################################################

def esperar_carregamento_invisivel(driver, timeout=60):
    """
    Espera até que a tela de carregamento do Power BI (spinner) desapareça.

    Args:
        driver: A instância do WebDriver do Selenium.
        timeout (int): O tempo máximo em segundos para esperar.
    
    Returns:
        bool: True se o carregamento desapareceu, False se o tempo esgotou.
    """
    print("[INFO] Verificando a tela de carregamento...")
    try:
        # Define o XPath para o contêiner do spinner de carregamento
        xpath_carregamento = "//*[@id='pbi-svg-loading']"
        
        # Cria um objeto de espera com o timeout definido
        wait = WebDriverWait(driver, timeout)
        
        # Espera até que o elemento se torne INVISÍVEL.
        # O Selenium verificará continuamente e só prosseguirá quando a condição for atendida.
        wait.until(EC.invisibility_of_element_located((By.XPATH, xpath_carregamento)))
        
        print("[SUCESSO] Tela de carregamento desapareceu. Continuando o script.")
        return True
    except TimeoutException:
        print(f"[ERRO] A tela de carregamento não desapareceu após {timeout} segundos.")
        return False
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro inesperado ao esperar pelo carregamento: {e}")
        return False


def extrair_dados_tabela_com_scroll(driver, tabela_element):
    """
    Extrai todas as linhas de uma tabela com rolagem virtual no Power BI.
    Esta versão utiliza ActionChains para mover para a última linha visível
    e forçar o carregamento de novas linhas, conforme sugerido.

    Args:
        driver: A instância do WebDriver do Selenium.
        tabela_element: O elemento da tabela principal (ex: pivotTable).

    Returns:
        list: Uma lista de listas, onde cada lista interna representa uma linha de dados.
    """
    print("   [INFO] Iniciando extração de tabela com rolagem (método ActionChains)...")
    
    linhas_extraidas = []
    dados_unicos = set()
    tentativas_sem_novas_linhas = 0

    # O loop continua enquanto encontrarmos novas linhas, com uma margem de 3 tentativas.
    while tentativas_sem_novas_linhas < 2:
        # Pega todas as linhas que estão no DOM naquele momento
        linhas_visiveis = tabela_element.find_elements(By.XPATH, ".//div[@role='row' and number(@aria-rowindex)>1]")
        
        if not linhas_visiveis:
            print("   [AVISO] Nenhuma linha de dados encontrada na tabela.")
            break

        novos_dados_encontrados_nesta_iteracao = False
        for linha in linhas_visiveis:
            try:
                # Extrai os valores da linha
                celulas = linha.find_elements(By.XPATH, ".//div[@role='rowheader' or @role='gridcell']")
                valores = tuple(c.text.strip() for c in celulas)

                # Se a linha tem conteúdo e ainda não foi extraída, adiciona à lista
                if valores and valores not in dados_unicos:
                    dados_unicos.add(valores)
                    linhas_extraidas.append(list(valores))
                    novos_dados_encontrados_nesta_iteracao = True
            except Exception:
                # Ignora linhas que podem desaparecer durante a extração (StaleElementReferenceException)
                continue
        
        # Se não encontramos nenhuma linha nova nesta iteração, incrementamos o contador de parada.
        if not novos_dados_encontrados_nesta_iteracao:
            tentativas_sem_novas_linhas += 1
            print(f"   [DEBUG] Nenhuma linha nova encontrada. Tentativa {tentativas_sem_novas_linhas}/3.")
        else:
            # Se encontramos, resetamos o contador.
            tentativas_sem_novas_linhas = 0

        # --- LÓGICA DE ROLAGEM COM ACTIONCHAINS ---
        # Move o mouse para a última linha visível para tentar carregar mais.
        try:
            ultima_linha_visivel = linhas_visiveis[-1]
            ActionChains(driver).move_to_element(ultima_linha_visivel).perform()
            time.sleep(0.7) # Pausa para a renderização após o movimento
        except IndexError:
            # Isso pode acontecer se a tabela ficar vazia ou não tiver linhas.
            print("   [AVISO] Não foi possível encontrar a última linha visível para mover. Finalizando.")
            break

    print(f"   [SUCESSO] Extração com rolagem finalizada. Total de {len(linhas_extraidas)} linhas únicas encontradas.")
    return linhas_extraidas


def encontrar_elemento(driver, by, value, timeout=10):
    """
    Função universal para encontrar um elemento, usando um loop de tentativas
    para aguardar o carregamento da página.
    
    Args:
        driver: A instância do WebDriver.
        by: A estratégia de busca (ex: By.XPATH, By.ID, By.CSS_SELECTOR).
        value: O valor do seletor (a string do XPath, o ID, etc.).
        timeout: O tempo máximo de espera em segundos.

    Returns:
        O WebElement se encontrado, ou None se ocorrer um erro ou timeout.
    """
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        try:
            # Tenta encontrar o elemento diretamente
            elemento = driver.find_element(by, value)
            # Se encontrou, retorna imediatamente
            return elemento
        except NoSuchElementException:
            # Se não encontrou, espera um pouco antes da próxima tentativa
            time.sleep(0.5) # Intervalo de 0.5 segundos entre as tentativas
    
    # Se o loop terminar sem encontrar o elemento, o timeout foi atingido
    print(f"[ERRO DE BUSCA] Tempo esgotado ({timeout}s). Elemento não encontrado com {by} = '{value}'")
    return None

def encontrar_e_clicar(driver, by, value, timeout=10):

    """
    Função universal para encontrar um elemento clicável e clicar nele.
    
    Args:
        driver: A instância do WebDriver.
        by: A estratégia de busca (ex: By.XPATH, By.ID, etc.).
        value: O valor do seletor.
        timeout: O tempo máximo de espera em segundos.

    Returns:
        True se o clique for bem-sucedido, False caso contrário.
    """
    try:
        wait = WebDriverWait(driver, timeout)
        elemento = wait.until(EC.element_to_be_clickable((by, value)))
        elemento.click()
        return True
    except TimeoutException:
        print(f"[ERRO DE CLIQUE] Tempo esgotado. Elemento não era clicável ou não foi encontrado com {by} = '{value}'")
        return False
    except Exception as e:
        print(f"[ERRO DE CLIQUE] Erro inesperado ao clicar no elemento: {e}")
        return False
    
def renomear_e_mover_arquivo_exportado(pagina, superintendencia, caminho_download):
    """
    Encontra o arquivo .xlsx mais recente na pasta de downloads,
    renomeia-o com base na página e superintendência, e o move para a pasta de destino.
    """
    try:
        print(f"\n--- GERENCIANDO ARQUIVO PARA: {pagina} / {superintendencia} ---")

        # 1. Encontrar o arquivo mais recente na pasta de downloads
        print(f"[INFO] Procurando o arquivo .xlsx mais recente em: {caminho_download}")
        arquivos_xlsx = [f for f in os.listdir(caminho_download) if f.endswith('.xlsx')]
        if not arquivos_xlsx:
            print("[ERRO] Nenhum arquivo .xlsx encontrado na pasta de downloads.")
            return False

        caminho_completo_arquivos = [os.path.join(caminho_download, f) for f in arquivos_xlsx]
        arquivo_mais_recente = max(caminho_completo_arquivos, key=os.path.getctime)
        print(f"[INFO] Arquivo mais recente encontrado: {os.path.basename(arquivo_mais_recente)}")

        # 2. Definir o novo nome e a pasta de destino
        if pagina and "Tabela de Incremento Tratamento Água" in pagina:
            pagina_abrev = "AGUA"
            novo_nome_arquivo = f"{pagina_abrev} - {superintendencia}.xlsx"
            pasta_destino = r"C:\Users\lcastro.eficien\Desktop\PAINEL ACOMPANHAMENTO\DADOS\Export Painel 2\AGUA"
        elif pagina and "Tabela de Incremento Esgoto" in pagina:
            pagina_abrev = "ESGOTO"
            novo_nome_arquivo = f"{pagina_abrev} - {superintendencia}.xlsx"
            pasta_destino = r"C:\Users\lcastro.eficien\Desktop\PAINEL ACOMPANHAMENTO\DADOS\Export Painel 2\ESGOTO"
        elif pagina is None:
            novo_nome_arquivo = f"{superintendencia}.xlsx"
            pasta_destino = r"C:\Users\lcastro.eficien\Desktop\PAINEL ACOMPANHAMENTO\DADOS\Export Painel 1"
        else:
            print(f"[AVISO] Tipo de página '{pagina}' não reconhecido. Usando 'OUTROS'.")
            novo_nome_arquivo = f"OUTROS - {superintendencia}.xlsx"
            pasta_destino = r"C:\Users\lcastro.eficien\Desktop\PAINEL ACOMPANHAMENTO\DADOS\Export Outros"

        # 3. Garante que a pasta de destino exista
        os.makedirs(pasta_destino, exist_ok=True)
        caminho_destino_completo = os.path.join(pasta_destino, novo_nome_arquivo)
        print(f"[INFO] O arquivo será movido para: {caminho_destino_completo}")

        # 4. Renomear e mover o arquivo
        shutil.move(arquivo_mais_recente, caminho_destino_completo)
        print(f"[SUCESSO] Arquivo renomeado e movido com sucesso.\n")
        return True

    except Exception as e:
        print(f"[ERRO] Ocorreu um erro ao renomear ou mover o arquivo: {e}")
        return False

def encontrar_elementos(driver, by, value, timeout=10):
    """
    Função para encontrar uma lista de elementos, aguardando até que pelo menos um seja encontrado.
    """
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        elementos = driver.find_elements(by, value)
        if elementos:
            return elementos
        time.sleep(0.5)
    print(f"[ERRO DE BUSCA] Tempo esgotado ({timeout}s). Nenhum elemento encontrado com {by} = '{value}'")
    return []

def gerar_xpath_container_grafico(nome_do_visual: str) -> str:
    """
    Gera o XPath mais robusto possível para o contêiner de um visual,
    buscando pelo atributo 'title' e tratando casos especiais como o '+'.
    """
    if '+' in nome_do_visual:
        partes = nome_do_visual.split(' + ')
        parte1, parte2 = partes[0].strip(), partes[1].strip()
        # Constrói um XPath que busca por ambas as partes no título
        return (f"//*[contains(@class, 'visual-container') and "
                f".//*[contains(@title, '{parte1}') and contains(@title, '{parte2}')]]")
    else:
        # Busca pelo título exato para outros gráficos
        return f"//*[contains(@class, 'visual-container') and .//*[@title='{nome_do_visual}']]"

######################################################################################
#                         --- FUNCOES PARA PAINEL 1 ---                              #
######################################################################################

def aplicar_filtros_superintendencia(driver, lista_superintendencias):
    """
    Abre o menu de Superintendência, verifica se uma opção já está selecionada,
    rola até ela se necessário e a seleciona.
    """
    if not lista_superintendencias:
        print("[INFO] Nenhuma superintendência para filtrar. Pulando esta etapa.")
        return True

    try:
        print("\n--- INICIANDO APLICAÇÃO DE FILTROS ---")
        # PASSO 1: Clicar no menu principal para abrir a lista
        print("[INFO] Abrindo o menu de Superintendência...")
        menu_principal_xpath = "//div[@aria-label='DS_CD_SUPERINTENDENCIA']"
        if not encontrar_e_clicar(driver, By.XPATH, menu_principal_xpath):
            return False
        
        time.sleep(1) # Pequena pausa para a animação do menu

        # PASSO 2: Clicar em cada opção da lista, com rolagem e verificação
        for nome_opcao in lista_superintendencias:
            print(f"  - Processando a opção: '{nome_opcao}'")
            try:
                # ⭐ XPATH ATUALIZADO: Encontra o container da linha diretamente pelo seu título.
                xpath_container = f"//div[contains(@class, 'slicerItemContainer') and @title='{nome_opcao}']"
                container_elemento = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, xpath_container))
                )
                
                # LÓGICA DE ROLAGEM COM JAVASCRIPT
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", container_elemento)
                time.sleep(0.5)
                
                # VERIFICAÇÃO: Checa se já está selecionado
                if container_elemento.get_attribute('aria-selected') == 'true':
                    print(f"    -> Opção '{nome_opcao}' já está selecionada. Pulando clique.")
                    continue  # Pula para a próxima iteração do loop
                
                # Se não estiver selecionado, clica diretamente no container da linha.
                print(f"    -> Selecionando a opção '{nome_opcao}'...")
                container_elemento.click()
                
            except Exception as e:
                print(f"[ERRO] Não foi possível encontrar ou processar a opção '{nome_opcao}': {e}")
                return False
        
        # PASSO 3: Fechar o menu para continuar
        print("[INFO] Fechando o menu de Superintendência...")
        encontrar_e_clicar(driver, By.XPATH, menu_principal_xpath)
        
        print("[SUCESSO] Filtros aplicados.")
        return True

    except Exception as e:
        print(f"[ERRO] Ocorreu um erro inesperado ao aplicar os filtros: {e}")
        return False

def esperar_download_concluir(pasta_download, nome_arquivo_esperado, timeout=120):
    """
    Espera um arquivo ser completamente baixado em uma pasta, monitorando
    a ausência de arquivos temporários (.crdownload).
    """
    print(f"\n[INFO] Aguardando o download de '{nome_arquivo_esperado}'...")
    print(f"       Pasta de destino: {pasta_download}")
    
    tempo_inicial = time.time()
    caminho_arquivo_final = os.path.join(pasta_download, nome_arquivo_esperado)
    caminho_arquivo_temp = caminho_arquivo_final + '.crdownload' # Para Chrome/Edge

    while time.time() - tempo_inicial < timeout:
        if os.path.exists(caminho_arquivo_final) and not os.path.exists(caminho_arquivo_temp):
            print(f"[SUCESSO] Download de '{nome_arquivo_esperado}' concluído.")
            return True
        time.sleep(1)

    print(f"[ERRO] O download não foi concluído dentro do tempo limite de {timeout} segundos.")
    return False

def limpar_todos_os_filtros(driver):
    """
    Encontra e clica no botão 'LIMPAR FILTROS' para resetar o painel.
    """
    print("\n--- LIMPANDO FILTROS ANTERIORES ---")
    # Este XPath procura por um elemento que contenha o texto 'LIMPAR FILTROS'.
    limpar_filtros_xpath = '//*[@id="pvExplorationHost"]/div/div/exploration/div/explore-canvas/div/div[2]/div/div[2]/div[2]/visual-container-repeat/visual-container[22]/transform/div/div[3]/div/div/visual-modern/div'
    
    # Tenta encontrar e clicar no botão. Se não encontrar, avisa e continua.
    if encontrar_e_clicar(driver, By.XPATH, limpar_filtros_xpath, timeout=15):
        print("[SUCESSO] Filtros foram limpos.")
        # Espera um tempo para o painel processar o reset dos filtros.
        time.sleep(5)
        return True
    else:
        print("[AVISO] Botão 'LIMPAR FILTROS' não encontrado ou não foi possível clicar. Prosseguindo...")
        # Retorna True para não parar o script se o botão não estiver presente
        return True




######################################################################################
#                           --- FUNCOES PARA O PAINEL 2 ---                          #
######################################################################################

def navegar_para_pagina_especifica(driver, nome_da_pagina):
    """
    Encontra e clica no botão de navegação para mudar de página no painel.
    Funciona para o painel 2 e 3 (que possuem a mesma estrutura de navegação).
    """
    print(f"\n--- NAVEGANDO PARA A PÁGINA: '{nome_da_pagina}' ---")
    # Este XPath é mais robusto pois procura pelo botão que contém o texto exato.
    xpath_pagina = f"//button[.//span[text()='{nome_da_pagina}']]"
    
    if encontrar_e_clicar(driver, By.XPATH, xpath_pagina, timeout=60):
        print(f"[SUCESSO] Navegou para a página '{nome_da_pagina}'.")
        # Espera a nova página carregar seus elementos
        time.sleep(10)
        return True
    else:
        print(f"[ERRO] Não foi possível encontrar ou clicar na página '{nome_da_pagina}'.")
        return False

def limpar_filtro_diretoria(driver):
    """
    Passa o mouse sobre o filtro 'DIRETORIA REGIONAL' para revelar o botão
    de limpar e, se ele estiver visível, clica nele.
    Funciona para o painel 2 e 3 (que possuem a mesma estrutura de navegação).
    """
    print("\n--- LIMPANDO FILTRO 'DIRETORIA REGIONAL' ---")
    try:
        # PASSO 1: Encontrar o contêiner do filtro para passar o mouse
        xpath_container_filtro = "//div[h3[@title='DIRETORIA REGIONAL']]"
        container_filtro = encontrar_elemento(driver, By.XPATH, xpath_container_filtro)
        
        if not container_filtro:
            print("[ERRO] Contêiner do filtro 'DIRETORIA REGIONAL' não encontrado.")
            return False

        # PASSO 2: Simular o mouse hover para revelar o botão de limpar
        print("[INFO] Passando o mouse sobre o filtro para revelar opções...")
        actions = ActionChains(driver)
        actions.move_to_element(container_filtro).perform()
        time.sleep(1) # Pausa para o botão aparecer

        # PASSO 3: Encontrar e clicar no botão de limpar, se ele estiver visível
        xpath_botao_limpar = "//span[@aria-label='Limpar seleções']"
        botao_limpar = encontrar_elemento(driver, By.XPATH, xpath_botao_limpar)

        if botao_limpar and botao_limpar.is_displayed():
            print("[INFO] Botão 'Limpar seleções' encontrado e visível. Clicando...")
            botao_limpar.click()
            print("[SUCESSO] Filtro 'DIRETORIA REGIONAL' foi limpo.")
            time.sleep(5)
        else:
            print("[INFO] Botão 'Limpar seleções' não está visível. Nenhum filtro para limpar.")
        
        return True

    except Exception as e:
        print(f"[ERRO] Ocorreu um erro inesperado ao tentar limpar o filtro: {e}")
        return False

def limpar_filtro_municipio(driver):
    """
    Passa o mouse sobre o filtro 'Município' para revelar o botão
    de limpar e, se ele estiver visível, clica nele.
    Funciona para o painel 2 e 3 (que possuem a mesma estrutura de navegação).
    """
    print("\n--- LIMPANDO FILTRO 'Município' ---")
    try:
        # PASSO 1: Encontrar o contêiner do filtro para passar o mouse
        xpath_container_filtro = "//div[h3[@title='Município']]"
        container_filtro = encontrar_elemento(driver, By.XPATH, xpath_container_filtro)
        
        if not container_filtro:
            print("[ERRO] Contêiner do filtro 'Município' não encontrado.")
            return False

        # PASSO 2: Simular o mouse hover para revelar o botão de limpar
        print("[INFO] Passando o mouse sobre o filtro para revelar opções...")
        actions = ActionChains(driver)
        actions.move_to_element(container_filtro).perform()
        time.sleep(1) # Pausa para o botão aparecer

        # PASSO 3: Encontrar e clicar no botão de limpar, se ele estiver visível
        xpath_botao_limpar = "//span[@aria-label='Limpar seleções']"
        botao_limpar = encontrar_elemento(driver, By.XPATH, xpath_botao_limpar)

        if botao_limpar and botao_limpar.is_displayed():
            print("[INFO] Botão 'Limpar seleções' encontrado e visível. Clicando...")
            botao_limpar.click()
            print("[SUCESSO] Filtro 'Município' foi limpo.")
            time.sleep(5)
        else:
            print("[INFO] Botão 'Limpar seleções' não está visível. Nenhum filtro para limpar.")
        
        return True

    except Exception as e:
        print(f"[ERRO] Ocorreu um erro inesperado ao tentar limpar o filtro: {e}")
        return False

def aplicar_filtro_diretoria_regional(driver, superintendencia):
    """
    Seleciona a superintendência no filtro 'DIRETORIA REGIONAL' de forma dinâmica,
    funcionando para ambos os painéis.
    """
    if not superintendencia:
        print("[INFO] Nenhuma superintendência para filtrar. Pulando esta etapa.")
        return True

    try:
        print("\n--- INICIANDO APLICAÇÃO DE FILTROS ---")
        # Busca o dropdown pelo aria-label, robusto para ambos os painéis
        menu_principal_xpath = "//div[@role='combobox' and contains(@aria-label, 'DIRETORIA REGIONAL')]"
        if not encontrar_e_clicar(driver, By.XPATH, menu_principal_xpath):
            print("[ERRO] Não foi possível abrir o menu de Superintendência.")
            return False

        time.sleep(1)  # Pequena pausa para a animação do menu

        try:
            # Busca o item da lista pelo título
            xpath_container = f"//div[contains(@class, 'slicerItemContainer') and @title='{superintendencia}']"
            container_elemento = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, xpath_container))
            )

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", container_elemento)
            time.sleep(0.5)

            # Verifica se já está selecionado
            if container_elemento.get_attribute('aria-selected') == 'true':
                print(f"    -> Opção '{superintendencia}' já está selecionada.")
            else:
                print(f"    -> Selecionando a opção '{superintendencia}'...")
                container_elemento.click()

        except Exception as e:
            print(f"[ERRO] Não foi possível encontrar ou processar a opção '{superintendencia}': {e}")
            return False

        # Fecha o menu para continuar
        print("[INFO] Fechando o menu de Superintendência...")
        encontrar_e_clicar(driver, By.XPATH, menu_principal_xpath)

        print("[SUCESSO] Filtro aplicado.")
        return True

    except Exception as e:
        print(f"[ERRO] Ocorreu um erro inesperado ao aplicar os filtros: {e}")
        return False




