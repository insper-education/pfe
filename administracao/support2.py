#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 23 de Janeiro de 2025
"""

import tablib

from projetos.resources import DisciplinasResource
from projetos.resources import Avaliacoes2Resource
from projetos.resources import ProjetosResource
from projetos.resources import OrganizacoesResource
from projetos.resources import OpcoesResource
from projetos.resources import ProfessoresResource
from projetos.resources import EstudantesResource
from projetos.resources import ParceirosResource
from projetos.resources import ConfiguracaoResource
from projetos.resources import FeedbacksResource
from projetos.resources import UsuariosResource
from projetos.resources import ParesResource
from projetos.resources import AlocacoesResource


def create_backup():
    """Rotina para criar um backup."""
    databook = tablib.Databook()

    data_projetos = ProjetosResource().export()
    data_projetos.title = "Projetos"
    databook.add_sheet(data_projetos)

    data_organizacoes = OrganizacoesResource().export()
    data_organizacoes.title = "Organizacoes"
    databook.add_sheet(data_organizacoes)

    data_opcoes = OpcoesResource().export()
    data_opcoes.title = "Opcoes"
    databook.add_sheet(data_opcoes)

    data_avaliacoes = Avaliacoes2Resource().export()
    data_avaliacoes.title = "Avaliações"
    databook.add_sheet(data_avaliacoes)

    data_usuarios = UsuariosResource().export()
    data_usuarios.title = "Usuarios"
    databook.add_sheet(data_usuarios)

    data_alunos = EstudantesResource().export()
    data_alunos.title = "Alunos"
    databook.add_sheet(data_alunos)

    data_professores = ProfessoresResource().export()
    data_professores.title = "Professores"
    databook.add_sheet(data_professores)

    data_configuracao = ConfiguracaoResource().export()
    data_configuracao.title = "Configuracao"
    databook.add_sheet(data_configuracao)

    return databook


def get_resource(dado):
    if dado == "disciplinas":
        resource = DisciplinasResource()
    elif dado == "estudantes":
        resource = EstudantesResource()
    elif dado == "avaliacoes":
        resource = Avaliacoes2Resource()
    elif dado == "projetos":
        resource = ProjetosResource()
    elif dado == "organizacoes":
        resource = OrganizacoesResource()
    elif dado == "opcoes":
        resource = OpcoesResource()
    elif dado == "usuarios":
        resource = UsuariosResource()
    elif dado == "professores":
        resource = ProfessoresResource()
    elif dado == "parceiros":
        resource = ParceirosResource()
    elif dado == "configuracao":
        resource = ConfiguracaoResource()
    elif dado == "feedbacks":
        resource = FeedbacksResource()
    elif dado == "alocacoes":
        resource = AlocacoesResource()
    elif dado == "pares":
        resource = ParesResource()
    else:
        resource = None
    return resource


def get_queryset(resource, dado, ano, semestre):

    queryset = None
    if dado == "projetos":
        queryset = resource._meta.model.objects.filter(ano=ano, semestre=semestre)
    elif dado == "estudantes":
        queryset = resource._meta.model.objects.filter(anoPFE=ano, semestrePFE=semestre)
    elif dado == "alocacoes":
        queryset = resource._meta.model.objects.filter(projeto__ano=ano, projeto__semestre=semestre)
    elif dado == "pares":
        queryset = resource._meta.model.objects.filter(alocacao_de__projeto__ano=ano, alocacao_de__projeto__semestre=semestre)

    if queryset is None:
        queryset = resource._meta.model.objects.all()
    
    return queryset
