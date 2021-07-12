#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 12 de Julho de 2021
"""

from projetos.models import Certificado

from django import template
register = template.Library()

@register.filter
def certificado_banca(banca, usuario):
    """Retorna o certificado de um membro de banca."""
    if banca.tipo_de_banca == 0:  # (0, 'Final'),
        certificado = Certificado.objects.filter(usuario=usuario, projeto=banca.projeto, tipo_de_certificado=104)  # (104, "Membro de Banca Final"),
    elif banca.tipo_de_banca == 1:  # (1, 'Intermediária'),
        certificado = Certificado.objects.filter(usuario=usuario, projeto=banca.projeto, tipo_de_certificado=103)  # (103, "Membro de Banca Intermediária"),
    elif banca.tipo_de_banca == 2:  # (2, 'Certificação Falconi'),
        certificado = Certificado.objects.filter(usuario=usuario, projeto=banca.projeto, tipo_de_certificado=105)  # (105, "Membro da Banca Falconi"),
    
    if certificado:
        return certificado.last().documento.url
    return None
