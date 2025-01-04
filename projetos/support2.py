#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 4 de Janeiro de 2025
"""

from .models import Area, AreaDeInteresse


def get_areas_estudantes(alunos):
    """Retorna dicionário com as áreas de interesse da lista de entrada."""
    usuarios = [aluno.user for aluno in alunos]

    todas_areas = Area.objects.filter(ativa=True)
    areaspfe = {
        area.titulo: (AreaDeInteresse.objects.filter(usuario__in=usuarios, area=area), area.descricao)
        for area in todas_areas
    }

    outras = AreaDeInteresse.objects.filter(usuario__in=usuarios, area__isnull=True)

    return areaspfe, outras

def get_areas_propostas(propostas):
    """Retorna dicionário com as áreas de interesse da lista de entrada."""
    areaspfe = {
        area.titulo: (AreaDeInteresse.objects.filter(proposta__in=propostas, area=area), area.descricao)
        for area in Area.objects.filter(ativa=True)
    }

    outras = AreaDeInteresse.objects.filter(proposta__in=propostas, area__isnull=True)

    return areaspfe, outras
