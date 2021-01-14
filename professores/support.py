#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Dezembro de 2020
"""

import dateutil.parser


from django.db.models.functions import Lower

from users.models import PFEUser, Professor, Aluno
from users.support import adianta_semestre

from projetos.models import Organizacao, Projeto, Banca


def editar_banca(banca, request):
    """Edita os valores de uma banca por um request Http."""
    if 'inicio' in request.POST:
        try:
            banca.startDate = dateutil.parser.parse(request.POST['inicio'])
        except (ValueError, OverflowError):
            banca.startDate = None
    if 'fim' in request.POST:
        try:
            banca.endDate = dateutil.parser.parse(request.POST['fim'])
        except (ValueError, OverflowError):
            banca.endDate = None
    if 'tipo' in request.POST and request.POST['tipo'] != "":
        banca.tipo_de_banca = int(request.POST['tipo'])
    if 'local' in request.POST:
        banca.location = request.POST['local']
    if 'link' in request.POST:
        banca.link = request.POST['link']

    try:
        if 'membro1' in request.POST:
            banca.membro1 = PFEUser.objects.get(id=int(request.POST['membro1']))
        else:
            banca.membro1 = None
        if 'membro2' in request.POST:
            banca.membro2 = PFEUser.objects.get(id=int(request.POST['membro2']))
        else:
            banca.membro2 = None
        if 'membro3' in request.POST:
            banca.membro3 = PFEUser.objects.get(id=int(request.POST['membro3']))
        else:
            banca.membro3 = None
    except PFEUser.DoesNotExist:
        return None

    banca.save()


def professores_membros_bancas():
    """Retorna potenciais usuários que podem ser membros de uma banca do PFE."""
    professores = PFEUser.objects.filter(tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[1][0])

    administradores = PFEUser.objects.filter(tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[3][0])

    pessoas = (professores | administradores).order_by(Lower("first_name"), Lower("last_name"))

    return pessoas


def falconi_membros_banca():
    """Coleta registros de possiveis membros de banca para Falconi."""

    try:
        organizacao = Organizacao.objects.get(sigla="Falconi")
    except Organizacao.DoesNotExist:
        return None

    falconis = PFEUser.objects.filter(parceiro__organizacao=organizacao)
    return falconis


def recupera_orientadores_por_semestre(configuracao):
    """ Recupera listas de orientadores de projetos ordenadas por semestre. """

    professores_pfe = []
    periodo = []

    ano = 2018    # Ano de início do PFE
    semestre = 2  # Semestre de início do PFE
    while True:
        professores = []
        grupos = []
        for professor in Professor.objects.all().order_by(Lower("user__first_name"),
                                                          Lower("user__last_name")):
            count_grupos = []
            grupos_pfe = Projeto.objects.filter(orientador=professor).\
                                        filter(ano=ano).\
                                        filter(semestre=semestre)
            if grupos_pfe:
                for grupo in grupos_pfe: # garante que tem alunos no projeto
                    alunos_pfe = Aluno.objects.filter(alocacao__projeto=grupo)
                    if alunos_pfe:
                        count_grupos.append(grupo)
                if count_grupos:
                    professores.append(professor)
                    grupos.append(count_grupos)

        if professores: # Se não houver nenhum orientador não cria entrada na lista
            professores_pfe.append(zip(professores, grupos))
            periodo.append(str(ano)+"."+str(semestre))

        # Para de buscar depois do semestre atual
        if ((semestre == configuracao.semestre + 1) and (ano == configuracao.ano)) or \
           (ano > configuracao.ano):
            break

        # Avança um semestre
        ano, semestre = adianta_semestre(ano, semestre)

    return zip(professores_pfe[::-1], periodo[::-1]) #inverti lista deixando os mais novos primeiro


def recupera_coorientadores_por_semestre(configuracao):
    """ Recupera listas de coorientadores de projetos ordenadas por semestre. """

    professores_pfe = []
    periodo = []

    ano = 2018    # Ano de início do PFE
    semestre = 2  # Semestre de início do PFE

    while True:
        professores = []
        grupos = []
        for professor in Professor.objects.all().order_by(Lower("user__first_name"),
                                                          Lower("user__last_name")):
            count_grupos = []
            grupos_pfe = Projeto.objects.filter(coorientador__usuario__professor=professor).\
                                        filter(ano=ano).\
                                        filter(semestre=semestre)
            if grupos_pfe:
                for grupo in grupos_pfe: # garante que tem alunos no projeto
                    alunos_pfe = Aluno.objects.filter(alocacao__projeto=grupo)
                    if alunos_pfe:
                        count_grupos.append(grupo)
                if count_grupos:
                    professores.append(professor)
                    grupos.append(count_grupos)
        if professores: # Se não houver nenhum co-orientador não cria entrada na lista
            professores_pfe.append(zip(professores, grupos))
            periodo.append(str(ano)+"."+str(semestre))

        # Para de buscar depois do semestre atual
        if ((semestre == configuracao.semestre + 1) and (ano == configuracao.ano)) or \
           (ano > configuracao.ano):
            break

        # Avança um semestre
        ano, semestre = adianta_semestre(ano, semestre)

    return zip(professores_pfe[::-1], periodo[::-1]) #inverti lista deixando os mais novos primeiro



def recupera_orientadores(ano, semestre):
    """ Recupera listas de todos os orientadores de projetos. """

    professores = []
    grupos = []

    for professor in Professor.objects.all().order_by(Lower("user__first_name"),
                                                      Lower("user__last_name")):

        count_grupos = []
        grupos_pfe = Projeto.objects.filter(orientador=professor)

        if semestre == 2:
            grupos_pfe = grupos_pfe.filter(ano__lte=ano)
        else:
            grupos_pfe = grupos_pfe.filter(ano__lte=ano).exclude(ano=ano, semestre=2)

        if grupos_pfe:
            for grupo in grupos_pfe: # garante que tem alunos no projeto
                alunos_pfe = Aluno.objects.filter(alocacao__projeto=grupo)
                if alunos_pfe:
                    count_grupos.append(grupo)
            if count_grupos:
                professores.append(professor)
                grupos.append(count_grupos)

    return zip(professores, grupos)


def recupera_coorientadores(ano, semestre):
    """ Recupera listas de todos os orientadores de projetos. """

    professores = []
    grupos = []

    for professor in Professor.objects.all().order_by(Lower("user__first_name"),
                                                      Lower("user__last_name")):

        count_grupos = []
        grupos_pfe = Projeto.objects.filter(coorientador__usuario__professor=professor)

        if semestre == 2:
            grupos_pfe = grupos_pfe.filter(ano__lte=ano)
        else:
            grupos_pfe = grupos_pfe.filter(ano__lte=ano).exclude(ano=ano, semestre=2)

        if grupos_pfe:
            for grupo in grupos_pfe: # garante que tem alunos no projeto
                alunos_pfe = Aluno.objects.filter(alocacao__projeto=grupo)
                if alunos_pfe:
                    count_grupos.append(grupo)
            if count_grupos:
                professores.append(professor)
                grupos.append(count_grupos)

    return zip(professores, grupos)


def recupera_bancas_intermediarias(ano, semestre):
    """ Recupera listas de todos os membros de bancas intermediárias. """

    professores = []
    grupos = []

    for professor in Professor.objects.all().order_by(Lower("user__first_name"),
                                                      Lower("user__last_name")):

        count_bancas = []

        bancas = Banca.objects.filter(tipo_de_banca=1) # (1, 'Intermediária'),

        bancas = bancas.filter(membro1=professor.user)|\
                 bancas.filter(membro2=professor.user)|\
                 bancas.filter(membro3=professor.user)

        if semestre == 2:
            bancas = bancas.filter(projeto__ano__lte=ano)
        else:
            bancas = bancas.filter(projeto__ano__lte=ano).exclude(projeto__ano=ano, projeto__semestre=2)

        if bancas:
            for banca in bancas:
                count_bancas.append(banca)
            if count_bancas:
                professores.append(professor)
                grupos.append(count_bancas)

    return zip(professores, grupos)


def recupera_bancas_finais(ano, semestre):
    """ Recupera listas de todos os membros de bancas intermediárias. """

    professores = []
    grupos = []

    for professor in Professor.objects.all().order_by(Lower("user__first_name"),
                                                      Lower("user__last_name")):

        count_bancas = []

        bancas = Banca.objects.filter(tipo_de_banca=0) # (0, 'Final')

        bancas = bancas.filter(membro1=professor.user)|\
                 bancas.filter(membro2=professor.user)|\
                 bancas.filter(membro3=professor.user)

        if semestre == 2:
            bancas = bancas.filter(projeto__ano__lte=ano)
        else:
            bancas = bancas.filter(projeto__ano__lte=ano).exclude(projeto__ano=ano, projeto__semestre=2)

        if bancas:
            for banca in bancas:
                count_bancas.append(banca)
            if count_bancas:
                professores.append(professor)
                grupos.append(count_bancas)

    return zip(professores, grupos)