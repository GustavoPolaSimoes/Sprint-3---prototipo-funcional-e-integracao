from flask import Flask, request, jsonify, send_from_directory
import json
from datetime import datetime
import os
import time


# CONFIGURAÇÃO DO SERVIDOR
app = Flask(__name__)

PASTA_PROJETO = os.path.dirname(
    os.path.abspath(__file__)
)

# CONFIGURAÇÕES DA RECARGA

# Potência simulada de cada carregador
POTENCIA_CARREGADOR_KW = 7.04

# Valor cobrado por kWh
TARIFA_KWH = 2.00

# 1 segundo real = 60 segundos simulados
# Ou seja: 1 segundo real = 1 minuto de recarga
FATOR_TEMPO = 60

# Cada device recebido do Tinkercad terá seu próprio registro.

carregadores = {}

# CRIA UM NOVO CARREGADOR

def criar_carregador(device):
    numero_vaga = len(carregadores) + 1

    carregador = {

        # Identificação
        "device": device,

        "numeroVaga": numero_vaga,

        "nome": (
            f"Vaga {numero_vaga:02d} - GoodWe HCA G2"
        ),

        # DADOS DO ARDUINO

        "login": 0,

        "solar": 0,

        "ldr": 0,

        "temperatura": 0,

        "altaDemanda": 0,

        "sobrecargaEletrica": 0,

        "sobrecargaTermica": 0,

        "status": "aguardando",

        "ultimaAtualizacao": None,

        # DADOS DA RECARGA

        "sessoesAtivas": 0,

        "carregando": 0,

        "potenciaAtual": 0.0,

        "energiaSessao": 0.0,

        "energiaTotal": 0.0,

        "tempoSessaoMinutos": 0.0,

        "tarifaKWh": TARIFA_KWH,

        "receitaSessao": 0.0,

        "receitaBruta": 0.0,


        "_ultimoInstanteSimulacao": (
            time.monotonic()
        )
    }

    carregadores[device] = carregador

    print("")
    print(
        f">>> NOVO CARREGADOR IDENTIFICADO: "
        f"{carregador['nome']}"
    )

    print(
        f">>> DEVICE: {device}"
    )

    return carregador

# OBTÉM UM CARREGADOR PELO DEVICE
def obter_carregador(device):

    if device not in carregadores:

        return criar_carregador(device)

    return carregadores[device]

# CALCULA O STATUS DE UM CARREGADOR
def calcular_status(carregador):

    # Sobrecarga elétrica ou térmica
    if (
        carregador["sobrecargaEletrica"] == 1
        or carregador["sobrecargaTermica"] == 1
    ):

        return "erro"


    # Alta demanda sem energia solar
    if (
        carregador["altaDemanda"] == 1
        and carregador["solar"] == 0
    ):

        return "alerta"


    # Login ativo e nenhuma condição de bloqueio
    if carregador["login"] == 1:

        return "operacional"


    return "livre"

# ATUALIZA O ESTADO DE RECARGA
def atualizar_estado_recarga(carregador):

    if carregador["login"] == 1:

        carregador["sessoesAtivas"] = 1

    else:

        carregador["sessoesAtivas"] = 0


    # Só fornece potência quando estiver operacional
    if (
        carregador["login"] == 1
        and carregador["status"] == "operacional"
    ):

        carregador["carregando"] = 1

        carregador["potenciaAtual"] = (
            POTENCIA_CARREGADOR_KW
        )

    else:

        carregador["carregando"] = 0

        carregador["potenciaAtual"] = 0.0

# SIMULA ENERGIA E RECEITA DE UM CARREGADOR
def atualizar_simulacao(carregador):

    agora = time.monotonic()

    segundos_reais = (
        agora
        - carregador["_ultimoInstanteSimulacao"]
    )

    carregador[
        "_ultimoInstanteSimulacao"
    ] = agora


    if segundos_reais <= 0:

        return


    atualizar_estado_recarga(carregador)

    if carregador["carregando"] == 0:

        return

    # CONVERTE O TEMPO REAL EM TEMPO SIMULADO

    segundos_simulados = (
        segundos_reais
        * FATOR_TEMPO
    )

    horas_simuladas = (
        segundos_simulados / 3600
    )

    minutos_simulados = (
        segundos_simulados / 60
    )

    energia_adicionada = (
        POTENCIA_CARREGADOR_KW
        * horas_simuladas
    )


    carregador[
        "energiaSessao"
    ] += energia_adicionada


    carregador[
        "energiaTotal"
    ] += energia_adicionada


    carregador[
        "tempoSessaoMinutos"
    ] += minutos_simulados

    receita_adicionada = (
        energia_adicionada
        * TARIFA_KWH
    )


    carregador[
        "receitaSessao"
    ] += receita_adicionada


    carregador[
        "receitaBruta"
    ] += receita_adicionada

# ATUALIZA TODOS OS CARREGADORES
def atualizar_todos_carregadores():

    for carregador in carregadores.values():

        atualizar_simulacao(
            carregador
        )


# PREPARA UM CARREGADOR PARA A API
def carregador_para_resposta(carregador):

    # Remove campos internos
    resposta = {
        chave: valor
        for chave, valor in carregador.items()
        if not chave.startswith("_")
    }


    resposta["potenciaAtual"] = round(
        resposta["potenciaAtual"],
        2
    )

    resposta["energiaSessao"] = round(
        resposta["energiaSessao"],
        2
    )

    resposta["energiaTotal"] = round(
        resposta["energiaTotal"],
        2
    )

    resposta["tempoSessaoMinutos"] = round(
        resposta["tempoSessaoMinutos"],
        1
    )

    resposta["tarifaKWh"] = round(
        resposta["tarifaKWh"],
        2
    )

    resposta["receitaSessao"] = round(
        resposta["receitaSessao"],
        2
    )

    resposta["receitaBruta"] = round(
        resposta["receitaBruta"],
        2
    )


    return resposta

# CALCULA OS INDICADORES DA LOJA
def calcular_resumo():

    sessoes_ativas = 0

    potencia_total = 0.0

    energia_total = 0.0

    receita_bruta = 0.0


    for carregador in carregadores.values():

        sessoes_ativas += (
            carregador["sessoesAtivas"]
        )

        potencia_total += (
            carregador["potenciaAtual"]
        )

        energia_total += (
            carregador["energiaTotal"]
        )

        receita_bruta += (
            carregador["receitaBruta"]
        )


    return {

        "quantidadeCarregadores": (
            len(carregadores)
        ),

        "sessoesAtivas": (
            sessoes_ativas
        ),

        "potenciaTotal": round(
            potencia_total,
            2
        ),

        "energiaTotal": round(
            energia_total,
            2
        ),

        "receitaBruta": round(
            receita_bruta,
            2
        ),

        "tarifaKWh": TARIFA_KWH
    }

# MONTA A RESPOSTA COMPLETA DA API
def montar_resposta_api():

    atualizar_todos_carregadores()


    # Ordena pela Vaga 01, Vaga 02...
    lista_carregadores = sorted(

        carregadores.values(),

        key=lambda carregador:
            carregador["numeroVaga"]
    )


    lista_resposta = [

        carregador_para_resposta(
            carregador
        )

        for carregador
        in lista_carregadores
    ]


    resumo = calcular_resumo()

    # RESPOSTA PRINCIPAL
    resposta = {

        "quantidadeCarregadores":
            resumo["quantidadeCarregadores"],

        "sessoesAtivas":
            resumo["sessoesAtivas"],

        "potenciaTotal":
            resumo["potenciaTotal"],

        "energiaTotal":
            resumo["energiaTotal"],

        "receitaBruta":
            resumo["receitaBruta"],

        "tarifaKWh":
            resumo["tarifaKWh"],

        "carregadores":
            lista_resposta
    }

    if len(lista_resposta) > 0:

        primeiro = lista_resposta[0]

        campos_primeiro_carregador = [

            "device",

            "numeroVaga",

            "nome",

            "login",

            "solar",

            "ldr",

            "temperatura",

            "altaDemanda",

            "sobrecargaEletrica",

            "sobrecargaTermica",

            "status",

            "ultimaAtualizacao",

            "carregando",

            "potenciaAtual",

            "energiaSessao",

            "tempoSessaoMinutos",

            "receitaSessao"
        ]


        for campo in campos_primeiro_carregador:

            resposta[campo] = (
                primeiro[campo]
            )


    else:

        resposta.update({

            "device": None,

            "numeroVaga": None,

            "nome": "Aguardando carregador",

            "login": 0,

            "solar": 0,

            "ldr": 0,

            "temperatura": 0,

            "altaDemanda": 0,

            "sobrecargaEletrica": 0,

            "sobrecargaTermica": 0,

            "status": "aguardando",

            "ultimaAtualizacao": None,

            "carregando": 0,

            "potenciaAtual": 0.0,

            "energiaSessao": 0.0,

            "tempoSessaoMinutos": 0.0,

            "receitaSessao": 0.0
        })


    return resposta

# CORS
@app.after_request
def permitir_acesso(response):

    response.headers[
        "Access-Control-Allow-Origin"
    ] = "*"

    return response

# RECEBE OS DADOS DO TINKERCAD
@app.route(
    "/arduinoserver",
    methods=["GET"]
)
def receber_arduino():

    tipo_mensagem = request.args.get(
        "msg",
        ""
    )

    # OUTPUT DO SERIAL
    if tipo_mensagem == "output":

        mensagem = request.args.get(
            "out",
            ""
        ).strip()

        device = request.args.get(
            "device"
        )


        if not device:

            return (
                "Device não informado",
                400
            )


        try:
            carregador = obter_carregador(
                device
            )

            atualizar_simulacao(
                carregador
            )

            login_anterior = (
                carregador["login"]
            )

            dados_recebidos = json.loads(
                mensagem
            )
        
            # ATUALIZA APENAS ESTE CARREGADOR
            carregador["login"] = int(
                dados_recebidos.get(
                    "login",
                    0
                )
            )


            carregador["solar"] = int(
                dados_recebidos.get(
                    "solar",
                    0
                )
            )


            carregador["ldr"] = int(
                dados_recebidos.get(
                    "ldr",
                    0
                )
            )


            carregador["temperatura"] = int(
                dados_recebidos.get(
                    "temperatura",
                    0
                )
            )


            carregador[
                "altaDemanda"
            ] = int(
                dados_recebidos.get(
                    "altaDemanda",
                    0
                )
            )


            carregador[
                "sobrecargaEletrica"
            ] = int(
                dados_recebidos.get(
                    "sobrecargaEletrica",
                    0
                )
            )


            carregador[
                "sobrecargaTermica"
            ] = int(
                dados_recebidos.get(
                    "sobrecargaTermica",
                    0
                )
            )

            # STATUS
            carregador["status"] = (
                calcular_status(
                    carregador
                )
            )

            if (
                login_anterior == 0
                and carregador["login"] == 1
            ):

                carregador[
                    "energiaSessao"
                ] = 0.0

                carregador[
                    "receitaSessao"
                ] = 0.0

                carregador[
                    "tempoSessaoMinutos"
                ] = 0.0


                print("")

                print(
                    f">>> NOVA SESSÃO INICIADA "
                    f"NA {carregador['nome']}"
                )


            atualizar_estado_recarga(
                carregador
            )


            carregador[
                "ultimaAtualizacao"
            ] = datetime.now().strftime(
                "%H:%M:%S"
            )

            # TERMINAL
            print("")

            print(
                "=========================================="
            )

            print(
                f" {carregador['nome'].upper()}"
            )

            print(
                "=========================================="
            )


            print(
                json.dumps(
                    carregador_para_resposta(
                        carregador
                    ),
                    indent=4,
                    ensure_ascii=False
                )
            )

        except json.JSONDecodeError:

            print("")

            print(
                "ERRO: mensagem inválida recebida:"
            )

            print(mensagem)


        return "", 200

    if tipo_mensagem == "allinputs":

        return jsonify({
            "inputs": []
        })


    return (
        "Servidor Arduino ativo",
        200
    )

# API DO DASHBOARD
@app.route(
    "/api/status",
    methods=["GET"]
)
def status():

    return jsonify(
        montar_resposta_api()
    )

# DASHBOARD
@app.route("/")
def pagina():

    return send_from_directory(
        PASTA_PROJETO,
        "index.html"
    )

# INICIA O SERVIDOR
if __name__ == "__main__":

    print("")

    print(
        "=========================================="
    )

    print(
        " BACKEND GOODWE - MÚLTIPLOS CARREGADORES"
    )

    print(
        "=========================================="
    )

    print("")

    print("Servidor iniciado!")

    print("")

    print(
        "Painel:"
    )

    print(
        "http://localhost:8080"
    )

    print("")

    print(
        "API:"
    )

    print(
        "http://localhost:8080/api/status"
    )

    print("")

    print(
        "Entrada do Tinkercad:"
    )

    print(
        "http://localhost:8080/arduinoserver"
    )

    print("")

    print(
        "Potência por carregador:",
        POTENCIA_CARREGADOR_KW,
        "kW"
    )

    print(
        "Tarifa:",
        "R$",
        TARIFA_KWH,
        "/ kWh"
    )

    print(
        "Simulação:",
        "1 segundo real =",
        FATOR_TEMPO,
        "segundos de recarga"
    )

    print("")

    print(
        "=========================================="
    )

    print("")


    app.run(
        host="localhost",
        port=8080,
        debug=True,
        use_reloader=False
    )
