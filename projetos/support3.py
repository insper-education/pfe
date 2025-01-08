#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 8 de Janeiro de 2025
"""

import datetime
import re

def converte_conceito(conceito):
    """Converte de Letra para Número."""
    if conceito == "A+":
        return 10
    elif conceito in ("A", "A "):
        return 9
    elif conceito == "B+":
        return 8
    elif conceito in ("B", "B "):
        return 7
    elif conceito == "C+":
        return 6
    elif conceito in ("C", "C "):
        return 5
    elif conceito in ("D+", "D+ "):
        return 4
    elif conceito in ("D", "D "):
        return 3
    elif conceito in ("D-", "D- "):
        return 2
    return 0


def converte_letra(nota, mais="+", espaco=""):
    """Converte de Número para Letra."""

    if nota is None:
        return None
    
    #if nota > 9.5:
    if nota > 9.99:
        return "A"+mais
    #elif nota >= 8.5:
    elif nota >= 9:
        return "A"+espaco
    #elif nota >= 7.5:
    elif nota >= 8:
        return "B"+mais
    #elif nota >= 6.5:
    elif nota >= 7:
        return "B"+espaco
    #elif nota >= 5.5:
    elif nota >= 6:
        return "C"+mais
    #elif nota >= 4.5:
    elif nota >= 5:
        return "C"+espaco
    #elif nota >= 3.5:
    elif nota >= 4:
        return "D"+mais
    #elif nota >= 2.5:
    elif nota >= 3:
        return "D"+espaco
    #elif nota >= 1.5:
    elif nota >= 2:
        return "D"+"-"
    return "I"+espaco



def get_objetivos_atuais(objetivos):
    
    # Só os objetivos atualmente em uso
    hoje = datetime.date.today()
    objetivos = objetivos.filter(data_final__gt=hoje) | objetivos.filter(data_final__isnull=True)

    objetivos = objetivos.order_by("ordem")

    return objetivos


def calcula_objetivos(alocacoes):
    """Calcula notas/conceitos por Objetivo de Aprendizagem."""

    avaliacoes = ["rii", "rig", "bi", "rfi", "rfg", "bf", "api", "apg", "afi", "afg"]

    notas = {key: {} for key in avaliacoes}
    pesos = {key: {} for key in avaliacoes}
    
    notas_lista = [x.get_edicoes for x in alocacoes]
    
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

