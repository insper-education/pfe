#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""

from django.core.files.storage import FileSystemStorage
from django.utils import text
from .models import ObjetivosDeAprendizagem

from .models import Area, AreaDeInteresse


def converte_conceito(conceito):
    """Converte de Letra para Número."""
    if conceito == "A+":
        return 10
    elif conceito == "A" or conceito == "A ":
        return 9
    elif conceito == "B+":
        return 8
    elif conceito == "B" or conceito == "B ":
        return 7
    elif conceito == "C+":
        return 6
    elif conceito == "C" or conceito == "C ":
        return 5
    elif conceito == "D" or conceito == "D ":
        return 4
    return 0


def converte_letra(nota, mais="+", espaco=""):
    """Converte de Número para Letra."""
    if nota == 10:
        return "A"+mais
    elif nota >= 9:
        return "A"+espaco
    elif nota >= 8:
        return "B"+mais
    elif nota >= 7:
        return "B"+espaco
    elif nota >= 6:
        return "C"+mais
    elif nota >= 5:
        return "C"+espaco
    elif nota >= 4:
        return "D"+espaco
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

    return areaspfe


def get_areas_propostas(propostas):
    """Retorna dicionário com as áreas de interesse da lista de entrada."""
    areaspfe = {}

    areas = Area.objects.filter(ativa=True)
    for area in areas:
        count = AreaDeInteresse.objects.filter(proposta__in=propostas, area=area).count()
        areaspfe[area.titulo] = (count, area.descricao)

    return areaspfe


# ISSO TEM DE VIRAR UM PARÂMETRO DE INTERFACE NO FUTURO ####
def get_peso(banca, objetivo):
    """Calcula peso nas notas da banca em função do objetivo de aprendizado."""
    if banca == 1:  # (1, 'intermediaria')
        if objetivo.titulo == "Execução Técnica":
            return 4.8
        if objetivo.titulo == "Organização":
            return 3.6
        if objetivo.titulo == "Design/Empreendedorismo":
            return 3.6
    elif banca == 2:  # ( 2, 'Banca Final'),
        if objetivo.titulo == "Execução Técnica":
            return 7.2
        if objetivo.titulo == "Organização":
            return 5.4
        if objetivo.titulo == "Design/Empreendedorismo":
            return 5.4
    elif banca == 99:  # ( 99, 'Banca Falconi'),
        return 0

    return 0  # Algum erro aconteceu


# Faz o upload de arquivos
def simple_upload(myfile, path="", prefix=""):
    """Faz uploads para o servidor."""
    file_system_storage = FileSystemStorage()
    filename = file_system_storage.save(path+prefix+text.get_valid_filename(myfile.name), myfile)
    uploaded_file_url = file_system_storage.url(filename)
    return uploaded_file_url


def calcula_objetivos(alocacoes):

    objetivos = ObjetivosDeAprendizagem.objects.all().order_by('id')

    cores = ["#c3cf95", "#d49fbf", "#ceb5ed", "#9efef9","#7cfa9f","#e8c3b9","#c45890"]
    count = 0
    cores_obj = {}
    for objetivo in objetivos:
        cores_obj[objetivo] = cores[count]
        count += 1

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

    for nota in notas:
        for objetivo in objetivos:
            notas[nota][objetivo] = 0
            pesos[nota][objetivo] = 0

    notas_lista = [x.get_edicoes for x in alocacoes]

    for nota2 in notas_lista:
        for nota in nota2:
            if nota[0] == "RII":
                for k,v in nota[1].items():
                    notas["rii"][k] += v[0] * v[1]
                    pesos["rii"][k] += v[1]
            elif nota[0] == "RIG":
                for k,v in nota[1].items():
                    notas["rig"][k] += v[0] * v[1]
                    pesos["rig"][k] += v[1]
            elif nota[0] == "BI":
                for k,v in nota[1].items():
                    notas["bi"][k] += v[0] * v[1]
                    pesos["bi"][k] += v[1]
            elif nota[0] == "RFI":
                for k,v in nota[1].items():
                    notas["rfi"][k] += v[0] * v[1]
                    pesos["rfi"][k] += v[1]
            elif nota[0] == "RFG":
                for k,v in nota[1].items():
                    notas["rfg"][k] += v[0] * v[1]
                    pesos["rfg"][k] += v[1]
            elif nota[0] == "BF":
                for k,v in nota[1].items():
                    notas["bf"][k] += v[0] * v[1]
                    pesos["bf"][k] += v[1]
            elif nota[0] == "API":
                for k,v in nota[1].items():
                    notas["api"][k] += v[0] * v[1]
                    pesos["api"][k] += v[1]
            elif nota[0] == "APG":
                for k,v in nota[1].items():
                    notas["apg"][k] += v[0] * v[1]
                    pesos["apg"][k] += v[1]
            elif nota[0] == "AFI":
                for k,v in nota[1].items():
                    notas["afi"][k] += v[0] * v[1]
                    pesos["afi"][k] += v[1]
            elif nota[0] == "AFG":
                for k,v in nota[1].items():
                    notas["afg"][k] += v[0] * v[1]
                    pesos["afg"][k] += v[1]

    medias_geral = {}
    for objetivo in objetivos:
        medias_geral[objetivo] = {}
        medias_geral[objetivo]["cor"] = cores_obj[objetivo]
        medias_geral[objetivo]["soma"] = 0
        medias_geral[objetivo]["peso"] = 0

    medias_rii = {}
    for objetivo in objetivos:
        if pesos["rii"][objetivo]>0:
            if not objetivo in medias_rii:
                medias_rii[objetivo] = {}
                medias_rii[objetivo]["cor"] = cores_obj[objetivo]
            medias_rii[objetivo]["media"] = notas["rii"][objetivo] / pesos["rii"][objetivo]
            medias_geral[objetivo]["soma"] += notas["rii"][objetivo]
            medias_geral[objetivo]["peso"] += pesos["rii"][objetivo]

    medias_rig = {}
    for objetivo in objetivos:
        if pesos["rig"][objetivo]>0:
            if not objetivo in medias_rig:
                medias_rig[objetivo] = {}
                medias_rig[objetivo]["cor"] = cores_obj[objetivo]
            medias_rig[objetivo]["media"] = notas["rig"][objetivo] / pesos["rig"][objetivo]
            medias_geral[objetivo]["soma"] += notas["rig"][objetivo]
            medias_geral[objetivo]["peso"] += pesos["rig"][objetivo]

    medias_bi = {}
    for objetivo in objetivos:
        if pesos["bi"][objetivo]>0:
            if not objetivo in medias_bi:
                medias_bi[objetivo] = {}
                medias_bi[objetivo]["cor"] = cores_obj[objetivo]
            medias_bi[objetivo]["media"] = notas["bi"][objetivo] / pesos["bi"][objetivo]
            medias_geral[objetivo]["soma"] += notas["bi"][objetivo]
            medias_geral[objetivo]["peso"] += pesos["bi"][objetivo]

    medias_rfi = {}
    for objetivo in objetivos:
        if pesos["rfi"][objetivo]>0:
            if not objetivo in medias_rfi:
                medias_rfi[objetivo] = {}
                medias_rfi[objetivo]["cor"] = cores_obj[objetivo]
            medias_rfi[objetivo]["media"] = notas["rfi"][objetivo] / pesos["rfi"][objetivo]
            medias_geral[objetivo]["soma"] += notas["rfi"][objetivo]
            medias_geral[objetivo]["peso"] += pesos["rfi"][objetivo]

    medias_rfg = {}
    for objetivo in objetivos:
        if pesos["rfg"][objetivo]>0:
            if not objetivo in medias_rfg:
                medias_rfg[objetivo] = {}
                medias_rfg[objetivo]["cor"] = cores_obj[objetivo]
            medias_rfg[objetivo]["media"] = notas["rfg"][objetivo] / pesos["rfg"][objetivo]
            medias_geral[objetivo]["soma"] += notas["rfg"][objetivo]
            medias_geral[objetivo]["peso"] += pesos["rfg"][objetivo]

    medias_bf = {}
    for objetivo in objetivos:
        if pesos["bf"][objetivo]>0:
            if not objetivo in medias_bf:
                medias_bf[objetivo] = {}
                medias_bf[objetivo]["cor"] = cores_obj[objetivo]
            medias_bf[objetivo]["media"] = notas["bf"][objetivo] / pesos["bf"][objetivo]
            medias_geral[objetivo]["soma"] += notas["bf"][objetivo]
            medias_geral[objetivo]["peso"] += pesos["bf"][objetivo]

    # ANTIGAS 
    medias_api = {}
    for objetivo in objetivos:
        if pesos["api"][objetivo]>0:
            if not objetivo in medias_api:
                medias_api[objetivo] = {}
                medias_api[objetivo]["cor"] = cores_obj[objetivo]
            medias_api[objetivo]["media"] = notas["api"][objetivo] / pesos["api"][objetivo]
            medias_geral[objetivo]["soma"] += notas["api"][objetivo]
            medias_geral[objetivo]["peso"] += pesos["api"][objetivo]

    medias_apg = {}
    for objetivo in objetivos:
        if pesos["apg"][objetivo]>0:
            if not objetivo in medias_apg:
                medias_apg[objetivo] = {}
                medias_apg[objetivo]["cor"] = cores_obj[objetivo]
            medias_apg[objetivo]["media"] = notas["apg"][objetivo] / pesos["apg"][objetivo]
            medias_geral[objetivo]["soma"] += notas["apg"][objetivo]
            medias_geral[objetivo]["peso"] += pesos["apg"][objetivo]

    medias_afi = {}
    for objetivo in objetivos:
        if pesos["afi"][objetivo]>0:
            if not objetivo in medias_afi:
                medias_afi[objetivo] = {}
                medias_afi[objetivo]["cor"] = cores_obj[objetivo]
            medias_afi[objetivo]["media"] = notas["afi"][objetivo] / pesos["afi"][objetivo]
            medias_geral[objetivo]["soma"] += notas["afi"][objetivo]
            medias_geral[objetivo]["peso"] += pesos["afi"][objetivo]

    medias_afg = {}
    for objetivo in objetivos:
        if pesos["afg"][objetivo]>0:
            if not objetivo in medias_afg:
                medias_afg[objetivo] = {}
                medias_afg[objetivo]["cor"] = cores_obj[objetivo]
            medias_afg[objetivo]["media"] = notas["afg"][objetivo] / pesos["afg"][objetivo]
            medias_geral[objetivo]["soma"] += notas["afg"][objetivo]
            medias_geral[objetivo]["peso"] += pesos["afg"][objetivo]

    for objetivo in objetivos:
        if medias_geral[objetivo]["peso"] > 0:
            medias_geral[objetivo]["media"] = medias_geral[objetivo]["soma"] / medias_geral[objetivo]["peso"]
        else:
            medias_geral[objetivo]["media"] = -1


    media_individual = {}
    media_grupo = {}

    for media in medias_geral:

        count = 0
        media_individual[media] = {}
        media_individual[media]["cor"] = medias_geral[media]["cor"]
        media_individual[media]["media"] = 0
        if media.avaliacao_aluno and media in medias_api: # antiga
            media_individual[media]["media"] += medias_api[media]["media"]
            count += 1
        if media.avaliacao_aluno and media in medias_afi: # antiga
            media_individual[media]["media"] += medias_afi[media]["media"]
            count += 1
        if media.avaliacao_aluno and media in medias_rii:
            media_individual[media]["media"] += medias_rii[media]["media"]
            count += 1
        if media.avaliacao_aluno and media in medias_rfi:
            media_individual[media]["media"] += medias_rfi[media]["media"]
            count += 1
        if count > 0:
            media_individual[media]["media"] /= count
        else:
            media_individual[media]["media"] = None

        count = 0
        media_grupo[media] = {}
        media_grupo[media]["cor"] = medias_geral[media]["cor"]
        media_grupo[media]["media"] = 0
        
        if media.avaliacao_grupo and media in medias_apg: # antiga
            media_grupo[media]["media"] += medias_apg[media]["media"]
            count += 1
        if media.avaliacao_grupo and media in medias_afg: # antiga
            media_grupo[media]["media"] += medias_afg[media]["media"]
            count += 1
        if media.avaliacao_grupo and media in medias_rig:
            media_grupo[media]["media"] += medias_rig[media]["media"]
            count += 1
        if media.avaliacao_grupo and media in medias_rfg:
            media_grupo[media]["media"] += medias_rfg[media]["media"]
            count += 1
        if media.avaliacao_banca and media in medias_bi:
            media_grupo[media]["media"] += medias_bi[media]["media"]
            count += 1
        if media.avaliacao_banca and media in medias_bf:
            media_grupo[media]["media"] += medias_bf[media]["media"]
            count += 1
        if count > 0:
            media_grupo[media]["media"] /= count
        else:
            media_grupo[media]["media"] = None


    context = {
        "medias_api": medias_api,
        "medias_apg": medias_apg,
        "medias_afi": medias_afi,
        "medias_afg": medias_afg,
        "medias_rii": medias_rii,
        "medias_rig": medias_rig,
        "medias_bi": medias_bi,
        "medias_rfi": medias_rfi,
        "medias_rfg": medias_rfg,
        "medias_bf": medias_bf,
        'medias_geral': medias_geral,
        "media_individual": media_individual,
        "media_grupo": media_grupo,
    }

    return context