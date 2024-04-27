#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Dezembro de 2020
"""

import dateutil.parser


from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404

from users.models import PFEUser, Professor, Aluno, Parceiro
from users.support import adianta_semestre

from projetos.models import Organizacao, Projeto, Banca, Encontro, Conexao
from projetos.models import Avaliacao_Velha, Observacao_Velha

def editar_banca(banca, request):
    """Edita os valores de uma banca por um request Http."""

    if "projeto" in request.POST:
        try:
            banca.projeto = Projeto.objects.get(id=int(request.POST['projeto']))
        except Projeto.DoesNotExist:
            return False
    else:
        return False

    if "inicio" in request.POST:
        try:
            banca.startDate = dateutil.parser.parse(request.POST['inicio'])
        except (ValueError, OverflowError):
            banca.startDate = None
    if "fim" in request.POST:
        try:
            banca.endDate = dateutil.parser.parse(request.POST['fim'])
        except (ValueError, OverflowError):
            banca.endDate = None
    if "tipo" in request.POST and request.POST['tipo'] != "":
        banca.tipo_de_banca = int(request.POST['tipo'])
    if "local" in request.POST:
        banca.location = request.POST['local']
    if "link" in request.POST:
        banca.link = request.POST['link']

    try:
        if "membro1" in request.POST and request.POST["membro1"].isnumeric():
            banca.membro1 = PFEUser.objects.get(id=int(request.POST["membro1"]))
        else:
            banca.membro1 = None
        if "membro2" in request.POST and request.POST["membro2"].isnumeric():
            banca.membro2 = PFEUser.objects.get(id=int(request.POST["membro2"]))
        else:
            banca.membro2 = None
        if "membro3" in request.POST and request.POST["membro3"].isnumeric():
            banca.membro3 = PFEUser.objects.get(id=int(request.POST["membro3"]))
        else:
            banca.membro3 = None
    except PFEUser.DoesNotExist:
        return False

    banca.save()

    return True


def professores_membros_bancas(banca=None):
    """Retorna potenciais usuários que podem ser membros de uma banca."""
    professores = PFEUser.objects.filter(tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[1][0])

    administradores = PFEUser.objects.filter(tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[3][0])

    pessoas = (professores | administradores).order_by(Lower("first_name"), Lower("last_name"))

    id_membros = []

    if banca:
        if banca.projeto and banca.projeto.orientador:
            id_membros.append(banca.projeto.orientador.user.id) # orientador
        for membro in banca.membros():
            id_membros.append(membro.id)

    membros = pessoas.filter(pk__in=id_membros)

    return pessoas, membros


def falconi_membros_banca(banca=None):
    """Coleta registros de possiveis membros de banca para Falconi."""
    try:
        organizacao = Organizacao.objects.get(sigla="Falconi")
    except Organizacao.DoesNotExist:
        return None

    falconis = PFEUser.objects.filter(parceiro__organizacao=organizacao)

    id_membros = []
    if banca:
        for membro in banca.membros():
            id_membros.append(membro.id)

    membros = falconis.filter(pk__in=id_membros)

    return falconis, membros


def recupera_orientadores_por_semestre(configuracao):
    """Recupera listas de orientadores de projetos ordenadas por semestre."""
    professores_pfe = []
    periodo = []

    ano = 2018    # Ano de início do programa
    semestre = 2  # Semestre de início do programa
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
                for grupo in grupos_pfe:  # garante que tem alunos no projeto
                    alunos_pfe = Aluno.objects.filter(alocacao__projeto=grupo)
                    if alunos_pfe:
                        count_grupos.append(grupo)
                if count_grupos:
                    professores.append(professor)
                    grupos.append(count_grupos)

        if professores:  # Se não houver nenhum orientador não cria entrada na lista
            professores_pfe.append(zip(professores, grupos))
            periodo.append(str(ano)+"."+str(semestre))

        # Para de buscar depois do semestre atual
        if ((semestre == configuracao.semestre + 1) and (ano == configuracao.ano)) or \
           (ano > configuracao.ano):
            break

        # Avança um semestre
        ano, semestre = adianta_semestre(ano, semestre)

    return zip(professores_pfe[::-1], periodo[::-1])  # inverti lista deixando os mais novos primeiro


def recupera_coorientadores_por_semestre(configuracao):
    """Recupera listas de coorientadores de projetos ordenadas por semestre."""
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
                for grupo in grupos_pfe:  # garante que tem alunos no projeto
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

    return zip(professores_pfe[::-1], periodo[::-1])  # inverti lista deixando os mais novos primeiro


def recupera_orientadores(ano, semestre):
    """Recupera listas de todos os orientadores de projetos."""
    professores = []
    grupos = []

    for professor in Professor.objects.all().order_by(Lower("user__first_name"),
                                                      Lower("user__last_name")):

        count_grupos = []
        grupos_pfe = Projeto.objects.filter(orientador=professor)

        grupos_pfe = grupos_pfe.filter(ano=ano, semestre=semestre)

        if grupos_pfe:
            for grupo in grupos_pfe:  # garante que tem alunos no projeto
                alunos_pfe = Aluno.objects.filter(alocacao__projeto=grupo)
                if alunos_pfe:
                    count_grupos.append(grupo)
            if count_grupos:
                professores.append(professor)
                grupos.append(count_grupos)

    return zip(professores, grupos)


def recupera_coorientadores(ano, semestre):
    """Recupera listas de todos os orientadores de projetos."""
    professores = []
    grupos = []

    for professor in Professor.objects.all().order_by(Lower("user__first_name"),
                                                      Lower("user__last_name")):

        count_grupos = []
        grupos_pfe = Projeto.objects.filter(coorientador__usuario__professor=professor)
        grupos_pfe = grupos_pfe.filter(ano=ano, semestre=semestre)

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
    """Recupera listas de todos os membros de bancas intermediárias."""
    professores = []
    grupos = []

    for professor in Professor.objects.all().order_by(Lower("user__first_name"),
                                                      Lower("user__last_name")):

        count_bancas = []

        bancas = Banca.objects.filter(tipo_de_banca=1)  # (1, 'Intermediária'),

        bancas = bancas.filter(membro1=professor.user) |\
                 bancas.filter(membro2=professor.user) |\
                 bancas.filter(membro3=professor.user)

        bancas = bancas.filter(projeto__ano=ano, projeto__semestre=semestre)

        if bancas:
            for banca in bancas:
                count_bancas.append(banca)
            if count_bancas:
                professores.append(professor)
                grupos.append(count_bancas)

    return zip(professores, grupos)


def recupera_bancas_finais(ano, semestre):
    """Recupera listas de todos os membros de bancas intermediárias."""
    professores = []
    grupos = []

    for professor in Professor.objects.all().order_by(Lower("user__first_name"),
                                                      Lower("user__last_name")):

        count_bancas = []

        bancas = Banca.objects.filter(tipo_de_banca=0)  # (0, 'Final')

        bancas = bancas.filter(membro1=professor.user) |\
                 bancas.filter(membro2=professor.user) |\
                 bancas.filter(membro3=professor.user)

        bancas = bancas.filter(projeto__ano=ano, projeto__semestre=semestre)

        if bancas:
            for banca in bancas:
                count_bancas.append(banca)
            if count_bancas:
                professores.append(professor)
                grupos.append(count_bancas)

    return zip(professores, grupos)


def recupera_bancas_falconi(ano, semestre):
    """Recupera listas de todos os membros de bancas falconi."""
    membros = []
    grupos = []

    organizacao = get_object_or_404(Organizacao, sigla="Falconi")
    falconis = Parceiro.objects.filter(organizacao=organizacao).order_by(Lower("user__first_name"),
                                                                         Lower("user__last_name"))

    for membro in falconis:

        count_bancas = []

        bancas = Banca.objects.filter(tipo_de_banca=2)  #  (2, 'Certificação Falconi'),

        bancas = bancas.filter(membro1=membro.user) |\
                 bancas.filter(membro2=membro.user) |\
                 bancas.filter(membro3=membro.user)

        bancas = bancas.filter(projeto__ano=ano, projeto__semestre=semestre)

        if bancas:
            for banca in bancas:
                count_bancas.append(banca)
            if count_bancas:
                membros.append(membro)
                grupos.append(count_bancas)

    return zip(membros, grupos)


def recupera_mentorias(ano, semestre):
    """Recupera listas de todos os mentores das dinâmicas no semestre."""
    membros = []
    grupos = []

    mentores = PFEUser.objects.filter(tipo_de_usuario__gt=1, is_active=True)  # estudantes não entram nos mentores
    mentores = mentores.order_by(Lower("first_name"), Lower("last_name"))

    for mentor in mentores:

        count_encontros = []

        encontros = Encontro.objects.filter(facilitador=mentor)
        
        if int(semestre) == 2:
            encontros = encontros.filter(startDate__year=ano, startDate__month__gte=7)
        else:
            encontros = encontros.filter(startDate__year=ano, startDate__month__lte=7)
            
        if encontros:
            for encontro in encontros:
                count_encontros.append(encontro)
            if count_encontros:
                membros.append(mentor)
                grupos.append(count_encontros)

    return zip(membros, grupos)


def recupera_mentorias_técnica(ano, semestre):
    """Recupera listas de todos os mentores nas empresas no semestre."""
    membros = []
    grupos = []

    mentores = PFEUser.objects.filter(tipo_de_usuario=3, is_active=True)  # soh parceiros ativos
    mentores = mentores.order_by(Lower("first_name"), Lower("last_name"))

    for mentor in mentores:

        count_conexoes = []

        conexoes = Conexao.objects.filter(projeto__ano=ano, projeto__semestre=semestre, parceiro=mentor.parceiro, mentor_tecnico=True)

        if conexoes:
            for conexao in conexoes:
                count_conexoes.append(conexao)
            if count_conexoes:
                membros.append(mentor)
                grupos.append(count_conexoes)

    return zip(membros, grupos)


def move_avaliacoes(avaliacoes_anteriores=[], observacoes_anteriores=[]):
    """Move avaliações anteriores para base de dados de Avaliações Velhas."""
    for avaliacao_velha in avaliacoes_anteriores:
        copia_avaliacao = Avaliacao_Velha()
        for field in avaliacao_velha.__dict__.keys():
            copia_avaliacao.__dict__[field] = avaliacao_velha.__dict__[field]
        copia_avaliacao.id = None
        copia_avaliacao.save()
        avaliacao_velha.delete()
    for observacao_velha in observacoes_anteriores:
        copia_observacao = Observacao_Velha()
        for field in observacao_velha.__dict__.keys():
            copia_observacao.__dict__[field] = observacao_velha.__dict__[field]
        copia_observacao.id = None
        copia_observacao.save()
        observacao_velha.delete()

def converte_conceitos(nota):
    if( nota >= 9.5 ): return ("A+")
    if( nota >= 9.0 ): return ("A")
    if( nota >= 8.0 ): return ("B+")
    if( nota >= 7.0 ): return ("B")
    if( nota >= 6.0 ): return ("C+")
    if( nota >= 5.0 ): return ("C")
    if( nota >= 4.0 ): return ("D+")
    if( nota >= 3.0 ): return ("D")
    if( nota >= 2.0 ): return ("D-")
    if( nota >= 0.0 ): return ("I")
    return "inválida"

def arredonda_conceitos(nota):
    if( nota >= 9.5 ): return 10
    if( nota >= 8.5 ): return 9
    if( nota >= 7.5 ): return 8
    if( nota >= 6.5 ): return 7
    if( nota >= 5.5 ): return 6
    if( nota >= 4.5 ): return 5
    if( nota >= 3.5 ): return 4
    if( nota >= 2.5 ): return 3
    if( nota >= 1.5 ): return 2
    return 0