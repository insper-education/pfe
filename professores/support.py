#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Dezembro de 2020
"""

import dateutil.parser


from django.db.models.functions import Lower

from users.models import PFEUser
from projetos.models import Organizacao


def editar_banca(banca, request):
    """Edita os valores de uma banca por um request Http."""
    if 'inicio' in request.POST:
        try:
            banca.startDate = dateutil.parser.parse(request.POST['inicio'])
        except (ValueError, OverflowError):
            banca.startDate = None
    if 'fim' in request.POST:
        try:
            banca.endDate = dateutil.parser.parse(request.POST['fim'])
        except (ValueError, OverflowError):
            banca.endDate = None
    if 'tipo' in request.POST and request.POST['tipo'] != "":
        banca.tipo_de_banca = int(request.POST['tipo'])
    if 'local' in request.POST:
        banca.location = request.POST['local']
    if 'link' in request.POST:
        banca.link = request.POST['link']

    try:
        if 'membro1' in request.POST:
            banca.membro1 = PFEUser.objects.get(id=int(request.POST['membro1']))
        else:
            banca.membro1 = None
        if 'membro2' in request.POST:
            banca.membro2 = PFEUser.objects.get(id=int(request.POST['membro2']))
        else:
            banca.membro2 = None
        if 'membro3' in request.POST:
            banca.membro3 = PFEUser.objects.get(id=int(request.POST['membro3']))
        else:
            banca.membro3 = None
    except PFEUser.DoesNotExist:
        return None

    banca.save()

def professores_membros_bancas():
    """Retorna potenciais usuários que podem ser membros de uma banca do PFE."""
    professores = PFEUser.objects.filter(tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[1][0])

    administradores = PFEUser.objects.filter(tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[3][0])

    pessoas = (professores | administradores).order_by(Lower("first_name"), Lower("last_name"))

    return pessoas


def falconi_membros_banca():
    """Coleta registros de possiveis membros de banca para Falconi."""

    try:
        organizacao = Organizacao.objects.get(sigla="Falconi")
    except Organizacao.DoesNotExist:
        return None

    falconis = PFEUser.objects.filter(parceiro__organizacao=organizacao)
    return falconis
