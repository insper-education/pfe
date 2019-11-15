#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

from import_export import resources, fields

from users.models import PFEUser, Aluno, Professor, Parceiro, Opcao
from .models import Projeto, Empresa, Configuracao, Disciplina


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
    nome = fields.Field(attribute='nome', column_name='nome')
    def get_instance(self, instance_loader, row):
        # Returning False prevents us from looking in the
        # database for rows that already exist
        return False
    def before_import_row(self, row, **kwargs): #forma que arrumei para evitar preencher com o mesmo dado
        nome = row.get('nome')
        if nome is None:
            print("Erro ao recuperar o nome da disciplina")
        elif nome != "":
            (reg, _created) = Disciplina.objects.get_or_create(nome=nome)
            row['id'] = reg.id
    def skip_row(self, instance, original):
        return True
    class Meta:
        model = Disciplina
        fields = ('nome',)
        export_order = fields
        skip_unchanged = True

## MOVER PARA RESOURCES DE USERS (ACCOUNTS)

class UsuariosResource(resources.ModelResource):
    class Meta:
        model = PFEUser

class AlunosResource(resources.ModelResource):
    def before_import_row(self, row, **kwargs): #forma que arrumei para evitar preencher com o mesmo dado
        username = row.get('username')
        if username is None:
            print("Erro ao recuperar o username")
        elif username != "":
            (user, _created) = PFEUser.objects.get_or_create(username=username, tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0])
            user.first_name = row.get('first_name')
            user.last_name = row.get('last_name')
            user.email = row.get('email')
            user.save()
            (aluno, _created) = Aluno.objects.get_or_create(user=user)
            if row.get('curso') == "GRENGCOMP":
                aluno.curso = 'C'
            elif row.get('curso') == "GRENGMECAT":
                aluno.curso = 'X'
            elif row.get('curso') == "GRENGMECA":
                aluno.curso = 'M'
            else:
                pass #erro
            aluno.matricula = row.get('matrícula')
            aluno.anoPFE = 2018
            aluno.semestrePFE = 2
            aluno.save()
            row['id'] = aluno.id
    def skip_row(self, instance, original):
        return True
    class Meta:
        model = Aluno

class ProfessoresResource(resources.ModelResource):
    class Meta:
        model = Professor

class OpcoesResource(resources.ModelResource):
    class Meta:
        model = Opcao