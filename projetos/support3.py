#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 8 de Janeiro de 2025
"""

import datetime
import re

from academica.models import Exame
from projetos.models import Avaliacao2

from users.models import Alocacao

from academica.support2 import get_objetivos
from academica.support4 import get_notas_estudante

def get_objetivos_atuais(objetivos):
    
    # Só os objetivos atualmente em uso
    hoje = datetime.date.today()
    objetivos = objetivos.filter(data_final__gt=hoje) | objetivos.filter(data_final__isnull=True)

    objetivos = objetivos.order_by("ordem")

    return objetivos


def get_edicoes_aluno(estudante):
    """Recuper as notas do Estudante."""
    edicao = {}  # dicionário para cada alocação do estudante (por exemplo DP, ou Capstone Avançado)

    siglas = [
        ("BI", "O"),
        ("BF", "O"), 
        ("RP", "N"), 
        ("RIG", "O"), 
        ("RFG", "O"), 
        ("RII", "I"), 
        ("RFI", "I"), 
        # NÃO MAIS USADAS, FORAM USADAS QUANDO AINDA EM DOIS SEMESTRES
        ("PPF", "N"), 
        ("API", "NI"), 
        ("AFI", "NI"), 
        ("APG", "O"), 
        ("AFG", "O"),
        ]
    exame = {}

    exame = {sigla: Exame.objects.get(sigla=sigla) for sigla, _ in siglas}

    alocacoes = Alocacao.objects.filter(aluno=estudante.pk)
    for alocacao in alocacoes:

        notas = []  # iniciando uma lista de notas vazia

        for sigla, tipo in siglas:
            if tipo == "O":  # Avaliações de Objetivos
                avaliacoes = Avaliacao2.objects.filter(projeto=alocacao.projeto, exame=exame[sigla])
            elif tipo == "I":  # Individual
                avaliacoes = Avaliacao2.objects.filter(alocacao=alocacao, exame=exame[sigla])
            elif tipo == "N":  # Notas
                avaliacoes = Avaliacao2.objects.filter(projeto=alocacao.projeto, exame=exame[sigla])
                avaliacao = avaliacoes.order_by("momento").last()
                if avaliacao and avaliacao.nota is not None:
                    notas.append((sigla, float(avaliacao.nota), avaliacao.peso / 100 if avaliacao.peso else 0))
                continue
            elif tipo == "NI":  # Notas Individuais
                avaliacoes = Avaliacao2.objects.filter(alocacao=alocacao, exame=exame[sigla])

            if avaliacoes:
                if tipo in ["O", "I", "NI"]:
                    nota, peso, _ = get_objetivos(estudante, avaliacoes)
                    notas.append((sigla, nota, peso / 100 if peso else 0))

        edicao[f"{alocacao.projeto.ano}.{alocacao.projeto.semestre}"] = notas

    return edicao


def get_notas_alocacao(alocacao, checa_banca=True):
    """Retorna notas do estudante no projeto."""
    edicoes = get_notas_estudante(alocacao.aluno, ano=alocacao.projeto.ano, semestre=alocacao.projeto.semestre, checa_banca=checa_banca)
    return edicoes[str(alocacao.projeto.ano)+"."+str(alocacao.projeto.semestre)]

def get_edicoes_alocacao(self):
    """Retorna objetivos."""
    edicoes = get_edicoes_aluno(self.aluno)
    semestre = str(self.projeto.ano)+"."+str(self.projeto.semestre)
    if semestre in edicoes:
        return edicoes[semestre]
    return None

# EVITAR USAR POIS MISTURA SEMESTRES (VER GET_OAS)
def calcula_objetivos(alocacoes):
    """Calcula notas/conceitos por Objetivo de Aprendizagem."""

    avaliacoes = ["rii", "rig", "bi", "rfi", "rfg", "bf", "api", "apg", "afi", "afg"]

    notas = {key: {} for key in avaliacoes}
    pesos = {key: {} for key in avaliacoes}
    
    notas_lista = [get_edicoes_alocacao(x) for x in alocacoes]
    
    objetivos_avaliados = set()

    for nota2 in notas_lista:
        for nota in nota2:
            avaliacao = nota[0].lower()
            if avaliacao in notas:
                for k, val in nota[1].items():
                    notas[avaliacao][k] = notas[avaliacao].get(k, 0) + val[0] * val[1]
                    pesos[avaliacao][k] = pesos[avaliacao].get(k, 0) + val[1]
                    objetivos_avaliados.add(k)


    # Ordena os objetivos pelo indice de ordem deles
    objetivos_avaliados = sorted(objetivos_avaliados, key=lambda oo: oo.ordem)

    cores = ["#c3cf95", "#d49fbf", "#ceb5ed", "#9efef9", "#7cfa9f", "#e8c3b9", "#c45890", "#375330", "#a48577"]
    cores_obj = {objetivo: cores[i % len(cores)] for i, objetivo in enumerate(objetivos_avaliados)}

    medias_geral = {}
    for objetivo in objetivos_avaliados:
        medias_geral[objetivo] = {"cor": cores_obj[objetivo], "soma": 0, "peso": 0}

    medias = {}
    for avaliacao in avaliacoes:
        medias[avaliacao] = {}
        for objetivo in objetivos_avaliados:
            if objetivo in pesos[avaliacao] and pesos[avaliacao][objetivo] > 0:
                if objetivo not in medias[avaliacao]:
                    medias[avaliacao][objetivo] = {}
                    medias[avaliacao][objetivo]["cor"] = cores_obj[objetivo]
                medias[avaliacao][objetivo]["media"] = notas[avaliacao][objetivo] / pesos[avaliacao][objetivo]
                medias_geral[objetivo]["soma"] += notas[avaliacao][objetivo]
                medias_geral[objetivo]["peso"] += pesos[avaliacao][objetivo]

    for objetivo in objetivos_avaliados:
        if medias_geral[objetivo]["peso"] > 0:
            media = medias_geral[objetivo]["soma"] / medias_geral[objetivo]["peso"]
            medias_geral[objetivo]["media"] = media
        else:
            medias_geral[objetivo]["media"] = -1

    media_individual = {}
    media_grupo = {}

    for media in medias_geral:

        media_individual[media] = {
            "cor": medias_geral[media]["cor"],
            "media": 0
        }

        count = 0
        avaliacoes_indiv = ["api", "afi", "rii", "rfi"]

        for avaliacao in avaliacoes_indiv:
            if media.avaliacao_aluno and media in medias[avaliacao]:
                media_individual[media]["media"] += medias[avaliacao][media]["media"]
                count += 1

        media_individual[media]["media"] = media_individual[media]["media"] / count if count > 0 else None


        media_grupo[media] = {
            "cor": medias_geral[media]["cor"],
            "media": 0
        }

        count = 0
        avaliacoes_grupo = ["apg", "afg", "rig", "rfg"]
        avaliacoes_banca = ["bi", "bf"]

        for avaliacao in avaliacoes_grupo:
            if media.avaliacao_grupo and media in medias[avaliacao]:
                media_grupo[media]["media"] += medias[avaliacao][media]["media"]
                count += 1

        for avaliacao in avaliacoes_banca:
            if media.avaliacao_banca and media in medias[avaliacao]:
                media_grupo[media]["media"] += medias[avaliacao][media]["media"]
                count += 1

        media_grupo[media]["media"] = media_grupo[media]["media"] / count if count > 0 else None

    context = {
        "medias_api": medias["api"],
        "medias_apg": medias["apg"],
        "medias_afi": medias["afi"],
        "medias_afg": medias["afg"],
        "medias_rii": medias["rii"],
        "medias_rig": medias["rig"],
        "medias_bi": medias["bi"],
        "medias_rfi": medias["rfi"],
        "medias_rfg": medias["rfg"],
        "medias_bf": medias["bf"],
        "medias_geral": medias_geral,
        "media_individual": media_individual,
        "media_grupo": media_grupo,
    }

    return context


def cap_name(name):
    """Capitaliza palavras."""
    excecoes = ["e", "da", "de", "di", "do", "du", "das", "dos",
                "la", "las", "les", "los", "van", "von", "y", "del"]
    items = []
    for item in re.split('([ \(")])', name):
        if item.lower() in excecoes:
            items.append(item.lower())
        else:
            items.append(item.capitalize())
    return ''.join(items)

# Calcula a média de uma lista de notas
def media(notas_lista):
    notas = [float(i) for i in notas_lista if i]
    if not notas:
        return None
    return sum(notas) / len(notas)

# Didide pela proporção de 5 e 7
def divide57(notas_lista):
    valores = [0, 0, 0]
    if not notas_lista:
        return valores
    for i in notas_lista:
        if i:
            if i < 5:
                valores[0] += 1
            elif i > 7:
                valores[2] += 1
            else:
                valores[1] += 1
    return valores

