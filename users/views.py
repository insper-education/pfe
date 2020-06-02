#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

import string
import random

from django.contrib.auth.decorators import login_required, permission_required

from django.db import transaction
from django.db.models.functions import Lower
from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import html
from django.utils import timezone
from django.views import generic

from projetos.models import Configuracao, Projeto, Conexao
from projetos.views import cria_areas
from projetos.messages import email

from .forms import PFEUserCreationForm
from .models import PFEUser, Aluno, Professor, Parceiro, Opcao, Administrador


@login_required
def perfil(request):
    """Retorna a página conforme o perfil do usuário."""
    try:
        user = PFEUser.objects.get(pk=request.user.pk)
    except PFEUser.DoesNotExist:
        return HttpResponse("Usuário não encontrado.", status=401)

    context = {'aluno' : False, 'professor' : False, 'parceiro' : False, 'administrador' : False,}
    if user.tipo_de_usuario == 1: #aluno
        try:
            context['aluno'] = Aluno.objects.get(pk=request.user.aluno.pk)
        except Aluno.DoesNotExist:
            return HttpResponse("Estudante não encontrado.", status=401)

    elif user.tipo_de_usuario == 2: #professor
        try:
            context['professor'] = Professor.objects.get(pk=request.user.professor.pk)
        except Professor.DoesNotExist:
            return HttpResponse("Professor não encontrado.", status=401)

    elif user.tipo_de_usuario == 3: #parceiro
        try:
            context['parceiro'] = Parceiro.objects.get(pk=request.user.parceiro.pk)
        except Parceiro.DoesNotExist:
            return HttpResponse("Parceiro não encontrado.", status=401)

    elif user.tipo_de_usuario == 4: #administrador
        try:
            context['administrador'] = Administrador.objects.get(pk=request.user.administrador.pk)
        except Administrador.DoesNotExist:
            return HttpResponse("Administrador não encontrado.", status=401)

    else:
        mensagem = "Seu perfil não foi encontrado!"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    return render(request, 'users/profile_detail.html', context=context)

@login_required
@transaction.atomic
def areas_interesse(request):
    """Para aluno definir suas áreas de interesse."""
    try:
        estudante = Aluno.objects.get(pk=request.user.aluno.pk)
    except Aluno.DoesNotExist:
        return HttpResponse("Estudante não encontrado.", status=401)

    configuracao = Configuracao.objects.first()
    ano = configuracao.ano
    semestre = configuracao.semestre

    vencido = timezone.now() > configuracao.prazo
    if semestre == 1:
        vencido = vencido or (estudante.anoPFE < ano)
        vencido = vencido or (estudante.anoPFE == ano and estudante.semestrePFE == 1)
        semestre = 2
    else:
        vencido = vencido or (estudante.anoPFE <= ano)
        ano += 1
        semestre = 1

    if (not vencido) and request.method == 'POST':
        areas = cria_areas(request, estudante.areas_de_interesse)
        estudante.areas_de_interesse = areas
        estudante.save()
        return render(request, 'users/atualizado.html',)

    context = {
        'vencido': vencido,
        'areas': estudante.areas_de_interesse,
    }
    return render(request, 'users/areas_interesse.html', context=context)

class SignUp(generic.CreateView):
    """Rotina para fazer o login."""
    form_class = PFEUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'

class Usuario(generic.DetailView):
    """Usuário."""
    model = Aluno

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def alunos_lista(request):
    """Mostra todos os alunos que estão que cursam semestre atual."""
    configuracao = Configuracao.objects.all().first()
    ano = configuracao.ano
    semestre = configuracao.semestre
    return redirect('alunos_listagem', anosemestre="{0}.{1}".format(ano, semestre))

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def alunos_listagem(request, anosemestre):
    """Gera lista com todos os alunos já registrados."""
    configuracao = Configuracao.objects.all().first()
    alunos_list = Aluno.objects.filter(user__tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0])\
        .order_by(Lower("user__first_name"), Lower("user__last_name")) # Conta soh alunos

    ano = 0
    semestre = 0

    tabela_alunos = {}

    totais = {}
    totais["computação"] = 0
    totais["mecânica"] = 0
    totais["mecatrônica"] = 0

    if anosemestre != "todos":
        ano = int(anosemestre.split(".")[0])
        semestre = int(anosemestre.split(".")[1])

        alunos_semestre = alunos_list.\
            filter(alocacao__projeto__ano=ano, alocacao__projeto__semestre=semestre).distinct()

        tabela_alunos[ano] = {}
        tabela_alunos[ano][semestre] = {}

        tabela_alunos[ano][semestre]["computação"] =\
            alunos_semestre.filter(curso__exact='C').count()
        totais["computação"] += tabela_alunos[ano][semestre]["computação"]
        tabela_alunos[ano][semestre]["mecânica"] =\
            alunos_semestre.filter(curso__exact='M').count()
        totais["mecânica"] += tabela_alunos[ano][semestre]["mecânica"]
        tabela_alunos[ano][semestre]["mecatrônica"] =\
            alunos_semestre.filter(curso__exact='X').count()
        totais["mecatrônica"] += tabela_alunos[ano][semestre]["mecatrônica"]
        tabela_alunos[ano][semestre]["total"] =\
            alunos_semestre.count()

        alunos_list = alunos_semestre | \
                      alunos_list.filter(anoPFE=ano, semestrePFE=semestre).distinct()

    else:
        ano_tmp = 2018
        semestre_tmp = 2
        while True:
            alunos_semestre = alunos_list.\
                filter(alocacao__projeto__ano=ano_tmp, alocacao__projeto__semestre=semestre_tmp).\
                distinct()
            if ano_tmp not in tabela_alunos:
                tabela_alunos[ano_tmp] = {}
            if semestre_tmp not in tabela_alunos[ano_tmp]:
                tabela_alunos[ano_tmp][semestre_tmp] = {}

            tabela_alunos[ano_tmp][semestre_tmp]["computação"] =\
                alunos_semestre.filter(curso__exact='C').count()
            totais["computação"] += tabela_alunos[ano_tmp][semestre_tmp]["computação"]
            tabela_alunos[ano_tmp][semestre_tmp]["mecânica"] =\
                alunos_semestre.filter(curso__exact='M').count()
            totais["mecânica"] += tabela_alunos[ano_tmp][semestre_tmp]["mecânica"]
            tabela_alunos[ano_tmp][semestre_tmp]["mecatrônica"] =\
                alunos_semestre.filter(curso__exact='X').count()
            totais["mecatrônica"] += tabela_alunos[ano_tmp][semestre_tmp]["mecatrônica"]
            tabela_alunos[ano_tmp][semestre_tmp]["total"] =\
                alunos_semestre.count()

            if ((ano_tmp == configuracao.ano) and (semestre_tmp == configuracao.semestre)):
                break

            if semestre_tmp == 1:
                semestre_tmp = 2
            else:
                ano_tmp += 1
                semestre_tmp = 1


    num_alunos = alunos_list.count()
    num_alunos_comp = alunos_list.filter(curso__exact='C').count() # Conta alunos computacao
    num_alunos_mxt = alunos_list.filter(curso__exact='X').count() # Conta alunos mecatrônica
    num_alunos_mec = alunos_list.filter(curso__exact='M').count() # Conta alunos mecânica

    num_alunos_masculino = alunos_list.filter(user__genero='M').count() # Estudantes masculino
    num_alunos_feminino = alunos_list.filter(user__genero='F').count() # Estudantes feminino

    totais["total"] = totais["computação"] + totais["mecânica"] + totais["mecatrônica"]

    context = {
        'alunos_list' : alunos_list,
        'num_alunos': num_alunos,
        'num_alunos_comp': num_alunos_comp,
        'num_alunos_mxt': num_alunos_mxt,
        'num_alunos_mec': num_alunos_mec,
        'num_alunos_masculino': num_alunos_masculino,
        'num_alunos_feminino': num_alunos_feminino,
        'configuracao': configuracao,
        'tabela_alunos': tabela_alunos,
        'totais': totais,
        'ano': ano,
        'semestre': semestre,
        'loop_anos': range(2018, configuracao.ano+1),
    }
    return render(request, 'users/alunos_lista.html', context=context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def alunos_inscrevendo(request):
    """Mostra todos os alunos que estão se inscrevendo em projetos no próximo semestre."""
    configuracao = Configuracao.objects.all().first()

    if configuracao.semestre == 1:
        ano = configuracao.ano
        semestre = 2
    else:
        ano = configuracao.ano+1
        semestre = 1

    return redirect('alunos_inscritos', anosemestre="{0}.{1}".format(ano, semestre))

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def alunos_inscritos(request, anosemestre):
    """Mostra todos os alunos que estão se inscrevendo em projetos."""
    configuracao = Configuracao.objects.all().first()

    ano = int(anosemestre.split(".")[0])
    semestre = int(anosemestre.split(".")[1])

    alunos_se_inscrevendo = Aluno.objects.filter(trancado=False).\
                                      filter(anoPFE=ano, semestrePFE=semestre).\
                                      order_by(Lower("user__first_name"), Lower("user__last_name"))

    # Conta soh alunos
    alunos = alunos_se_inscrevendo.filter(user__tipo_de_usuario=\
                                          PFEUser.TIPO_DE_USUARIO_CHOICES[0][0])

    num_alunos = alunos.count()
    num_alunos_comp = alunos.filter(curso__exact='C').count() # Conta alunos computacao
    num_alunos_mxt = alunos.filter(curso__exact='X').count() # Conta alunos mecatrônica
    num_alunos_mec = alunos.filter(curso__exact='M').count() # Conta alunos mecânica

    inscritos = 0
    ninscritos = 0
    opcoes = []
    for aluno in alunos:
        opcao = Opcao.objects.filter(aluno=aluno).\
                              filter(proposta__ano=ano, proposta__semestre=semestre)
        opcoes.append(opcao)
        if opcao.count() >= 5:
            inscritos += 1
        else:
            ninscritos += 1
    alunos_list = zip(alunos, opcoes)

    context = {
        'alunos_list' : alunos_list,
        'num_alunos': num_alunos,
        'num_alunos_comp': num_alunos_comp,
        'num_alunos_mxt': num_alunos_mxt,
        'num_alunos_mec': num_alunos_mec,
        'inscritos': inscritos,
        'ninscritos': ninscritos,
        'ano': ano,
        'semestre': semestre,
        'loop_anos': range(2018, configuracao.ano+1),
    }
    return render(request, 'users/alunos_inscritos.html', context=context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def aluno_detail(request, primarykey):
    """Mostra detalhes sobre o aluno."""
    aluno = Aluno.objects.filter(pk=primarykey).first()
    configuracao = Configuracao.objects.all().first()
    context = {
        'configuracao': configuracao,
        'aluno': aluno,
        'areas': aluno.areas_de_interesse,
    }
    return render(request, 'users/aluno_detail.html', context=context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def professor_detail(request, primarykey):
    """Mostra detalhes sobre o professor."""
    try:
        professor = Professor.objects.get(pk=primarykey)
    except Professor.DoesNotExist:
        return HttpResponse("Professor não encontrado.", status=401)

    projetos = Projeto.objects.filter(orientador=professor)
    context = {
        'professor': professor,
        'projetos': projetos,
    }
    return render(request, 'users/professor_detail.html', context=context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def parceiro_detail(request, primarykey):
    """Mostra detalhes sobre o parceiro."""
    try:
        parceiro = Parceiro.objects.get(pk=primarykey)
    except Professor.DoesNotExist:
        return HttpResponse("Professor não encontrado.", status=401)

    configuracao = Configuracao.objects.all().first()
    conexoes = Conexao.objects.filter(parceiro=parceiro)
    context = {
        'configuracao': configuracao,
        'parceiro': parceiro,
        'conexoes': conexoes,
    }
    return render(request, 'users/parceiro_detail.html', context=context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def contas_senhas(request, anosemestre):
    """Envia conta e senha para todos os estudantes que estão no semestre."""
    configuracao = Configuracao.objects.all().first()

    ano = int(anosemestre.split(".")[0])
    semestre = int(anosemestre.split(".")[1])

    estudantes = Aluno.objects.filter(trancado=False).\
                               filter(anoPFE=ano, semestrePFE=semestre).\
                               filter(user__tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0]).\
                               order_by(Lower("user__first_name"), Lower("user__last_name"))

    if request.method == 'POST':
        mensagem = "Enviado para:<br>\n<br>\n"
        for estudante in estudantes:
            mensagem += estudante.user.get_full_name() + " " +\
                        "&lt;" + estudante.user.email + "&gt;<br>\n"

            # Atualizando senha do usuário.
            senha = ''.join(random.SystemRandom().\
                        choice(string.ascii_lowercase + string.digits) for _ in range(6))
            estudante.user.set_password(senha)
            estudante.user.save()

            # Preparando mensagem para enviar para usuário.
            message_email = estudante.user.get_full_name() + ",\n\n\n"
            message_email += "Você está recebendo sua conta e senha para acessar o sistema do PFE."
            message_email += "\n\n"
            message_email += "O endereço do servidor é: "
            message_email += "<a href='http://pfe.insper.edu.br/'>http://pfe.insper.edu.br/</a>"
            message_email += "\n\n"
            message_email += "Preencha suas áreas de interesse, "
            message_email += "bem como o formulário de informações adicionais.\n"
            message_email += "Faça sua seleção de propostas de projetos "
            message_email += "conforme sua ordem de interesse.\n"
            message_email += "O prazo para a escolha de projetos é: " +\
                             configuracao.prazo.strftime("%d/%m/%Y %H:%M") + "\n"
            message_email += "Você pode alterar quantas vezes desejar suas escolhas "
            message_email += "até a data limite."
            message_email += "\n"
            message_email += "Sua conta é: <b>" + estudante.user.username + "</b>\n"
            message_email += "Sua senha é: <b>" + senha + "</b>\n"
            message_email += "\n\n"
            message_email += "atenciosamente, coordenação do PFE\n"
            message_email = message_email.replace('\n', '<br>\n')

            # Enviando e-mail com mensagem para usuário.
            subject = 'Conta PFE : ' + estudante.user.get_full_name()
            recipient_list = [estudante.user.email, 'pfeinsper@gmail.com',]
            check = email(subject, recipient_list, message_email)
            if check != 1:
                mensagem = "Algum problema de conexão, contacte: lpsoares@insper.edu.br"

        mensagem = html.urlize(mensagem)
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    context = {
        'estudantes' : estudantes,
        'ano': ano,
        'semestre': semestre,
        'loop_anos': range(2018, configuracao.ano+1),
    }
    return render(request, 'users/contas_senhas.html', context=context)
