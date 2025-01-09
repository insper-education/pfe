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
from academica.support import filtra_composicoes, filtra_entregas

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
                AreaDeInteresse.create_estudante_area(estudante, area).save()
        else:
            if AreaDeInteresse.objects.filter(area=area, usuario=estudante.user).exists():
                AreaDeInteresse.objects.get(area=area, usuario=estudante.user).delete()

    outras = request.POST.get("outras", "").strip()
    if outras != "":
        (outra, _) = AreaDeInteresse.objects.get_or_create(area=None, usuario=estudante.user)
        outra.ativa = True
        outra.outras = request.POST.get("outras", "")
        outra.save()
    else:
        if AreaDeInteresse.objects.filter(area=None, usuario=estudante.user).exists():
            AreaDeInteresse.objects.get(area=None, usuario=estudante.user).delete()


def check_alocacao_semanal(alocacao, ano, semestre, PRAZO):
    # Verifica se todas as bancas do semestre foram avaliadas
    context = {}
    alocacao_semanal = 'b'
    alocacao_semanal__prazo = None
    hoje = datetime.date.today()
    if len(alocacao.horarios) >= 11*8:
        alocacao_semanal = 'g'
    else:
        evento = Evento.get_evento(sigla="IA", ano=ano, semestre=semestre)  # Início das aulas
        if evento:
            alocacao_semanal__prazo = evento.endDate + datetime.timedelta(days=(PRAZO+4))
            if hoje < evento.endDate + datetime.timedelta(days=4):
                alocacao_semanal = 'b'
            elif hoje > alocacao_semanal__prazo:
                alocacao_semanal = 'r'
            else:
                alocacao_semanal = 'y'
    context["alocacao_semanal"] = (alocacao_semanal, alocacao_semanal__prazo)
    return context


def check_relato_quinzenal(alocacao):
    # Verifica se o relato quinzenal foi submetido
    configuracao = get_object_or_404(Configuracao)
    context = {}
    relato_quinzenal = 'b'
    relato_quinzenal__prazo = None
    hoje = datetime.date.today()
    tevento = TipoEvento.objects.get(nome="Relato quinzenal (Individual)")
    prazo = Evento.objects.filter(tipo_evento=tevento, endDate__gte=hoje).order_by("endDate").first()

    if prazo and prazo.endDate - hoje <= datetime.timedelta(days=configuracao.periodo_relato):
        relato_anterior = Evento.objects.filter(tipo_evento=tevento, endDate__lt=hoje).order_by("endDate").last()
        prazo_anterior = relato_anterior.endDate if relato_anterior else None
        relato = Relato.objects.filter(alocacao=alocacao, momento__gt=prazo_anterior).exists() if prazo_anterior else False
        if relato:
            relato_quinzenal = 'g'
        else:
            relato_quinzenal__prazo = prazo.endDate
            relato_quinzenal = 'r' if prazo.endDate == hoje else 'y'

    context["relato_quinzenal"] = (relato_quinzenal, relato_quinzenal__prazo)
    return context

def check_submissao_documento(alocacao, ano, semestre):
    # Verifica se documentos foram submetido no prazo
    context = {}
    submissao_documento = 'b'
    submissao_documento__prazo = None
    hoje = datetime.date.today()
    projeto = alocacao.projeto  
    if projeto:
        composicoes = filtra_composicoes(Composicao.objects.filter(entregavel=True), ano, semestre)
        entregas = filtra_entregas(composicoes, projeto, alocacao.aluno.user)
        for entrega in entregas:
            diff = (entrega["evento"].endDate - hoje).days
            if diff < 7:  # 7 dias antes do prazo já avisa o estudante (Eventos são mostrados duas semanas antes do prazo)
                if entrega["documentos"] and submissao_documento not in ['y', 'r']:
                    submissao_documento = 'g'
                else:
                    if not submissao_documento__prazo:
                        submissao_documento__prazo = entrega["evento"].endDate
                    if diff < 0:
                        submissao_documento = 'r'
                    elif submissao_documento != 'r':
                        submissao_documento = 'y'
    context["submissao_documento"] = (submissao_documento, submissao_documento__prazo)
    return context

def check_encontros_marcar(alocacao):
    # Verifica se encontros foram marcados
    context = {}
    encontros_marcar = 'b'
    encontros_marcar__prazo = None
    hoje = datetime.date.today()
    encontros = Encontro.objects.filter(startDate__gt=hoje).order_by("startDate")
    if encontros:
        encontros_marcar__prazo = encontros.first().startDate - datetime.timedelta(days=1)
        if encontros.filter(projeto=alocacao.projeto).exists():
            encontros_marcar = 'g'
        else:
            encontros_marcar = 'y'
    context["encontros_marcar"] = (encontros_marcar, encontros_marcar__prazo)
    return context


def check_avaliacao_pares(alocacao, sigla, chave):
    # Verifica se avaliação de pares intermediária foi submetida no prazo
    context = {}
    avaliacao_pares = 'b'
    avaliacao_pares_prazo = None
    hoje = datetime.date.today()
    prazo = Evento.objects.filter(tipo_evento__sigla=sigla, startDate__gte=hoje).order_by("startDate").first()
    if prazo and prazo.endDate - hoje <= datetime.timedelta(days=7):
        pares = Pares.objects.filter(alocacao_de=alocacao, tipo=0).exists()  # (0, "intermediaria"),   # (1, "final"),
        if pares:
            avaliacao_pares = 'g'
        else:
            avaliacao_pares_prazo = prazo.endDate
            avaliacao_pares = 'r' if prazo.endDate == hoje else 'y'

    context[chave] = (avaliacao_pares, avaliacao_pares_prazo)
    return context

def check_avaliacao_pares_intermediaria(alocacao,):
    return check_avaliacao_pares(alocacao, "API", "avaliacao_pares_intermediaria")

def check_avaliacao_pares_final(alocacao):
    return check_avaliacao_pares(alocacao, "APF", "avaliacao_pares_final")


def ver_pendencias_estudante(user, ano, semestre):
    PRAZO = 7
    context = {}
    if user.tipo_de_usuario in [1,2,4]:  # Estudante, Professor ou Administrador
        alocacao = Alocacao.objects.filter(aluno=user.aluno, projeto__ano=ano, projeto__semestre=semestre).last()
        if alocacao:
            context.update(check_alocacao_semanal(alocacao, ano, semestre, PRAZO))
            context.update(check_relato_quinzenal(alocacao))
            context.update(check_submissao_documento(alocacao, ano, semestre))
            context.update(check_encontros_marcar(alocacao))
            context.update(check_avaliacao_pares_intermediaria(alocacao))
            context.update(check_avaliacao_pares_final(alocacao))
    return context

