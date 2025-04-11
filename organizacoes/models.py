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

    icone = models.CharField(max_length=6, default="", help_text="icone que representa o segmento da organização")

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Segmento"
        verbose_name_plural = "Segmentos"
        ordering = ["nome"]
