#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 10 de Abril de 2023
"""

#import datetime
#import dateutil.parser

#from urllib.parse import quote, unquote

#from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
# from django.db import transaction
# from django.db.models.functions import Lower
# from django.http import HttpResponse, HttpResponseNotFound

from django.shortcuts import render, get_object_or_404

# from django.utils import html

from users.models import PFEUser, Professor

# from users.support import get_edicoes

# from projetos.models import Coorientador, ObjetivosDeAprendizagem, Avaliacao2, Observacao
# from projetos.models import Banca, Evento, Encontro
# from projetos.models import Projeto, Configuracao, Organizacao
# from projetos.support import converte_letra, converte_conceito
# from projetos.support import get_objetivos_atuais
# from projetos.messages import email

# from .support import professores_membros_bancas, falconi_membros_banca
# from .support import editar_banca
# from .support import recupera_orientadores_por_semestre
# from .support import recupera_coorientadores_por_semestre

# from estudantes.models import Relato, Pares

@login_required
@permission_required("users.altera_professor", login_url='/')
def index_academica(request):
    """Mostra página principal do usuário professor."""
    user = get_object_or_404(PFEUser, pk=request.user.pk)

    if user.tipo_de_usuario != 2 and user.tipo_de_usuario != 4:
        mensagem = "Você não está cadastrado como professor!"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    professor_id = 0
    try:
        professor_id = Professor.objects.get(pk=request.user.professor.pk).id
    except Professor.DoesNotExist:
        pass
        # Administrador não possui também conta de professor

    context = {
        'professor_id': professor_id,
    }
    return render(request, 'academica/index_academica.html', context=context)
