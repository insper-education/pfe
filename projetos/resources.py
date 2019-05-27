# Desenvolvido para o Projeto Final de Engenharia
# Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
# Data: 15 de Maio de 2019

from import_export import resources

from .models import Projeto, Empresa
from users.models import PFEUser, Aluno, Professor, Funcionario, Opcao

class ProjetosResource(resources.ModelResource):
    class Meta:
        model = Projeto

class OrganizacoesResource(resources.ModelResource):
    class Meta:
        model = Empresa


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