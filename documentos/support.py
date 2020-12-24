#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 18 de Dezembro de 2020
"""

from io import BytesIO # Para gerar o PDF
from xhtml2pdf import pisa # Para gerar o PDF
from django.template.loader import get_template

def render_to_pdf(template_src, context_dict=None):
    """Renderiza um documento em PDF."""

    template = get_template(template_src)
    html_doc = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_doc.encode("utf-8")), result)
    if not pdf.err:
        return result

    return None