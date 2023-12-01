#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 1 de Dezembro de 2023
"""

from django.db import models


class TipoDocumento(models.Model):
    """Tipos de documentos usados."""

    nome = models.TextField("Nome", max_length=128, null=True, blank=True, unique=True,
                              help_text="Título do Exame")

    projeto = models.BooleanField(default=False, help_text="Relevante para projetos")

    # Temporario, soh para fazer a migracao    
    tmp_id = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return str(self.nome) 

    @classmethod
    def create(cls, nome):
        """Cria um objeto (entrada) em TipoDocumento."""
        exame = cls(nome=nome)
        return exame
    
    class Meta:
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documentos"
