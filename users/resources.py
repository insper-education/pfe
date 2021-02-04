#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

from import_export import resources

from .models import Aluno

# ISSO AINDA ESTA SENDO USADO, VERIFICAR !!
class AlunoResource(resources.ModelResource):
    """Classe de recursos para alunos."""
    class Meta:
        """Classe Meta."""
        model = Aluno
