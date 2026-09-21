console.log("GoodWe Connector: content.js carregado");

// Guarda o último JSON enviado para não repetir
let ultimoJsonEnviado = "";


/*
    Procura no texto da página a linha JSON
    que o Arduino está imprimindo no Serial Monitor.
*/
function procurarDadosSerial() {

    const textoPagina = document.body.innerText;

    // Formato enviado pelo nosso Arduino
    const regex = /\{"login":\d+,"solar":\d+,"ldr":\d+,"temperatura":-?\d+,"altaDemanda":\d+,"sobrecargaEletrica":\d+,"sobrecargaTermica":\d+\}/g;

    const resultados = textoPagina.match(regex);

    // Ainda não encontrou nenhum dado do Arduino
    if (!resultados || resultados.length === 0) {
        return;
    }

    // Pega a linha mais recente
    const ultimoJson = resultados[resultados.length - 1];

    // Não envia novamente se os dados forem exatamente iguais
    if (ultimoJson === ultimoJsonEnviado) {
        return;
    }

    ultimoJsonEnviado = ultimoJson;

    console.log(
        "GoodWe Connector encontrou:",
        ultimoJson
    );


    // Envia para o background.js
    chrome.runtime.sendMessage(
        {
            msg: "send-output",
            output: ultimoJson
        },
        function(response) {

            if (chrome.runtime.lastError) {

                console.log(
                    "Erro ao enviar:",
                    chrome.runtime.lastError.message
                );

                return;
            }

            console.log(
                "Resposta do backend:",
                response
            );
        }
    );
}


// Procura novos dados duas vezes por segundo
setInterval(procurarDadosSerial, 500);