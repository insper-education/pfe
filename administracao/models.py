#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 16 de Junho de 2023
"""

from django.db import models
from django.db.models.functions import Lower

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
        ordering = [ "template",]
        verbose_name = "Carta"
        verbose_name_plural = "Cartas"

    @classmethod
    def create(cls):
        """Cria um objeto (entrada) em Carta."""
        carta = cls()
        return carta

    def __str__(self):
        """Retorno padrão textual."""
        return self.template


class TipoCertificado(models.Model):
    """Tipos de certificados."""
    
    titulo = models.CharField("Título", max_length=48, null=True, blank=True,
                              help_text="Título do tipo de certificado")
    
    sigla = models.CharField("Sigla", max_length=4, null=True, blank=True, unique=True,
                                help_text="Sigla do tipo de certificado")

    descricao = models.CharField("Descrição", max_length=256, null=True, blank=True,
                                help_text="Descrição do tipo de certificado")
    
    # REMOVER, após migração de dados
    tmpID = models.PositiveSmallIntegerField("ID Temporário", null=True, blank=True,
                                            help_text="ID temporário para migração de dados de certificados")
    # ˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆ

    grupo_cert = models.CharField("Grupo de Certificado", max_length=4, null=True, blank=True,
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
    
    tmpID = models.PositiveSmallIntegerField("ID Temporário", null=True, blank=True,
                                            help_text="ID temporário para migração de dados de eventos")
                                            

    def __str__(self):
        return self.nome
    
    class Meta:
        ordering = [ "nome",]
        verbose_name = "Tipo de Evento"
        verbose_name_plural = "Tipos de Eventos"
        