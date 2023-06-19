#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 27 de Dezembro de 2022
"""

from django.db import models


class Curso(models.Model):
    """Classe para os cursos da escola."""

    nome = models.CharField("Nome", max_length=50, null=True,
                                    blank=True,
                                    help_text='Nome do curso')

    # LIGAR ISSO EM ALGUM MOMENTO !!!!
    # sigla = models.CharField("Sigla", max_length=10, null=True,
    #                                   blank=True,
    #                                   help_text='Sigla do curso, ex: GRENGCOMP, GRENGMECAT, GRENGMECA')

    sigla_curta = models.CharField("Sigla Curta", max_length=3, null=True,
                                      blank=True,
                                      help_text='Sigla curta do curso: ex: C, X, M')

    cor = models.CharField(max_length=6, default="000000", help_text='Cor para curso')

    curso_do_insper = models.BooleanField("Curso do Insper", default=True,
                             help_text='Indicar caso seja um curso do Insper (outros são usados para estudantes de intercâmbio)')

    class Meta:
        ordering = ['nome']
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'

    def __str__(self):
        """Retorna o nome do curso."""
        return self.nome
