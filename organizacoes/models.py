#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 11 de Abril de 2025
"""

from django.db import models

class Segmento(models.Model):
    """Tipos de retorno de comunicações com as organizações parceiras."""

    nome = models.CharField(max_length=64, help_text="nome do segmento da organização")

    nome_en = models.CharField(max_length=64, default="", help_text="nome do segmento da organização em inglês")

    icone = models.CharField(max_length=8, default="", help_text="icone que representa o segmento da organização")

    cor = models.CharField(max_length=8, default="000000", help_text="cor que representa o segmento da organização")

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Segmento"
        verbose_name_plural = "Segmentos"
        ordering = ["nome"]
