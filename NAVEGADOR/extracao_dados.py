# ===================================================================
# ARQUIVO: extracao_dados.py (MODIFICADO)
# Adicionada a lógica de HOVER para revelar o menu.
# ===================================================================

import time
import csv
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from NAVEGADOR.selenium_utils import *
import os
from DADOS.sistema_log import log_print

def iniciar_exportacao_painel_1(
    driver,
    url_painel,
    xpath_container_visual,
    xpath_tres_pontos,
    xpath_exportar_botao,
    lista_superintendencias
):
    """
    Navega para a URL, passa o mouse sobre um visual para revelar o menu,
    e inicia o processo de exportação.
    """
    try:
        print(f"[INFO] Navegando para: {url_painel}")
        log_print(f"[INFO] Navegando para: {url_painel}")
        driver.get(url_painel)
        time.sleep(15)

        # --- VERIFICAÇÃO PROATIVA DE LOGIN ---
        if encontrar_elemento(driver, By.XPATH, "//input[@id='email' or @type='email']", timeout=3) or encontrar_elemento(driver, By.XPATH, "//div[text()='Insira a senha']", timeout=3):
            print("[ALERTA] Tela de login detectada. A sessão expirou.")
            log_print("[ALERTA] Tela de login detectada. A sessão expirou.")
            return "LOGIN_REQUIRED"
        print("[INFO] Sessão ativa. Prosseguindo com a exportação.")
        log_print("[INFO] Sessão ativa. Prosseguindo com a exportação.")
        
        # ESPERAR O CARREGAMENTO DO PAINEL
        print("[INFO] Aguardando o carregamento do painel...") 
        log_print("[INFO] Aguardando o carregamento do painel...")
        esperar_carregamento_invisivel(driver,timeout=60)

        # --- LIMPAR FILTROS ANTERIORES ---
        if not limpar_todos_os_filtros(driver):
            print("[ERRO FATAL] Falha ao tentar limpar os filtros. Abortando.")
            log_print("[ERRO FATAL] Falha ao tentar limpar os filtros. Abortando.")
            return False

        # --- APLICAR FILTROS ---
        if not aplicar_filtros_superintendencia(driver, lista_superintendencias):
            print("[ERRO FATAL] Falha ao aplicar os filtros. Abortando a exportação.")
            log_print("[ERRO FATAL] Falha ao aplicar os filtros. Abortando a exportação.")
            return False

        print("[INFO] Aguardando o painel atualizar com os filtros...")
        log_print("[INFO] Aguardando o painel atualizar com os filtros...")
        time.sleep(5)

        # --- HOVER PARA REVELAR O MENU ---
        print("\n--- INICIANDO PROCESSO DE EXPORTAÇÃO ---")
        container_visual = encontrar_elemento(driver, By.XPATH, xpath_container_visual, timeout=30)
        if not container_visual:
            print("[ERRO] Não foi possível encontrar o container do visual para fazer o hover.")
            log_print("[ERRO] Não foi possível encontrar o container do visual para fazer o hover.")
            return False

        actions = ActionChains(driver)
        actions.move_to_element(container_visual).perform()
        time.sleep(1)

        # --- CLICAR NOS MENUS DE EXPORTAÇÃO ---
        if not encontrar_e_clicar(driver, By.XPATH, xpath_tres_pontos, timeout=10):
            return False
        time.sleep(1)

        if not encontrar_e_clicar(driver, By.XPATH, "//button[@title='Exportar dados']", timeout=10):
            return False

        if not encontrar_e_clicar(driver, By.XPATH, xpath_exportar_botao, timeout=10):
            return False

        print("[SUCESSO] Clique de exportação realizado.")
        log_print("[SUCESSO] Clique de exportação realizado.")

        # --- AGUARDAR DOWNLOAD ---
        pasta_downloads = os.path.join(os.path.expanduser('~'), 'Downloads')
        nome_arquivo_download = "Exportar Base de Dados (Limitado a 150 mil linhas).xlsx"

        if not esperar_download_concluir(pasta_downloads, nome_arquivo_download):
            print("[ERRO FATAL] Falha ao concluir o download do arquivo.")
            log_print("[ERRO FATAL] Falha ao concluir o download do arquivo.")
            return False

        # --- RENOMEAR E MOVER O ARQUIVO ---
        if not renomear_e_mover_arquivo_exportado(None, "DADOS PAINEL 1", pasta_downloads):
            print("[ERRO FATAL] Falha ao renomear ou mover o arquivo exportado.")
            log_print("[ERRO FATAL] Falha ao renomear ou mover o arquivo exportado.")
            return False

        print("[INFO] Processo de exportação e download finalizado com sucesso.")
        log_print("[INFO] Processo de exportação e download finalizado com sucesso.")
        return True

    except Exception as e:
        print(f"[ERRO] Ocorreu um erro inesperado no processo de exportação: {e}")
        log_print(f"[ERRO] Ocorreu um erro inesperado no processo de exportação: {e}")
        return False

def iniciar_exportacao_painel_2(
    driver,
    url_painel,
    xpath_container_visual,
    xpath_tres_pontos,
    xpath_botao_exportar_dados,
    pagina
):
    """
    Exporta dados do Painel 2 para cada superintendência, aplicando filtros e baixando os arquivos.
    """
    try:
        driver.get(url_painel)
        time.sleep(5)

        # --- VERIFICAÇÃO PROATIVA DE LOGIN ---
        if encontrar_elemento(driver, By.XPATH, "//input[@id='email' or @type='email']", timeout=3):
            print("[ALERTA] Tela de login detectada. A sessão expirou.")
            log_print("[ALERTA] Tela de login detectada. A sessão expirou.")
            return "LOGIN_REQUIRED"
        print("[INFO] Sessão ativa. Prosseguindo com a exportação.")
        log_print("[INFO] Sessão ativa. Prosseguindo com a exportação.")

        esperar_carregamento_invisivel(driver,timeout=60)

        # NAVEGAÇÃO INTERNA DO PAINEL
        if not navegar_para_pagina_especifica(driver, pagina):
            return False

        # LIMPEZA DE FILTROS
        if not limpar_filtro_diretoria(driver):
            return False
        if not limpar_filtro_municipio(driver):
            return False

        lista_superintendencias = [
            "BAIXADA SANTISTA E VALE DO RIBEIRA",
            "BAIXO E ALTO PARANAPANEMA",
            "CAPIVAI, JUNDIAÍ, PARDO E GRANDE",
            "CENTRO",
            "LESTE",
            "MÉDIO E BAIXO TIETÊ",
            "NORTE",
            "OESTE",
            "SUL",
            "VALE DO PARAÍBA E LITORAL NORTE"
        ]

        # Para cada superintendência, aplica o filtro e exporta
        for superintendencia in lista_superintendencias:
            print(f"[INFO] Iniciando exportação para a Superintendência: {superintendencia}")
            log_print(f"[INFO] Iniciando exportação para a Superintendência: {superintendencia}")

            if not aplicar_filtro_diretoria_regional(driver, superintendencia):
                print(f"[ERRO] Falha ao aplicar filtro para a Superintendência: {superintendencia}")
                log_print(f"[ERRO] Falha ao aplicar filtro para a Superintendência: {superintendencia}")
                continue

            time.sleep(5)  # Aguarda atualização do painel

            # --- HOVER PARA REVELAR O MENU ---
            container_visual = encontrar_elemento(driver, By.XPATH, xpath_container_visual, timeout=30)
            if not container_visual:
                print("[ERRO] Não foi possível encontrar o container do visual para fazer o hover.")
                log_print("[ERRO] Não foi possível encontrar o container do visual para fazer o hover.")
                return False

            actions = ActionChains(driver)
            actions.move_to_element(container_visual).perform()
            time.sleep(1)

            # --- CLICAR NOS MENUS DE EXPORTAÇÃO ---
            if not encontrar_e_clicar(driver, By.XPATH, xpath_tres_pontos, timeout=10):
                print("[ERRO] Não foi possível clicar nos três pontos.")
                log_print("[ERRO] Não foi possível clicar nos três pontos.")
                return False
            time.sleep(1)

            if not encontrar_e_clicar(driver, By.XPATH, "//button[@title='Exportar dados']", timeout=10):
                print("[ERRO] Não foi possível clicar no botão de exportação de dados.")
                log_print("[ERRO] Não foi possível clicar no botão de exportação de dados.")
                return False
            time.sleep(1)

            if not encontrar_e_clicar(driver, By.XPATH, xpath_botao_exportar_dados, timeout=10):
                print("[ERRO] Não foi possível clicar no botão de exportação.")
                log_print("[ERRO] Não foi possível clicar no botão de exportação.")
                return False
            time.sleep(1)

            # --- AGUARDAR DOWNLOAD ---
            pasta_downloads = os.path.join(os.path.expanduser('~'), 'Downloads')
            nome_arquivo_download = "data.xlsx"

            if not esperar_download_concluir(pasta_downloads, nome_arquivo_download):
                print("[ERRO FATAL] Falha ao concluir o download do arquivo.")
                log_print("[ERRO FATAL] Falha ao concluir o download do arquivo.")
                return False

            # --- RENOMEAR E MOVER O ARQUIVO ---
            if not renomear_e_mover_arquivo_exportado(pagina, superintendencia, pasta_downloads):
                print("[ERRO FATAL] Falha ao renomear ou mover o arquivo exportado.")
                log_print("[ERRO FATAL] Falha ao renomear ou mover o arquivo exportado.")
                return False

        return True

    except Exception as e:
        print(f"[ERRO] Ocorreu um erro ao acessar o Painel 2: {e}")
        log_print(f"[ERRO] Ocorreu um erro ao acessar o Painel 2: {e}")
        return False


def iniciar_exportacao_painel_3(driver, url_painel, xpath_mostrar_como_tabela, pagina_3):
    try:
        driver.get(url_painel)
        
        # --- ETAPA 1: TRATAMENTO INTELIGENTE DE IFRAME ---
        #print("[INFO] Verificando a presença de um iframe...")
        
        wait = WebDriverWait(driver, 20) # Espera no máximo 20 segundos
        # try:
        #     iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'iframe')))
        #     driver.switch_to.frame(iframe)
        #     print("[INFO] Foco alterado para o iframe do painel.")
        # except TimeoutException:
        #     print("[INFO] Nenhum iframe encontrado. Continuando na página principal.")

        # --- ETAPA 2: VERIFICAÇÃO DE SESSÃO E NAVEGAÇÃO ---
        if encontrar_elemento(driver, By.XPATH, "//input[@id='email' or @type='email']", timeout=3):
            return "LOGIN_REQUIRED"
        print("[INFO] Sessão ativa.")
        log_print("[INFO] Sessão ativa.")
        esperar_carregamento_invisivel(driver,timeout=60)

        if not navegar_para_pagina_especifica(driver, pagina_3):
            return False
            
        lista_superintendencias = [
            "BAIXADA SANTISTA E VALE DO RIBEIRA", "BAIXO E ALTO PARANAPANEMA", "CAPIVAI, JUNDIAÍ, PARDO E GRANDE",
            "CENTRO", "LESTE", "MÉDIO E BAIXO TIETÊ", "NORTE", "OESTE", "SUL", "VALE DO PARAÍBA E LITORAL NORTE"
        ]
        
        nomes_dos_graficos = [
            "Incremento de Água - Urbano", "Incremento de Água - Rural + Informal",
            "Incremento de Esgoto - Urbano", "Incremento de Esgoto Rural + Informal"
        ]
        
        
        caminho_arquivo = r"C:\Users\lcastro.eficien\Desktop\PAINEL ACOMPANHAMENTO\DADOS\Export Painel 3\dados_extraidos.csv"

        with open(caminho_arquivo, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=';')
            cabecalho_escrito = False
            
            for superintendencia in lista_superintendencias:
                print(f"\n[INFO] Iniciando para a Superintendência: {superintendencia}")
                
                if not limpar_filtro_diretoria(driver) or not limpar_filtro_municipio(driver):
                    continue
                if not aplicar_filtro_diretoria_regional(driver, superintendencia):
                    continue
                
                # Pausa para garantir que os filtros sejam aplicados antes de prosseguir
                time.sleep(5) 

                for nome_grafico in nomes_dos_graficos:
                    print(f"  [INFO] Processando gráfico: {nome_grafico}")
                    log_print(f"  [INFO] Processando gráfico: {nome_grafico}")
                    try:
                        # --- ETAPA 3: ESPERA INTELIGENTE PELO GRÁFICO ---
                        xpath_container = gerar_xpath_container_grafico(nome_grafico)
                        
                        # O Selenium vai esperar ATÉ 30 segundos o elemento aparecer
                        container_grafico = wait.until(EC.presence_of_element_located((By.XPATH, xpath_container)))
                        
                        # --- ETAPA 4: INTERAÇÃO RELATIVA (HOVER E CLIQUE) ---
                        area_hover = container_grafico.find_element(By.XPATH, ".//visual-modern")
                        ActionChains(driver).move_to_element(area_hover).perform()
                        time.sleep(1)

                        botao_opcoes = container_grafico.find_element(By.XPATH, ".//button[@data-testid='visual-more-options-btn']")
                        botao_opcoes.click()
                        time.sleep(1)

                        if not encontrar_e_clicar(driver, By.XPATH, xpath_mostrar_como_tabela, timeout=10):
                            print("      [ERRO] Não foi possível clicar em 'Mostrar como uma tabela'.")
                            log_print("      [ERRO] Não foi possível clicar em 'Mostrar como uma tabela'.")
                            continue
                        print("     [SUCESSO] Mudou para visualização de tabela.")
                        log_print("     [SUCESSO] Mudou para visualização de tabela.")
                        
                        # Espera inteligente pela tabela
                        tabela = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'pivotTable')]")))

                        # --- ETAPA 5: EXTRAÇÃO DE DADOS ---
                        cabecalho = tabela.find_elements(By.XPATH, ".//div[@role='row' and @aria-rowindex='1']//div[@role='columnheader']")
                        cabecalho_texto = [c.text.strip() for c in cabecalho]

                        if not cabecalho_escrito:
                            writer.writerow(['Superintendencia', 'Gráfico'] + cabecalho_texto)
                            cabecalho_escrito = True

                        # --- Bloco novo com a função de rolagem ---
                        # Chama a nova função para extrair todas as linhas, lidando com a rolagem
                        todas_as_linhas = extrair_dados_tabela_com_scroll(driver, tabela)

                        # Itera sobre os dados retornados e escreve no CSV
                        for valores_linha in todas_as_linhas:
                            writer.writerow([superintendencia, nome_grafico] + valores_linha)

                        print(f"     [INFO] {len(todas_as_linhas)} linhas de dados extraídas e salvas.")
                        log_print(f"     [INFO] {len(todas_as_linhas)} linhas de dados extraídas e salvas.")

                        botao_voltar = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='back-to-report-button']")))
                        botao_voltar.click()
                        print("     [INFO] Voltou ao relatório.")
                        log_print("     [INFO] Voltou ao relatório.")
                        time.sleep(2) # Espera a tela principal recarregar

                    except TimeoutException:
                        print(f"      [AVISO] Gráfico '{nome_grafico}' não encontrado para esta superintendência. Pulando.")
                        log_print(f"      [AVISO] Gráfico '{nome_grafico}' não encontrado para esta superintendência. Pulando.")
                    except Exception as e:
                        print(f"      [ERRO] Falha crítica ao interagir com o gráfico '{nome_grafico}': {e}")
                        log_print(f"      [ERRO] Falha crítica ao interagir com o gráfico '{nome_grafico}': {e}")
                        # Tenta voltar para não travar o processo
                        try:
                            driver.find_element(By.XPATH, "//button[@data-testid='back-to-report-button']").click()
                        except:
                            pass
                            
            # Ao final de tudo, retorna o driver ao conteúdo principal da página
            driver.switch_to.default_content()
            return True

    except Exception as e:
        print(f"[ERRO] Ocorreu um erro geral e fatal ao acessar o Painel 3: {e}")
        log_print(f"[ERRO] Ocorreu um erro geral e fatal ao acessar o Painel 3: {e}")
         # Garante que o foco seja resetado em caso de erro
        driver.switch_to.default_content() # Garante que o foco seja resetado em caso de erro
        return False