#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

import datetime
from import_export import resources, fields

from users.models import PFEUser, Aluno, Professor, Parceiro, Opcao, Alocacao
from .models import Projeto, Proposta, Organizacao, Configuracao, Disciplina
from .models import Feedback, Avaliacao2, ObjetivosDeAprendizagem, Observacao
from .models import Area, AreaDeInteresse

from .support import converte_conceito
# from .support import converte_letra


class ProjetosResource(resources.ModelResource):
    """Model Resource para tratar dados de Projetos."""
    class Meta:
        model = Projeto


class Avaliacao2Resource(resources.ModelResource):
    """Model Resource para tratar dados de Avaliações."""
    class Meta:
        model = Avaliacao2


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

    # forma que arrumei para evitar preencher com o mesmo dado
    def before_import_row(self, row, **kwargs):
        nome = row.get('nome')
        if nome is None:
            pass
            # print("Erro ao recuperar o nome da disciplina")
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


def recupera_objetivo(objetivo_str):

    if objetivo_str == "Comunicação" or objetivo_str == "Comunicacao" or objetivo_str == "CO":
        objetivo = ObjetivosDeAprendizagem.objects.get(titulo="Comunicação",
                                                       avaliacao_grupo=True)

    elif objetivo_str == "Design/Empreendedorismo" or\
      objetivo_str == "Design e Empreendedorismo" or objetivo_str == "DE":
        objetivo = ObjetivosDeAprendizagem.objects.get(titulo="Design/Empreendedorismo",
                                                       avaliacao_grupo=True)

    elif objetivo_str == "Trabalho em Equipe" or objetivo_str == "TW":
        objetivo = ObjetivosDeAprendizagem.objects.get(titulo="Trabalho em Equipe",
                                                       avaliacao_grupo=True)

    elif objetivo_str == "Organização" or objetivo_str == "Organizacao" or objetivo_str == "OR":
        objetivo = ObjetivosDeAprendizagem.objects.get(titulo="Organização",
                                                       avaliacao_grupo=True)

    elif objetivo_str == "Execução Técnica" or\
      objetivo_str == "Execucao Tecnica" or\
      objetivo_str == "TK":
        objetivo = ObjetivosDeAprendizagem.objects.get(titulo="Execução Técnica",
                                                       avaliacao_grupo=True)

    else:
        return "ERROR"

    return objetivo


def le_momento(mnt):
    """Para ler o momento das células."""
    d = int(mnt[-11:-9])
    m = int(mnt[-9:-7])
    a = int("20"+mnt[-7:-5])  # bug do milênio
    h = int(mnt[-4:-2])
    min = int(mnt[-2:])
    t = datetime.datetime(a, m, d, h, min)  # momento da última atualização
    return t


class Avaliacoes2Resource(resources.ModelResource):
    """Model Resource para tratar dados de Avaliações."""
    campos = [
        'estudante ou user_id (primeira parte do e-mail, obrigatório)',
        'ano',
        'semestre',
        'avaliação',
        'objetivo ou criterio',
        'peso',
        'nota ou score (se não houver procura por desempenho)',
        'desempenho (opcional primeiro procura a nota)',
        'momento ou date_modified (dd/mm/aa hh:mm)',
        'observação ou feedback',
    ]

    # forma que arrumei para evitar preencher com o mesmo dado
    def before_import_row(self, row, **kwargs):
        if 'estudante' in row:
            estudante_str = row.get('estudante')
        elif 'user_id' in row:
            estudante_str = row.get('user_id')
        else:
            pass
            # print("Erro ao recuperar coluna estudante ou user_id")

        if estudante_str is None:
            pass
            # print("Erro ao recuperar o estudante [estudante_str]")
        elif estudante_str != "":

            # try:
            aluno = Aluno.objects.get(user__username=estudante_str)
            # except Aluno.DoesNotExist:
            # pass

            ano = int(row.get('ano'))
            semestre = int(row.get('semestre'))

            alocacao = Alocacao.objects.get(aluno=aluno,
                                            projeto__ano=ano,
                                            projeto__semestre=semestre)

            projeto = alocacao.projeto

            avaliador = projeto.orientador.user

            if "avaliação" in row:
                avaliacao = row.get('avaliação')
            else:
                pass
                # print("Erro ao recuperar coluna avaliação")

            if "momento" in row:
                t = le_momento(row.get('momento'))
            elif "date_modified" in row:  # caso esqueça de alterar o nome na coluna
                t = le_momento(row.get('date_modified'))
            else:
                t = datetime.datetime.now()

            tipo_de_avaliacao = 0  # padrão, mas que não deve acontecer

            avaliador = projeto.orientador.user  # por padrão o avaliador é o orientador

            # recupera objetivo, se houver
            if 'objetivo' in row:
                objetivo = recupera_objetivo(row.get('objetivo'))
            elif 'criterio' in row:
                objetivo = recupera_objetivo(row.get('criterio'))
            else:
                objetivo = None

            if avaliacao == "RP" or avaliacao == "Relatório de Planejamento" or avaliacao == "Relatorio de Planejamento":
                tipo_de_avaliacao = 10  # (10, 'Relatório de Planejamento'),
                (aval, _created) = Avaliacao2.objects.get_or_create(projeto=projeto,
                                                                    avaliador=avaliador,
                                                                    momento=t,
                                                                    tipo_de_avaliacao=tipo_de_avaliacao)

            elif avaliacao == "RIG" or avaliacao == "Relatório Intermediário Grupo" or avaliacao == "Relatorio Intermediario Grupo":
                tipo_de_avaliacao = 11  # (11, 'Relatório Intermediário de Grupo'),
                (aval, _created) = Avaliacao2.objects.get_or_create(objetivo=objetivo,
                                                                    projeto=projeto,
                                                                    avaliador=avaliador,
                                                                    momento=t,
                                                                    tipo_de_avaliacao=tipo_de_avaliacao)

            elif avaliacao == "RFG" or avaliacao == "Relatório Final Grupo" or avaliacao == "Relatório Final de Grupo" or avaliacao == "Relatorio Final Grupo" or avaliacao == "Relatorio Final de Grupo":
                tipo_de_avaliacao = 12  # (12, 'Relatório Final de Grupo'),
                (aval, _created) = Avaliacao2.objects.get_or_create(objetivo=objetivo,
                                                                    projeto=projeto,
                                                                    avaliador=avaliador,
                                                                    momento=t,
                                                                    tipo_de_avaliacao=tipo_de_avaliacao)

            elif avaliacao == "RII" or avaliacao == "Relatório Intermediário Individual" or avaliacao == "Relatorio Intermediario Individual" or avaliacao == "Relatório Parcial Individual" or avaliacao == "Relatorio Parcial Individual":
                tipo_de_avaliacao = 21  # (21, 'Relatório Intermediário Individual'),
                (aval, _created) = Avaliacao2.objects.get_or_create(objetivo=objetivo,
                                                                    projeto=projeto,
                                                                    alocacao=alocacao,
                                                                    avaliador=avaliador,
                                                                    momento=t,
                                                                    tipo_de_avaliacao=tipo_de_avaliacao)

            elif avaliacao == "RFI" or avaliacao == "Relatório Final Individual" or avaliacao == "Relatorio Final Individual":
                tipo_de_avaliacao = 22  # (22, 'Relatório Final Individual'),
                (aval, _created) = Avaliacao2.objects.get_or_create(objetivo=objetivo,
                                                                    projeto=projeto,
                                                                    alocacao=alocacao,
                                                                    avaliador=avaliador,
                                                                    momento=t,
                                                                    tipo_de_avaliacao=tipo_de_avaliacao)

            elif avaliacao == "BI" or avaliacao == "Banca Intermediária" or avaliacao == "Banca Intermediaria":
                tipo_de_avaliacao = 1  # ( 1, 'Banca Intermediária'),
                # o certo seria procurar avaliador
                (aval, _created) = Avaliacao2.objects.get_or_create(objetivo=objetivo,
                                                                    projeto=projeto,
                                                                    avaliador=avaliador,
                                                                    momento=t,
                                                                    tipo_de_avaliacao=tipo_de_avaliacao)

            elif avaliacao == "BF" or avaliacao == "Banca Final":
                tipo_de_avaliacao = 2  # ( 2, 'Banca Final'),
                # o certo seria procurar avaliador
                (aval, _created) = Avaliacao2.objects.get_or_create(objetivo=objetivo,
                                                                    projeto=projeto,
                                                                    avaliador=avaliador,
                                                                    momento=t,
                                                                    tipo_de_avaliacao=tipo_de_avaliacao)

            # NÃO MAIS USADAS, FORAM USADAS QUANDO O PFE ERA AINDA EM DOIS SEMESTRES
            elif avaliacao == "PPF" or avaliacao == "Planejamento Primeira Fase":
                tipo_de_avaliacao = 50  # (50, 'Planejamento Primeira Fase'),
                (aval, _created) = Avaliacao2.objects.get_or_create(projeto=projeto,
                                                                    avaliador=avaliador,
                                                                    momento=t,
                                                                    tipo_de_avaliacao=tipo_de_avaliacao)

            elif avaliacao == "API" or avaliacao == "Avaliação Parcial Individual":
                tipo_de_avaliacao = 51  # (51, 'Avaliação Parcial Individual'),
                (aval, _created) = Avaliacao2.objects.get_or_create(objetivo=objetivo,
                                                                    projeto=projeto,
                                                                    alocacao=alocacao,
                                                                    avaliador=avaliador,
                                                                    momento=t,
                                                                    tipo_de_avaliacao=tipo_de_avaliacao)

            elif avaliacao == "AFI" or avaliacao == "Avaliação Final Individual":
                tipo_de_avaliacao = 52  # (52, 'Avaliação Final Individual'),
                (aval, _created) = Avaliacao2.objects.get_or_create(objetivo=objetivo,
                                                                    projeto=projeto,
                                                                    alocacao=alocacao,
                                                                    avaliador=avaliador,
                                                                    momento=t,
                                                                    tipo_de_avaliacao=tipo_de_avaliacao)

            else:
                pass
                # print("ERRO, AVALIAÇÃO NÃO RECONHECIDA !!!!")
                # print(avaliacao)

            # CASO A LEITURA TENHA ALGUM FEEDBACK/OBSERVAÇÃO
            if "observação" in row:
                obs_str = row.get('observação')
            if "feedback" in row:
                obs_str = row.get('feedback')
            else:
                obs_str = ""

            if obs_str != "":
                (obs, _created) = Observacao.objects.get_or_create(objetivo=objetivo,
                                                                   projeto=projeto,
                                                                   avaliador=avaliador,
                                                                   alocacao=alocacao,
                                                                   momento=t,
                                                                   tipo_de_avaliacao=tipo_de_avaliacao)
                obs.observacoes = obs_str
                obs.save()

            # recuper nota, se houver
            if 'nota' in row:
                aval.nota = float(row.get('nota'))
            elif 'score' in row:
                aval.nota = float(row.get('score'))
            elif 'desempenho' in row:
                desempenho = row.get('desempenho')
                aval.nota = converte_conceito(desempenho)  # CALCULAR NOTA
            else:
                pass
                # print("Erro ao recuperar a nota")

            # Todas as avaliações tem de ter peso
            # Pesos são convertidos para porcentagens
            if "peso" in row:
                peso = float(row.get('peso'))*100
                aval.peso = peso
            else:
                pass
                # print("Erro ao recuperar o peso da avaliação")

            aval.save()
            row['id'] = aval.id

    def skip_row(self, instance, original):
        return True

    class Meta:
        model = Avaliacao2


# MOVER PARA RESOURCES DE USERS (ACCOUNTS)

class UsuariosResource(resources.ModelResource):
    """Model Resource para tratar dados de Usuários."""
    class Meta:
        model = PFEUser


def atualizar_campo(registro, campo, valor):
    if (valor is not None) and (valor != ""):
        tmp = getattr(registro, campo)
        if (tmp is not None) and (tmp != "") and (tmp != valor):
            # print("Dado atualizado de {0} para {1}".format(tmp, valor))
            pass
        else:
            # print("Dados iguais em {0} : {0}".format(campo, tmp))
            pass
        setattr(registro, campo, valor)
    else:
        # print("Não houve atualização de {0}".format(campo))
        pass


class EstudantesResource(resources.ModelResource):
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

    def before_import_row(self, row, **kwargs):  # forma que arrumei para evitar preencher com o mesmo dado
        username = row.get('usuário')
        if username is None:
            pass
            # print("Erro ao recuperar o usuário [username]")
        elif username != "":
            # recupera dados do estudante se ele já estava cadastrado
            (user, _created) = PFEUser.objects.get_or_create(username=username,
                                                             tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0])

            atualizar_campo(user, 'first_name', row.get('nome'))
            atualizar_campo(user, 'last_name', row.get('sobrenome'))
            atualizar_campo(user, 'email', row.get('email'))
            atualizar_campo(user, 'genero', row.get('gênero'))

            user.save()
            (aluno, _created) = Aluno.objects.get_or_create(user=user)
            if row.get('curso') == "GRENGCOMP":
                aluno.curso = 'C'
            elif row.get('curso') == "GRENGMECAT":
                aluno.curso = 'X'
            elif row.get('curso') == "GRENGMECA":
                aluno.curso = 'M'
            else:
                pass  # erro

            atualizar_campo(aluno, 'matricula', row.get('matrícula'))
            atualizar_campo(aluno, 'cr', row.get('cr'))
            atualizar_campo(aluno, 'anoPFE', row.get('anoPFE'))
            atualizar_campo(aluno, 'semestrePFE', row.get('semestrePFE'))

            if "familia" in row:
                aluno.familia = row["familia"]

            aluno.save()

            # Isso caça propostas, não deverá ser novamente usado no futuro
            # Esta criando Opções sem ver se já existiam
            contador = 1
            while contador < 100:
                if str(contador) in row and row[str(contador)] != "":
                    proposta = Proposta.objects.get(id=contador)

                    (op, _created) = Opcao.objects.get_or_create(aluno=aluno,
                                                                 proposta=proposta,
                                                                 prioridade=int(row[str(contador)]))

                    op.save()
                contador += 1

            if "areas" in row:
                if "Programação" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Sistemas de Informação")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area, usuario=user)
                    area_int.save()

                if "Gestão de Projetos" in row["areas"] or "finanças" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Administração, Economia e Finanças")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area, usuario=user)
                    area_int.save()

                if "Manufatura" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Manufatura Avançada")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area, usuario=user)
                    area_int.save()

                if "Dados" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Ciência dos Dados")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area, usuario=user)
                    area_int.save()

                if "Controle" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Controle de Sistemas Dinâmicos")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area, usuario=user)
                    area_int.save()

                if "Social" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Inovação Social")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area, usuario=user)
                    area_int.save()

                if "Eletrônica" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Sistemas Embarcados")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area, usuario=user)
                    area_int.save()

                if "3D" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Sistemas Interativos")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area, usuario=user)
                    area_int.save()

                if "Robótica" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Robótica")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area, usuario=user)
                    area_int.save()

                if "Automação" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Automação Industrial")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area, usuario=user)
                    area_int.save()

                if "Machine" in row["areas"] or "AI" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Inteligência Artificial")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area, usuario=user)
                    area_int.save()

                if "Machine" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Inteligência Artificial")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area, usuario=user)
                    area_int.save()

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
