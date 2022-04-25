#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""

import datetime

from django.core.files.storage import FileSystemStorage
from django.utils import text
from .models import Avaliacao2, ObjetivosDeAprendizagem

from .models import Area, AreaDeInteresse


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

def cria_area_estudante(request, estudante):
    """Cria um objeto Areas e preenche ele."""
    check_values = request.POST.getlist('selection')

    todas_areas = Area.objects.filter(ativa=True)
    for area in todas_areas:
        if area.titulo in check_values:
            if not AreaDeInteresse.objects.filter(area=area, usuario=estudante.user).exists():
                AreaDeInteresse.create_estudante_area(estudante, area).save()
        else:
            if AreaDeInteresse.objects.filter(area=area, usuario=estudante.user).exists():
                AreaDeInteresse.objects.get(area=area, usuario=estudante.user).delete()

    outras = request.POST.get("outras", "").strip()
    if outras != "":
        (outra, _created) = AreaDeInteresse.objects.get_or_create(area=None, usuario=estudante.user)
        outra.ativa = True
        outra.outras = request.POST.get("outras", "")
        outra.save()
    else:
        if AreaDeInteresse.objects.filter(area=None, usuario=estudante.user).exists():
            AreaDeInteresse.objects.get(area=None, usuario=estudante.user).delete()


def get_areas_estudantes(alunos):
    """Retorna dicionário com as áreas de interesse da lista de entrada."""
    areaspfe = {}

    usuarios = []
    for aluno in alunos:
        usuarios.append(aluno.user)

    todas_areas = Area.objects.filter(ativa=True)
    for area in todas_areas:
        count = AreaDeInteresse.objects.filter(usuario__in=usuarios, area=area).count()
        areaspfe[area.titulo] = (count, area.descricao)

    outras = AreaDeInteresse.objects.filter(usuario__in=usuarios, area__isnull=True)

    return areaspfe, outras


def get_areas_propostas(propostas):
    """Retorna dicionário com as áreas de interesse da lista de entrada."""
    areaspfe = {}

    areas = Area.objects.filter(ativa=True)
    for area in areas:
        count = AreaDeInteresse.objects.filter(proposta__in=propostas, area=area).count()
        areaspfe[area.titulo] = (count, area.descricao)

    outras = AreaDeInteresse.objects.filter(proposta__in=propostas, area__isnull=True)

    return areaspfe, outras


# ISSO TEM DE VIRAR UM PARÂMETRO DE INTERFACE NO FUTURO ####
# def get_peso(banca, objetivo):
#     """Calcula peso nas notas da banca em função do objetivo de aprendizado."""
#     if banca == 1:  # (1, 'intermediaria')
#         if objetivo.titulo == "Execução Técnica":
#             return 4.8
#         if objetivo.titulo == "Organização":
#             return 3.6
#         if objetivo.titulo == "Design/Empreendedorismo":
#             return 3.6
#     elif banca == 2:  # ( 2, 'Banca Final'),
#         if objetivo.titulo == "Execução Técnica":
#             return 7.2
#         if objetivo.titulo == "Organização":
#             return 5.4
#         if objetivo.titulo == "Design/Empreendedorismo":
#             return 5.4
#     elif banca == 99:  # ( 99, 'Banca Falconi'),
#         return 0

#     return 0  # Algum erro aconteceu

# Substituir por:
# if tipo_de_avaliacao == 1:  # (1, 'intermediaria')        
#                         julgamento[i].peso = julgamento[i].objetivo.peso_banca_intermediaria
#                     elif tipo_de_avaliacao == 2:  # ( 2, 'Banca Final'),
#                         julgamento[i].peso = julgamento[i].objetivo.peso_banca_intermediaria
#                     elif tipo_de_avaliacao == 99:  # ( 99, 'Banca Falconi'),
#                         julgamento[i].peso = julgamento[i].objetivo.peso_banca_falconi


# Faz o upload de arquivos
def simple_upload(myfile, path="", prefix=""):
    """Faz uploads para o servidor."""
    file_system_storage = FileSystemStorage()
    filename = str(myfile.name.encode('utf-8').decode('ascii', 'ignore'))
    name = path+prefix+text.get_valid_filename(filename)
    filename = file_system_storage.save(name, myfile)
    uploaded_file_url = file_system_storage.url(filename)
    return uploaded_file_url


def get_objetivos_atuais():
    objetivos = ObjetivosDeAprendizagem.objects.all()

    # Só os objetivos atualmente em uso
    hoje = datetime.date.today()
    objetivos = objetivos.filter(data_final__gt=hoje) | objetivos.filter(data_final__isnull=True)

    objetivos = objetivos.order_by("ordem")

    return objetivos

def get_objetivos_alocacao(alocacao):
    """Retorna todos objetivos de aprendizado da época de uma alocação."""
    objetivos = ObjetivosDeAprendizagem.objects.all()

    if alocacao.projeto.semestre == 1:
        mes = 3
    else:
        mes = 9

    data_projeto = datetime.datetime(alocacao.projeto.ano, mes, 1)

    objetivos = objetivos.filter(data_inicial__lt=data_projeto)
    objetivos = objetivos.filter(data_final__gt=data_projeto) | objetivos.filter(data_final__isnull=True)

    objetivos = objetivos.order_by("ordem")

    return objetivos


def get_objetivos_alocacoes(alocacoes):
    """Verifica todos os objetivos de aprendizado de várias alocações."""
    objetivos = None

    if len(alocacoes) > 0:
        objetivos = get_objetivos_alocacao(alocacoes[0])

        for alocacao in alocacoes[1:]:
            objetivos = objetivos | get_objetivos_alocacao(alocacao)

        objetivos = objetivos.order_by("ordem")

    return objetivos


def calcula_objetivos(alocacoes):
    """Calcula notas/conceitos por Objetivo de Aprendizagem."""
    objetivos = get_objetivos_alocacoes(alocacoes)

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

    cores = ["#c3cf95", "#d49fbf", "#ceb5ed", "#9efef9", "#7cfa9f", "#e8c3b9", "#c45890", "#375330", "#a48577"]
    count = 0
    cores_obj = {}
    for objetivo in objetivos_avaliados:
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
