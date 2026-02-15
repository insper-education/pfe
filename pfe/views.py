#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Junho de 2023
"""

import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

# from django.db.models import Count
from users.models import PFEUser
from projetos.models import Projeto
from projetos.models import Organizacao

from .support import get_navigation_items

from administracao.models import Carta

# Get an instance of a logger
logger = logging.getLogger("django")


def index(request):
    """Página principal do sistema."""
    if request.user.is_authenticated:

        cards = get_navigation_items()
        
        # Filtrando cards que o usuário pode ver
        visible_cards = []
        for card in cards:
            visible = False
            
            # Cards visíveis para todos
            if card.get("visible_to_all"):
                visible = True
            
            # Cards baseados em atributos do usuário
            if "visible_for_type" in card:
                for attr in card["visible_for_type"]:
                    # Verificar atributos no usuário
                    if attr.startswith("eh_") or attr.startswith("membro_"):
                        if getattr(request.user, attr, False):
                            visible = True
                            break
            
            # Cards baseados em permissões
            if "visible_for_permission" in card:
                for perm in card["visible_for_permission"]:
                    if request.user.has_perm(f"{card.get('app', 'projetos')}.{perm}"):
                        visible = True
                        break
            
            if visible:
                visible_cards.append(card)
        
        # Organizar por grupos
        card_groups = {}
        for card in visible_cards:
            group = card.get("group", "main")
            if group not in card_groups:  # Cria o grupo automaticamente se não existir
                card_groups[group] = []
            card_groups[group].append(card)
        
        context = {
            "card_groups": card_groups
        }
        
        return render(request, "index.html", context)

    else:
        info = get_object_or_404(Carta, template="Informação")
        return render(request, "info.html", {"info": info, "titulo": {"pt": "Informações Capstone", "en": "Capstone Information"}})

def info(request):
    """Página com informações."""
    info = get_object_or_404(Carta, template="Informação")
    return render(request, "info.html", {"info": info, "titulo": {"pt": "Informações Capstone", "en": "Capstone Information"}})

def sistema(request):
    """Página com informações sobre o sistema."""
    from datetime import datetime
    import os
    
    # Calcular estatísticas
    stats = {
        "anos_ativo": datetime.now().year - 2019,
        "total_projetos": Projeto.objects.filter(ano__isnull=False).count(),
        'total_usuarios': PFEUser.objects.count(),
        'total_organizacoes': Organizacao.objects.count(),
    }
    
    context = {
        "titulo": {"pt": "Sobre o Sistema", "en": "About the System"},
        "stats": stats,
    }

    return render(request, "sistema.html", context)

def manutencao(request):
    """Página de Manutenção do sistema."""
    return render(request, "manutencao.html")

def custom_400(request, exception):
    mensagem = "<h1>Bad Request (400)</h1>"
    if (exception):
        mensagem += str(exception) + "<br>"
    mensagem += "Em caso de dúvida " + settings.CONTATO
    #t = loader.get_template("400.html")
    #t.render(Context({"exception_value": value,})
    return HttpResponse(mensagem)


from projetos.models import Banca
from administracao.models import TipoEvento

@login_required
@permission_required("users.view_administrador", raise_exception=True)
def migracao(request):
    """temporário."""
    message = "Nada Feito"

    bi = TipoEvento.objects.get(sigla="BI")
    bf = TipoEvento.objects.get(sigla="BF")
    f = TipoEvento.objects.get(sigla="F")
    p = TipoEvento.objects.get(sigla="P")

    bancas = Banca.objects.all()
    for banca in bancas:
        if banca.composicao.exame.sigla == "BI":
            banca.tipo_evento = bi
            banca.save()
        elif banca.composicao.exame.sigla == "BF":
            banca.tipo_evento = bf
            banca.save()
        elif banca.composicao.exame.sigla == "P":
            banca.tipo_evento = p
            banca.save()
        elif banca.composicao.exame.sigla == "F":
            banca.tipo_evento = f
            banca.save()

    message = "Feito"
    return HttpResponse(message)
