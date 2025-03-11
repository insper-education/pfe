#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 23 de Janeiro de 2025
"""

from django.http import HttpResponse

from administracao.models import TipoEvento


def trata_aviso(aviso, request):
    """Puxa dados do request e põe em aviso."""
    try:
        aviso.titulo = request.POST["titulo"]
        aviso.delta = int(request.POST["delta"])
        aviso.mensagem = request.POST["mensagem"]

        id_evento = int(request.POST["evento"])
        tipo_evento = TipoEvento.objects.get(id=id_evento)
        aviso.tipo_evento = tipo_evento

        aviso.coordenacao = "coordenacao" in request.POST
        aviso.operacional = "operacional" in request.POST
        aviso.comite = "comite" in request.POST
        aviso.todos_alunos = "todos_alunos" in request.POST
        aviso.todos_orientadores = "todos_orientadores" in request.POST
        aviso.contatos_nas_organizacoes = "contatos_nas_organizacoes" in request.POST

    except (ValueError, OverflowError):
        return HttpResponse("Algum erro não identificado.", status=401)

    aviso.save()

    return None
