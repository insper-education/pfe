#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

from import_export import resources, fields

from users.models import PFEUser, Aluno, Professor, Parceiro, Opcao, Alocacao
from .models import Projeto, Organizacao, Configuracao, Disciplina, Feedback, Avaliacao


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


def converte_conceito(conceito):
    """ Converte de Letra para Número. """
    if conceito == "A+":
        return 10
    elif conceito == "A" or conceito == "A ":
        return 9
    elif conceito == "B+":
        return 8
    elif conceito == "B" or conceito == "B ":
        return 7
    elif conceito == "C+":
        return 6
    elif conceito == "C" or conceito == "C ":
        return 5
    elif conceito == "D" or conceito == "D ":
        return 4
    return 0

def recupera_objetivo(objetivo_str):

    if objetivo_str == "Comunicação" or objetivo_str == "Comunicacao" or objetivo_str == "CO":
        objetivo = ObjetivosDeAprendizagem.objects.get(titulo="Comunicação", avaliacao_grupo=True)

    elif objetivo_str == "Comunicação" or objetivo_str == "Comunicacao" or objetivo_str == "DE":
        objetivo = ObjetivosDeAprendizagem.objects.get(titulo="Design/Empreendedorismo", avaliacao_grupo=True)
    
    elif objetivo_str == "Comunicação" or objetivo_str == "Comunicacao" or objetivo_str == "TW":
        objetivo = ObjetivosDeAprendizagem.objects.get(titulo="Trabalho em Equipe", avaliacao_grupo=True)

    elif objetivo_str == "Organização" or objetivo_str == "Organizacao" or objetivo_str == "OR":
        objetivo = ObjetivosDeAprendizagem.objects.get(titulo="Organização", avaliacao_grupo=True)

    elif objetivo_str == "Execução Técnica" or objetivo_str == "Execucao Tecnica" or objetivo_str == "TK":
        objetivo = ObjetivosDeAprendizagem.objects.get(titulo="Execução Técnica", avaliacao_grupo=True)

    else:
        return "ERROR"

    return objetivo

class Avaliacoes2Resource(resources.ModelResource):
    """Model Resource para tratar dados de Avaliações."""
    campos = [
        'estudante (primeira parte do e-mail, obrigatório)',
        'ano',
        'semestre',
        'avaliação',
        'peso',
        'nota',
    ]
    def before_import_row(self, row, **kwargs): #forma que arrumei para evitar preencher com o mesmo dado
        estudante_str = row.get('estudante')
        if estudante_str is None:
            pass
            #print("Erro ao recuperar o estudante [estudante_str]")
        elif estudante_str != "":

            #try:
            aluno = Aluno.objects.get(user__username=estudante_str)
            #except Aluno.DoesNotExist:
            #pass

            ano = int(row.get('ano'))
            semestre = int(row.get('semestre'))

            alocacao = Alocacao.objects.get(aluno=aluno, projeto__ano=ano, projeto__semestre=semestre)
            
            projeto = alocacao.projeto
            
            avaliacao = row.get('avaliação')
            
            # ( 0, 'Banca'),
            # (12, 'Relatório Final de Grupo'),
            # (21, 'Relatório Intermediário Individual'),
            # (22, 'Relatório Final Individual'),

            if avaliacao=="RP" or avaliacao=="Relatório de Planejamento" or avaliacao=="Relatorio de Planejamento":
                (aval, _created) = Avaliacao2.objects.get_or_create(projeto=projeto, tipo_de_entrega=10) #(10, 'Relatório de Planejamento'),
                aval.nota = float(row.get('nota'))
                aval.avaliador = projeto.orientador.user

            if avaliacao=="RIG" or avaliacao=="Relatório Intermediário Grupo" or avaliacao=="Relatorio Intermediario Grupo":
                (aval, _created) = Avaliacao2.objects.get_or_create(projeto=projeto, tipo_de_entrega=11) # (11, 'Relatório Intermediário de Grupo'),
                
                objetivo_str = row.get('objetivo')
                aval.objetivo = recupera_objetivo(objetivo_str)
                aval.avaliador = projeto.orientador.user

                if 'nota' in row:
                    aval.nota = float(row.get('nota'))
                else:
                    desempenho = row.get('desempenho')
                    aval.nota = converte_conceito(desempenho) # CALCULAR NOTA

            aval.peso = int(float(row.get('peso'))*100)

            aval.save()
            row['id'] = aval.id

    def skip_row(self, instance, original):
        return True

    class Meta:
        model = Avaliacao



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
