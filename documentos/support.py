#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 18 de Dezembro de 2020
"""

import os
from io import BytesIO # Para gerar o PDF
from xhtml2pdf import pisa # Para gerar o PDF

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template import Template, Context
from django.template.loader import get_template

from documentos.models import TipoDocumento

from projetos.models import Documento, Configuracao, Certificado
from projetos.support import get_upload_path



def render_to_pdf(template_src, context_dict=None):
    """Renderiza um documento em PDF."""
    template = get_template(template_src)
    if template:
        html_doc = template.render(context_dict)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html_doc.encode("utf-16")), result)
        if not pdf.err:
            return result
    return None


def render_pdf_file(template_src, context_dict, path):
    """Renderiza um documento em PDF (lendo de um arquivo template)."""
    template = get_template(template_src)
    if template:
        html_doc = template.render(context_dict)
        result = open(path, "wb")
        pdf = pisa.pisaDocument(BytesIO(html_doc.encode("utf-8")), result)
        result.close()
        return pdf
    return None


def render_from_text_to_pdf_file(template_txt, context_dict, path):
    """Renderiza um documento em PDF  (lendo de um texto)."""
    template = Template(template_txt)
    if template:
        html_doc = template.render(Context(context_dict))
        result = open(path, "wb")
        pdf = pisa.pisaDocument(BytesIO(html_doc.encode("utf-8")), result)
        result.close()
        return pdf
    return None


def atualiza_certificado(usuario, projeto, tipo, contexto=None, alocacao=None):
    """Atualiza os certificados."""
    configuracao = get_object_or_404(Configuracao)

    certificado, _ = \
        Certificado.objects.get_or_create(usuario=usuario, projeto=projeto, tipo_certificado=tipo, alocacao=alocacao)

    if projeto and not certificado.documento:

        tipo_documento = TipoDocumento.objects.get(sigla="PT")
        papel_timbrado = Documento.objects.filter(tipo_documento=tipo_documento).last()

        context = {
            "usuario": usuario,
            "projeto": projeto,
            "configuracao": configuracao,
            "papel_timbrado": papel_timbrado.documento.url[1:],
        }
        if contexto:
            context.update(contexto)

        subtitulo = tipo.subtitulo if tipo.subtitulo else ""

        path = get_upload_path(certificado, "")

        full_path = settings.MEDIA_ROOT + "/" + path
        os.makedirs(full_path, mode=0o777, exist_ok=True)

        filename = full_path + "certificado" + subtitulo + ".pdf"

        pdf = render_from_text_to_pdf_file(tipo.template.texto, context, filename)

        if (not pdf) or pdf.err:
            return HttpResponse("Erro ao gerar certificados.", status=401)

        certificado.documento = path + "certificado" + subtitulo + ".pdf"
        certificado.save()

        return certificado

    return None


# Function to generate a unique arcname if the provided one already exists in the zip file
def generate_unique_arcname(zip_file, arcname):
    arcname = arcname.replace('\\','/')
    if arcname not in zip_file.namelist():
        return arcname
    else:
        base_name, extension = os.path.splitext(arcname)
        counter = 1
        while True:
            new_arcname = f"{base_name}_{counter}{extension}"
            if new_arcname not in zip_file.namelist():
                return new_arcname
            counter += 1
