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

from users.models import PFEUser, Aluno, Opcao, Alocacao

from .models import Projeto, Proposta, Disciplina
from .models import Avaliacao2, ObjetivosDeAprendizagem, Observacao
from .models import Area, AreaDeInteresse

from operacional.models import Curso

from academica.support_notas import converte_conceito

from academica.models import Exame



# class ProjetosResource(resources.ModelResource):
#     """Model Resource para tratar dados de Projetos."""
#     titulo_org_periodo_seguro = fields.Field()  # Campo com a pasta que serão salvo os documentos
#     class Meta:
#         model = Projeto       
#     def dehydrate_titulo_org_periodo_seguro(self, obj):
#         return obj.get_titulo_org_periodo_seguro()


def get_ProjetosResource(field_names=None):
    """Retorna o Model Resource para Projetos."""

    class ProjetosResource(resources.ModelResource):
        """Model Resource para tratar dados de Projetos."""
        titulo_org_periodo_seguro = fields.Field()  # Campo com a pasta que serão salvo os documentos
        class Meta:
            model = Projeto
            if field_names:
                fields = tuple(field_names)   
        def dehydrate_titulo_org_periodo_seguro(self, obj):
            return obj.get_titulo_org_periodo_seguro()
    
    return ProjetosResource()




# class DisciplinasResource(resources.ModelResource):
#     """Model Resource para tratar dados de Disciplinas."""

#     campos = ["nome"]
#     nome = fields.Field(attribute='nome', column_name='nome')

#     def get_instance(self, instance_loader, row):
#         return False

#     def before_import_row(self, row, **kwargs):
#         """Forma que arrumei para evitar preencher com o mesmo dado."""
#         nome = row.get('nome')
#         if nome is None:
#             pass  # "Erro ao recuperar o nome da disciplina"
#         elif nome != "":
#             reg, _ = Disciplina.objects.get_or_create(nome=nome)
#             row["id"] = reg.id

#     def skip_row(self, instance, original):
#         """Sempre pula linha."""
#         return True

#     class Meta:
#         """Meta do Projeto."""
#         model = Disciplina
#         fields = ('nome',)
#         export_order = fields
#         skip_unchanged = True


def get_DisciplinasResource(field_names=None):

    class DisciplinasResource(resources.ModelResource):
        """Model Resource para tratar dados de Disciplinas."""

        campos = ["nome"]
        nome = fields.Field(attribute='nome', column_name='nome')

        def get_instance(self, instance_loader, row):
            return False

        def before_import_row(self, row, **kwargs):
            """Forma que arrumei para evitar preencher com o mesmo dado."""
            nome = row.get('nome')
            if nome is None:
                pass  # "Erro ao recuperar o nome da disciplina"
            elif nome != "":
                reg, _ = Disciplina.objects.get_or_create(nome=nome)
                row["id"] = reg.id

        def skip_row(self, instance, original):
            """Sempre pula linha."""
            return True

        class Meta:
            """Meta do Projeto."""
            model = Disciplina
            # fields = ('nome',)
            if field_names:
                fields = tuple(field_names)   
            export_order = fields
            skip_unchanged = True

    return DisciplinasResource()


def le_momento(mnt):
    """Para ler o momento das células."""
    dia = int(mnt[-11:-9])
    mes = int(mnt[-9:-7])
    ano = int("20"+mnt[-7:-5])  # bug do milênio
    hora = int(mnt[-4:-2])
    minuto = int(mnt[-2:])
    tempo = datetime.datetime(ano, mes, dia, hora, minuto)  # momento da última atualização
    return tempo


def get_Avaliacoes2Resource(field_names=None):

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
            if "estudante" in row:
                estudante_str = row.get("estudante")
            elif "user_id" in row:
                estudante_str = row.get("user_id")
            else:
                pass  # "Erro ao recuperar coluna estudante ou user_id"

            if estudante_str is None:
                pass  # "Erro ao recuperar o estudante [estudante_str]"
            elif estudante_str != "":

                aluno = Aluno.objects.get(user__username=estudante_str)

                ano = int(row.get("ano"))
                semestre = int(row.get("semestre"))

                alocacao = Alocacao.objects.get(aluno=aluno, projeto__ano=ano, projeto__semestre=semestre)

                projeto = alocacao.projeto

                avaliador = projeto.orientador.user

                if "avaliação" in row:
                    avaliacao = row.get("avaliação")
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
                    objetivo = ObjetivosDeAprendizagem.objects.get(titulo=row.get("objetivo"))
                elif "criterio" in row:
                    objetivo = ObjetivosDeAprendizagem.objects.get(titulo=row.get("criterio"))
                else:
                    objetivo = None

                avaliacao_map = {
                    "RP":   {"avaliador": avaliador},
                    "RIG":  {"objetivo": objetivo, "avaliador": avaliador},
                    "RFG":  {"objetivo": objetivo, "avaliador": avaliador},
                    "RII":  {"objetivo": objetivo, "alocacao": alocacao, "avaliador": avaliador},
                    "RFI":  {"objetivo": objetivo, "alocacao": alocacao, "avaliador": avaliador},
                    "BI":   {"objetivo": objetivo},
                    "BF":   {"objetivo": objetivo},
                    "PPF":  {"avaliador": avaliador},
                    "API":  {"objetivo": objetivo, "alocacao": alocacao, "avaliador": avaliador},
                    "AFI":  {"objetivo": objetivo, "alocacao": alocacao, "avaliador": avaliador},
                }

                entry = avaliacao_map.get(avaliacao)
                if entry:  # AVALIAÇÃO RECONHECIDA
                    kwargs = entry.copy()
                    exame = Exame.objects.get(sigla=avaliacao)
                    kwargs.update({"projeto": projeto, "momento": momento, "exame": exame})
                    aval, _ = Avaliacao2.objects.get_or_create(**kwargs)
                
                # recuper nota, se houver
                if "nota" in row:
                    aval.nota = float(row.get("nota"))
                elif "desempenho" in row:
                    aval.nota = converte_conceito(row.get("desempenho"))  # CALCULAR NOTA
                
                if "peso" in row:  # Todas as avaliações tem de ter peso e Pesos são convertidos para porcentagens
                    peso = float(row.get("peso"))*100
                    aval.peso = peso
                
                aval.save()
                row["id"] = aval.id

                # CASO A LEITURA TENHA ALGUM FEEDBACK/OBSERVAÇÃO
                obs_str = row.get("observação", "")
                if obs_str:
                    obs, _ = Observacao.objects.get_or_create(
                        objetivo=objetivo,
                        projeto=projeto,
                        avaliador=avaliador,
                        alocacao=alocacao,
                        momento=momento,
                        exame=exame
                    )
                    obs.observacoes_orientador = obs_str
                    obs.save()

        def skip_row(self, instance, original):
            """Sempre pula linha."""
            return True

        class Meta:
            """Meta para Avaliações."""
            model = Avaliacao2
            if field_names:
                fields = tuple(field_names) 

    return Avaliacoes2Resource()



def atualizar_campo(registro, campo, valor):
    """Atualiza o campo."""
    if (valor is not None) and (valor != ""):
        max_length = registro.__class__._meta.get_field(campo).max_length
        if max_length is not None:
            if len(valor) > max_length:
                raise SuspiciousOperation(f"Tamanho do campo '{campo}', maior que o permitido pelo registro ({max_length}).")
        setattr(registro, campo, valor)


def get_EstudantesResource(field_names=None):

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
            "ano (ano em que o estudante cursará no Capstone)",
            "semestre (semestre em que o estudante cursará no Capstone)",
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
                user, _created = PFEUser.objects.get_or_create(username=username,
                                                                email=email.strip(),
                                                                tipo_de_usuario=1)

                nome_compl = row.get("nome_compl")
                if (nome_compl is not None) and (nome_compl != ""):
                    nome_compl_txt = nome_compl.split(" ",1)
                    user.first_name = nome_compl_txt[0].strip()
                    user.last_name = nome_compl_txt[1].strip()

                atualizar_campo(user, "first_name", row.get("nome"))
                atualizar_campo(user, "last_name", row.get("sobrenome"))
                
                genero = row.get("gênero").upper().strip()
                if genero not in ("M", "F", ""):
                    raise ValueError(f"Gênero informado inválido: {genero}. Só pode ser M, F ou vazio.")
                atualizar_campo(user, "genero", genero)

                atualizar_campo(user, "nome_social", row.get("nome_social"))
                atualizar_campo(user, "pronome_tratamento", row.get("pronome_tratamento"))

                user.save()
                if not dry_run:
                    if _created:
                        self.registros["novos"].append(user)
                    else:
                        self.registros["atualizados"].append(user)

                user.groups.add(Group.objects.get(name="Estudante"))  # Grupo de permissões

                aluno, _created = Aluno.objects.get_or_create(user=user)

                try:
                    aluno.curso2 = Curso.objects.get(sigla=row.get("curso").upper().strip())
                except Curso.DoesNotExist: # Não encontrou o curso, deixa vazio
                    aluno.curso2 = None

                atualizar_campo(aluno, "matricula", row.get("matrícula"))
                atualizar_campo(aluno, "cr", row.get("cr"))

                ano = row.get("ano")[:4]  # só os 4 primeiros dígitos
                if not ano.isdigit() or len(ano) != 4:
                    raise ValueError(f"Ano informado inválido: {ano}. Deve ser um ano com 4 dígitos.")
                atualizar_campo(aluno, "ano", ano)

                semestre = row.get("semestre")[:1]  # só o primeiro dígito
                if semestre not in ('1', '2'):
                    raise ValueError(f"Semestre informado inválido: {semestre}. Só pode ser 1 ou 2.")
                atualizar_campo(aluno, "semestre", semestre)

                if "familia" in row:
                    aluno.familia = row["familia"]

                aluno.save()

                # Isso caça propostas, não deverá ser novamente usado no futuro
                # Esta criando Opções sem ver se já existiam
                contad = 1
                while contad < 100:
                    if str(contad) in row and row[str(contad)] != "":
                        proposta = Proposta.objects.get(id=contad)

                        opt, _ = Opcao.objects.get_or_create(aluno=aluno,
                                                                    proposta=proposta,
                                                                    prioridade=int(row[str(contad)]))

                        opt.save()
                    contad += 1

                if "areas" in row:
                    area_keywords = {
                        "Programação": "Sistemas de Informação",
                        "Gestão de Projetos": "Administração, Economia e Finanças",
                        "finanças": "Administração, Economia e Finanças",
                        "Manufatura": "Manufatura Avançada",
                        "Dados": "Ciência dos Dados",
                        "Controle": "Controle de Sistemas Dinâmicos",
                        "Social": "Inovação Social",
                        "Eletrônica": "Sistemas Embarcados",
                        "3D": "Sistemas Interativos",
                        "Robótica": "Robótica",
                        "Automação": "Automação Industrial",
                        "AI": "Inteligência Artificial",
                        "Machine": "Inteligência Artificial",
                    }
                    for keyword, titulo in area_keywords.items():
                        if keyword in row["areas"]:
                            area = Area.objects.get(ativa=True, titulo=titulo)
                            area_int, _ = AreaDeInteresse.objects.get_or_create(area=area, usuario=user)
                            area_int.save()

                row["id"] = aluno.id

        def skip_row(self, instance, original):
            """Sempre pula linha."""
            return True

        class Meta:
            """Meta de Estudantes."""

            model = Aluno
            if field_names:
                fields = tuple(field_names) 

    return EstudantesResource()
