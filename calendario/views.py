#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Dezembro de 2020
"""

import datetime
import dateutil.parser

from icalendar import Calendar, Event, vCalAddress

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.sites.models import Site
from django.db import transaction
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from django.shortcuts import render, redirect, get_object_or_404

from users.models import PFEUser, Aluno

from projetos.models import Banca, Configuracao, Evento

from projetos.tipos import TIPO_EVENTO



def get_calendario_context(user=None):
    """Contexto para gerar calendário."""
    eventos = Evento.objects.all()

    # Estudantes e parceiros só conseguem ver os eventos até o semestre atual
    configuracao = get_object_or_404(Configuracao)

    # Se usuário não for Professor nem Admin
    if user and user.tipo_de_usuario != 2 and user.tipo_de_usuario != 4:
        if configuracao.semestre == 1:
            eventos_ano = eventos.filter(startDate__year__lt=configuracao.ano)
            eventos_semestre = eventos.filter(startDate__month__lte=7, startDate__year=configuracao.ano)
            eventos = eventos_ano | eventos_semestre
        else:
            eventos = eventos.filter(startDate__year__lte=configuracao.ano)

    eventos_gerais = eventos.exclude(tipo_de_evento=12).\
        exclude(tipo_de_evento=40).\
        exclude(tipo_de_evento=41).\
        exclude(tipo_de_evento=20).\
        exclude(tipo_de_evento=30).\
        exclude(tipo_de_evento__gte=100)

    # 12, 'Aula PFE'
    aulas = eventos.filter(tipo_de_evento=12)

    # 40, 'Laboratório'
    laboratorios = eventos.filter(tipo_de_evento=40)

    # 41, 'Semana de Provas'
    provas = eventos.filter(tipo_de_evento=41)

    # 20, 'Relato Quinzenal'
    quinzenais = eventos.filter(tipo_de_evento=20)

    # 30, 'Feedback dos Estudantes sobre PFE'
    feedbacks = eventos.filter(tipo_de_evento=30)

    # Eventos da coordenação
    coordenacao = Evento.objects.filter(tipo_de_evento__gte=100)

    # ISSO NAO ESTA BOM, FAZER ALGO MELHOR

    # TAMBÉM ESTOU USANDO NO CELERY PARA AVISAR DOS EVENTOS

    context = {
        "eventos": eventos_gerais,
        "aulas": aulas,
        "laboratorios": laboratorios,
        "provas": provas,
        "quinzenais": quinzenais,
        "feedbacks": feedbacks,
        "coordenacao": coordenacao,
        "semestre": configuracao.semestre,
        "tipos_eventos": TIPO_EVENTO,
        "Evento": Evento,
    }

    return context


@login_required
def calendario(request):
    """Para exibir um calendário de eventos."""
    context = get_calendario_context(request.user)
    if context:
        return render(request, 'calendario/calendario.html', context)

    return HttpResponse("Problema ao gerar calendário.", status=401)


@login_required
def calendario_limpo(request):
    """Para exibir um calendário de eventos."""
    context = get_calendario_context(request.user.pk)
    if context:
        context['limpo'] = True
        return render(request, 'calendario/calendario.html', context)

    return HttpResponse("Problema ao gerar calendário.", status=401)


def adicionar_participante_em_evento(ical_event, usuario):
    """Adiciona um usuario em um evento."""
    # REMOVER OS xx DOS EMAILS
    atnd = vCalAddress("MAILTO:{}".format(usuario.email))
    atnd.params["CN"] = "{0}".format(usuario.get_full_name())
    atnd.params["ROLE"] = "REQ-PARTICIPANT"
    ical_event.add("attendee", atnd, encode=0)


def gera_descricao_banca(banca, alunos):
    """Gera um descrição para colocar no aviso do agendamento."""
    description = "Banca do Projeto {0}".format(banca.projeto)
    if banca.link:
        description += "\n\nLink: {0}".format(banca.link)
    description += "\n\nOrientador:\n- {0}".format(banca.projeto.orientador)
    if banca.membro1 or banca.membro2 or banca.membro3:
        description += "\n\nMembros da Banca:"
        if banca.membro1:
            description += "\n- {0}".format(banca.membro1.get_full_name())
        if banca.membro2:
            description += "\n- {0}".format(banca.membro2.get_full_name())
        if banca.membro3:
            description += "\n- {0}".format(banca.membro3.get_full_name())
    description += "\n\nAlunos:"
    for aluno in alunos:
        description += "\n- {0}".format(aluno.user.get_full_name())
    return description


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def export_calendar(request, event_id):
    """Gera evento de calendário."""
    banca = get_object_or_404(Banca, pk=event_id)

    cal = Calendar()
    site = Site.objects.get_current()

    cal.add('prodid', '-//PFE//Insper//')
    cal.add('version', '2.0')

    site_token = site.domain.split('.')
    site_token.reverse()
    site_token = '.'.join(site_token)

    ical_event = Event()

    ical_event['uid'] = "Banca{0}{1}{2}".format(
        banca.startDate.strftime("%Y%m%d%H%M%S"),
        banca.projeto.pk,
        banca.tipo_de_banca)
    ical_event.add('summary', "Banca {0}".format(banca.projeto))
    ical_event.add('dtstart', banca.startDate)
    ical_event.add('dtend', banca.endDate)
    ical_event.add('dtstamp', datetime.datetime.now().date())
    ical_event.add('tzid', "America/Sao_Paulo")
    ical_event.add('location', banca.location)

    ical_event.add('geo', (-25.598749, -46.676368))

    cal_address = vCalAddress('MAILTO:lpsoares@insper.edu.br')
    cal_address.params["CN"] = "Luciano Pereira Soares"
    ical_event.add('organizer', cal_address)

    if banca.membro1:
        adicionar_participante_em_evento(ical_event, banca.membro1)

    if banca.membro2:
        adicionar_participante_em_evento(ical_event, banca.membro2)

    if banca.membro3:
        adicionar_participante_em_evento(ical_event, banca.membro3)

    alunos = Aluno.objects.filter(alocacao__projeto=banca.projeto)\
        .filter(trancado=False)

    for aluno in alunos:
        adicionar_participante_em_evento(ical_event, aluno.user)

    description = gera_descricao_banca(banca, alunos)

    ical_event.add('description', description)

    cal.add_component(ical_event)

    response = HttpResponse(cal.to_ical())
    response['Content-Type'] = 'text/calendar'
    response['Content-Disposition'] = \
        'attachment; filename=Banca{0}.ics'.format(banca.pk)

    return response


@login_required
@transaction.atomic
@permission_required('users.altera_professor', raise_exception=True)
def atualiza_evento(request):
    """Ajax para atualizar eventos."""
    try:
        event_id = int(request.POST.get('id', None))
        if event_id:
            evento = Evento.objects.get(id=event_id)
        else:
            evento = Evento.create()
    except Evento.DoesNotExist:
        return HttpResponseNotFound("<h1>Evento não encontrado!</h1>")

    evento.tipo_de_evento = int(request.POST.get("type", None))
    evento.startDate = dateutil.parser.parse(request.POST.get("startDate", None))
    evento.endDate = dateutil.parser.parse(request.POST.get("endDate", None))
    evento.location = request.POST.get("location", '')[:Evento._meta.get_field("location").max_length] 
    evento.observacao = request.POST.get("observation", '')[:Evento._meta.get_field("observacao").max_length]
    evento.descricao = request.POST.get("descricao", '')[:Evento._meta.get_field("descricao").max_length]
    evento.save()

    data = {
        "atualizado": True,
        "evento_id": evento.id,
    }

    return JsonResponse(data)


@login_required
@transaction.atomic
@permission_required('users.altera_professor', raise_exception=True)
def remove_evento(request):
    """Ajax para remover eventos."""
    event_id = int(request.POST.get('id', None))
    evento = get_object_or_404(Evento, id=event_id)    
    evento.delete()

    return JsonResponse({"atualizado": True,})


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def copia_calendario(request):
    """Copia eventos de um semestre para o outro."""
    configuracao = get_object_or_404(Configuracao)

    if configuracao.semestre == 1:
        eventos = Evento.objects.filter(startDate__month__lte=7, startDate__year=configuracao.ano)
    else:
        eventos_ano = Evento.objects.filter(startDate__month__gt=7, startDate__year=configuracao.ano)
        eventos_prox_ano = Evento.objects.filter(startDate__month=1, startDate__year=configuracao.ano+1)
        eventos = eventos_ano | eventos_prox_ano

    for evento in eventos:
        evento.pk = None
        evento.startDate += datetime.timedelta(days=182)
        evento.endDate += datetime.timedelta(days=182)

        # Verifica se não está criando outra duplicata
        if not Evento.objects.filter(startDate=evento.startDate, endDate=evento.endDate,
                                     location=evento.location, tipo_de_evento=evento.tipo_de_evento,
                                     descricao=evento.descricao, observacao=evento.observacao).exists():
            evento.save()

    return redirect('calendario')
