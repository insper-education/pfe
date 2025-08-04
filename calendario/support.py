#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 23 de Janeiro de 2025
"""

import datetime
from icalendar import vCalAddress

from django.conf import settings
from django.shortcuts import get_object_or_404

from administracao.models import TipoEvento

from documentos.models import TipoDocumento

from projetos.models import Configuracao, Evento, Documento
from projetos.support import get_upload_path, simple_upload
from projetos.tipos import TIPO_EVENTO


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

    tipos_eventos_sorter = sorted(TIPO_EVENTO, key=lambda x: (x[0]>100, x[1]))
    tipos_eventos = [list(tipo) + ["Operação"] if tipo[0] > 100 else list(tipo) + ["Acadêmico"] for tipo in tipos_eventos_sorter]

    tipos_eventos = TipoEvento.objects.all().order_by("coordenacao", "nome")

    eventos_academicos = {
        "eventos": eventos.exclude(tipo_evento__sigla__in=["A", "L", "SP", "RQ", "FE", "FERI", "M", "MA"]).exclude(tipo_evento__coordenacao=True),
        "aulas": eventos.filter(tipo_evento__sigla="A"), # Aula
        "laboratorios": eventos.filter(tipo_evento__sigla="L"),  # Laboratório
        "quinzenais": eventos.filter(tipo_evento__sigla="RQ"),  # Relato Quinzenal
        "feedbacks": eventos.filter(tipo_evento__sigla="FE"),  # Feedback dos Estudantes sobre Capstone
        "mentorias_profissionais": eventos.filter(tipo_evento__sigla="M"),  # Mentorias (Profissional)
        "mentorias_academicas": eventos.filter(tipo_evento__sigla="MA"),  # Mentorias (Acadêmica)
        "provas": eventos.filter(tipo_evento__sigla="SP"),  # Semana de Provas
        "feriados": eventos.filter(tipo_evento__sigla="FERI"),  # Feriado
    }
    
    context = {
        "configuracao": configuracao,
        "eventos_academicos": eventos_academicos,
        "coordenacao": Evento.objects.filter(tipo_evento__coordenacao=True),  # Eventos da coordenação
        "tipos_eventos": tipos_eventos,
        "Evento": Evento,
        "mentorias": Evento.objects.filter(tipo_evento__sigla__in=["M", "MA"]),
    }

    return context  # TAMBÉM ESTOU USANDO NO CELERY PARA AVISAR DOS EVENTOS


def adicionar_participante_em_evento(ical_event, usuario):
    """Adiciona um usuario em um evento."""
    # REMOVER OS xx DOS EMAILS
    atnd = vCalAddress("MAILTO:{}".format(usuario.email))
    atnd.params["CN"] = "{0}".format(usuario.get_full_name())
    atnd.params["ROLE"] = "REQ-PARTICIPANT"
    ical_event.add("attendee", atnd, encode=0)


def gera_descricao_banca(banca, estudantes):
    """Gera um descrição para colocar no aviso do agendamento."""
    description = "Banca do Projeto {0}".format(banca.get_projeto())
    if banca.link:
        description += "\n\nLink: {0}".format(banca.link)
    description += "\n\nOrientador:\n- {0}".format(banca.get_projeto().orientador)
    if banca.membros():
        description += "\n\nMembros da Banca:"
    for membro in banca.membros():
        description += "\n- {0}".format(membro.get_full_name())
        if membro == banca.projeto.orientador.user:
            description += " [orientador]"
    description += "\n\nEstudantes:"
    for estudante in estudantes:
        description += "\n- {0}".format(estudante.user.get_full_name())
    return description


def cria_material_documento(request, campo_arquivo, campo_link=None, sigla="MAS", confidencial=True, projeto=None, prefix="", usuario=None):
        """Cria documento."""

        # ESSE CODIGO É MUITO SEMELHANTE AO DE CRIA_DOCUMENTO NO ORGANIZACOES / SUPPORT.PY

        max_length_link = Documento._meta.get_field("link").max_length
        if campo_link in request.POST and len(request.POST[campo_link]) > max_length_link - 1:
            raise ValueError("Erro: Link maior que " + str(max_length_link) + " caracteres.")

        max_length_doc = Documento._meta.get_field("documento").max_length
        if campo_arquivo in request.FILES and len(request.FILES[campo_arquivo].name) > max_length_doc - 1:
            raise ValueError("Erro: Nome do arquivo maior que " + str(max_length_doc) + " caracteres.")
        
        # if request.user.tipo_de_usuario not in json.loads(tipo.gravar):  # Verifica se usuário tem privilégios para gravar tipo de arquivo
        #     return "<h1>Sem privilégios para gravar tipo de arquivo!</h1>"

        documento = Documento()  # Criando documento na base de dados
        documento.tipo_documento = get_object_or_404(TipoDocumento, sigla=sigla)
        documento.data = datetime.datetime.now()
        
        documento.lingua_do_documento = 0  # (0, "Português")
        documento.confidencial = confidencial
        if usuario:
            documento.usuario = usuario
        else:
            if request.user.is_authenticated:
                documento.usuario = request.user
        documento.projeto = projeto

        if projeto and projeto.organizacao:
            documento.organizacao = projeto.organizacao
    
        if campo_arquivo and campo_arquivo in request.FILES:
            arquivo = simple_upload(request.FILES[campo_arquivo],
                                    path=get_upload_path(documento, ""),
                                    prefix=prefix)
            documento.documento = arquivo[len(settings.MEDIA_URL):]

        if campo_link and campo_link in request.POST:
            link = request.POST.get(campo_link, "")
            documento.link = link

        documento.save()
        return documento
