#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""

import datetime
import re

from django.core.files.storage import FileSystemStorage
from django.utils import text

from django.template.defaultfilters import slugify
from django.utils.encoding import force_text


def get_upload_path(instance, filename):
    """Caminhos para armazenar os arquivos."""
    caminho = ""
    #if isinstance(instance, Documento):
    if instance.__class__.__name__ == "Documento":
        if instance.organizacao:
            caminho += slugify(instance.organizacao.sigla_limpa()) + "/"
        if instance.projeto:
            caminho += "projeto" + str(instance.projeto.pk) + '/'
        if instance.usuario:
            caminho += slugify(instance.usuario.username) + '/'
        if caminho == "":
            caminho = "documentos/"
    elif instance.__class__.__name__ == "Projeto":
        caminho += slugify(instance.organizacao.sigla_limpa()) + '/'
        caminho += "projeto" + str(instance.pk) + '/'
    elif instance.__class__.__name__ == "Organizacao":
        caminho += slugify(instance.sigla_limpa()) + "/logotipo/"
    elif instance.__class__.__name__ == "Certificado":
        if instance.projeto and instance.projeto.organizacao:
            caminho += slugify(instance.projeto.organizacao.sigla_limpa()) + '/'
            caminho += "projeto" + str(instance.projeto.pk) + '/'
        if instance.usuario:
            caminho += slugify(instance.usuario.username) + '/'
    elif instance.__class__.__name__ == "Configuracao" or instance.__class__.__name__ == "Administrador":
        caminho += "configuracao/"
    elif instance.__class__.__name__ == "Proposta":
        caminho += "propostas/proposta"+ str(instance.pk) + '/'
    else:  # Arquivo Temporário
        caminho += "tmp/"

    if filename:
        filename = force_text(filename).strip().replace(' ', '_')
        filename = re.sub(r'(?u)[^-\w.]', '', filename)
        return "{0}/{1}".format(caminho, filename)

    return "{0}".format(caminho)


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
    if nota > 9.5:
        return "A"+mais
    elif nota >= 8.5:
        return "A"+espaco
    elif nota >= 7.5:
        return "B"+mais
    elif nota >= 6.5:
        return "B"+espaco
    elif nota >= 5.5:
        return "C"+mais
    elif nota >= 4.5:
        return "C"+espaco
    elif nota >= 3.5:
        return "D"+mais
    elif nota >= 2.5:
        return "D"+espaco
    elif nota >= 1.5:
        return "D"+"-"
    return "I"+espaco


def simple_upload(myfile, path="", prefix=""):
    """Faz uploads para o servidor."""
    file_system_storage = FileSystemStorage()
    filename = str(myfile.name.encode('utf-8').decode('ascii', 'ignore'))
    name = path+prefix+text.get_valid_filename(filename)
    filename = file_system_storage.save(name, myfile)
    uploaded_file_url = file_system_storage.url(filename)
    return uploaded_file_url


def get_objetivos_atuais(objetivos):
    
    # Só os objetivos atualmente em uso
    hoje = datetime.date.today()
    objetivos = objetivos.filter(data_final__gt=hoje) | objetivos.filter(data_final__isnull=True)

    objetivos = objetivos.order_by("ordem")

    return objetivos


def calcula_objetivos(alocacoes):
    """Calcula notas/conceitos por Objetivo de Aprendizagem."""
    #objetivos = get_objetivos_alocacoes(ObjetivosDeAprendizagem.objects.all(), alocacoes)

    valor = {}
    valor["ideal"] = 7.0
    valor["regular"] = 5.0

    notas = {
        "rii": {},
        "rig": {},
        "bi":  {},
        "rfi": {},
        "rfg": {},
        "bf":  {},
        "api": {},  # antiga
        "apg": {},  # antiga
        "afi": {},  # antiga
        "afg": {},  # antiga
    }

    pesos = {
        "rii": {},
        "rig": {},
        "bi":  {},
        "rfi": {},
        "rfg": {},
        "bf":  {},
        "api": {},  # antiga
        "apg": {},  # antiga
        "afi": {},  # antiga
        "afg": {},  # antiga
    }

    notas_lista = [x.get_edicoes for x in alocacoes]

    avaliacoes = [("RII", "rii"), ("RIG", "rig"), ("BI", "bi"), ("RFI", "rfi"), ("RFG", "rfg"),
                  ("BF", "bf"), ("API", "api"), ("APG", "apg"), ("AFI", "afi"), ("AFG", "afg"),]

    objetivos_avaliados = set()

    for nota2 in notas_lista:
        if nota2:
            for nota in nota2:
                for avaliacao in avaliacoes:
                    if nota[0] == avaliacao[0]:
                        for k, val in nota[1].items():
                            if k in notas[avaliacao[1]]:
                                notas[avaliacao[1]][k] += val[0] * val[1]
                                pesos[avaliacao[1]][k] += val[1]
                            else:
                                notas[avaliacao[1]][k] = val[0] * val[1]
                                pesos[avaliacao[1]][k] = val[1]
                                objetivos_avaliados.add(k)

    # Ordena os objetivos pelo indice de ordem deles
    objetivos_avaliados = sorted(objetivos_avaliados, key=lambda oo: oo.ordem)

    cores = ["#c3cf95", "#d49fbf", "#ceb5ed", "#9efef9", "#7cfa9f", "#e8c3b9", "#c45890", "#375330", "#a48577"]
    count = 0
    cores_obj = {}
    for objetivo in objetivos_avaliados:
        if count >= len(cores):
            count = 0
        cores_obj[objetivo] = cores[count]
        count += 1

    medias_geral = {}
    for objetivo in objetivos_avaliados:
        medias_geral[objetivo] = {}
        medias_geral[objetivo]["cor"] = cores_obj[objetivo]
        medias_geral[objetivo]["soma"] = 0
        medias_geral[objetivo]["peso"] = 0

    medias = {}

    for avaliacao in avaliacoes:
        medias[avaliacao[1]] = {}
        for objetivo in objetivos_avaliados:
            if objetivo in pesos[avaliacao[1]] and pesos[avaliacao[1]][objetivo] > 0:
                if objetivo not in medias[avaliacao[1]]:
                    medias[avaliacao[1]][objetivo] = {}
                    medias[avaliacao[1]][objetivo]["cor"] = cores_obj[objetivo]
                medias[avaliacao[1]][objetivo]["media"] = notas[avaliacao[1]][objetivo] / pesos[avaliacao[1]][objetivo]
                medias_geral[objetivo]["soma"] += notas[avaliacao[1]][objetivo]
                medias_geral[objetivo]["peso"] += pesos[avaliacao[1]][objetivo]

    for objetivo in objetivos_avaliados:
        if medias_geral[objetivo]["peso"] > 0:
            media = medias_geral[objetivo]["soma"] / medias_geral[objetivo]["peso"]
            medias_geral[objetivo]["media"] = media
        else:
            medias_geral[objetivo]["media"] = -1

    media_individual = {}
    media_grupo = {}

    for media in medias_geral:

        count = 0
        media_individual[media] = {}
        media_individual[media]["cor"] = medias_geral[media]["cor"]
        media_individual[media]["media"] = 0
        if media.avaliacao_aluno and media in medias["api"]: # antiga
            media_individual[media]["media"] += medias["api"][media]["media"]
            count += 1
        if media.avaliacao_aluno and media in medias["afi"]: # antiga
            media_individual[media]["media"] += medias["afi"][media]["media"]
            count += 1
        if media.avaliacao_aluno and media in medias["rii"]:
            media_individual[media]["media"] += medias["rii"][media]["media"]
            count += 1
        if media.avaliacao_aluno and media in medias["rfi"]:
            media_individual[media]["media"] += medias["rfi"][media]["media"]
            count += 1
        if count > 0:
            media_individual[media]["media"] /= count
        else:
            media_individual[media]["media"] = None

        count = 0
        media_grupo[media] = {}
        media_grupo[media]["cor"] = medias_geral[media]["cor"]
        media_grupo[media]["media"] = 0

        if media.avaliacao_grupo and media in medias["apg"]: # antiga
            media_grupo[media]["media"] += medias["apg"][media]["media"]
            count += 1
        if media.avaliacao_grupo and media in medias["afg"]: # antiga
            media_grupo[media]["media"] += medias["afg"][media]["media"]
            count += 1
        if media.avaliacao_grupo and media in medias["rig"]:
            media_grupo[media]["media"] += medias["rig"][media]["media"]
            count += 1
        if media.avaliacao_grupo and media in medias["rfg"]:
            media_grupo[media]["media"] += medias["rfg"][media]["media"]
            count += 1
        if media.avaliacao_banca and media in medias["bi"]:
            media_grupo[media]["media"] += medias["bi"][media]["media"]
            count += 1
        if media.avaliacao_banca and media in medias["bf"]:
            media_grupo[media]["media"] += medias["bf"][media]["media"]
            count += 1
        if count > 0:
            media_grupo[media]["media"] /= count
        else:
            media_grupo[media]["media"] = None

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
        'medias_geral': medias_geral,
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
