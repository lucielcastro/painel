# ===================================================================
# ARQUIVO: app.py (MODIFICADO)
# Adicionada a nova rota /graficos.
# ===================================================================
from flask import Flask, render_template
from datetime import datetime
import locale
# Importa a nova função do database
from banco.database import fetch_kpi_data, fetch_ranking_data, fetch_ranking_nla_nle, fetch_dados_graficos , fetch_update_dates_separately

# --- Configurações Iniciais ---
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    print("Aviso: Localidade 'pt_BR.UTF-8' não encontrada.")

app = Flask(__name__)

@app.route('/')
def index():
    """
    Rota principal que busca os dados e renderiza a página do dashboard.
    """
    kpi_data = fetch_kpi_data()
    ranking_agua = fetch_ranking_data('tb_agua', 'total_jan__atual_2025')
    ranking_esgoto = fetch_ranking_data('tb_esgoto', 'total_jan__atual_2025')
    ranking_nla_nle = fetch_ranking_nla_nle()
    
    #data_atualizacao = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    # Chama a nova função e desempacota os 3 valores em variáveis separadas
    data_nla_nle, data_agua, data_esgoto = fetch_update_dates_separately()

    return render_template(
        'dashboard.html', 
        kpis=kpi_data,
        ranking_agua=ranking_agua,
        ranking_esgoto=ranking_esgoto,
        ranking_nla_nle=ranking_nla_nle,
        # Passa cada data como uma variável individual para o HTML
        data_atualizacao_nla_nle=data_nla_nle,
        data_atualizacao_agua=data_agua,
        data_atualizacao_esgoto=data_esgoto
    )

@app.route('/graficos')
def graficos():
    """
    Nova rota para a página de gráficos.
    """
    # Busca os dados processados do CSV
    dados_graficos = fetch_dados_graficos()
    #data_atualizacao = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    data_nla_nle, data_agua, data_esgoto = fetch_update_dates_separately()

    return render_template(
        'graficos.html',
        dados_graficos=dados_graficos,
        data_atualizacao=data_esgoto
    )

if __name__ == '__main__':
    print("--- Dashboard Web Local ---")
    print("Para visualizar, abra seu navegador e acesse:")
    print("[http://127.0.0.1:5000](http://127.0.0.1:5000) (no seu computador)")
    print("http://SEU_IP_LOCAL:5000 (em outros dispositivos na mesma rede)")
    print("Pressione CTRL+C para encerrar o servidor.")
    app.run(host='0.0.0.0', port=5000, debug=False)