#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 1 de Dezembro de 2023
"""

import datetime
import dateutil.parser
import json

from collections import OrderedDict

from PyPDF2 import PdfFileReader

from django.shortcuts import get_object_or_404

from django.conf import settings

from projetos.models import Projeto, Organizacao, Documento
from projetos.support import get_upload_path, simple_upload

from documentos.models import TipoDocumento


def _getFields(obj, tree=None, retval=None, fileobj=None):
    """
    Extracts field data if this PDF contains interactive form fields.

    The *tree* and *retval* parameters are for recursive use.

    :param fileobj: A file object (usually a text file) to write
        a report to on all interactive form fields found.
    :return: A dictionary where each key is a field name, and each
        value is a :class:`Field<PyPDF2.generic.Field>` object. By
        default, the mapping name is used for keys.
    :rtype: dict, or ``None`` if form data could not be located.
    """
    fieldAttributes = {'/FT': 'Field Type', '/Parent': 'Parent', '/T': 'Field Name', '/TU': 'Alternate Field Name',
                       '/TM': 'Mapping Name', '/Ff': 'Field Flags', '/V': 'Value', '/DV': 'Default Value'}
    if retval is None:
        retval = OrderedDict()
        catalog = obj.trailer["/Root"]
        # get the AcroForm tree
        if "/AcroForm" in catalog:
            tree = catalog["/AcroForm"]
        else:
            return None
    if tree is None:
        return retval

    obj._checkKids(tree, retval, fileobj)
    for attr in fieldAttributes:
        if attr in tree:
            # Tree is a field
            obj._buildField(tree, retval, fileobj, fieldAttributes)
            break

    if "/Fields" in tree:
        fields = tree["/Fields"]
        for f in fields:
            field = f.getObject()
            obj._buildField(field, retval, fileobj, fieldAttributes)

    return retval


# Para pegar os campos do PDF
def get_form_fields(infile):
    try:
        infile = PdfFileReader(open(infile, "rb"))
        fields = _getFields(infile)
        return fields
    except Exception as e:
        raise ValueError(f"Erro ao ler o arquivo PDF: {str(e)}")

# Adiciona um novo documento na base de dados
def cria_documento(request, forca_confidencial=False, usuario=None):
    projeto = None
    projeto_id = request.POST.get("projeto", "")
    if projeto_id:
        projeto = Projeto.objects.get(id=projeto_id)

    data = datetime.datetime.now()
    if "data" in request.POST:
        try:
            data = dateutil.parser\
                .parse(request.POST["data"])
        except (ValueError, OverflowError):
            pass

    tipo_documento = 38   # Outros
    try:
        tipo_documento = int(request.POST.get("tipo_documento", 38))
    except (ValueError, OverflowError):
        pass

    tipo = get_object_or_404(TipoDocumento, id=tipo_documento)
    if request.user.tipo_de_usuario not in json.loads(tipo.gravar):  # Verifica se usuário tem privilégios para gravar tipo de arquivo
        return "<h1>Sem privilégios para gravar tipo de arquivo!</h1>"

    link = request.POST.get("link", None)
    if not (link and link.strip()):
        link = None
    if link:
        if link[:4] != "http":
            link = "http://" + link

        max_length = Documento._meta.get_field("link").max_length
        if len(link) > max_length - 1:
            return "<h1>Erro: Nome do link maior que " + str(max_length) + " caracteres.</h1>"

    max_length = Documento._meta.get_field("documento").max_length
    if "arquivo" in request.FILES and len(request.FILES["arquivo"].name) > max_length - 1:
            return "<h1>Erro: Nome do arquivo maior que " + str(max_length) + " caracteres.</h1>"

    # (0, 'Português'),
    # (1, 'Inglês'),
    lingua_do_documento = 0 # Valor default
    lingua = request.POST.get("lingua_do_documento", "portugues")
    if lingua == "ingles":
        lingua_do_documento = 1
    
    anotacao = request.POST.get("anotacao", None)
    if not (anotacao and anotacao.strip()):
        anotacao = None
    if anotacao:
        max_length = Documento._meta.get_field("anotacao").max_length
        if len(anotacao) > max_length - 1:
            return "<h1>Erro: Anotação maior que " + str(max_length) + " caracteres.</h1>"

    if forca_confidencial:
        confidencial = True
    else:
        confidencial = "confidencial" in request.POST and request.POST["confidencial"] == "true"

    if "documentos" in request.POST and len(request.POST["documentos"])>0:
        # Buscando documento na base de dados
        documento = get_object_or_404(Documento, id=request.POST["documentos"])
    else:
        documento = Documento()  # Criando documento na base de dados

    if "organizacao" in request.POST and request.POST["organizacao"] != "":
        documento.organizacao = get_object_or_404(Organizacao, id=request.POST["organizacao"])

    documento.projeto = projeto
    documento.tipo_documento = tipo
    documento.data = data
    documento.link = link
    documento.anotacao = anotacao
    documento.lingua_do_documento = lingua_do_documento
    documento.confidencial = confidencial

    if usuario is not None:
        documento.usuario = usuario
    else:
        documento.usuario = request.user

    algum_arquivo = False
    if "arquivo" in request.FILES:
        arquivo = simple_upload(request.FILES["arquivo"],
                                path=get_upload_path(documento, ''))
        documento.documento = arquivo[len(settings.MEDIA_URL):]
        algum_arquivo = True

    if "documentos" in request.POST:
        algum_arquivo = True

    if (not algum_arquivo) and (link is None):
        return "<h1>Erro: Arquivo ou link não informado corretamente.</h1>"

    documento.save()

    return None
