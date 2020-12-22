#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""

from django.core.files.storage import FileSystemStorage
from django.utils import text

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

    if banca == 1: #(1, 'intermediaria')
        if objetivo.titulo == "Execução Técnica":
            return 3.6
        if objetivo.titulo == "Organização":
            return 2.7
        if objetivo.titulo == "Design/Empreendedorismo":
            return 2.7
    elif banca == 2: #( 2, 'Banca Final'),
        if objetivo.titulo == "Execução Técnica":
            return 8.4
        if objetivo.titulo == "Organização":
            return 6.3
        if objetivo.titulo == "Design/Empreendedorismo":
            return 6.3
    elif banca == 99: #( 99, 'Banca Falconi'),
        return 0

    return 0 # Algum erro aconteceu


# Faz o upload de arquivos
def simple_upload(myfile, path="", prefix=""):
    """Faz uploads para o servidor."""
    file_system_storage = FileSystemStorage()
    filename = file_system_storage.save(path+prefix+text.get_valid_filename(myfile.name), myfile)
    uploaded_file_url = file_system_storage.url(filename)
    return uploaded_file_url
