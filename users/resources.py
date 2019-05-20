# Desenvolvido para o Projeto Final de Engenharia
# Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
# Data: 15 de Maio de 2019

from import_export import resources

from .models import Aluno

class AlunoResource(resources.ModelResource):
    class Meta:
        model = Aluno