from flask import Flask, render_template, request, redirect, send_file
import sqlite3
import uuid
import pandas as pd
import io
from datetime import datetime

app = Flask(__name__)

# As 10 afirmações do Questionário de Afinidade com Áreas de TI.
AFIRMACOES = [
    {
        "id": 1,
        "texto": "Gosto de transformar uma ideia em uma experiência visual com a qual outras pessoas possam interagir."
    },
    {
        "id": 2,
        "texto": "Tenho interesse em entender como as diferentes partes de um sistema se comunicam e como suas regras internas funcionam."
    },
    {
        "id": 3,
        "texto": "Gosto de analisar informações, identificar padrões e utilizar dados para chegar a conclusões."
    },
    {
        "id": 4,
        "texto": "Tenho interesse em automatizar tarefas repetitivas para tornar processos mais rápidos e confiáveis."
    },
    {
        "id": 5,
        "texto": "Gosto de investigar problemas em sistemas e descobrir a causa de comportamentos inesperados."
    },
    {
        "id": 6,
        "texto": "Tenho interesse em compreender como sistemas podem identificar padrões e produzir resultados a partir de dados."
    },
    {
        "id": 7,
        "texto": "Gosto de pensar em maneiras de proteger informações e sistemas contra acessos ou comportamentos não autorizados."
    },
    {
        "id": 8,
        "texto": "Tenho interesse em trabalhar com ambientes, servidores e ferramentas que permitem que aplicações funcionem de maneira estável."
    },
    {
        "id": 9,
        "texto": "Gosto de organizar e interpretar informações para encontrar tendências, relações ou oportunidades de melhoria."
    },
    {
        "id": 10,
        "texto": "Tenho interesse em desenvolver soluções considerando tanto o funcionamento interno do sistema quanto a forma como ele será utilizado pelas pessoas."
    },
]

# Escala Likert fixa de 5 pontos.
ESCALA_LIKERT = [
    (1, "Discordo Totalmente"),
    (2, "Discordo"),
    (3, "Neutro"),
    (4, "Concordo"),
    (5, "Concordo Totalmente"),
]

VALORES_LIKERT_VALIDOS = {str(valor) for valor, _ in ESCALA_LIKERT}

# Áreas de TI padronizadas, usadas como target (y) do modelo SVM.
AREAS_TI = [
    "Front-end",
    "Back-end",
    "DevOps / Infraestrutura",
    "Dados / Data Science",
    "Inteligência Artificial",
    "Segurança da Informação",
]


def conectar_banco():
    return sqlite3.connect("quiz.db")


def criar_banco():

    banco = conectar_banco()
    cursor = banco.cursor()

    colunas_q = ",\n            ".join(
        f"q{n} INTEGER" for n in range(1, 11)
    )

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS respostas (

            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario TEXT UNIQUE NOT NULL,
            data_hora TEXT NOT NULL,
            {colunas_q},
            area_ti_atual TEXT

        )
    """)

    banco.commit()
    banco.close()


def validar_respostas(form):
    """Garante que as 10 afirmações foram respondidas com um valor
    válido da escala Likert (1 a 5). Retorna (respostas, faltantes)."""

    respostas = {}
    faltantes = []

    for afirmacao in AFIRMACOES:
        numero = afirmacao["id"]
        valor = form.get(f"q{numero}", "").strip()

        if valor not in VALORES_LIKERT_VALIDOS:
            faltantes.append(numero)
        else:
            respostas[numero] = int(valor)

    return respostas, faltantes


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/quiz")
def iniciar_quiz():

    usuario_id = str(uuid.uuid4())

    return render_template(
        "quiz.html",
        afirmacoes=AFIRMACOES,
        escala=ESCALA_LIKERT,
        areas=AREAS_TI,
        usuario_id=usuario_id,
        respostas_atual={},
        area_atual="",
        faltantes=[],
    )


@app.route("/finalizar", methods=["POST"])
def finalizar():

    usuario_id = request.form.get("usuario_id") or str(uuid.uuid4())
    area_ti_atual = request.form.get("area_ti_atual", "").strip()

    if area_ti_atual not in AREAS_TI:
        area_ti_atual = None

    respostas, faltantes = validar_respostas(request.form)

    if faltantes:
        return render_template(
            "quiz.html",
            afirmacoes=AFIRMACOES,
            escala=ESCALA_LIKERT,
            areas=AREAS_TI,
            usuario_id=usuario_id,
            respostas_atual=respostas,
            area_atual=area_ti_atual or "",
            faltantes=faltantes,
        ), 400

    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    banco = conectar_banco()
    cursor = banco.cursor()

    colunas_q = ", ".join(f"q{n}" for n in range(1, 11))
    marcadores_q = ", ".join("?" for _ in range(1, 11))
    valores_q = [respostas[n] for n in range(1, 11)]

    try:
        cursor.execute(f"""
            INSERT INTO respostas (
                id_usuario,
                data_hora,
                {colunas_q},
                area_ti_atual
            )
            VALUES (?, ?, {marcadores_q}, ?)
        """, (usuario_id, data_hora, *valores_q, area_ti_atual))

        banco.commit()
    except sqlite3.IntegrityError:
        # Reenvio do mesmo id_usuario (ex.: duplo clique / voltar página):
        # não duplica o registro já salvo.
        pass
    finally:
        banco.close()

    return render_template(
        "resultado.html",
        usuario_id=usuario_id,
        data_hora=data_hora,
        afirmacoes=AFIRMACOES,
        escala=dict(ESCALA_LIKERT),
        respostas=respostas,
        area_ti_atual=area_ti_atual,
    )


@app.route("/relatorio")
def relatorio():

    banco = conectar_banco()

    colunas = ["id_usuario", "data_hora"] + [f"q{n}" for n in range(1, 11)] + ["area_ti_atual"]

    df = pd.read_sql_query(
        f"SELECT {', '.join(colunas)} FROM respostas ORDER BY id",
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
            sheet_name="Respostas"
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
