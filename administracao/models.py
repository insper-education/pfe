#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 16 de Junho de 2023
"""

from django.db import models

class Carta(models.Model):
    """Dados das organizações que propõe projetos para o PFE."""

    template = models.CharField("Nome do Template", max_length=32,
                            help_text="Nome do Template")

    texto = models.TextField("Texto", max_length=5000, null=True, blank=True,
                                   help_text="Texto para ser enviado")
    
    class Meta:
        ordering = ["template"]
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
