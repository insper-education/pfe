#!/usr/bin/env python

"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 20 de Abril de 2024
"""

import os
import zipfile
import os

from django.conf import settings
from django.http import Http404
from django.views.static import serve as static_serve
from django.shortcuts import get_object_or_404
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from users.models import Alocacao
from projetos.models import Projeto, Configuracao


def sites(request, projeto_id, path):
    """Redireciona para páginas de desenvolvimento dos projetos."""
    if not request.user.is_authenticated:
        raise Http404
    
    projeto = get_object_or_404(Projeto, id=projeto_id)
    if request.user.tipo_de_usuario == 1 : # Estudante
        if not Alocacao.objects.filter(projeto=projeto, aluno=request.user.aluno).exists():
            raise Http404
    elif request.user.tipo_de_usuario == 2: # Professor
        pass
    elif request.user.tipo_de_usuario == 3: # Organização
        if request.user.parceiro.organizacao != projeto.organizacao:
            raise Http404
    elif request.user.tipo_de_usuario != 4: # Administrador
        raise Http404
    
    site_root = settings.SITE_ROOT + "/projeto" + str(projeto.id)

    # If path is empty, try to serve index.html or index.htm
    if not path:
        for index_file in ["index.html", "index.htm"]:
            try:
                return static_serve(request, index_file, document_root=site_root)
            except Http404:
                pass

    return static_serve(request, os.path.normpath(path), document_root=site_root)


@login_required
def upload_site(request, projeto_id):
    if request.method == "POST":
        zip_file = request.FILES["zipsite"]
        if isinstance(zip_file, (InMemoryUploadedFile, TemporaryUploadedFile)):
            configuracao = get_object_or_404(Configuracao)
            MAX_SIZE = configuracao.maxMB_filesize * 1048576
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                total_size = sum((file.file_size for file in zip_ref.infolist()))
                if total_size > MAX_SIZE:
                    return HttpResponse("Arquivo descomprimido maior que o limite: " + str(configuracao.maxMB_filesize) + "MB.")
                projeto = get_object_or_404(Projeto, id=projeto_id)
                site_root = settings.SITE_ROOT + "/projeto"+str(projeto.id)
                if os.path.exists(site_root):
                    os.system("rm -rf " + site_root)
                zip_ref.extractall(site_root)  # extract the zip file to the project path
                mensagem = "Site atualizado com sucesso."
                mensagem += "<br><a href='/sites/"+str(projeto_id)+"/'>Visualizar site</a>"
                context = {
                    "area_principal": True,
                    "mensagem": mensagem,
                }
                return render(request, "generic.html", context=context)
        else:
            return HttpResponse("Não é arquivo.")
        
    return HttpResponse("Invalid request.")