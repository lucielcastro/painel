# atualizar_login.py
from NAVEGADOR.login import criar_nova_sessao_manual

# URL de qualquer um dos seus painéis, apenas para iniciar o processo de login
URL_INICIAL = "https://app.powerbi.com/groups/me/reports/8f55c63e-74cf-46ac-aa4d-247c6be2e061/ReportSectioncb86dd011d57a9e9c1d2?experience=power-bi"

def atualizar_login():
    """
    Função para (re)criar a sessão de login no Power BI manualmente.
    """
    print("--- Iniciando processo para (re)criar a sessão de login ---")
    criar_nova_sessao_manual(URL_INICIAL)