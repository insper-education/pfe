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
    if banca.composicao and banca.composicao.exame:
        if banca.composicao.exame.sigla == "BI":  # (1, 'Intermediária'),
            tipo = get_object_or_404(TipoCertificado, titulo="Membro de Banca Intermediária")
            certificado = Certificado.objects.filter(usuario=usuario, projeto=banca.get_projeto(), tipo_certificado=tipo)
        elif banca.composicao.exame.sigla == "BF":  # (0, 'Final'),
            tipo = get_object_or_404(TipoCertificado, titulo="Membro de Banca Final")
            certificado = Certificado.objects.filter(usuario=usuario, projeto=banca.get_projeto(), tipo_certificado=tipo)
        elif banca.composicao.exame.sigla == "F":  # (2, 'Certificação Falconi'),
            tipo = get_object_or_404(TipoCertificado, titulo="Membro da Banca Falconi")
            certificado = Certificado.objects.filter(usuario=usuario, projeto=banca.get_projeto(), tipo_certificado=tipo)
        elif banca.composicao.exame.sigla == "P":  # (3, 'Probation'),
            tipo = get_object_or_404(TipoCertificado, titulo="Membro de Banca de Probation")
            certificado = Certificado.objects.filter(usuario=usuario, projeto=banca.get_projeto(), tipo_certificado=tipo)
        else:
            certificado = None
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


@register.filter
def certificado_orientador(projeto):
    """Retorna link do certificado."""
    try:
        tipo_certificado = get_object_or_404(TipoCertificado, titulo="Orientação de Projeto")
        certificado = Certificado.objects.filter(usuario=projeto.orientador.user, projeto=projeto, tipo_certificado=tipo_certificado)
        return certificado
    except:
        return None

@register.filter
def certificado_coorientador(coorientacao):
    """Se o coorientador pode emitir certificado."""
    try:
        tipo_certificado = get_object_or_404(TipoCertificado, titulo="Coorientação de Projeto")
        certificado = Certificado.objects.filter(projeto=coorientacao.projeto, usuario=coorientacao.usuario, tipo_certificado=tipo_certificado)
        return certificado
    except:
        return None

@register.filter
def get_certificados_est(alocacao):
    """Retorna todos os certificados recebidos pelo estudante nessa alocação."""
    certificados = Certificado.objects.filter(usuario=alocacao.aluno.user, projeto=alocacao.projeto)
    return certificados