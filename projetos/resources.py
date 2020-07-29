#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

from import_export import resources, fields

from users.models import PFEUser, Aluno, Professor, Parceiro, Opcao
from .models import Projeto, Organizacao, Configuracao, Disciplina, Feedback


class ProjetosResource(resources.ModelResource):
    """Model Resource para tratar dados de Projetos."""
    class Meta:
        model = Projeto

class OrganizacoesResource(resources.ModelResource):
    """Model Resource para tratar dados de Organizações."""
    class Meta:
        model = Organizacao

class ConfiguracaoResource(resources.ModelResource):
    """Model Resource para tratar dados de Configurações."""
    class Meta:
        model = Configuracao

class FeedbacksResource(resources.ModelResource):
    """Model Resource para tratar dados de Feedbacks."""
    class Meta:
        model = Feedback

class DisciplinasResource(resources.ModelResource):
    """Model Resource para tratar dados de Disciplinas."""
    campos = [
        'FAZER',
    ]
    nome = fields.Field(attribute='nome', column_name='nome')
    def get_instance(self, instance_loader, row):
        # Returning False prevents us from looking in the
        # database for rows that already exist
        return False
    def before_import_row(self, row, **kwargs): #forma que arrumei para evitar preencher com o mesmo dado
        nome = row.get('nome')
        if nome is None:
            pass
            #print("Erro ao recuperar o nome da disciplina")
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
    """Model Resource para tratar dados de Usuários."""
    class Meta:
        model = PFEUser

class AlunosResource(resources.ModelResource):
    """Model Resource para tratar dados de Estudantes."""
    campos = [
        'usuário (primeira parte do e-mail, obrigatório)',
        'nome',
        'sobrenome',
        'email (sem o traço separando "e" de "mail")',
        'gênero (M|F)',
        'curso (GRENGCOMP|GRENGMECAT|GRENGMECA)',
        'matrícula',
        'cr (ponto como separador decimal)',
        'anoPFE',
        'semestrePFE',
    ]
    def before_import_row(self, row, **kwargs): #forma que arrumei para evitar preencher com o mesmo dado
        username = row.get('usuário')
        if username is None:
            pass
            #print("Erro ao recuperar o usuário [username]")
        elif username != "":
            # recupera dados do aluno se ele já estava cadastrado
            (user, _created) = PFEUser.objects.get_or_create(username=username,
                                                             tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0])
            user.first_name = row.get('nome')
            user.last_name = row.get('sobrenome')
            user.email = row.get('email')
            user.genero = row.get('gênero')
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
            aluno.cr = float(row.get('cr'))
            aluno.anoPFE = int(row.get('anoPFE'))
            aluno.semestrePFE = int(row.get('semestrePFE'))

            aluno.save()
            row['id'] = aluno.id
    def skip_row(self, instance, original):
        return True
    class Meta:
        model = Aluno

class ProfessoresResource(resources.ModelResource):
    """Model Resource para tratar dados de Professores."""
    class Meta:
        model = Professor

class ParceirosResource(resources.ModelResource):
    """Model Resource para tratar dados de Parceiros."""
    class Meta:
        model = Parceiro

class OpcoesResource(resources.ModelResource):
    """Model Resource para tratar dados de Opções."""
    class Meta:
        model = Opcao
