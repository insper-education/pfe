#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 4 de Janeiro de 2025
"""

import datetime

from .models import Area, AreaDeInteresse, Observacao

from academica.models import Exame
from estudantes.models import Pares, Relato
from operacional.models import Curso
from users.models import Alocacao


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

def get_alocacoes(projeto):
    """Retorna todas as alocações do projeto."""
    if projeto.time_misto:
        # Em caso de time misto, estudantes de fora da instituição não são listados
        cursos_do_insper = Curso.objects.filter(curso_do_insper=True)
        return Alocacao.objects.filter(projeto=projeto, aluno__curso2__in=cursos_do_insper)
    return Alocacao.objects.filter(projeto=projeto)

def get_pares_colegas(projeto, tipo=0):
    alocacoes = Alocacao.objects.filter(projeto=projeto)
    pares = []
    for alocacao in alocacoes:
        pares.append(Pares.objects.filter(alocacao_de__projeto=projeto, alocacao_para=alocacao, tipo=tipo))
    colegas = zip(alocacoes, pares)
    return colegas

def get_nativamente(self):
    """Retorna em string com curso mais nativo da proposta."""

    # Initialize count dictionary for all cursos
    count = {curso: 0 for curso in Curso.objects.all()}
    total = 0

    # Count occurrences of each curso in perfis
    for perfil in self.perfis():
        for curso in perfil.all():
            count[curso] += 1
            total += 1

    if total == 0:
        return " "

    # Find the curso with the maximum count
    keymax = max(count, key=count.get)
    if count[keymax] > total // 2:
        return keymax
    return "?"

def get_relatos(self):
    """Retorna todos os possiveis relatos quinzenais para o projeto."""
    
    proximo = datetime.date.today() + datetime.timedelta(days=14)

    eventos = self.tem_relatos().filter(startDate__lt=proximo).order_by("endDate")

    relatos = []
    avaliados = []  # se o orientador fez alguma avaliação dos relatos
    observacoes = []  # observações do orientador

    exame = Exame.objects.get(titulo="Relato Quinzenal")

    for index in range(len(eventos)):
    
        if not index: # index == 0:
            relato = Relato.objects.filter(alocacao__projeto=self,
                                            momento__lte=eventos[0].endDate + datetime.timedelta(days=1))

            obs = Observacao.objects.filter(projeto=self, exame=exame,
                                            momento__lte=eventos[0].endDate + datetime.timedelta(days=1)).last()
        else:
            relato = Relato.objects.filter(alocacao__projeto=self,
                                            momento__gt=eventos[index-1].endDate + datetime.timedelta(days=1), 
                                            momento__lte=eventos[index].endDate + datetime.timedelta(days=1))

            obs = Observacao.objects.filter(projeto=self, exame=exame,
                                            momento__gt=eventos[index-1].endDate + datetime.timedelta(days=1), 
                                            momento__lte=eventos[index].endDate + datetime.timedelta(days=1)).last()

        avaliado = []
        for r in relato:
            if r.avaliacao > 0:
                avaliado.append([True, r.alocacao.aluno])
            if r.avaliacao == 0:
                avaliado.append([False, r.alocacao.aluno])

        relatos.append([u[0] for u in relato.order_by().values("alocacao").distinct().values_list("alocacao_id")])

        avaliados.append(avaliado)

        observacoes.append(obs)

    return zip(eventos, relatos, avaliados, observacoes)

