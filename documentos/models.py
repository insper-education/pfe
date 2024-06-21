#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 1 de Dezembro de 2023
"""

from django.db import models


class TipoDocumento(models.Model):
    """Tipos de documentos usados."""

    nome = models.CharField("Nome", max_length=128, null=True, blank=True, unique=True,
                              help_text="Nome do Tipo de Documento")

    sigla = models.CharField("Sigla", max_length=8, null=True, blank=True, unique=True,
                              help_text="Sigla para Tipo de Documento")
    
    projeto = models.BooleanField(default=False, help_text="Relevante para projetos")

    arquivo = models.BooleanField(default=True, help_text="Se idealmente pode ser gravado como arquivo")

    link = models.BooleanField(default=True, help_text="Se idealmente pode ser gravado como link")

    gravar = models.CharField("Gravar", max_length=32, default="[4]",
                            help_text="Tipo de usuário com permissão de gravar tipo de arquivo")
    
    individual = models.BooleanField(default=False, help_text="Se é um documento individual")
    
    def __str__(self):
        return str(self.nome) 

    @classmethod
    def create(cls, nome):
        """Cria um objeto (entrada) em TipoDocumento."""
        exame = cls(nome=nome)
        return exame
    
    class Meta:
        ordering = [ "nome",]
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documentos"
