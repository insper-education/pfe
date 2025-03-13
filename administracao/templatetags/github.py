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


def get_all_commits(url, headers):
    """Fetch all commits from the GitHub API, handling pagination."""
    commits = []
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            break
        commits.extend(response.json())
        url = None
        if "Link" in response.headers:
            links = response.headers["Link"].split(',')
            for link in links:
                if 'rel="next"' in link:
                    url = link[link.find('<') + 1:link.find('>')]
                    break
    return commits


@register.filter
def contributor(dados):
    """Transforma JSON em dicionário e puxa contributions."""

    if not dados:
        return None
    url = dados["contributors_url"]

    if not url:
        return None

    headers = {"Authorization": f"token {settings.GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return [ (None, f"Erro: {response.status_code}") ]
        #raise Exception(f"Erro ao acessar a API do GitHub: {response.status_code}")

    contributors = response.json()
    
    # # Retorna os commits de um repositório (muito lento)
    # url = dados["commits_url"]
    # if not url:
    #     return None
    # url = url.split("{")[0]  # Removendo o {/sha} do final da URL
    # commits = get_all_commits(url, headers)

    resposta = {}
    for d in contributors:

        # # Seria uma rotina para mostrar o número de linhas adicionadas e removidas
        # # Porém, a API do GitHub não retorna essa informação rapidamente
        # # Além disso, o números não batem
        # lines_added = 0
        # lines_removed = 0
        # for commit in commits:
        #     if commit["author"]["login"] == d["login"]:
        #         commit_url = commit["url"]
        #         commit_response = requests.get(commit_url, headers=headers)
        #         if commit_response.status_code != 200:
        #             continue
        #         commit_data = commit_response.json()
        #         for file in commit_data["files"]:
        #             lines_added += file["additions"]
        #             lines_removed += file["deletions"]
        # d["lines_added"] = lines_added
        # d["lines_removed"] = lines_removed

        resposta[d["login"]] = d
        
    return resposta.items()
