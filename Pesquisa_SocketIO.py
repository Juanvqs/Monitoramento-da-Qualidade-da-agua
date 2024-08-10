from flask import Flask, render_template
from flask_socketio import SocketIO
import numpy as np
import pandas as pd
import time

app = Flask(__name__)
socketio = SocketIO(app)

def ler_dados(caminho_arquivo):
    dados = {'pH': [], 'mercurio': [], 'temperatura': []}
    with open(caminho_arquivo, 'r') as arquivo:
        for linha in arquivo:
            if not linha.strip():
                continue
            try:
                pH, mercurio, temperatura = map(float, linha.split())
                dados['pH'].append(pH)
                dados['mercurio'].append(mercurio)
                dados['temperatura'].append(temperatura)
            except ValueError:
                print(f"Linhas ignoradas: {linha.strip()}")
                continue
    return dados

def calcular_estatisticas(dados):
    estatisticas = {}
    for chave in dados:
        estatisticas[chave] = {
            'media': np.mean(dados[chave]),
            'desvio_padrao': np.std(dados[chave])
        }
    return estatisticas

def classificar_agua(dados):
    limiares = {
        'pH': (6.5, 8.5),
        'mercurio': 0.001,
        'temperatura': (0, 35)
    }
    classificacoes = []
    for i in range(len(dados['pH'])):
        pH = dados['pH'][i]
        mercurio = dados['mercurio'][i]
        temperatura = dados['temperatura'][i]

        if limiares['pH'][0] <= pH <= limiares['pH'][1] and \
           mercurio <= limiares['mercurio'] and \
           limiares['temperatura'][0] <= temperatura <= limiares['temperatura'][1]:
            classificacoes.append('Boa')
        else:
            classificacoes.append('Contaminada')
    dados['classificacao'] = classificacoes
    return dados

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def tratar_conexao():
    print('Cliente conectado')
    while True:
        dados = ler_dados('agua_dados.txt')
        estatisticas = calcular_estatisticas(dados)
        dados_classificados = classificar_agua(dados)

        for chave, valor in estatisticas.items():
            socketio.emit('stats', {'parametro': chave, 'media': valor['media'], 'desvio_padrao': valor['desvio_padrao']})
        
        for i, classificacao in enumerate(dados_classificados['classificacao']):
            socketio.emit('classification', {'amostra': i+1, 'classificacao': classificacao})
        
        time.sleep(10)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
