#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 1 de Dezembro de 2023
"""

import datetime
import dateutil.parser

from collections import OrderedDict

from PyPDF2 import PdfFileReader

from django.shortcuts import get_object_or_404

from django.conf import settings

from projetos.models import Projeto, Organizacao, Documento
from projetos.support import get_upload_path, simple_upload

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
    infile = PdfFileReader(open(infile, "rb"))
    fields = _getFields(infile)
    return fields


# Adiciona um novo documento na base de dados
def cria_documento(request):

    projeto = None
    projeto_id = request.POST.get("projeto", "")
    if projeto_id:
        projeto = Projeto.objects.get(id=projeto_id)

    data = datetime.date.today()
    if "data" in request.POST:
        try:
            data = dateutil.parser\
                .parse(request.POST["data"])
        except (ValueError, OverflowError):
            pass

    tipo_de_documento = 255
    try:
        tipo_de_documento = request.POST.get("tipo_de_documento", "")
    except (ValueError, OverflowError):
        pass

    link = request.POST.get("link", None)
    if not (link and link.strip()):
        link = None
    if link:    
        if link[:4] != "http":
            link = "http://" + link

        max_length = Documento._meta.get_field("link").max_length
        if len(link) > max_length - 1:
            return "<h1>Erro: Nome do link maior que " + str(max_length) + " caracteres.</h1>"

    max_length = Documento._meta.get_field('documento').max_length
    if "arquivo" in request.FILES and len(request.FILES["arquivo"].name) > max_length - 1:
            return "<h1>Erro: Nome do arquivo maior que " + str(max_length) + " caracteres.</h1>"

    # (0, 'Português'),
    # (1, 'Inglês'),
    lingua_do_documento = 0 # Valor default
    lingua = request.POST.get("lingua_do_documento", "portugues")
    if lingua == "ingles":
        lingua_do_documento = 1

    confidencial = "confidencial" in request.POST and request.POST["confidencial"] == "true"

    if "documentos" in request.POST and len(request.POST["documentos"])>0:
        # Buscando documento na base de dados
        documento = get_object_or_404(Documento, id=request.POST["documentos"])
    else:
        # Criando documento na base de dados
        documento = Documento.create()

    if "organizacao" in request.POST:
        documento.organizacao = get_object_or_404(Organizacao, id=request.POST["organizacao"])
    documento.projeto = projeto
    documento.tipo_de_documento = tipo_de_documento
    documento.data = data
    documento.link = link
    documento.lingua_do_documento = lingua_do_documento
    documento.confidencial = confidencial

    # if tipo_de_documento == 25:  #(25, 'Relatório Publicado'),
    #     documento.confidencial = False
    # else:
    #     documento.confidencial = True

    if "arquivo" in request.FILES:
        arquivo = simple_upload(request.FILES["arquivo"],
                                path=get_upload_path(documento, ''))
        documento.documento = arquivo[len(settings.MEDIA_URL):]

    if ("arquivo" not in request.FILES) and (link is None):
        return "<h1>Erro: Arquivo ou link não informado corretamente.</h1>"

    documento.save()

    return None