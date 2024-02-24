#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Dezembro de 2020
"""

import datetime
import dateutil.parser

from icalendar import Calendar, Event, vCalAddress

from django.conf import settings

from django.db.models.functions import Lower

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.sites.models import Site
from django.db import transaction
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from django.shortcuts import render, redirect, get_object_or_404

from users.models import PFEUser, Aluno

from projetos.models import Banca, Configuracao, Evento, Organizacao, Documento

from projetos.tipos import TIPO_EVENTO
from projetos.support import get_upload_path, simple_upload

from documentos.models import TipoDocumento

def get_calendario_context(user=None):
    """Contexto para gerar calendário."""
    eventos = Evento.objects.all()
    configuracao = get_object_or_404(Configuracao)

    # Se usuário não for Professor nem Admin filtra os eventos do próximo semestre
    if user and user.tipo_de_usuario != 2 and user.tipo_de_usuario != 4:
        if configuracao.semestre == 1:
            eventos_ano = eventos.filter(startDate__year__lt=configuracao.ano)
            eventos_semestre = eventos.filter(startDate__month__lte=7, startDate__year=configuracao.ano)
            eventos = eventos_ano | eventos_semestre
        else:
            eventos = eventos.filter(startDate__year__lte=configuracao.ano)

    context = {
        "configuracao": configuracao,
        "eventos": eventos.exclude(tipo_de_evento__in=[12, 40, 41, 20, 30]).exclude(tipo_de_evento__gte=100),
        "aulas": eventos.filter(tipo_de_evento=12),  # 12, 'Aula PFE'
        "laboratorios": eventos.filter(tipo_de_evento=40),  # 40, 'Laboratório'
        "provas": eventos.filter(tipo_de_evento=41),  # 41, 'Semana de Provas'
        "quinzenais": eventos.filter(tipo_de_evento=20),  # 20, 'Relato Quinzenal'
        "feedbacks": eventos.filter(tipo_de_evento=30),  # 30, 'Feedback dos Estudantes sobre PFE'
        "coordenacao": Evento.objects.filter(tipo_de_evento__gte=100),  # Eventos da coordenação
        "tipos_eventos": TIPO_EVENTO,
        "Evento": Evento,
    }

    return context  # TAMBÉM ESTOU USANDO NO CELERY PARA AVISAR DOS EVENTOS


@login_required
def calendario(request):
    """Para exibir um calendário de eventos."""
    context = get_calendario_context(request.user)

    if context:
    
        pessoas = {}
        professores = PFEUser.objects.filter(tipo_de_usuario=2) # Professores
        administradores = PFEUser.objects.filter(tipo_de_usuario=4) # Administradores
        pessoas["insper"] = (professores | administradores).order_by(Lower("first_name"), Lower("last_name"))

        organizacao = Organizacao.objects.filter(sigla="Falconi").last()
        pessoas["falconi"] = PFEUser.objects.filter(parceiro__organizacao=organizacao)

        context["pessoas"] = pessoas

        context["documentos"] = Documento.objects.filter(tipo_documento=43)  # Somente Material de Aula (pelo momento)
    
        return render(request, "calendario/calendario.html", context)

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

    cal.add("prodid", "-//PFE//Insper//")
    cal.add("version", "2.0")

    site_token = site.domain.split('.')
    site_token.reverse()
    site_token = '.'.join(site_token)

    ical_event = Event()

    ical_event["uid"] = "Banca{0}{1}{2}".format(
        banca.startDate.strftime("%Y%m%d%H%M%S"),
        banca.projeto.pk,
        banca.tipo_de_banca)
    ical_event.add("summary", "Banca {0}".format(banca.projeto))
    ical_event.add("dtstart", banca.startDate)
    ical_event.add("dtend", banca.endDate)
    ical_event.add("dtstamp", datetime.datetime.now().date())
    ical_event.add("tzid", "America/Sao_Paulo")
    ical_event.add("location", banca.location)

    ical_event.add("geo", (-25.598749, -46.676368))

    cal_address = vCalAddress("MAILTO:lpsoares@insper.edu.br")
    cal_address.params["CN"] = "Luciano Pereira Soares"
    ical_event.add("organizer", cal_address)

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

    ical_event.add("description", description)

    cal.add_component(ical_event)

    response = HttpResponse(cal.to_ical())
    response["Content-Type"] = "text/calendar"
    response["Content-Disposition"] = \
        "attachment; filename=Banca{0}.ics".format(banca.pk)

    return response


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def atualiza_evento(request):
    """Ajax para atualizar eventos."""
    try:
        event_id = request.POST.get("event-index", 0)
        if event_id:
            evento = Evento.objects.get(id=event_id)
        else:
            evento = Evento.create()
    except Evento.DoesNotExist:
        return HttpResponseNotFound("<h1>Evento não encontrado!</h1>")

    type = request.POST.get("event-type", None)
    if type:
        evento.tipo_de_evento = int(type)
    
    startDate = request.POST.get("startDate", None)  # Data foi ajustada para YYYY-MM-DD
    if startDate:
        evento.startDate = dateutil.parser.parse(startDate)
    
    endDate = request.POST.get("endDate", None)  # Data foi ajustada para YYYY-MM-DD
    if endDate:
        evento.endDate = dateutil.parser.parse(endDate)
    
    location = request.POST.get("event-location", "")
    if location:
        evento.location = location[:Evento._meta.get_field("location").max_length]

    observacao = request.POST.get("event-observation", "")
    if observacao:
        evento.observacao = observacao[:Evento._meta.get_field("observacao").max_length]

    atividade = request.POST.get("event-atividade", "")
    if atividade:
        evento.atividade = atividade[:Evento._meta.get_field("atividade").max_length]

    descricao = request.POST.get("event-descricao", "")
    if descricao:
        evento.descricao = descricao[:Evento._meta.get_field("descricao").max_length]

    responsavel = request.POST.get("event-responsavel", None)
    evento.responsavel = PFEUser.objects.get(id=responsavel) if responsavel else None


    max_length = Documento._meta.get_field("documento").max_length
    if "arquivo" in request.FILES:

        #link = request.POST.get("link", None)
        max_length = Documento._meta.get_field("documento").max_length
        if "arquivo" in request.FILES and len(request.FILES["arquivo"].name) > max_length - 1:
                return "<h1>Erro: Nome do arquivo maior que " + str(max_length) + " caracteres.</h1>"
        
        documento = Documento.create()  # Criando documento na base de dados
        documento.tipo_documento = get_object_or_404(TipoDocumento, id=43)  # Material de Aula
        documento.data = datetime.datetime.now()
        #documento.link = link
        documento.lingua_do_documento = 0  # (0, 'Português')
        documento.confidencial = False  # Por padrão aulas não são confidenciais
        documento.usuario = request.user

        if len(request.FILES["arquivo"].name) > max_length - 1:
            return "<h1>Erro: Nome do arquivo maior que " + str(max_length) + " caracteres.</h1>"
    
        arquivo = simple_upload(request.FILES["arquivo"],
                                path=get_upload_path(documento, ""))
        documento.documento = arquivo[len(settings.MEDIA_URL):]
        documento.save()
        evento.documento = documento
    else:
        material = request.POST.get("event-material", None)
        evento.documento = Documento.objects.get(id=material) if material else None

    evento.save()

    data = {
        "atualizado": True,
        "evento_id": evento.id,
    }

    return JsonResponse(data)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def remove_evento(request):
    """Ajax para remover eventos."""
    event_id = int(request.POST.get("id", None))
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
                                     atividade=evento.atividade).exists():
            evento.save()

    return redirect("calendario")
