#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 16 de Junho de 2023
"""

from django.db import models


class Carta(models.Model):
    """Textos para serem usados em comunicações."""

    template = models.CharField("Nome do Template", max_length=64, unique=True,
                                help_text="Nome do Template")

    sigla = models.CharField("Sigla", max_length=4, null=True, blank=True, unique=True,
                            help_text="Sigla do template")

    texto = models.TextField("Texto", max_length=18000, null=True, blank=True,
                             help_text="Texto em português para ser usado em comunicações")
    
    texto_en = models.TextField("Texto EN", max_length=18000, null=True, blank=True,
                                help_text="Texto em inglês para ser usado em comunicações")
    
    class Meta:
        ordering = ["template",]
        verbose_name = "Carta"
        verbose_name_plural = "Cartas"

    def __str__(self):
        """Retorno padrão textual."""
        return self.template


class GrupoCertificado(models.Model):
    """Grupos de certificados."""

    nome = models.CharField("Nome", max_length=128, unique=True,
                            help_text="Nome do grupo de certificado")
    
    nome_en = models.CharField("Nome EN", max_length=128, null=True, blank=True,
                               help_text="Nome do grupo de certificado em inglês")
    
    sigla = models.CharField("Sigla", max_length=4, null=True, blank=True, unique=True,
                             help_text="Sigla do grupo de certificado")
    
    cor = models.CharField("Cor", max_length=6, null=True, blank=True,
                           help_text="Cor do grupo de certificado em hexadecimal")
    
    def __str__(self):
        return self.nome

    class Meta:
        ordering = ["nome",]
        verbose_name = "Grupo de Certificado"
        verbose_name_plural = "Grupos de Certificados"


class TipoCertificado(models.Model):
    """Tipos de certificados."""
    
    titulo = models.CharField("Título", max_length=48, null=True, blank=True,
                              help_text="Título do tipo de certificado")
    
    sigla = models.CharField("Sigla", max_length=4, null=True, blank=True, unique=True,
                                help_text="Sigla do tipo de certificado")

    descricao = models.CharField("Descrição", max_length=256, null=True, blank=True,
                                help_text="Descrição do tipo de certificado")
    
    grupo_certificado = models.ForeignKey("administracao.GrupoCertificado", null=True, blank=True, on_delete=models.SET_NULL,
                                            help_text="Grupo de certificado")
    
    subtitulo = models.CharField("Subtítulo", max_length=48, null=True, blank=True,
                                 help_text="Subtítulo do tipo de certificado, para o nome dos arquivos")
    
    template = models.ForeignKey("administracao.Carta", null=True, blank=True, on_delete=models.SET_NULL,
                                    help_text="Template de certificado")

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = "Tipo de Certificado"
        verbose_name_plural = "Tipos de Certificados"


class TipoEvento(models.Model):
    """Tipos de eventos."""

    nome = models.CharField("Nome", max_length=128, unique=True,
                            help_text="Nome do tipo de evento")
    
    nome_en = models.CharField("Nome EN", max_length=128, null=True, blank=True,
                               help_text="Nome do tipo de evento em inglês")
    
    cor = models.CharField("Cor", max_length=6, null=True, blank=True,
                            help_text="Cor do tipo de evento em hexadecimal")
    
    sigla = models.CharField("Sigla", max_length=4, null=True, blank=True, unique=True,
                            help_text="Sigla do tipo de evento")
    
    coordenacao = models.BooleanField("Coordenação", default=False,
                                      help_text="Evento de coordenação, senão é para estudantes")                                        

    def __str__(self):
        return self.nome
    
    class Meta:
        ordering = ["nome",]
        verbose_name = "Tipo de Evento"
        verbose_name_plural = "Tipos de Eventos"
        