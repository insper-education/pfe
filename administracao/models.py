#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 16 de Junho de 2023
"""

import json
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
    
    exame = models.ForeignKey("academica.Exame", null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="Exame associado ao certificado")

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = "Tipo de Certificado"
        verbose_name_plural = "Tipos de Certificados"
        ordering = ["titulo",]


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
    
    descricao = models.CharField("Descrição", max_length=256, null=True, blank=True,
                                help_text="Descrição do tipo de evento")
    
    sublinhado = models.BooleanField("Sublinhado", default=False,
                                    help_text="Sublinhado no calendário")
    
    duracao = models.PositiveSmallIntegerField("Duração padrão", default=0,
                                                help_text="Duração padrão em minutos")

    def __str__(self):
        return self.nome
    
    class Meta:
        ordering = ["nome",]
        verbose_name = "Tipo de Evento"
        verbose_name_plural = "Tipos de Eventos"


class Despesa(models.Model):
    """Despesa realiza."""

    TIPO_DE_DESPESA = (
        (0, "outros"),
        (1, "projeto"), #(equipamentos, aws, etc)
        (2, "evento"), #(de encerramento)
        (3, "banca"), #(coffebreak, etc)
        (4, "reunião"), #(comitê, etc)
        (5, "infraestrutura"), #(aws servidor, etc)
    )

    tipo_de_despesa = models.PositiveSmallIntegerField(choices=TIPO_DE_DESPESA, default=0,
                                                       help_text="Tipo de despesa")

    projeto = models.ForeignKey("projetos.Projeto", on_delete=models.CASCADE, null=True, blank=True,
                                help_text="Projeto")
    
    data = models.DateField("Data", null=True, blank=True,
                            help_text="Data da despesa")
    
    descricao = models.CharField("Descrição", max_length=512, null=True, blank=True,
                                 help_text="Descrição da despesa")
    
    fornecedor = models.CharField("Fornecedor", max_length=512, null=True, blank=True,
                                  help_text="Fornecedor (com contato se possível)")
    
    valor_r = models.DecimalField("Valor R$", max_digits=12, decimal_places=2, null=True, blank=True,
                                  help_text="Valor da despesa em reais")
    
    valor_d = models.DecimalField("Valor US$", max_digits=12, decimal_places=2, null=True, blank=True,
                                  help_text="Valor da despessa em dólares")

    documentos = models.ManyToManyField("projetos.Documento",
                                       help_text="Imagem ou outro documento da despesa")
    
    def __str__(self):
        return f"{self.get_tipo_de_despesa_display()} - {self.descricao}"
    
    class Meta:
        ordering = ["projeto", "data",]
        verbose_name = "Despesa"
        verbose_name_plural = "Despesas"


class Estrutura(models.Model):
    """Estrutura de dados usadas em diversas partes."""
    
    nome = models.CharField("Nome", max_length=128, null=True, blank=True,
                            help_text="Nome da estrutura")
    
    sigla = models.CharField("Sigla", max_length=5, null=True, blank=True, unique=True,
                            help_text="Sigla da estrutura")
    
    descricao = models.CharField("Descrição", max_length=256, null=True, blank=True,
                                help_text="Descrição da estrutura")
    
    json = models.TextField("JSON", max_length=32000, null=True, blank=True,
                            help_text="JSON com a estrutura")

    def __str__(self):
        return self.nome
    
    @staticmethod
    def loads(nome):
        """Carrega o JSON."""
        estrutura = Estrutura.objects.get(nome=nome)
        return json.loads(estrutura.json) if estrutura.json else None

    class Meta:
        verbose_name = "Estrutura"
        verbose_name_plural = "Estruturas"
        ordering = ["nome",]
