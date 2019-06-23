# Desenvolvido para o Projeto Final de Engenharia
# Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
# Data: 15 de Maio de 2019

from import_export import resources, fields

from .models import Projeto, Empresa, Configuracao, Disciplina
from users.models import PFEUser, Aluno, Professor, Funcionario, Opcao

class ProjetosResource(resources.ModelResource):
    class Meta:
        model = Projeto

class OrganizacoesResource(resources.ModelResource):
    class Meta:
        model = Empresa

class ConfiguracaoResource(resources.ModelResource):
    class Meta:
        model = Configuracao

class DisciplinasResource(resources.ModelResource):
    nome = fields.Field(attribute='nome',column_name='nome')
    def get_instance(self, instance_loader, row):
        # Returning False prevents us from looking in the
        # database for rows that already exist
        return False
    class Meta:
        model = Disciplina
        fields = ('nome',)
        export_order = fields

## MOVER PARA RESOURCES DE USERS (ACCOUNTS)

class UsuariosResource(resources.ModelResource):
    class Meta:
        model = PFEUser

class AlunosResource(resources.ModelResource):
    class Meta:
        model = Aluno

class ProfessoresResource(resources.ModelResource):
    class Meta:
        model = Professor

class OpcoesResource(resources.ModelResource):
    class Meta:
        model = Opcao