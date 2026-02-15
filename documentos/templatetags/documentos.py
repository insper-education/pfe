#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 8 de Janeiro de 2025
"""

from django import template

from documentos.models import TipoDocumento
from projetos.models import Documento

register = template.Library()

@register.filter()
def get_planos_de_orientacao(projeto):
    """Retorna todos os planos de orientação do projeto."""
    tipo_documento = TipoDocumento.objects.get(nome="Plano de Orientação")
    documentos = Documento.objects.filter(tipo_documento=tipo_documento, projeto=projeto)
    return documentos



@register.filter()
def get_parecer_de_probatorio(projeto):
    """Retorna todos os pareceres de probatório do projeto."""
    tipo_documento = TipoDocumento.objects.get(sigla="PPP")
    documento = Documento.objects.filter(tipo_documento=tipo_documento, projeto=projeto).last()
    return documento


@register.filter()
def get_documentos_publicos(self):
    """Retorna certos documentos publicos do projeto."""
    
    nome = ["RPU", "VP", "B", "ABF"]
    
    documentos = {}
    for tipo in nome:
        documento = Documento.objects.filter(confidencial=False, tipo_documento__sigla=tipo, projeto=self).last()
        documentos[tipo] = documento

    return documentos

@register.filter()
def get_relatorio(banca):
    """Retorna o relatórios necessários para a banca."""
    if banca.sigla:
        if banca.sigla == "BF": # Final
            tipo_documento = TipoDocumento.objects.filter(nome="Relatório Final de Grupo")
            documentos = Documento.objects.filter(tipo_documento__in=tipo_documento, projeto=banca.projeto)
        elif banca.sigla == "BI": # Intermediária
            tipo_documento = TipoDocumento.objects.filter(nome="Relatório Intermediário de Grupo")
            documentos = Documento.objects.filter(tipo_documento__in=tipo_documento, projeto=banca.projeto)
        elif banca.sigla == "F":  # Falconi
            # Reaproveita o tipo de documento da banca final
            tipo_documento = TipoDocumento.objects.filter(nome="Relatório Final de Grupo")
            documentos = Documento.objects.filter(tipo_documento__in=tipo_documento, projeto=banca.projeto)
        elif banca.sigla == "P":  # Probation
            documentos = Documento.objects.filter(tipo_documento__sigla="RFG", projeto=banca.alocacao.projeto)
        else:
            return None
    else:
        return None
    
    if documentos.exists():
        return documentos.order_by("data").last()
    
    return None


@register.filter()
def get_relatorios_individuais(banca):
    """Retorna o relatórios necessários para a banca."""
    if banca.tipo_evento and banca.sigla:
        if banca.sigla == "P":  # Probation
            documentos = Documento.objects.filter(tipo_documento__sigla="RII", usuario=banca.alocacao.aluno.user) | Documento.objects.filter(tipo_documento__sigla="RFI", usuario=banca.alocacao.aluno.user)
        else:
            return None
    else:
        return None
    
    if documentos.exists():
        return documentos.order_by("data")
    
    return None


@register.filter()
def get_parecer(banca):  # Para probatório
    """Retorna o parecer produzido pelo orientador."""
    if banca.tipo_evento and banca.sigla:
        if banca.sigla == "P":  # Probation
            documentos = Documento.objects.filter(tipo_documento__sigla="PPP", projeto=banca.alocacao.projeto)
        else:
            return None
    else:
        return None
    
    if documentos.exists():
        return documentos.order_by("data").last()
    
    return None
    
    if documento.exists():
        return documento.order_by("data").last()
    
    return None

@register.filter()
def get_relatorio_final(projeto):
        tipo_documento = TipoDocumento.objects.filter(nome="Relatório Final de Grupo")
        documento = Documento.objects.filter(tipo_documento__in=tipo_documento, projeto=projeto)

        if documento.exists():
            return documento.order_by("data").last()
        return None

@register.filter()
def get_relatorio_intermediario(projeto):
    tipo_documento = TipoDocumento.objects.filter(nome="Relatório Intermediário de Grupo")
    documento = Documento.objects.filter(tipo_documento__in=tipo_documento, projeto=projeto)
    
    if documento.exists():
        return documento.order_by("data").last()
    return None

@register.filter()
def get_documentos_individuais(alocacao):
    """Retorna os documentos individuais de uma alocação."""
    tipo_documento = TipoDocumento.objects.filter(individual=True)
    documentos = Documento.objects.filter(tipo_documento__in=tipo_documento, usuario=alocacao.aluno.user, projeto=alocacao.projeto)
    return documentos.order_by("data")
    