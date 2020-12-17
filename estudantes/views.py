"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 14 de Dezembro de 2020
"""

import datetime

from django.contrib.auth.decorators import login_required

from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from projetos.models import Projeto, Proposta, Configuracao, Area
from projetos.models import Encontro, Banca, Entidade

from projetos.views import cria_area_estudante

from projetos.messages import email, message_agendamento, create_message

from users.models import PFEUser, Aluno, Professor, Alocacao, Opcao

from users.support import configuracao_estudante_vencida, adianta_semestre


@login_required
def index_estudantes(request):
    """Mostra página principal do usuário estudante."""

    try:
        usuario = PFEUser.objects.get(pk=request.user.pk)
    except PFEUser.DoesNotExist:
        return HttpResponse("Usuário não encontrado.", status=401)

    try:
        configuracao = Configuracao.objects.get()
        vencido = timezone.now() > configuracao.prazo
        ano = configuracao.ano
        semestre = configuracao.semestre
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    context = {}
    context['configuracao'] = configuracao

    if usuario.tipo_de_usuario == 1: # Estudante
        try:
            estudante = Aluno.objects.get(pk=request.user.aluno.pk)
        except Aluno.DoesNotExist:
            return HttpResponse("Estudante não encontrado.", status=401)

        context['projeto'] = Projeto.objects.filter(alocacao__aluno=estudante).last()

        # Estudantes de processos passados sempre terrão seleção vencida
        if semestre == 1:
            vencido = vencido or (estudante.anoPFE < ano)
            vencido = vencido or (estudante.anoPFE == ano and estudante.semestrePFE == 1)
        else:
            vencido = vencido or (estudante.anoPFE <= ano)

    elif usuario.tipo_de_usuario == 2 or usuario.tipo_de_usuario == 4: # professor & administrador
        try:
            professor_id = Professor.objects.get(pk=request.user.professor.pk).id
            context['professor_id'] = professor_id
        except Professor.DoesNotExist:
            return HttpResponse("Professor não encontrado.", status=401)

    context['vencido'] = vencido

    ano, semestre = adianta_semestre(ano, semestre)
    context['ano'] = ano
    context['semestre'] = semestre

    return render(request, 'estudantes/index_estudantes.html', context=context)


@login_required
def areas_interesse(request):
    """Para estudantes definirem suas áreas de interesse."""

    try:
        user = PFEUser.objects.get(pk=request.user.pk)
    except PFEUser.DoesNotExist:
        return HttpResponse("Usuário não encontrado.", status=401)

    areas = Area.objects.filter(ativa=True)
    context = {
        'areast': areas,
    }

    # Caso seja estudante
    if user.tipo_de_usuario == 1: # Estudante
        try:
            estudante = Aluno.objects.get(pk=request.user.aluno.pk)
        except Aluno.DoesNotExist:
            return HttpResponse("Estudante não encontrado.", status=401)

        vencido = configuracao_estudante_vencida(estudante)

        if (not vencido) and request.method == 'POST':
            cria_area_estudante(request, estudante)
            return render(request, 'users/atualizado.html',)

        context['vencido'] = vencido
        context['aluno'] = estudante

    elif user.tipo_de_usuario == 2 or user.tipo_de_usuario == 4: #  Professores ou Administrador
        context['mensagem'] = "Você não está cadastrado como estudante."
        context['vencido'] = True

    else: # Caso não seja Estudante, Professor ou Administrador (ou seja Parceiro)
        mensagem = "Você não está cadastrado como estudante!"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    return render(request, 'estudantes/areas_interesse.html', context=context)


@login_required
def encontros_marcar(request):
    """Encontros a serem agendados pelos alunos."""

    try:
        configuracao = Configuracao.objects.get()
        ano = configuracao.ano
        semestre = configuracao.semestre
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    hoje = datetime.date.today()
    encontros = Encontro.objects.filter(startDate__gt=hoje).order_by('startDate')

    try:
        usuario = PFEUser.objects.get(pk=request.user.pk)
    except PFEUser.DoesNotExist:
        return HttpResponse("Usuário não encontrado.", status=401)

    if usuario.tipo_de_usuario == 1: # Estudante
        try:
            estudante = Aluno.objects.get(pk=request.user.aluno.pk)
        except Aluno.DoesNotExist:
            return HttpResponse("Estudante não encontrado.", status=401)

        projeto = Projeto.objects.filter(alocacao__aluno=estudante).\
                                  distinct().\
                                  filter(ano=ano).\
                                  filter(semestre=semestre).last()

    elif usuario.tipo_de_usuario == 2 or usuario.tipo_de_usuario == 4: # Professor ou Administrador
        projeto = None
    else:
        return HttpResponse("Estudante não encontrado (você não possui conta de estudante).",
                            status=401)


    if request.method == 'POST':
        check_values = request.POST.getlist('selection')
        agendado = None
        for encontro in encontros:
            if str(encontro.id) == check_values[0]:
                if encontro.projeto != projeto:
                    encontro.projeto = projeto
                    encontro.save()
                agendado = encontro
            else:
                if encontro.projeto == projeto:
                    encontro.projeto = None
                    encontro.save()

        if agendado:
            subject = 'Dinâmica PFE agendada'
            recipient_list = []
            alocacoes = Alocacao.objects.filter(projeto=projeto)
            for alocacao in alocacoes:
                recipient_list.append(alocacao.aluno.user.email) #mandar para cada membro do grupo
            recipient_list.append('pfeinsper@gmail.com') #sempre mandar para a conta do gmail

            message = message_agendamento(agendado)
            check = email(subject, recipient_list, message)
            if check != 1:
                message = "Algum problema de conexão, contacte: lpsoares@insper.edu.br"

            mensagem = "Agendado: " + str(agendado.startDate)
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

        return HttpResponse("Problema! Por favor reportar.")

    else:
        context = {
            'encontros': encontros,
            'projeto': projeto,
        }
        return render(request, 'estudantes/encontros_marcar.html', context)


@login_required
def informacoes_adicionais(request):
    """Para perguntas descritivas ao aluno de onde trabalho, entidades, sociais e familia."""

    try:
        user = PFEUser.objects.get(pk=request.user.pk)
    except PFEUser.DoesNotExist:
        return HttpResponse("Usuário não encontrado.", status=401)

    if user.tipo_de_usuario == 3:
        mensagem = "Você não está cadastrado como aluno!"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    if user.tipo_de_usuario == 1:

        estudante = Aluno.objects.get(pk=request.user.aluno.pk)

        vencido = configuracao_estudante_vencida(estudante)

        if (not vencido) and request.method == 'POST':

            estudante.trabalhou = request.POST.get("trabalhou", None)
            estudante.social = request.POST.get("social", None)
            estudante.entidade = request.POST.get("entidade", None)
            estudante.familia = request.POST.get("familia", None)

            estudante.user.linkedin = request.POST.get("linkedin", None)
            estudante.user.save()

            estudante.save()
            return render(request, 'users/atualizado.html',)

        context = {
            'vencido': vencido,
            'trabalhou' : estudante.trabalhou,
            'social' : estudante.social,
            'entidade' : estudante.entidade,
            'familia' : estudante.familia,
            'linkedin' : estudante.user.linkedin,
            'entidades' : Entidade.objects.all(),
        }
    else: # Supostamente professores
        context = {
            'mensagem': "Você não está cadastrado como estudante.",
            'vencido': True,
            'trabalhou': "",
            'social': "",
            'entidade': "",
            'familia': "",
            'linkedin': user.linkedin,
            'entidades': Entidade.objects.all(),
        }
    return render(request, 'estudantes/informacoes_adicionais.html', context)


@login_required
def minhas_bancas(request):
    """Lista as bancas agendadas para um aluno."""
    try:
        aluno = Aluno.objects.get(pk=request.user.aluno.pk)
    except Aluno.DoesNotExist:
        return HttpResponse("Aluno não encontrado.", status=401)

    configuracao = Configuracao.objects.get()
    if not configuracao.liberados_projetos:
        if aluno.anoPFE > configuracao.ano or\
          (aluno.anoPFE == configuracao.ano and aluno.semestrePFE > configuracao.semestre):
            mensagem = "Projetos ainda não disponíveis para o seu período de PFE."
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

    projetos = Projeto.objects.filter(alocacao__aluno=aluno)
    bancas = Banca.objects.filter(projeto__in=projetos).order_by("-startDate")

    context = {
        'bancas' : bancas,
    }
    return render(request, 'estudantes/minhas_bancas.html', context)


@login_required
def selecao_propostas(request):
    """Exibe todos os projetos para os alunos aplicarem."""

    try:
        user = PFEUser.objects.get(pk=request.user.pk)
    except PFEUser.DoesNotExist:
        return HttpResponse("Usuário não encontrado.", status=401)

    configuracao = Configuracao.objects.get()
    ano = configuracao.ano
    semestre = configuracao.semestre

    liberadas_propostas = configuracao.liberadas_propostas

    # Vai para próximo semestre
    if semestre == 1:
        semestre = 2
    else:
        ano += 1
        semestre = 1

    propostas = Proposta.objects.filter(ano=ano).\
                                filter(semestre=semestre).\
                                filter(disponivel=True)

    warnings = ""

    vencido = True

    if user.tipo_de_usuario == 1:

        vencido = timezone.now() > configuracao.prazo

        try:
            aluno = Aluno.objects.get(pk=request.user.aluno.pk)
        except Aluno.DoesNotExist:
            return HttpResponse("Estudante não encontrado.", status=401)

        if configuracao.semestre == 1:
            vencido = vencido or (aluno.anoPFE < configuracao.ano)
            vencido = vencido or (aluno.anoPFE == configuracao.ano and aluno.semestrePFE == 1)
        else:
            vencido = vencido or (aluno.anoPFE <= configuracao.ano)

        if vencido:
            mensagem = "Prazo para seleção de propostas de propostas de projetos vencido!"
            context = {
                "area_aluno": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

        if liberadas_propostas and request.method == 'POST':
            prioridade = {}
            for proposta in propostas:
                check_values = request.POST.get('selection'+str(proposta.pk), "0")
                prioridade[proposta.pk] = check_values
            for i in range(1, len(propostas)+1):
                if i < 6 and list(prioridade.values()).count(str(i)) == 0:
                    warnings += "Nenhuma proposta com prioridade "+str(i)+"\n"
                if list(prioridade.values()).count(str(i)) > 1:
                    warnings += "Mais de uma proposta com prioridade "+str(i)+"\n"
            if warnings == "":
                for proposta in propostas:
                    if prioridade[proposta.pk] != "0":
                        if not aluno.opcoes.filter(pk=proposta.pk): # Se lista for vazia
                            Opcao.objects.create(aluno=aluno, proposta=proposta,
                                                 prioridade=int(prioridade[proposta.pk]))
                        elif Opcao.objects.get(aluno=aluno, proposta=proposta).\
                                        prioridade != int(prioridade[proposta.pk]):
                            opc = Opcao.objects.get(aluno=aluno, proposta=proposta)
                            opc.prioridade = int(prioridade[proposta.pk])
                            opc.save()
                    else:
                        if aluno.opcoes.filter(pk=proposta.pk): # Se lista não for vazia
                            Opcao.objects.filter(aluno=aluno, proposta=proposta).delete()
                message = create_message(aluno, ano, semestre)

                subject = 'PFE : '+aluno.user.username
                recipient_list = ['pfeinsper@gmail.com', aluno.user.email,]
                check = email(subject, recipient_list, message)
                if check != 1:
                    message = "Algum problema de conexão, contacte: lpsoares@insper.edu.br"

                context = {'message': message,}
                return render(request, 'projetos/confirmacao.html', context)

            context = {'warnings': warnings,}
            return render(request, 'projetos/projetosincompleto.html', context)

        opcoes = Opcao.objects.filter(aluno=aluno)

    elif user.tipo_de_usuario == 2 or user.tipo_de_usuario == 4:
        opcoes = []

    else:
        return HttpResponse("Acesso irregular.", status=401)

    context = {
        'liberadas_propostas': liberadas_propostas,
        'vencido': vencido,
        'propostas': propostas,
        'opcoes': opcoes,
        'ano': ano,
        'semestre': semestre,
        'warnings': warnings,
    }
    return render(request, 'estudantes/selecao_propostas.html', context)
