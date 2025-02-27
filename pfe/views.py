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

from administracao.models import Carta

# Get an instance of a logger
logger = logging.getLogger("django")

@login_required
def index_old(request):
    """Antiga Página principal do sistema."""
    return render(request, "index_old.html")

#@login_required
def index(request):
    """Página principal do sistema."""
    if request.user.is_authenticated:
        return render(request, "index.html")
    else:
        info = get_object_or_404(Carta, template="Informação")
        return render(request, "info.html", {"info": info})

def info(request):
    """Página com informações."""
    info = get_object_or_404(Carta, template="Informação")
    return render(request, "info.html", {"info": info})

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

# import os
# import requests
# from git import Repo

@login_required
@permission_required("users.view_administrador", raise_exception=True)
def migracao(request):
    """temporário."""
    message = "Nada Feito"

    # pip install requests gitpython urllib3 idna certifi charset_normalizer gitdb smmap --no-deps

    # print(settings.GITHUB_USERNAME)
    # print(settings.GITHUB_TOKEN)

    # # Directory where you want to save the backups
    BACKUP_DIR = "teste"

    # # GitHub API URL to list repositories
    REPOS_URL = f'https://api.github.com//orgs/pfeinsper/repos'

    headers = {
        "Authorization": f"token {settings.GITHUB_TOKEN}"
    }
    # response = requests.get(REPOS_URL, headers=headers)
    # repos = response.json()

    # print(repos)

    #     if not os.path.exists(BACKUP_DIR):
    #         os.makedirs(BACKUP_DIR)

    #     for repo in repos:
    #         repo_name = repo['name']
    #         clone_url = repo['clone_url']
    #         repo_dir = os.path.join(BACKUP_DIR, repo_name)

    #         if os.path.exists(repo_dir):
    #             print(f'Updating repository: {repo_name}')
    #             repo = Repo(repo_dir)
    #             repo.remotes.origin.pull()
    #         else:
    #             print(f'Cloning repository: {repo_name}')
    #             Repo.clone_from(clone_url, repo_dir)


    message = "Feito"
    return HttpResponse(message)
