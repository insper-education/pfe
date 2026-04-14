#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Junho de 2023
"""

import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils.html import escape

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

from academica.models import Exame, ExibeNota
from projetos.models import Documento, Evento, Avaliacao2, Observacao
from users.models import PFEUser, Professor
from projetos.models import Area, AreaDeInteresse


@login_required
@permission_required("users.view_administrador", raise_exception=True)
def migracao(request):
    """temporário."""
    message = "Nada Feito"
    message = ""

    for professor in Professor.objects.all():
        if professor.areas:
            outra, _ = AreaDeInteresse.objects.get_or_create(area=None, usuario=professor.user)
            outra.outras = professor.areas
            outra.save()
            message += f"Professor {professor.user.get_full_name()} migrado com sucesso!<br>"

    return HttpResponse(message)

    # Imprimir em JSON dados de Avaliacao2
    dados = []

    # exames = Exame.objects.filter(titulo__in=["Banca Final", "Banca Intermediária",])
    # avaliacoes = Avaliacao2.objects.filter(exame__in=exames).order_by("-momento")[1:10]
    # for avaliacao in avaliacoes:
    #     dados.append({
    #         "exam_type": avaliacao.exame.titulo_en,
    #         "timestamp": avaliacao.momento.isoformat(),
    #         "grade": float(avaliacao.nota) if avaliacao.nota is not None else None,
    #         "weight": avaliacao.peso,
    #         "evaluator": avaliacao.avaliador.id,
    #         "advisor": avaliacao.projeto.orientador.user.id == avaliacao.avaliador.id,
    #         "project": avaliacao.projeto.id,
    #         "learning_goal": avaliacao.objetivo.titulo_en if avaliacao.objetivo else None,
    #         "not_evaluated": avaliacao.na is None,
    #     })

    # projetos = Projeto.objects.filter(ano__isnull=False).order_by("-ano", "-semestre")[:10]
    # for projeto in projetos:
    #     areas = []
    #     for areadeinteresse in projeto.proposta.areadeinteresse_set.all():
    #         if areadeinteresse.area:
    #             areas.append(areadeinteresse.area.titulo_en)
    #     dados.append({
    #         "project": projeto.id,
    #         "year": projeto.ano,
    #         "semester": projeto.semestre,
    #         "advisor": projeto.orientador.user.id if projeto.orientador else None,
    #         "areas": areas,
    #     })

    # return JsonResponse(
    #     dados,
    #     safe=False,
    #     json_dumps_params={"ensure_ascii": False, "indent": 2},
    # )

@login_required
@permission_required("users.altera_professor", raise_exception=True)
def tmp(request):
    """temporário."""
    return HttpResponse("temporário")


