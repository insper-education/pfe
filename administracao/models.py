#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 16 de Junho de 2023
"""

from django.db import models
from django.db.models.functions import Lower

class Carta(models.Model):
    """Dados das organizações que propõe projetos."""

    template = models.CharField("Nome do Template", max_length=64, unique=True,
                            help_text="Nome do Template")

    texto = models.TextField("Texto", max_length=18000, null=True, blank=True,
                                   help_text="Texto para ser enviado")
    
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
