#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""

import re

from django.core.files.storage import FileSystemStorage
from django.template.defaultfilters import slugify
from django.utils import text
from django.utils.encoding import force_text


def get_upload_path(instance, filename):
    """Caminhos para armazenar os arquivos."""
    caminho = ""
    if instance.__class__.__name__ == "Documento":
        if instance.organizacao:
            caminho += slugify(instance.organizacao.sigla_limpa()) + "/"
        if instance.projeto:
            if (not instance.organizacao) and instance.projeto.organizacao:
                caminho += slugify(instance.projeto.organizacao.sigla_limpa()) + '/'
            caminho += "projeto" + str(instance.projeto.pk) + '/'
        if instance.usuario:
            caminho += slugify(instance.usuario.username) + '/'
        if caminho == "":
            caminho = "documentos/"
    elif instance.__class__.__name__ == "Projeto":
        caminho += slugify(instance.organizacao.sigla_limpa()) + '/'
        caminho += "projeto" + str(instance.pk) + '/'
    elif instance.__class__.__name__ == "Organizacao":
        caminho += slugify(instance.sigla_limpa()) + "/logotipo/"
    elif instance.__class__.__name__ == "Certificado":
        if instance.projeto and instance.projeto.organizacao:
            caminho += slugify(instance.projeto.organizacao.sigla_limpa()) + '/'
            caminho += "projeto" + str(instance.projeto.pk) + '/'
        if instance.usuario:
            caminho += slugify(instance.usuario.username) + '/'
    elif instance.__class__.__name__ == "Configuracao" or instance.__class__.__name__ == "Administrador":
        caminho += "configuracao/"
    elif instance.__class__.__name__ == "Proposta":
        caminho += "propostas/proposta"+ str(instance.pk) + '/'
    else:  # Arquivo Temporário
        caminho += "tmp/"

    if filename:
        filename = force_text(filename).strip().replace(' ', '_')
        filename = re.sub(r'(?u)[^-\w.]', '', filename)
        return "{0}/{1}".format(caminho, filename)

    return "{0}".format(caminho)


def simple_upload(arquivo, path="", prefix="", valida=None):
    """Faz uploads para o servidor."""
    if valida:
        if valida == "pdf":
            if arquivo.content_type != "application/pdf":
                return None  # Não é PDF
    file_system_storage = FileSystemStorage()
    filename = str(arquivo.name.encode("utf-8").decode("ascii", "ignore"))
    while ".." in filename:  # Remove .. do nome do arquivo
        filename = filename.replace("..", ".")

    sanitized_filename = text.get_valid_filename(filename)

    if not sanitized_filename:
        raise ValueError(f"Erro com nome do arquivo: {arquivo.name}")
    
    name = path+prefix+sanitized_filename
    filename = file_system_storage.save(name, arquivo)
    uploaded_file_url = file_system_storage.url(filename)
    return uploaded_file_url

