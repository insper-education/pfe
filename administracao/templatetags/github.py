#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 8 de Março de 2025
"""

import requests

from django import template
from django.conf import settings

from users.models import PFEUser

register = template.Library()


@register.filter
def git_usuario(usuario):
    """Puxa informações do usuário no GitHub."""
    try:
        return PFEUser.objects.get(conta_github=usuario)
    except Exception:
        return None


@register.filter
def contributor(url):
    """Transforma JSON em dicionário e puxa contributions."""

    if not url:
        return None

    headers = {"Authorization": f"token {settings.GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return [ (None, f"Erro: {response.status_code}") ]
        #raise Exception(f"Erro ao acessar a API do GitHub: {response.status_code}")
    
    data = response.json()

    resposta = {}
    for d in data:
        resposta[d["login"]] = d

    return resposta.items()
