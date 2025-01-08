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
def get_documentos_publicos(self):
    """Retorna certos documentos publicos do projeto."""
            
    tipos_documento = TipoDocumento.objects.filter(
        nome__in=["Vídeo do Projeto", "Banner", "Apresentação da Banca Final"]
    )
    
    documentos = []
    for tipo in tipos_documento:
        documento = Documento.objects.filter(confidencial=False, tipo_documento=tipo, projeto=self).last()
        if documento:
            documentos.append(documento)

    return documentos

@register.filter()
def get_relatorio(banca):
    """Retorna o relatório da banca."""
    if banca.composicao.exame.sigla == "BF": # Final
        tipo_documento = TipoDocumento.objects.filter(nome="Relatório Final de Grupo")
        documento = Documento.objects.filter(tipo_documento__in=tipo_documento, projeto=banca.projeto)
    elif banca.composicao.exame.sigla == "BI": # Intermediária
        tipo_documento = TipoDocumento.objects.filter(nome="Relatório Intermediário de Grupo")
        documento = Documento.objects.filter(tipo_documento__in=tipo_documento, projeto=banca.projeto)
    elif banca.composicao.exame.sigla == "F":  # Falconi
        # Reaproveita o tipo de documento da banca final
        tipo_documento = TipoDocumento.objects.filter(nome="Relatório Final de Grupo")
        documento = Documento.objects.filter(tipo_documento__in=tipo_documento, projeto=banca.projeto)
    elif banca.composicao.exame.sigla == "P":  # Probation
        tipo_documento = TipoDocumento.objects.filter(nome="Relatório para Probation")
        documento = Documento.objects.filter(tipo_documento__in=tipo_documento, projeto=banca.alocacao.projeto)
    else:
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