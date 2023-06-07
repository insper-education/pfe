#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

import datetime
from import_export import resources, fields

from users.models import PFEUser, Aluno, Professor, Parceiro, Opcao, Alocacao
from .models import Projeto, Proposta, Organizacao, Configuracao, Disciplina
from .models import Feedback, Avaliacao2, ObjetivosDeAprendizagem, Observacao
from .models import Area, AreaDeInteresse

from operacional.models import Curso

from .support import converte_conceito


class ProjetosResource(resources.ModelResource):
    """Model Resource para tratar dados de Projetos."""

    class Meta:
        """Meta do Projeto."""

        model = Projeto


class OrganizacoesResource(resources.ModelResource):
    """Model Resource para tratar dados de Organizações."""

    class Meta:
        """Meta do Projeto."""

        model = Organizacao


class ConfiguracaoResource(resources.ModelResource):
    """Model Resource para tratar dados de Configurações."""

    class Meta:
        """Meta do Configuração."""

        model = Configuracao


class FeedbacksResource(resources.ModelResource):
    """Model Resource para tratar dados de Feedbacks."""

    class Meta:
        """Meta do Projeto."""

        model = Feedback


class DisciplinasResource(resources.ModelResource):
    """Model Resource para tratar dados de Disciplinas."""

    campos = [
        'FAZER',
    ]
    nome = fields.Field(attribute='nome', column_name='nome')

    def get_instance(self, instance_loader, row):
        """
        Return False.

        Prevents us from looking in the
        database for rows that already exist.
        """
        return False

    def before_import_row(self, row, **kwargs):
        """Forma que arrumei para evitar preencher com o mesmo dado."""
        nome = row.get('nome')
        if nome is None:
            pass
            # print("Erro ao recuperar o nome da disciplina")
        elif nome != "":
            (reg, _created) = Disciplina.objects.get_or_create(nome=nome)
            row['id'] = reg.id

    def skip_row(self, instance, original):
        """Sempre pula linha."""
        return True

    class Meta:
        """Meta do Projeto."""

        model = Disciplina
        fields = ('nome',)
        export_order = fields
        skip_unchanged = True


def recupera_objetivo(objetivo_str):
    """Recupera o objeto ObjetivoDeAprendizagem pelo nome."""
    objetivo = ObjetivosDeAprendizagem.objects.get(titulo=objetivo_str)
    return objetivo


def le_momento(mnt):
    """Para ler o momento das células."""
    dia = int(mnt[-11:-9])
    mes = int(mnt[-9:-7])
    ano = int("20"+mnt[-7:-5])  # bug do milênio
    hora = int(mnt[-4:-2])
    minuto = int(mnt[-2:])
    tempo = datetime.datetime(ano, mes, dia, hora, minuto)  # momento da última atualização
    return tempo


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

    def before_import_row(self, row, **kwargs):
        """Forma que arrumei para evitar preencher com o mesmo dado."""
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
                momento = le_momento(row.get('momento'))
            elif "date_modified" in row:  # caso esqueça de alterar o nome na coluna
                momento = le_momento(row.get('date_modified'))
            else:
                momento = datetime.datetime.now()

            tipo = 0  # tipo de avaliação padrão, mas que não deve acontecer

            avaliador = projeto.orientador.user  # por padrão o avaliador é o orientador

            # recupera objetivo, se houver
            if 'objetivo' in row:
                objetivo = recupera_objetivo(row.get('objetivo'))
            elif 'criterio' in row:
                objetivo = recupera_objetivo(row.get('criterio'))
            else:
                objetivo = None

            if avaliacao in ("RP",
                             "Relatório de Planejamento",
                             "Relatorio de Planejamento"):
                tipo = 10  # (10, 'Relatório de Planejamento'),
                (aval, _created) = Avaliacao2.objects.get_or_create(projeto=projeto,
                                                                    avaliador=avaliador,
                                                                    momento=momento,
                                                                    tipo_de_avaliacao=tipo)

            elif avaliacao in ("RIG",
                               "Relatório Intermediário Grupo",
                               "Relatorio Intermediario Grupo"):
                tipo = 11  # (11, 'Relatório Intermediário de Grupo'),
                (aval, _created) = Avaliacao2.objects.get_or_create(objetivo=objetivo,
                                                                    projeto=projeto,
                                                                    avaliador=avaliador,
                                                                    momento=momento,
                                                                    tipo_de_avaliacao=tipo)

            elif avaliacao in ("RFG",
                               "Relatório Final Grupo",
                               "Relatório Final de Grupo",
                               "Relatorio Final Grupo",
                               "Relatorio Final de Grupo"):
                tipo = 12  # (12, 'Relatório Final de Grupo'),
                (aval, _created) = Avaliacao2.objects.get_or_create(objetivo=objetivo,
                                                                    projeto=projeto,
                                                                    avaliador=avaliador,
                                                                    momento=momento,
                                                                    tipo_de_avaliacao=tipo)

            elif avaliacao in ("RII",
                               "Relatório Intermediário Individual",
                               "Relatorio Intermediario Individual",
                               "Relatório Parcial Individual",
                               "Relatorio Parcial Individual"):
                tipo = 21  # (21, 'Relatório Intermediário Individual'),
                (aval, _created) = Avaliacao2.objects.get_or_create(objetivo=objetivo,
                                                                    projeto=projeto,
                                                                    alocacao=alocacao,
                                                                    avaliador=avaliador,
                                                                    momento=momento,
                                                                    tipo_de_avaliacao=tipo)

            elif avaliacao in ("RFI",
                               "Relatório Final Individual",
                               "Relatorio Final Individual"):
                tipo = 22  # (22, 'Relatório Final Individual'),
                (aval, _created) = Avaliacao2.objects.get_or_create(objetivo=objetivo,
                                                                    projeto=projeto,
                                                                    alocacao=alocacao,
                                                                    avaliador=avaliador,
                                                                    momento=momento,
                                                                    tipo_de_avaliacao=tipo)

            elif avaliacao in ("BI",
                               "Banca Intermediária",
                               "Banca Intermediaria"):
                tipo = 1  # ( 1, 'Banca Intermediária'),
                # o certo seria procurar avaliador
                (aval, _created) = Avaliacao2.objects.get_or_create(objetivo=objetivo,
                                                                    projeto=projeto,
                                                                    avaliador=avaliador,
                                                                    momento=momento,
                                                                    tipo_de_avaliacao=tipo)

            elif avaliacao in ("BF",
                               "Banca Final"):
                tipo = 2  # ( 2, 'Banca Final'),
                # o certo seria procurar avaliador
                (aval, _created) = Avaliacao2.objects.get_or_create(objetivo=objetivo,
                                                                    projeto=projeto,
                                                                    avaliador=avaliador,
                                                                    momento=momento,
                                                                    tipo_de_avaliacao=tipo)

            # NÃO MAIS USADAS, FORAM USADAS QUANDO O PFE ERA AINDA EM DOIS SEMESTRES
            elif avaliacao in ("PPF",
                               "Planejamento Primeira Fase"):
                tipo = 50  # (50, 'Planejamento Primeira Fase'),
                (aval, _created) = Avaliacao2.objects.get_or_create(projeto=projeto,
                                                                    avaliador=avaliador,
                                                                    momento=momento,
                                                                    tipo_de_avaliacao=tipo)

            elif avaliacao in ("API",
                               "Avaliação Parcial Individual"):
                tipo = 51  # (51, 'Avaliação Parcial Individual'),
                (aval, _created) = Avaliacao2.objects.get_or_create(objetivo=objetivo,
                                                                    projeto=projeto,
                                                                    alocacao=alocacao,
                                                                    avaliador=avaliador,
                                                                    momento=momento,
                                                                    tipo_de_avaliacao=tipo)

            elif avaliacao in ("AFI",
                               "Avaliação Final Individual"):
                tipo = 52  # (52, 'Avaliação Final Individual'),
                (aval, _created) = Avaliacao2.objects.get_or_create(objetivo=objetivo,
                                                                    projeto=projeto,
                                                                    alocacao=alocacao,
                                                                    avaliador=avaliador,
                                                                    momento=momento,
                                                                    tipo_de_avaliacao=tipo)

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
                                                                   momento=momento,
                                                                   tipo_de_avaliacao=tipo)
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
        """Sempre pula linha."""
        return True

    class Meta:
        """Meta para Avaliações."""

        model = Avaliacao2


# MOVER PARA RESOURCES DE USERS (ACCOUNTS)

class UsuariosResource(resources.ModelResource):
    """Model Resource para tratar dados de Usuários."""

    class Meta:
        """Meta para PFEUser."""

        model = PFEUser


def atualizar_campo(registro, campo, valor):
    """Atualiza o campo."""
    if (valor is not None) and (valor != ""):
        setattr(registro, campo, valor)
    # else: # ("Não houve atualização de {0}".format(campo))


class EstudantesResource(resources.ModelResource):
    """Model Resource para tratar dados de Estudantes."""

    campos = [
        'email (e-mail institucional, com titulo da coluna sem o traço separando "e" de "mail")',
        'nome',
        'sobrenome',
        'nome_compl (somente usado se nome e sobrenome não presentes)',
        'gênero (M|F)',
        'curso [GRENGCOMP|GRENGMECAT|GRENGMECA]',
        'matrícula (número)',
        'cr (ponto como separador decimal)',
        'anoPFE',
        'semestrePFE',
        'usuário (desnecessário, pois é pego pelo e-mail)',
    ]

    def before_import_row(self, row, **kwargs):
        """Forma que arrumei para evitar preencher com o mesmo dado."""
        EMAIL_ESTUDANTE = "@al.insper.edu.br"

        email = row.get("email")
        if email is None:
            pass
            # print("Erro ao recuperar o e-mail do usuário [email]")
        elif EMAIL_ESTUDANTE in email:

            username = email.split(EMAIL_ESTUDANTE)[0].strip()

            # recupera dados do estudante se ele já estava cadastrado
            # TIPO_DE_USUARIO_CHOICES = (1, 'aluno')
            (user, _created) = PFEUser.objects.get_or_create(username=username,
                                                             email=email.strip(),
                                                             tipo_de_usuario=1)

            nome_compl = row.get('nome_compl')
            if (nome_compl is not None) and (nome_compl != ""):
                nome_compl_txt = nome_compl.split(" ",1)
                user.first_name = nome_compl_txt[0].strip()
                user.last_name = nome_compl_txt[1].strip()

            atualizar_campo(user, 'first_name', row.get('nome'))
            atualizar_campo(user, 'last_name', row.get('sobrenome'))
            
            atualizar_campo(user, 'genero', row.get('gênero'))

            user.save()

            (aluno, _created) = Aluno.objects.get_or_create(user=user)
            # Remover o curso e só usar curso2
            if row.get('curso') == "GRENGCOMP":
                aluno.curso = 'C'
                aluno.curso2 = Curso.objects.get(nome="Engenharia de Computação")
            elif row.get('curso') == "GRENGMECAT":
                aluno.curso = 'X'
                aluno.curso2 = Curso.objects.get(nome="Engenharia Mecatrônica")
            elif row.get('curso') == "GRENGMECA":
                aluno.curso = 'M'
                aluno.curso2 = Curso.objects.get(nome="Engenharia Mecânica")
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
            contad = 1
            while contad < 100:
                if str(contad) in row and row[str(contad)] != "":
                    proposta = Proposta.objects.get(id=contad)

                    (opt, _created) = Opcao.objects.get_or_create(aluno=aluno,
                                                                  proposta=proposta,
                                                                  prioridade=int(row[str(contad)]))

                    opt.save()
                contad += 1

            if "areas" in row:
                if "Programação" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Sistemas de Informação")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area,
                                                                                 usuario=user)
                    area_int.save()

                if "Gestão de Projetos" in row["areas"] or "finanças" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Administração, Economia e Finanças")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area,
                                                                                 usuario=user)
                    area_int.save()

                if "Manufatura" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Manufatura Avançada")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area,
                                                                                 usuario=user)
                    area_int.save()

                if "Dados" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Ciência dos Dados")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area,
                                                                                 usuario=user)
                    area_int.save()

                if "Controle" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Controle de Sistemas Dinâmicos")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area,
                                                                                 usuario=user)
                    area_int.save()

                if "Social" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Inovação Social")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area,
                                                                                 usuario=user)
                    area_int.save()

                if "Eletrônica" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Sistemas Embarcados")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area,
                                                                                 usuario=user)
                    area_int.save()

                if "3D" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Sistemas Interativos")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area,
                                                                                 usuario=user)
                    area_int.save()

                if "Robótica" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Robótica")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area,
                                                                                 usuario=user)
                    area_int.save()

                if "Automação" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Automação Industrial")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area,
                                                                                 usuario=user)
                    area_int.save()

                if "Machine" in row["areas"] or "AI" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Inteligência Artificial")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area,
                                                                                 usuario=user)
                    area_int.save()

                if "Machine" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Inteligência Artificial")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area,
                                                                                 usuario=user)
                    area_int.save()

            row['id'] = aluno.id

    def skip_row(self, instance, original):
        """Sempre pula linha."""
        return True

    class Meta:
        """Meta de Estudantes."""

        model = Aluno


class ProfessoresResource(resources.ModelResource):
    """Model Resource para tratar dados de Professores."""

    class Meta:
        """Meta do Professores."""

        model = Professor


class ParceirosResource(resources.ModelResource):
    """Model Resource para tratar dados de Parceiros."""

    class Meta:
        """Meta do Parceiros."""

        model = Parceiro


class OpcoesResource(resources.ModelResource):
    """Model Resource para tratar dados de Opções."""

    class Meta:
        """Meta do Opções."""

        model = Opcao
