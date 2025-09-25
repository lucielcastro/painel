// ===================================================================
// ARQUIVO: static/js/graficos.js (NOVO FICHEIRO)
// Contém toda a lógica JavaScript para criar os gráficos.
// ===================================================================

// Esta função será executada assim que a página HTML carregar completamente.
document.addEventListener('DOMContentLoaded', function () {
    // A variável 'dadosGraficos' é passada pelo HTML e fica disponível globalmente.
    // Verificamos se ela existe antes de continuar.
    if (typeof dadosGraficos === 'undefined' || !dadosGraficos) {
        console.error("Erro: A variável 'dadosGraficos' não foi encontrada ou está vazia.");
        return;
    }

    const chartsContainer = document.getElementById('charts-container');
    if (!chartsContainer) {
        console.error("Erro: O elemento 'charts-container' não foi encontrado no HTML.");
        return;
    }

    // Mapeia os nomes das categorias para títulos e cores
    const configCategorias = {
        'AGUA_FORMAL': { titulo: 'Meta FORMAL - ÁGUA', cor: '#3b82f6' }, // Azul
        'AGUA_INFORMAL': { titulo: 'Meta INFORMAL - ÁGUA', cor: '#22d3ee' }, // Ciano
        'ESGOTO_FORMAL': { titulo: 'Meta FORMAL - ESGOTO', cor: '#22c55e' }, // Verde
        'ESGOTO_INFORMAL': { titulo: 'Meta INFORMAL - ESGOTO', cor: '#a3e635' }  // Lima
    };

    // Itera sobre cada superintendência para criar um grupo de KPIs
    for (const superintendencia in dadosGraficos) {
        const dados_sup = dadosGraficos[superintendencia];
        
        let cardsHtml = ''; // String para acumular o HTML dos cards para esta SUP

        // Itera sobre cada categoria para criar um card de KPI
        for (const categoria in dados_sup) {
            const config = configCategorias[categoria];
            if (!config) continue; // Pula se a categoria não estiver configurada

            const dados = dados_sup[categoria];
            const meta = dados.meta || 0;
            const realizado = dados.realizado || 0;

            const restante = meta > realizado ? meta - realizado : 0;
            const percentualAtingido = meta > 0 ? (realizado / meta) * 100 : 0;
            
            // Gera o HTML para um único card de gráfico
            cardsHtml += `
                <div class="chart-card flex flex-col items-center">
                    <h4 class="text-md font-semibold text-gray-600 mb-3">${config.titulo}</h4>
                    <div class="w-full flex items-center justify-center space-x-4">
                        <div class="text-sm text-left">
                            <p>Meta: <span class="font-bold">${meta.toLocaleString('pt-BR')}</span></p>
                            <p>Realizado: <span class="font-bold">${realizado.toLocaleString('pt-BR')}</span></p>
                        </div>
                        <div class="relative w-24 h-24">
                            <canvas id="chart-${superintendencia.replace(/\s/g, '')}-${categoria}"></canvas>
                            <div class="absolute inset-0 flex items-center justify-center text-xl font-bold text-gray-800">
                                ${percentualAtingido.toFixed(0)}%
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        // Cria o HTML para o grupo da superintendência e insere os cards
        const groupHtml = `
            <div class="kpi-group">
                <h2 class="text-2xl font-bold text-gray-800 mb-4 text-center">${superintendencia}</h2>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    ${cardsHtml}
                </div>
            </div>
        `;
        chartsContainer.innerHTML += groupHtml;
    }

    // Após criar toda a estrutura HTML, inicializa os gráficos
    for (const superintendencia in dadosGraficos) {
        for (const categoria in dadosGraficos[superintendencia]) {
            const config = configCategorias[categoria];
            if (!config) continue;

            const dados = dadosGraficos[superintendencia][categoria];
            const meta = dados.meta || 0;
            const realizado = dados.realizado || 0;
            const restante = meta > realizado ? meta - realizado : 0;

            const canvasId = `chart-${superintendencia.replace(/\s/g, '')}-${categoria}`;
            const ctx = document.getElementById(canvasId).getContext('2d');
            
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    datasets: [{
                        data: [realizado, restante],
                        backgroundColor: [config.cor, '#e5e7eb'],
                        borderColor: '#FFFFFF',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    cutout: '75%',
                    plugins: { legend: { display: false }, tooltip: { enabled: false } }
                }
            });
        }
    }
});