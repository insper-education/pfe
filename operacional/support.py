#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 23 de Janeiro de 2025
"""

from django.core.exceptions import ValidationError

from administracao.models import TipoEvento


def trata_aviso(aviso, request):
    """Puxa dados do request e põe em aviso."""
    
    titulo = request.POST.get("titulo", "").strip()
    delta = request.POST.get("delta", None)
    id_evento = request.POST.get("evento", None)

    if not all([id_evento, titulo, delta]):
        raise ValidationError("Campos obrigatórios ausentes.")
    
    try:
        aviso.titulo = titulo
        aviso.delta = int(delta)
        aviso.tipo_evento = TipoEvento.objects.get(id=id_evento)
        aviso.mensagem = request.POST["mensagem"]
    except (ValueError, TipoEvento.DoesNotExist):
        raise ValidationError("Dados inválidos fornecidos.")

    for campo in ["coordenacao", "operacional", "comite", "todos_alunos", "todos_orientadores", "contatos_nas_organizacoes"]:
        setattr(aviso, campo, campo in request.POST)

    aviso.save()

    return aviso
