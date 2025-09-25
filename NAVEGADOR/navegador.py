# ===================================================================
# ARQUIVO: navegador.py (MODIFICADO)
# Atualizado para passar o XPath do container do visual.
# ===================================================================

import time
from NAVEGADOR.login import iniciar_sessao_existente
from NAVEGADOR.extracao_dados import iniciar_exportacao_painel_1, iniciar_exportacao_painel_2, iniciar_exportacao_painel_3
from DADOS.sistema_log import log_print



def main():
    print("--- Iniciando processo de extração de dados ---")

    # Excluir arquivo residual  "data.xslx" se existir
    try:
        import os
        from pathlib import Path
        downloads_folder = str(Path.home() / "Downloads")
        file_path = os.path.join(downloads_folder, "data.xlsx")
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"[INFO] Arquivo '{file_path}' removido.")
            log_print(f"[INFO] Arquivo '{file_path}' removido.")    
        else:
            print("[INFO] Arquivo 'data.xlsx' não encontrado, nada a remover.")
            log_print("[INFO] Arquivo 'data.xlsx' não encontrado, nada a remover.")
    except Exception as e:
        print(f"[ERRO] Não foi possível remover 'data.xlsx': {e}")
        log_print(f"[ERRO] Não foi possível remover 'data.xlsx': {e}")




    driver = iniciar_sessao_existente()
    if driver is None:
        print("Execute 'atualizar_login.py' para criar a sessão.")
        log_print("Execute 'atualizar_login.py' para criar a sessão.")
        return

    

    # #DAQUI PRA BAIXO PODE COMENTAR PORQUE ESTA PRONTO    
    try:
        # -------------------------------------------------- PAINEL 1 ---------------------------------------------------------
        lista_superintendencias = [
            "SUP ALTO PARANAPANEMA",
            "SUP B PARANAPANEMA",
            "SUP B TIETÊ E GRANDE",
            "SUP BAIXADA SANTISTA",
            "SUP CAPIVARI JUNDIAÍ",
            "SUP CENTRO",
            "SUP LESTE",
            "SUP LITORAL NORTE",
            "SUP MÉDIO TIETÊ",
            "SUP NORTE",
            "SUP OESTE",
            "SUP PARDO E GRANDE",
            "SUP SUL",
            "SUP VALE DO PARAÍBA",
            "SUP VALE DO RIBEIRA"
        ]

        url_painel_1 = "https://app.powerbi.com/groups/me/reports/f5f01274-2da5-4665-aa49-275a12363915/ReportSection97b8ebdafba6af1b7931?ctid=5f9d74c8-ec92-4488-a2c7-bdce634262fa&experience=power-bi"
        xpath_container_painel_1 = "/html/body/div[1]/root/mat-sidenav-container/mat-sidenav-content/tri-shell-panel-outlet/tri-item-renderer-panel/tri-extension-panel-outlet/mat-sidenav-container/mat-sidenav-content/div/div/div[1]/tri-shell/tri-item-renderer/tri-extension-page-outlet/div[2]/report/exploration-container/div/div/docking-container/div/div/div/div/exploration-host/div/div/exploration/div/explore-canvas/div/div[2]/div/div[2]/div[2]/visual-container-repeat/visual-container[9]/transform/div/div[3]/div/div/visual-modern"
        xpath_tres_pontos_painel_1 = "//button[@aria-label='Mais opções']"
        xpath_exportar_dados = "//mat-dialog-actions//button[contains(., 'Exportar')]"

        resultado_1 = iniciar_exportacao_painel_1(
            driver,
            url_painel_1,
            xpath_container_painel_1,
            xpath_tres_pontos_painel_1,
            xpath_exportar_dados,
            lista_superintendencias
        )

        if not resultado_1 or resultado_1 == "LOGIN_REQUIRED":
            print("\n[AÇÃO NECESSÁRIA] Falha ao exportar do Painel 1. Execute 'atualizar_login.py'.")
            log_print("\n[AÇÃO NECESSÁRIA] Falha ao exportar do Painel 1. Execute 'atualizar_login.py'.")
            return 'LOGIN_REQUIRED'

        print("\n[INFO] Exportação do Painel 1 concluída com sucesso.")
        log_print("\n[INFO] Exportação do Painel 1 concluída com sucesso.")
        






        #-------------------------------------------------- PAINEL 2 ---------------------------------------------------------
        paginas = [
            'Tabela de Incremento Tratamento Água',
            'Tabela de Incremento Esgoto'
        ]

        for pagina in paginas:
            url_painel_2 = "https://app.powerbi.com/groups/me/reports/8f55c63e-74cf-46ac-aa4d-247c6be2e061/ReportSection7e65b0c060b06dc103b3?experience=power-bi"
            xpath_container_painel_2 = "/html/body/div[1]/root/mat-sidenav-container/mat-sidenav-content/tri-shell-panel-outlet/tri-item-renderer-panel/tri-extension-panel-outlet/mat-sidenav-container/mat-sidenav-content/div/div/div[1]/tri-shell/tri-item-renderer/tri-extension-page-outlet/div[2]/report/exploration-container/div/div/docking-container/div/div/div/div/exploration-host/div/div/exploration/div/explore-canvas/div/div[2]/div/div[2]/div[2]/visual-container-repeat/visual-container[4]/transform/div/div[3]/div/div/visual-modern"
            xpath_tres_pontos_painel_2 = "/html/body/div[1]/root/mat-sidenav-container/mat-sidenav-content/tri-shell-panel-outlet/tri-item-renderer-panel/tri-extension-panel-outlet/mat-sidenav-container/mat-sidenav-content/div/div/div[1]/tri-shell/tri-item-renderer/tri-extension-page-outlet/div[2]/report/exploration-container/div/div/docking-container/div/div/div/div/exploration-host/div/div/exploration/div/explore-canvas/div/div[2]/div/div[2]/div[2]/visual-container-repeat/visual-container[4]/transform/div/visual-container-header/div/div/div/visual-container-options-menu/visual-header-item-container/div/button"
            xpath_botao_exportar_dados_painel_2 = "//mat-dialog-actions//button[contains(., 'Exportar')]"

            resultado_2 = iniciar_exportacao_painel_2(
                driver,
                url_painel_2,
                xpath_container_painel_2,
                xpath_tres_pontos_painel_2,
                xpath_botao_exportar_dados_painel_2,
                pagina
            )

            if not resultado_2:
                print(f"\n[AVISO] Falha ao exportar do Painel 2: {pagina}")
                log_print(f"\n[AVISO] Falha ao exportar do Painel 2: {pagina}")
            print("\n--- Processo Concluído para a página:", pagina, "---")
            log_print(f"\n--- Processo Concluído para a página: {pagina} ---")
        
        
        
        
        
        
        
        # --- PAINEL 3 ---
        url_painel_3 = "https://app.powerbi.com/groups/me/reports/8f55c63e-74cf-46ac-aa4d-247c6be2e061/ReportSection7e65b0c060b06dc103b3?experience=power-bi"
        pagina_3 = 'Evolução de Economias por Recorte 2025'
        #xpath_graficos = "//visual-container[.//div[contains(@class, 'visual-lineChart')]]"
        xpath_mostrar_como_tabela = "//button[@data-testid='pbimenu-item.Mostrar como uma tabela']"
        
        resultado_3 = iniciar_exportacao_painel_3(
            driver, 
            url_painel_3, 
            xpath_mostrar_como_tabela, 
            pagina_3
        )

        if resultado_3 == "LOGIN_REQUIRED":
            print("\n[AÇÃO NECESSÁRIA] A sua sessão do Power BI expirou.")
            log_print("\n[AÇÃO NECESSÁRIA] A sua sessão do Power BI expirou.")
            return 'LOGIN_REQUIRED'
        
        if not resultado_3:
            print("\n[AVISO] Falha ao exportar do Painel 3.")
            log_print("\n[AVISO] Falha ao exportar do Painel 3.")
            return False


    finally:
        print("[INFO] Fechando o navegador.")
        log_print("[INFO] Fechando o navegador.")
         # Fecha o navegador
         # Certifique-se de que o driver foi inicializado corretamente antes de tentar fechá-lo
         # Isso evita erros caso o driver seja None
        if driver:
            driver.quit()
