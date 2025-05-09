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
from django.db.models.functions import Lower
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from django.shortcuts import render, redirect, get_object_or_404

from .support import get_calendario_context, adicionar_participante_em_evento
from .support import gera_descricao_banca, cria_material_documento

from administracao.models import TipoEvento

from documentos.models import TipoDocumento

from projetos.models import Banca, Configuracao, Evento, Organizacao, Documento

from users.models import PFEUser, Aluno


@login_required
def calendario(request):
    """Para exibir um calendário de eventos."""
    context = get_calendario_context(request.user)
    context["titulo"] = { "pt": "Calendário de Eventos", "en": "Events Calendar" }

    if context:
    
        pessoas = {}
        professores = PFEUser.objects.filter(tipo_de_usuario=2) # Professores
        administradores = PFEUser.objects.filter(tipo_de_usuario=4) # Administradores
        pessoas["insper"] = (professores | administradores).order_by(Lower("first_name"), Lower("last_name"))

        org_falconi = Organizacao.objects.filter(sigla="Falconi").last()
        pessoas["falconi"] = PFEUser.objects.filter(parceiro__organizacao=org_falconi)

        pessoas["outros"] = PFEUser.objects.filter(tipo_de_usuario=3).exclude(parceiro__organizacao=org_falconi)
        
        context["pessoas"] = pessoas

        context["DocumentoModel"] = Documento
        try:
            tipo_documento = TipoDocumento.objects.get(sigla="MAS")  # Somente Material de Aula (pelo momento)
            context["documentos"] = Documento.objects.filter(tipo_documento=tipo_documento).order_by("-data")
        except TipoDocumento.DoesNotExist:
            context["documentos"] = None
    
        return render(request, "calendario/calendario.html", context)

    return HttpResponse("Problema ao gerar calendário.", status=401)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def export_calendar(request, event_id):
    """Gera evento de calendário."""
    banca = get_object_or_404(Banca, pk=event_id)

    cal = Calendar()
    site = Site.objects.get_current()

    cal.add("prodid", "-//Capstone//Insper//")
    cal.add("version", "2.0")

    site_token = site.domain.split('.')
    site_token.reverse()
    site_token = '.'.join(site_token)

    ical_event = Event()

    ical_event["uid"] = "Banca{0}{1}{2}".format(
        banca.startDate.strftime("%Y%m%d%H%M%S"),
        banca.get_projeto().pk,
        banca.composicao.exame.sigla)
    ical_event.add("summary", "Banca {0}".format(banca.get_projeto()))
    ical_event.add("dtstart", banca.startDate)
    ical_event.add("dtend", banca.endDate)
    ical_event.add("dtstamp", datetime.datetime.now().date())
    ical_event.add("tzid", "America/Sao_Paulo")
    ical_event.add("location", banca.location)

    ical_event.add("geo", (-25.598749, -46.676368))

    cal_address = vCalAddress("MAILTO:lpsoares@insper.edu.br")
    cal_address.params["CN"] = "Luciano Pereira Soares"
    ical_event.add("organizer", cal_address)

    for membro in banca.membros():
        adicionar_participante_em_evento(ical_event, membro)

    alunos = Aluno.objects.filter(alocacao__projeto=banca.get_projeto())\
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
            evento = Evento()
            
    except Evento.DoesNotExist:
        return HttpResponseNotFound("<h1>Evento não encontrado!</h1>")

    type = request.POST.get("event-type", None)
    if type:
        tevento = TipoEvento.objects.get(id=type)
        evento.tipo_evento = tevento
    
    if "startDate" in request.POST:
        startDate = request.POST.get("startDate", None)  # Data foi ajustada para YYYY-MM-DD
        if startDate:
            evento.startDate = dateutil.parser.parse(startDate)
        else:
            evento.startDate = None
    
    if "endDate" in request.POST:
        endDate = request.POST.get("endDate", None)  # Data foi ajustada para YYYY-MM-DD
        if endDate:
            evento.endDate = dateutil.parser.parse(endDate)
        else:
            evento.endDate = None
    
    if "event-location" in request.POST:
        location = request.POST.get("event-location", "")
        evento.location = location[:Evento._meta.get_field("location").max_length]
    
    if "event-observacao" in request.POST:
        observacao = request.POST.get("event-observacao", "")
        evento.observacao = observacao[:Evento._meta.get_field("observacao").max_length]

    if "event-atividade" in request.POST:
        atividade = request.POST.get("event-atividade", "")
        evento.atividade = atividade[:Evento._meta.get_field("atividade").max_length]
    
    if "event-descricao" in request.POST:
        descricao = request.POST.get("event-descricao", "")
        evento.descricao = descricao[:Evento._meta.get_field("descricao").max_length]
    
    responsavel = request.POST.get("event-responsavel", None)
    evento.responsavel = PFEUser.objects.get(id=responsavel) if responsavel else None

    if "arquivo" in request.FILES or ("link1" in request.POST and request.POST["link1"] != ""):
        documento = cria_material_documento(request, "arquivo", "link1", sigla="MAS", confidencial=False)
        evento.documento = documento
    else:
        material = request.POST.get("event-material", None)
        evento.documento = Documento.objects.get(id=material) if material else None

    if "arquivo2" in request.FILES or ("link2" in request.POST and request.POST["link2"] != ""):
        documento = cria_material_documento(request, "arquivo2", "link2", sigla="MAS", confidencial=False)
        evento.documento2 = documento
    else:
        material = request.POST.get("event-material2", None)
        evento.documento2 = Documento.objects.get(id=material) if material else None

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
                                     location=evento.location,
                                     tipo_evento=evento.tipo_evento,
                                     atividade=evento.atividade).exists():
            
            # Limpa os anexos das aulas (serão repostos)
            if evento.tipo_evento.sigla == "A":
                evento.documento = None
                evento.documento2 = None

            evento.save()

    return redirect("calendario")
