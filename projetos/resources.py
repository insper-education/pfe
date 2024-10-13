#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

import datetime
from import_export import resources, fields
from django.core.exceptions import SuspiciousOperation  # Para erro 400
from django.contrib.auth.models import Group

from users.models import PFEUser, Aluno, Professor, Parceiro, Opcao, Alocacao
from estudantes.models import Pares
from .models import Projeto, Proposta, Organizacao, Configuracao, Disciplina
from .models import Feedback, Avaliacao2, ObjetivosDeAprendizagem, Observacao
from .models import Area, AreaDeInteresse

from operacional.models import Curso

from .support import converte_conceito

from academica.models import Exame

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
            pass  # "Erro ao recuperar o nome da disciplina"
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
        "estudante ou user_id (primeira parte do e-mail, obrigatório)",
        "ano",
        "semestre",
        "avaliação",
        "objetivo ou criterio",
        "peso",
        "nota ou score (se não houver procura por desempenho)",
        "desempenho (opcional primeiro procura a nota)",
        "momento ou date_modified (dd/mm/aa hh:mm)",
        "observação ou feedback",
    ]

    def before_import_row(self, row, **kwargs):
        """Forma que arrumei para evitar preencher com o mesmo dado."""
        if 'estudante' in row:
            estudante_str = row.get('estudante')
        elif 'user_id' in row:
            estudante_str = row.get('user_id')
        else:
            pass  # "Erro ao recuperar coluna estudante ou user_id"

        if estudante_str is None:
            pass  # "Erro ao recuperar o estudante [estudante_str]"
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
                pass  # "Erro ao recuperar coluna avaliação"

            if "momento" in row:
                momento = le_momento(row.get('momento'))
            elif "date_modified" in row:  # caso esqueça de alterar o nome na coluna
                momento = le_momento(row.get('date_modified'))
            else:
                momento = datetime.datetime.now()

            exame = None  # tipo de avaliação padrão, mas que não deve acontecer

            avaliador = projeto.orientador.user  # por padrão o avaliador é o orientador

            # recupera objetivo, se houver
            if "objetivo" in row:
                objetivo = recupera_objetivo(row.get('objetivo'))
            elif "criterio" in row:
                objetivo = recupera_objetivo(row.get('criterio'))
            else:
                objetivo = None

            if avaliacao in ("RP",
                             "Relatório Preliminar",
                             "Relatório de Planejamento",
                             "Relatorio de Planejamento"):
                exame = Exame.objects.get(sigla="RP")
                (aval, _created) = Avaliacao2.objects.get_or_create(projeto=projeto,
                                                                    avaliador=avaliador,
                                                                    momento=momento,
                                                                    exame=exame)

            elif avaliacao in ("RIG",
                               "Relatório Intermediário Grupo",
                               "Relatorio Intermediario Grupo"):
                exame = Exame.objects.get(sigla="RIG")
                (aval, _created) = Avaliacao2.objects.get_or_create(objetivo=objetivo,
                                                                    projeto=projeto,
                                                                    avaliador=avaliador,
                                                                    momento=momento,
                                                                    exame=exame)

            elif avaliacao in ("RFG",
                               "Relatório Final Grupo",
                               "Relatório Final de Grupo",
                               "Relatorio Final Grupo",
                               "Relatorio Final de Grupo"):
                exame = Exame.objects.get(titulo="Relatório Final de Grupo")
                (aval, _created) = Avaliacao2.objects.get_or_create(objetivo=objetivo,
                                                                    projeto=projeto,
                                                                    avaliador=avaliador,
                                                                    momento=momento,
                                                                    exame=exame)

            elif avaliacao in ("RII",
                               "Relatório Intermediário Individual",
                               "Relatorio Intermediario Individual",
                               "Relatório Parcial Individual",
                               "Relatorio Parcial Individual"):
                exame = Exame.objects.get(titulo="Relatório Intermediário Individual")
                (aval, _created) = Avaliacao2.objects.get_or_create(objetivo=objetivo,
                                                                    projeto=projeto,
                                                                    alocacao=alocacao,
                                                                    avaliador=avaliador,
                                                                    momento=momento,
                                                                    exame=exame)

            elif avaliacao in ("RFI",
                               "Relatório Final Individual",
                               "Relatorio Final Individual"):
                exame = Exame.objects.get(titulo="Relatório Final Individual")
                (aval, _created) = Avaliacao2.objects.get_or_create(objetivo=objetivo,
                                                                    projeto=projeto,
                                                                    alocacao=alocacao,
                                                                    avaliador=avaliador,
                                                                    momento=momento,
                                                                    exame=exame)

            elif avaliacao in ("BI",
                               "Banca Intermediária",
                               "Banca Intermediaria"):
                exame = Exame.objects.get(titulo="Banca Intermediária")
                # o certo seria procurar avaliador
                (aval, _created) = Avaliacao2.objects.get_or_create(objetivo=objetivo,
                                                                    projeto=projeto,
                                                                    avaliador=avaliador,
                                                                    momento=momento,
                                                                    exame=exame)

            elif avaliacao in ("BF",
                               "Banca Final"):
                exame = Exame.objects.get(titulo="Banca Final")
                # o certo seria procurar avaliador
                (aval, _created) = Avaliacao2.objects.get_or_create(objetivo=objetivo,
                                                                    projeto=projeto,
                                                                    avaliador=avaliador,
                                                                    momento=momento,
                                                                    exame=exame)

            # NÃO MAIS USADAS, FORAM USADAS QUANDO A DISCIPLINA AINDA ERA EM DOIS SEMESTRES
            elif avaliacao in ("PPF",
                               "Planejamento Primeira Fase"):
                exame = Exame.objects.get(titulo="Planejamento Primeira Fase")
                (aval, _created) = Avaliacao2.objects.get_or_create(projeto=projeto,
                                                                    avaliador=avaliador,
                                                                    momento=momento,
                                                                    exame=exame)

            elif avaliacao in ("API",
                               "Avaliação Parcial Individual"):
                exame = Exame.objects.get(titulo="Avaliação Parcial Individual")
                (aval, _created) = Avaliacao2.objects.get_or_create(objetivo=objetivo,
                                                                    projeto=projeto,
                                                                    alocacao=alocacao,
                                                                    avaliador=avaliador,
                                                                    momento=momento,
                                                                    exame=exame)

            elif avaliacao in ("AFI",
                               "Avaliação Final Individual"):
                exame = Exame.objects.get(titulo="Avaliação Final Individual")
                (aval, _created) = Avaliacao2.objects.get_or_create(objetivo=objetivo,
                                                                    projeto=projeto,
                                                                    alocacao=alocacao,
                                                                    avaliador=avaliador,
                                                                    momento=momento,
                                                                    exame=exame)

            else:
                pass  # "ERRO, AVALIAÇÃO NÃO RECONHECIDA !!!!"

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
                                                                   exame=exame)
                obs.observacoes_orientador = obs_str
                obs.save()

            # recuper nota, se houver
            if "nota" in row:
                aval.nota = float(row.get("nota"))
            elif "score" in row:
                aval.nota = float(row.get("score"))
            elif "desempenho" in row:
                desempenho = row.get("desempenho")
                aval.nota = converte_conceito(desempenho)  # CALCULAR NOTA
            else:
                pass  # "Erro ao recuperar a nota"

            # Todas as avaliações tem de ter peso
            # Pesos são convertidos para porcentagens
            if "peso" in row:
                peso = float(row.get("peso"))*100
                aval.peso = peso
            else:
                pass  # "Erro ao recuperar o peso da avaliação"

            aval.save()
            row["id"] = aval.id

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
        max_length = registro.__class__._meta.get_field(campo).max_length
        if max_length is not None:
            if len(valor) > max_length:
                raise SuspiciousOperation(f"Tamanho do campo '{campo}', maior que o permitido pelo registro ({max_length}).")
        setattr(registro, campo, valor)
    # else: # ("Não houve atualização de {0}".format(campo))


class EstudantesResource(resources.ModelResource):
    """Model Resource para tratar dados de Estudantes."""

    campos = [
        'email [obrigatório] (e-mail institucional, com titulo da coluna sem o traço separando "e" de "mail")',
        "nome",
        "sobrenome",
        "nome_compl (somente usado se nome e sobrenome não presentes)",
        "gênero (M|F)",
        "curso [GRENGCOMP|GRENGMECAT|GRENGMECA|GRCIECOMP]",
        "matrícula (número)",
        "cr (ponto como separador decimal)",
        "anoPFE (ano em que o estudante cursará no Capstone)",
        "semestrePFE (semestre em que o estudante cursará no Capstone)",
        "usuário (desnecessário, pois é pego pelo e-mail)",
        "nome_social (opcional, mas quando usado será usado sempre que se referir ao estudante)",
        "pronome_tratamento (opcional, por exemplo Dr. ou Dra.)",
    ]

    def __init__(self):
        super().__init__()  # Call the constructor of the parent class
        self.registros = {}
        self.registros["novos"] = []
        self.registros["atualizados"] = []

    def before_import_row(self, row, **kwargs):
        """Forma que arrumei para evitar preencher com o mesmo dado."""
        EMAIL_ESTUDANTE = "@al.insper.edu.br"

        before_import_kwargs = kwargs.get("before_import_kwargs", None)
        if before_import_kwargs is not None:
            dry_run = before_import_kwargs.get("dry_run", True)
        else:
            dry_run = True
        
        email = row.get("email")
        if email is None:
            pass  # "Erro ao recuperar o e-mail do usuário [email]"
        elif EMAIL_ESTUDANTE in email:

            username = email.split(EMAIL_ESTUDANTE)[0].strip()

            # recupera dados do estudante se ele já estava cadastrado
            # TIPO_DE_USUARIO_CHOICES = (1, "estudante")
            (user, _created) = PFEUser.objects.get_or_create(username=username,
                                                             email=email.strip(),
                                                             tipo_de_usuario=1)

            nome_compl = row.get("nome_compl")
            if (nome_compl is not None) and (nome_compl != ""):
                nome_compl_txt = nome_compl.split(" ",1)
                user.first_name = nome_compl_txt[0].strip()
                user.last_name = nome_compl_txt[1].strip()

            atualizar_campo(user, "first_name", row.get("nome"))
            atualizar_campo(user, "last_name", row.get("sobrenome"))
            
            atualizar_campo(user, "genero", row.get("gênero"))

            atualizar_campo(user, "nome_social", row.get("nome_social"))
            atualizar_campo(user, "pronome_tratamento", row.get("pronome_tratamento"))

            user.save()
            if not dry_run:
                if _created:
                    self.registros["novos"].append(user)
                else:
                    self.registros["atualizados"].append(user)

            user.groups.add(Group.objects.get(name="Estudante"))  # Grupo de permissões

            (aluno, _created) = Aluno.objects.get_or_create(user=user)

            try:
                aluno.curso2 = Curso.objects.get(sigla=row.get("curso"))
            except Curso.DoesNotExist: # Não encontrou o curso, deixa vazio
                aluno.curso2 = None

            atualizar_campo(aluno, "matricula", row.get("matrícula"))
            atualizar_campo(aluno, "cr", row.get("cr"))
            atualizar_campo(aluno, "anoPFE", row.get("anoPFE"))
            atualizar_campo(aluno, "semestrePFE", row.get("semestrePFE"))

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

                if "AI" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Inteligência Artificial")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area,
                                                                                 usuario=user)
                    area_int.save()

                if "Machine" in row["areas"]:
                    area = Area.objects.get(ativa=True, titulo="Inteligência Artificial")
                    (area_int, _created) = AreaDeInteresse.objects.get_or_create(area=area,
                                                                                 usuario=user)
                    area_int.save()

            row["id"] = aluno.id

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

class ParesResource(resources.ModelResource):
    """Model Resource para tratar dados de Opções."""

    class Meta:
        """Meta do Opções."""

        model = Pares
