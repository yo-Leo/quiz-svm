from flask import Flask, render_template, request, redirect, send_file
import sqlite3
import uuid
import pandas as pd
import io
from datetime import datetime

app = Flask(__name__)

PERGUNTAS = [
    {
        "id": 1,
        "pergunta": "O que significa SVM?",
        "opcoes": {
            "A": "Simple Vector Machine",
            "B": "Support Vector Machine",
            "C": "Statistical Variable Model",
            "D": "Supervised Variable Method"
        },
        "resposta": "B"
    },

    {
        "id": 2,
        "pergunta": "Qual é o principal objetivo de uma SVM em um problema de classificação?",
        "opcoes": {
            "A": "Encontrar a maior quantidade possível de dados",
            "B": "Criar uma fronteira que separe diferentes classes",
            "C": "Remover todos os dados duplicados",
            "D": "Aumentar o tamanho do conjunto de dados"
        },
        "resposta": "B"
    },

    {
        "id": 3,
        "pergunta": "O que são os Support Vectors (vetores de suporte)?",
        "opcoes": {
            "A": "Os pontos mais próximos da fronteira de decisão",
            "B": "Todos os pontos utilizados no treinamento",
            "C": "Os dados que foram removidos durante o treinamento",
            "D": "Os pontos mais distantes de todas as classes"
        },
        "resposta": "A"
    },

    {
        "id": 4,
        "pergunta": "Em uma SVM linear, o que representa a hyperplane?",
        "opcoes": {
            "A": "Uma técnica para remover dados",
            "B": "A fronteira utilizada para separar as classes",
            "C": "O conjunto de dados de teste",
            "D": "O resultado final da previsão"
        },
        "resposta": "B"
    },

    {
        "id": 5,
        "pergunta": "Qual destes é um exemplo de classificação que poderia utilizar SVM?",
        "opcoes": {
            "A": "Classificar e-mails como spam ou não spam",
            "B": "Somar dois números",
            "C": "Ordenar uma lista de números",
            "D": "Calcular a média de uma turma"
        },
        "resposta": "A"
    },

    {
        "id": 6,
        "pergunta": "Para que serve o train_test_split normalmente utilizado antes do treinamento de uma SVM?",
        "opcoes": {
            "A": "Dividir os dados em conjuntos de treinamento e teste",
            "B": "Normalizar os dados",
            "C": "Criar a hyperplane",
            "D": "Escolher automaticamente o kernel"
        },
        "resposta": "A"
    },

    {
        "id": 7,
        "pergunta": "Por que podemos utilizar StandardScaler antes de treinar uma SVM?",
        "opcoes": {
            "A": "Para transformar os dados em texto",
            "B": "Para colocar as características em escalas comparáveis",
            "C": "Para remover a variável alvo",
            "D": "Para aumentar automaticamente a quantidade de dados"
        },
        "resposta": "B"
    },

    {
        "id": 8,
        "pergunta": "Qual destes é um kernel disponível no SVC do Scikit-learn?",
        "opcoes": {
            "A": "rbf",
            "B": "linearize",
            "C": "vector",
            "D": "classify"
        },
        "resposta": "A"
    },

    {
        "id": 9,
        "pergunta": "O que o parâmetro C de uma SVM influencia?",
        "opcoes": {
            "A": "A quantidade de linhas do dataset",
            "B": "O equilíbrio entre uma margem mais ampla e erros de classificação",
            "C": "O número de classes obrigatoriamente",
            "D": "O formato do arquivo Excel"
        },
        "resposta": "B"
    },

    {
        "id": 10,
        "pergunta": "O que acontece quando utilizamos uma SVM treinada para fazer uma previsão?",
        "opcoes": {
            "A": "O modelo recebe novos dados e determina a classe prevista",
            "B": "O modelo apaga os dados utilizados no treinamento",
            "C": "O modelo cria automaticamente um novo dataset",
            "D": "O modelo necessariamente precisa ser treinado novamente para cada previsão"
        },
        "resposta": "A"
    }
]

def conectar_banco():
    return sqlite3.connect("quiz.db")

def criar_banco():

    banco = conectar_banco()
    cursor = banco.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resultados (

            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id TEXT UNIQUE NOT NULL,
            q1 TEXT,
            q2 TEXT,
            q3 TEXT,
            q4 TEXT,
            q5 TEXT,
            q6 TEXT,
            q7 TEXT,
            q8 TEXT,
            q9 TEXT,
            q10 TEXT,
            tempo_segundos INTEGER,
            acertos INTEGER,
            porcentagem REAL,
            data_hora TEXT

        )
    """)

    banco.commit()
    banco.close()


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/quiz")
def iniciar_quiz():

    usuario_id = uuid.uuid4().hex[:8].upper()

    return render_template(
        "quiz.html",
        perguntas=PERGUNTAS,
        usuario_id=usuario_id
    )

@app.route("/finalizar", methods=["POST"])
def finalizar():

    usuario_id = request.form["usuario_id"]

    tempo = int(request.form["tempo"])

    respostas = {}

    acertos = 0

    for pergunta in PERGUNTAS:

        numero = pergunta["id"]

        resposta = request.form.get(
            f"q{numero}",
            ""
        )

        respostas[numero] = resposta

        if resposta == pergunta["resposta"]:

            acertos += 1

    total = len(PERGUNTAS)

    porcentagem = (acertos / total) * 100

    banco = conectar_banco()
    cursor = banco.cursor()

    cursor.execute("""
        INSERT INTO resultados (
            usuario_id,
            q1,
            q2,
            q3,
            q4,
            q5,
            q6,
            q7,
            q8,
            q9,
            q10,
            tempo_segundos,
            acertos,
            porcentagem,
            data_hora
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        usuario_id,

        respostas[1],
        respostas[2],
        respostas[3],
        respostas[4],
        respostas[5],
        respostas[6],
        respostas[7],
        respostas[8],
        respostas[9],
        respostas[10],

        tempo,

        acertos,

        porcentagem,

        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    ))


    banco.commit()
    banco.close()

    return render_template(
        "resultado.html",
        usuario_id=usuario_id,
        acertos=acertos,
        total=total,
        porcentagem=porcentagem,
        tempo=tempo
    )

@app.route("/relatorio")
def relatorio():

    banco = conectar_banco()

    df = pd.read_sql_query(
        "SELECT * FROM resultados",
        banco
    )

    banco.close()

    arquivo = io.BytesIO()

    with pd.ExcelWriter(
        arquivo,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Resultados"
        )


    arquivo.seek(0)


    return send_file(

        arquivo,

        as_attachment=True,

        download_name="relatorio_quiz_svm.xlsx",

        mimetype=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )

if __name__ == "__main__":
    criar_banco()
    app.run(debug=True)