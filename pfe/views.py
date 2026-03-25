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
from django.http import HttpResponse
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

@login_required
@permission_required("users.view_administrador", raise_exception=True)
def migracao(request):
    """temporário."""
    message = "Nada Feito"
    return HttpResponse(message)

from users.models import Aluno

@login_required
@permission_required("users.view_administrador", raise_exception=True)
def tmp(request):
    """temporário."""
    def texto_resposta_binaria(aluno, campo):
        valor = getattr(aluno, campo)
        if not valor:
            return "Não respondeu"
        metodo_display = getattr(aluno, f"get_{campo}_display")
        return metodo_display()

    def texto_resposta_horario(aluno):
        if not aluno.escolha_horario_trab_grupo:
            return "Não respondeu"
        return aluno.get_escolha_horario_trab_grupo_display()

    alunos = Aluno.objects.filter(
        Q(ano__gte=2027) | Q(ano=2026, semestre=2)
    ).select_related("user", "curso2").order_by("ano", "semestre", "user__first_name", "user__last_name")

    linhas = []
    for aluno in alunos:
        curso = aluno.curso2.sigla if aluno.curso2 and aluno.curso2.sigla else "-"
        linhas.append(
            "<tr>"
            f"<td style='border:1px solid #d0d7de; padding:8px;'>{escape(aluno.user.get_full_name())}</td>"
            f"<td style='border:1px solid #d0d7de; padding:8px; text-align:center;'>{aluno.ano}/{aluno.semestre}</td>"
            f"<td style='border:1px solid #d0d7de; padding:8px; text-align:center;'>{escape(curso)}</td>"
            f"<td style='border:1px solid #d0d7de; padding:8px;'>{escape(texto_resposta_horario(aluno))}</td>"
            f"<td style='border:1px solid #d0d7de; padding:8px; text-align:center;'>{texto_resposta_binaria(aluno, 'aulas_mudando_meio_semestre')}</td>"
            f"<td style='border:1px solid #d0d7de; padding:8px; text-align:center;'>{texto_resposta_binaria(aluno, 'aula_de_cybersec_no_mesmo_dia')}</td>"
            "</tr>"
        )

    if not linhas:
        linhas.append(
            "<tr><td colspan='6' style='border:1px solid #d0d7de; padding:12px; text-align:center;'>Nenhum aluno encontrado.</td></tr>"
        )

    html = (
        "<html><head><meta charset='utf-8'><title>Respostas Temporárias</title></head><body "
        "style='font-family: Arial, sans-serif; margin: 24px;'>"
        "<h2 style='margin-bottom:16px;'>Respostas das perguntas temporárias</h2>"
        f"<div style='margin-bottom:12px; color:#57606a;'>Total de alunos: {alunos.count()}</div>"
        "<table style='border-collapse: collapse; width: 100%; font-size: 14px;'>"
        "<thead>"
        "<tr style='background:#f6f8fa;'>"
        "<th style='border:1px solid #d0d7de; padding:8px; text-align:left;'>Aluno</th>"
        "<th style='border:1px solid #d0d7de; padding:8px; text-align:center;'>Período</th>"
        "<th style='border:1px solid #d0d7de; padding:8px; text-align:center;'>Curso</th>"
        "<th style='border:1px solid #d0d7de; padding:8px; text-align:left;'>Horário de grupo</th>"
        "<th style='border:1px solid #d0d7de; padding:8px; text-align:center;'>Troca no meio</th>"
        "<th style='border:1px solid #d0d7de; padding:8px; text-align:center;'>Cybersec mesmo dia</th>"
        "</tr>"
        "</thead>"
        f"<tbody>{''.join(linhas)}</tbody>"
        "</table>"
        "</body></html>"
    )

    return HttpResponse(html)


