#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 9 de Outubro de 2023
"""

from django.db import models


# from django.contrib.postgres.fields import ArrayField

# from operacional.models import Curso

# class PerfilVaga(models.Model):
#     """Perfil de estudante para uma vaga em proposta de projeto."""

#     # curso = models.ForeignKey('operacional.Curso', null=True, blank=True,
#     #                              on_delete=models.SET_NULL,
#     #                              help_text="Perfis desejados para uma vaga")
    
#     curso = ArrayField(models.ForeignKey(Curso, on_delete=models.SET_NULL))

#     class Meta:
#         verbose_name = 'Perfil de Vaga'
#         verbose_name_plural = 'Perfil de Vagas'

#     @classmethod
#     def create(cls):
#         """Cria um objeto (entrada) em PerfilVaga."""
#         perfil = cls()
#         return perfil

#     def __str__(self):
#         """Retorno padrão textual."""
#         return self.template
