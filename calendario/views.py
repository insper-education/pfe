#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Dezembro de 2020
"""

import datetime


from icalendar import Calendar, Event, vCalAddress

from django.contrib.auth.decorators import login_required, permission_required

from django.shortcuts import render

from django.http import HttpResponse

from django.contrib.sites.models import Site

from users.models import PFEUser, Aluno

#from projetos.models import Banca, Documento, Encontro, Banco, Reembolso, Aviso, Conexao
from projetos.models import Banca


from projetos.models import Configuracao, Evento


def get_calendario_context(primarykey):
    """Contexto para gerar calendário."""

    try:
        user = PFEUser.objects.get(pk=primarykey)
    except PFEUser.DoesNotExist:
        return None

    eventos = Evento.objects.all()

    # Estudantes e parceiros não conseguem ver o calendário no futuro

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    if user.tipo_de_usuario != 2 and user.tipo_de_usuario != 4: # Professor e Admin
        eventos = eventos.filter(startDate__year__lte=configuracao.ano)
        if configuracao.semestre == 1:
            eventos = eventos.filter(startDate__month__lte=7)

    eventos_gerais = eventos.exclude(tipo_de_evento=12).\
                             exclude(tipo_de_evento=40).\
                             exclude(tipo_de_evento=41).\
                             exclude(tipo_de_evento=20).\
                             exclude(tipo_de_evento=30).\
                             exclude(tipo_de_evento__gte=100)
    aulas = eventos.filter(tipo_de_evento=12) #12, 'Aula PFE'
    laboratorios = eventos.filter(tipo_de_evento=40) #40, 'Laboratório'
    provas = eventos.filter(tipo_de_evento=41) #41, 'Semana de Provas'
    quinzenais = eventos.filter(tipo_de_evento=20) #20, 'Relato Quinzenal'
    feedbacks = eventos.filter(tipo_de_evento=30) #30, 'Feedback dos Alunos sobre PFE'
    coordenacao = Evento.objects.filter(tipo_de_evento__gte=100) # Eventos da coordenação

    # ISSO NAO ESTA BOM, FAZER ALGO MELHOR

    # TAMBÉM ESTOU USANDO NO CELERY PARA AVISAR DOS EVENTOS

    context = {
        'eventos': eventos_gerais,
        'aulas': aulas,
        'laboratorios': laboratorios,
        'provas' : provas,
        'quinzenais' : quinzenais,
        'feedbacks' : feedbacks,
        'coordenacao' : coordenacao,
        'semestre' : configuracao.semestre,
    }

    return context


@login_required
def calendario(request):
    """Para exibir um calendário de eventos."""

    context = get_calendario_context(request.user.pk)
    if context:
        return render(request, 'calendario/calendario.html', context)

    HttpResponse("Problema ao gerar calendário.", status=401)


@login_required
def calendario_limpo(request):
    """Para exibir um calendário de eventos."""

    context = get_calendario_context(request.user.pk)
    if context:
        context['limpo'] = True
        return render(request, 'calendario/calendario.html', context)

    HttpResponse("Problema ao gerar calendário.", status=401)


@login_required
@permission_required("users.altera_professor", login_url='/')
def export_calendar(request, event_id):
    """Gera evento de calendário."""

    try:
        banca = Banca.objects.all().get(pk=event_id)
    except Banca.DoesNotExist:
        return HttpResponse("Banca não encontrada.", status=401)

    cal = Calendar()
    site = Site.objects.get_current()

    cal.add('prodid', '-//PFE//Insper//')
    cal.add('version', '2.0')

    site_token = site.domain.split('.')
    site_token.reverse()
    site_token = '.'.join(site_token)

    ical_event = Event()

    ical_event['uid'] = "Banca{0}{1}{2}".format(banca.startDate.strftime("%Y%m%d%H%M%S"),
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

    #REMOVER OS xx DOS EMAILS
    if banca.membro1:
        atnd = vCalAddress("MAILTO:{}".format(banca.membro1.email))
        atnd.params["CN"] = "{0} {1}".format(banca.membro1.first_name, banca.membro1.last_name)
        atnd.params["ROLE"] = "REQ-PARTICIPANT"
        ical_event.add("attendee", atnd, encode=0)

    if banca.membro2:
        atnd = vCalAddress("MAILTO:{}".format(banca.membro2.email))
        atnd.params["CN"] = "{0} {1}".format(banca.membro2.first_name, banca.membro2.last_name)
        atnd.params["ROLE"] = "REQ-PARTICIPANT"
        ical_event.add("attendee", atnd, encode=0)

    if banca.membro3:
        atnd = vCalAddress("MAILTO:{}".format(banca.membro3.email))
        atnd.params["CN"] = "{0} {1}".format(banca.membro3.first_name, banca.membro3.last_name)
        atnd.params["ROLE"] = "REQ-PARTICIPANT"
        ical_event.add("attendee", atnd, encode=0)

    alunos = Aluno.objects.filter(alocacao__projeto=banca.projeto).filter(trancado=False)
    for aluno in alunos:
        atnd = vCalAddress("MAILTO:{}".format(aluno.user.email))
        atnd.params["CN"] = "{0} {1}".format(aluno.user.first_name, aluno.user.last_name)
        atnd.params["ROLE"] = "REQ-PARTICIPANT"
        ical_event.add("attendee", atnd, encode=0)

    description = "Banca do Projeto {0}".format(banca.projeto)
    if banca.link:
        description += "\n\nLink: {0}".format(banca.link)
    description += "\n\nOrientador:\n- {0}".format(banca.projeto.orientador)
    if banca.membro1 or banca.membro2 or banca.membro3:
        description += "\n\nMembros da Banca:"
        if banca.membro1:
            description += "\n- {0} {1}".format(banca.membro1.first_name, banca.membro1.last_name)
        if banca.membro2:
            description += "\n- {0} {1}".format(banca.membro2.first_name, banca.membro2.last_name)
        if banca.membro3:
            description += "\n- {0} {1}".format(banca.membro3.first_name, banca.membro3.last_name)
    description += "\n\nAlunos:"
    for aluno in alunos:
        description += "\n- {0} {1}".format(aluno.user.first_name, aluno.user.last_name)

    ical_event.add('description', description)

    cal.add_component(ical_event)

    response = HttpResponse(cal.to_ical())
    response['Content-Type'] = 'text/calendar'
    response['Content-Disposition'] = 'attachment; filename=Banca{0}.ics'.format(banca.pk)

    return response
