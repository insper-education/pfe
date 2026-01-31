#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""

import datetime
import logging

from django.shortcuts import get_object_or_404

from .models import Pares, Relato

from academica.models import Composicao
from academica.support import filtra_entregas
from academica.support5 import filtra_composicoes

from administracao.models import TipoEvento

from projetos.models import Area, AreaDeInteresse, Configuracao
from projetos.models import Encontro, Evento

from users.models import Alocacao


# Get an instance of a logger
logger = logging.getLogger("django")

def cria_area_estudante(request, estudante):
    """Cria um objeto Areas e preenche ele."""
    check_values = request.POST.getlist("selection")

    todas_areas = Area.objects.filter(ativa=True)
    for area in todas_areas:
        if area.titulo in check_values:
            if not AreaDeInteresse.objects.filter(area=area, usuario=estudante.user).exists():
                area = AreaDeInteresse.objects.create(usuario=estudante.user, area=area)
                area.save()
        else:
            if AreaDeInteresse.objects.filter(area=area, usuario=estudante.user).exists():
                AreaDeInteresse.objects.get(area=area, usuario=estudante.user).delete()

    outras = request.POST.get("outras", "").strip()
    if outras != "":
        outra, _ = AreaDeInteresse.objects.get_or_create(area=None, usuario=estudante.user)
        outra.ativa = True
        outra.outras = request.POST.get("outras", "")
        outra.save()
    else:
        if AreaDeInteresse.objects.filter(area=None, usuario=estudante.user).exists():
            AreaDeInteresse.objects.get(area=None, usuario=estudante.user).delete()


def check_alocacao_semanal(alocacao, ano, semestre, PRAZO):
    # Verifica se todas as bancas do semestre foram avaliadas
    cor = 'b'
    prazo = None
    hoje = datetime.date.today()
    if alocacao and alocacao.horarios and len(alocacao.horarios) >= 11*8:
        cor = 'g'
    else:
        evento = Evento.get_evento(sigla="PAS", ano=ano, semestre=semestre)  # Preenchimento de Alocação Semanal
        if evento:
            prazo = evento.endDate
            if hoje < prazo - datetime.timedelta(days=9):
                cor = 'b'
            elif hoje > prazo:
                cor = 'r'
            else:
                cor = 'y'
    return {"alocacao_semanal": {"cor": cor, "prazo": prazo, "itens": None, "atraso": None}}



def check_relato_quinzenal(alocacao):
    # Verifica se o relato quinzenal foi submetido
    configuracao = get_object_or_404(Configuracao)
    cor = 'b'
    prazo = None
    hoje = datetime.date.today()
    tevento = TipoEvento.objects.get(nome="Relato quinzenal (Individual)")
    evento = Evento.objects.filter(tipo_evento=tevento, endDate__gte=hoje).order_by("endDate").first()

    if evento and evento.endDate - hoje <= datetime.timedelta(days=configuracao.periodo_relato):
        evento_relato_anterior = Evento.objects.filter(tipo_evento=tevento, endDate__lt=hoje).order_by("endDate").last()
        prazo_anterior = evento_relato_anterior.endDate + datetime.timedelta(days=1) if evento_relato_anterior else None    # Senão pega o relato anterior preenchido no último dia
        relato = Relato.objects.filter(alocacao=alocacao, momento__gt=prazo_anterior).exists() if prazo_anterior else False
        if relato:
            cor = 'g'
        else:
            prazo = evento.endDate
            cor = 'r' if evento.endDate == hoje else 'y'
    return {"relato_quinzenal": {"cor": cor, "prazo": prazo, "itens": None, "atraso": None}}




def check_submissao_documentos(alocacao, ano, semestre):
    # Verifica se documentos foram submetido no prazo
    cor = 'b'
    prazo = None
    itens = []
    hoje = datetime.date.today()
    projeto = alocacao.projeto if alocacao else None
    if projeto:
        composicoes = filtra_composicoes(Composicao.objects.filter(entregavel=True), ano, semestre)
        entregas = filtra_entregas(composicoes, projeto, alocacao.aluno.user)
        for entrega in entregas:
            if "evento" in entrega and entrega["evento"] and entrega["evento"].endDate:
                diff = (entrega["evento"].endDate - hoje).days
                if diff < 7:  # 7 dias antes do prazo já avisa o estudante (Eventos são mostrados duas semanas antes do prazo)
                    if entrega["documentos"] and cor not in ['y', 'r']:
                        cor = 'g'
                    else:
                        if not prazo:
                            prazo = entrega["evento"].endDate
                        if diff < 0:
                            cor = 'r'
                        elif cor != 'r':
                            cor = 'y'
                        itens.append( entrega["evento"] )
    return {"submissao_documento": {"cor": cor, "prazo": prazo, "itens": itens, "atraso": None}}


def check_encontros_marcar(alocacao):
    # Verifica se encontros foram marcados
    cor = 'b'
    prazo = None
    agora = datetime.datetime.now()
    encontro_futuro = Encontro.objects.filter(startDate__gt=agora).order_by("startDate").first()
    if encontro_futuro and alocacao and alocacao.projeto:
        encontros_semestre = Encontro.objects.filter(projeto__ano=alocacao.projeto.ano, projeto__semestre=alocacao.projeto.semestre)
        prazo = encontro_futuro.startDate - datetime.timedelta(days=1)
        if encontros_semestre.filter(projeto=alocacao.projeto, tematica=encontro_futuro.tematica).exists():
            cor = 'g'
        elif prazo > agora:
            cor = 'y'
        else:
            cor = 'r'
    return {"encontros_marcar": {"cor": cor, "prazo": prazo, "itens": None, "atraso": None}}



def check_avaliacao_pares(alocacao, sigla, chave):
    # Verifica se avaliação de pares intermediária foi submetida no prazo
    cor = 'b'
    prazo = None
    hoje = datetime.date.today()
    evento = Evento.objects.filter(tipo_evento__sigla=sigla, startDate__gte=hoje).order_by("startDate").first()
    if evento and evento.endDate - hoje <= datetime.timedelta(days=7):
        tipo = 0 if sigla == "API" else 1
        pares = Pares.objects.filter(alocacao_de=alocacao, tipo=tipo).exists()  # (0, "intermediaria"),   # (1, "final"),
        if pares:
            cor = 'g'
        else:
            prazo = evento.endDate
            cor = 'r' if evento.endDate == hoje else 'y'
    return {chave: {"cor": cor, "prazo": prazo, "itens": None, "atraso": None}}



def check_avaliacao_pares_intermediaria(alocacao,):
    return check_avaliacao_pares(alocacao, "API", "avaliacao_pares_intermediaria")


def check_avaliacao_pares_final(alocacao):
    return check_avaliacao_pares(alocacao, "APF", "avaliacao_pares_final")


def ver_pendencias_estudante(user, ano, semestre):
    PRAZO = 7
    context = {}
    if user and user.tipo_de_usuario in [1,2,4]:  # Estudante, Professor ou Administrador
        alocacao = Alocacao.objects.filter(aluno=user.aluno, projeto__ano=ano, projeto__semestre=semestre).last()
    else:
        alocacao = None
    context.update(check_alocacao_semanal(alocacao, ano, semestre, PRAZO))
    context.update(check_relato_quinzenal(alocacao))
    context.update(check_submissao_documentos(alocacao, ano, semestre))
    context.update(check_encontros_marcar(alocacao))
    context.update(check_avaliacao_pares_intermediaria(alocacao))
    context.update(check_avaliacao_pares_final(alocacao))
    return context

