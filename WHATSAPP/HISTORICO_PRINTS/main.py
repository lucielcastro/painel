import os
import time
import base64
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions

# --- Configurações ---
URL_PAGINA_INICIAL = "http://10.51.109.226:5000/"
URL_GRAFICOS = "http://10.51.109.226:5000/graficos"
# DIRETORIO_SALVAR não é mais necessário aqui, definimos o caminho na função.

def salvar_screenshot_pagina_inteira(driver, file_path):
    # ... (sua função auxiliar, sem alterações) ...
    layout_metrics = driver.execute_cdp_cmd("Page.getLayoutMetrics", {})
    width = layout_metrics['contentSize']['width']
    height = layout_metrics['contentSize']['height']
    clip = {'x': 0, 'y': 0, 'width': width, 'height': height, 'scale': 1}
    screenshot_data = driver.execute_cdp_cmd("Page.captureScreenshot", {"clip": clip, "captureBeyondViewport": True})
    
    with open(file_path, 'wb') as f:
        f.write(base64.b64decode(screenshot_data['data']))

def tirar_prints_corrigido():
    print("Iniciando o script com resolução de desktop...")
    caminho_historico_prints = r'C:\Users\lcastro.eficien\Desktop\PAINEL ACOMPANHAMENTO\WHATSAPP\HISTORICO_PRINTS'
    
    # --- CORREÇÃO 1: Garante que a pasta de destino exista ---
    # Se a pasta não existir, este comando a criará.
    os.makedirs(caminho_historico_prints, exist_ok=True)
    
    options = EdgeOptions()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080") 
    options.add_argument("--hide-scrollbars")

    driver = webdriver.Edge(options=options)
    
    try:
        # --- Print da Página Inicial ---
        print(f"Acessando a página inicial: {URL_PAGINA_INICIAL}")
        driver.get(URL_PAGINA_INICIAL)
        time.sleep(2)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo_1 = f"screenshot_pagina_inicial_{timestamp}.png"
        
        # --- CORREÇÃO 2: Junta o caminho da pasta com o nome do arquivo ---
        caminho_completo_1 = os.path.join(caminho_historico_prints, nome_arquivo_1)
        
        # --- CORREÇÃO 3: Passa o caminho completo para a função ---
        salvar_screenshot_pagina_inteira(driver, caminho_completo_1)
        print(f"✅ Print da página inicial salvo em: {caminho_completo_1}")

        # --- Print da Página de Gráficos ---
        print(f"\nAcessando a página de gráficos: {URL_GRAFICOS}")
        driver.get(URL_GRAFICOS)
        time.sleep(2)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo_2 = f"screenshot_pagina_graficos_{timestamp}.png"
        
        # --- REPETE AS CORREÇÕES PARA O SEGUNDO PRINT ---
        caminho_completo_2 = os.path.join(caminho_historico_prints, nome_arquivo_2)
        salvar_screenshot_pagina_inteira(driver, caminho_completo_2)
        print(f"✅ Print da página de gráficos salvo em: {caminho_completo_2}")

    except Exception as e:
        print(f"❌ Ocorreu um erro durante a execução: {e}")
    finally:
        if driver:
            driver.quit()
        print("\nScript finalizado.")

# Executa a função principal corrigida
if __name__ == "__main__":
    tirar_prints_corrigido()