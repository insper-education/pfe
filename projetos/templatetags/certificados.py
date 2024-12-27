#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 12 de Julho de 2021
"""

from django import template
from django.shortcuts import get_object_or_404

from administracao.models import TipoCertificado

from projetos.models import Certificado

register = template.Library()

@register.filter
def certificado_banca(banca, usuario):
    """Retorna o certificado de um membro de banca."""
    if banca.tipo_de_banca == 0:  # (0, 'Final'),
        tipo = get_object_or_404(TipoCertificado, titulo="Membro de Banca Final")
        certificado = Certificado.objects.filter(usuario=usuario, projeto=banca.get_projeto(), tipo_certificado=tipo)
    elif banca.tipo_de_banca == 1:  # (1, 'Intermediária'),
        tipo = get_object_or_404(TipoCertificado, titulo="Membro de Banca Intermediária")
        certificado = Certificado.objects.filter(usuario=usuario, projeto=banca.get_projeto(), tipo_certificado=tipo)
    elif banca.tipo_de_banca == 2:  # (2, 'Certificação Falconi'),
        tipo = get_object_or_404(TipoCertificado, titulo="Membro da Banca Falconi")
        certificado = Certificado.objects.filter(usuario=usuario, projeto=banca.get_projeto(), tipo_certificado=tipo)
    elif banca.tipo_de_banca == 3:  # (3, 'Probation'),
        tipo = get_object_or_404(TipoCertificado, titulo="Membro de Banca de Probation")
        certificado = Certificado.objects.filter(usuario=usuario, projeto=banca.get_projeto(), tipo_certificado=tipo)
    else:
        certificado = None
    
    if certificado:
        documento = certificado.last()
        if documento.documento:
            return documento.documento.url

    return None


@register.filter
def certificado_mentoria(mentoria, usuario):
    """Retorna o certificado de um membro de banca."""
    tipo = get_object_or_404(TipoCertificado, titulo="Mentoria Profissional")
    certificado = Certificado.objects.filter(usuario=usuario, projeto=mentoria.projeto, tipo_certificado=tipo)
    
    if certificado:
        documento = certificado.last()
        if documento.documento:
            return documento.documento.url

    return None
