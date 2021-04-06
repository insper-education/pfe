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

# Estudar raise Http404
# from django.http import Http404


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

    outras = request.POST.get("outras", "")
    if outras != "":
        (outra, _created) = AreaDeInteresse.objects.get_or_create(area=None, usuario=estudante.user)
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

    areas = Area.objects.filter(ativa=True)
    for area in areas:
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


#### ISSO TEM DEVIRAR UM PARÂMETRO DE INTERFACE NO FUTURO ####
def get_peso(banca, objetivo):
    """Calcula peso nas notas da banca em função do objetivo de aprendizado."""
    if banca == 1:  # (1, 'intermediaria')
        if objetivo.titulo == "Execução Técnica":
            return 3.6
        if objetivo.titulo == "Organização":
            return 2.7
        if objetivo.titulo == "Design/Empreendedorismo":
            return 2.7
    elif banca == 2:  # ( 2, 'Banca Final'),
        if objetivo.titulo == "Execução Técnica":
            return 8.4
        if objetivo.titulo == "Organização":
            return 6.3
        if objetivo.titulo == "Design/Empreendedorismo":
            return 6.3
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
    }

    pesos = {
        "rii": {},
        "rig": {},
        "bi":  {},
        "rfi": {},
        "rfg": {},
        "bf":  {},
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
            if nota[0] == "RIG":
                for k,v in nota[1].items():
                    notas["rig"][k] += v[0] * v[1]
                    pesos["rig"][k] += v[1]
            if nota[0] == "BI":
                for k,v in nota[1].items():
                    notas["bi"][k] += v[0] * v[1]
                    pesos["bi"][k] += v[1]
            if nota[0] == "RFI":
                for k,v in nota[1].items():
                    notas["rfi"][k] += v[0] * v[1]
                    pesos["rfi"][k] += v[1]
            if nota[0] == "RFG":
                for k,v in nota[1].items():
                    notas["rfg"][k] += v[0] * v[1]
                    pesos["rfg"][k] += v[1]
            if nota[0] == "BF":
                for k,v in nota[1].items():
                    notas["bf"][k] += v[0] * v[1]
                    pesos["bf"][k] += v[1]


    medias_geral = {}
    for objetivo in objetivos:
        medias_geral[objetivo] = {}
        medias_geral[objetivo]["cor"] = cores_obj[objetivo]
        medias_geral[objetivo]["soma"] = 0
        medias_geral[objetivo]["peso"] = 0

    medias_rii = {}
    for objetivo in objetivos:
        medias_rii[objetivo] = {}
        medias_rii[objetivo]["cor"] = cores_obj[objetivo]
        if pesos["rii"][objetivo]>0:
            medias_rii[objetivo]["media"] = notas["rii"][objetivo] / pesos["rii"][objetivo]
            medias_geral[objetivo]["soma"] += notas["rii"][objetivo]
            medias_geral[objetivo]["peso"] += pesos["rii"][objetivo]
        else:
            medias_rii[objetivo]["media"] = 0

    medias_rig = {}
    for objetivo in objetivos:
        medias_rig[objetivo] = {}
        medias_rig[objetivo]["cor"] = cores_obj[objetivo]
        if pesos["rig"][objetivo]>0:
            medias_rig[objetivo]["media"] = notas["rig"][objetivo] / pesos["rig"][objetivo]
            medias_geral[objetivo]["soma"] += notas["rig"][objetivo]
            medias_geral[objetivo]["peso"] += pesos["rig"][objetivo]
        else:
            medias_rig[objetivo]["media"] = 0


    medias_bi = {}
    for objetivo in objetivos:
        medias_bi[objetivo] = {}
        medias_bi[objetivo]["cor"] = cores_obj[objetivo]
        if pesos["bi"][objetivo]>0:
            medias_bi[objetivo]["media"] = notas["bi"][objetivo] / pesos["bi"][objetivo]
            medias_geral[objetivo]["soma"] += notas["bi"][objetivo]
            medias_geral[objetivo]["peso"] += pesos["bi"][objetivo]
        else:
            medias_bi[objetivo]["media"] = 0


    medias_rfi = {}
    for objetivo in objetivos:
        medias_rfi[objetivo] = {}
        medias_rfi[objetivo]["cor"] = cores_obj[objetivo]
        if pesos["rfi"][objetivo]>0:
            medias_rfi[objetivo]["media"] = notas["rfi"][objetivo] / pesos["rfi"][objetivo]
            medias_geral[objetivo]["soma"] += notas["rfi"][objetivo]
            medias_geral[objetivo]["peso"] += pesos["rfi"][objetivo]
        else:
            medias_rfi[objetivo]["media"] = 0


    medias_rfg = {}
    for objetivo in objetivos:
        medias_rfg[objetivo] = {}
        medias_rfg[objetivo]["cor"] = cores_obj[objetivo]
        if pesos["rfg"][objetivo]>0:
            medias_rfg[objetivo]["media"] = notas["rfg"][objetivo] / pesos["rfg"][objetivo]
            medias_geral[objetivo]["soma"] += notas["rfg"][objetivo]
            medias_geral[objetivo]["peso"] += pesos["rfg"][objetivo]
        else:
            medias_rfg[objetivo]["media"] = 0


    medias_bf = {}
    for objetivo in objetivos:
        medias_bf[objetivo] = {}
        medias_bf[objetivo]["cor"] = cores_obj[objetivo]
        if pesos["bf"][objetivo]>0:
            medias_bf[objetivo]["media"] = notas["bf"][objetivo] / pesos["bf"][objetivo]
            medias_geral[objetivo]["soma"] += notas["bf"][objetivo]
            medias_geral[objetivo]["peso"] += pesos["bf"][objetivo]
        else:
            medias_bf[objetivo]["media"] = 0

    for objetivo in objetivos:
        if medias_geral[objetivo]["peso"] > 0:
            medias_geral[objetivo]["media"] = medias_geral[objetivo]["soma"] / medias_geral[objetivo]["peso"]
        else:
            medias_geral[objetivo]["media"] = 0

    context = {
        "medias_rii": medias_rii,
        "medias_rig": medias_rig,
        "medias_bi": medias_bi,
        "medias_rfi": medias_rfi,
        "medias_rfg": medias_rfg,
        "medias_bf": medias_bf,
        'medias_geral': medias_geral,
    }

    return context