#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

from django.utils import timezone

from django.shortcuts import render
#from django.http import Http404, HttpResponseRedirect,
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views import generic
#from django.contrib import messages
#from django.shortcuts import redirect
#from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django import template


from projetos.models import Configuracao, Projeto
from .forms import PFEUserCreationForm
#from .forms import PFEUserForm,
#from .forms import AlunoForm
from .models import PFEUser, Aluno, Professor, Parceiro, Opcao, Alocacao

#from tablib import Dataset

#from django.shortcuts import render_to_response
#from django.template import RequestContext

#from django.http import HttpResponse
#from .resources import AlunoResource

@login_required
def perfil(request):
    """Retorna a página conforme o perfil do usuário."""
    user = PFEUser.objects.get(pk=request.user.pk)
    if user.tipo_de_usuario == 1: #aluno
        aluno = Aluno.objects.get(pk=request.user.pk)
        context = {'aluno' : aluno,}
        return render(request, 'users/profile_detail.html', context=context)
    elif user.tipo_de_usuario == 2: #professor
        professor = Professor.objects.get(pk=request.user.pk)
        context = {'professor' : professor,}
        return render(request, 'users/profile_detail.html', context=context)
    elif user.tipo_de_usuario == 3: #parceiro
        parceiro = Parceiro.objects.get(pk=request.user.pk)
        context = {'parceiro' : parceiro,}
        return render(request, 'users/profile_detail.html', context=context)
    return HttpResponse("Seu perfil não foi encontrado!")

@login_required
@transaction.atomic
def areas_interesse(request):
    if request.method == 'POST':

        configuracao = Configuracao.objects.all().first()
        if timezone.now() > configuracao.prazo:
            return HttpResponse("Prazo para seleção de áreas vencido!") #<br>Hora atual:  "+str(timezone.now())+"<br>Hora limite:"+str(configuracao.prazo)

        check_values = request.POST.getlist('selection')
        aluno = Aluno.objects.get(pk=request.user.pk)

        aluno.inovacao_social = (True if "inovacao_social" in check_values else False)
        aluno.ciencia_dos_dados = (True if "ciencia_dos_dados" in check_values else False)
        aluno.modelagem_3D = (True if "modelagem_3D" in check_values else False)
        aluno.manufatura = (True if "manufatura" in check_values else False)
        aluno.resistencia_dos_materiais = (True if "resistencia_dos_materiais" in check_values else False)
        aluno.modelagem_de_sistemas = (True if "modelagem_de_sistemas" in check_values else False)
        aluno.controle_e_automacao = (True if "controle_e_automacao" in check_values else False)
        aluno.termodinamica = (True if "termodinamica" in check_values else False)
        aluno.fluidodinamica = (True if "fluidodinamica" in check_values else False)
        aluno.eletronica_digital = (True if "eletronica_digital" in check_values else False)
        aluno.programacao = (True if "programacao" in check_values else False)
        aluno.inteligencia_artificial = (True if "inteligencia_artificial" in check_values else False)
        aluno.banco_de_dados = (True if "banco_de_dados" in check_values else False)
        aluno.computacao_em_nuvem = (True if "computacao_em_nuvem" in check_values else False)
        aluno.visao_computacional = (True if "visao_computacional" in check_values else False)
        aluno.computacao_de_alto_desempenho = (True if "computacao_de_alto_desempenho" in check_values else False)
        aluno.robotica = (True if "robotica" in check_values else False)
        aluno.realidade_virtual_aumentada = (True if "realidade_virtual_aumentada" in check_values else False)
        aluno.protocolos_de_comunicacao = (True if "protocolos_de_comunicacao" in check_values else False)
        aluno.eficiencia_energetica = (True if "eficiencia_energetica" in check_values else False)
        aluno.administracao_economia_financas = (True if "administracao_economia_financas" in check_values else False)
        aluno.save()
        return render(request, 'users/atualizado.html',)
    else:
        return render(request, 'users/areas_interesse.html',)

class SignUp(generic.CreateView):
    form_class = PFEUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'

class Usuario(generic.DetailView):
    model = Aluno

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def alunos(request):
    configuracao = Configuracao.objects.all().first()
    alunos_list = Aluno.objects.filter(user__tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0]) # Conta soh alunos
    num_alunos = alunos_list.count()
    num_alunos_comp = alunos_list.filter(curso__exact='C').count() # Conta alunos computacao
    num_alunos_mxt = alunos_list.filter(curso__exact='X').count() # Conta alunos mecatrônica
    num_alunos_mec = alunos_list.filter(curso__exact='M').count() # Conta alunos mecânica

    tabela_alunos = {}
    ano = 2018
    semestre = 2
    while True:
        #print(str(ano)+" "+str(semestre))
        alunos_semestre = alunos_list.filter(anoPFE=ano).filter(semestrePFE=semestre)
        if ano not in tabela_alunos:
            tabela_alunos[ano] = {}
        if semestre not in tabela_alunos[ano]:
            tabela_alunos[ano][semestre] = {}
        tabela_alunos[ano][semestre]["computação"] = alunos_semestre.filter(curso__exact='C').count()
        tabela_alunos[ano][semestre]["mecânica"] = alunos_semestre.filter(curso__exact='M').count()
        tabela_alunos[ano][semestre]["mecatrônica"] = alunos_semestre.filter(curso__exact='X').count()
        tabela_alunos[ano][semestre]["total"] = alunos_semestre.count()

        if ((ano == configuracao.ano) and (semestre == configuracao.semestre)):
            break

        if semestre == 1:
            semestre = 2
        else:
            ano += 1
            semestre = 1

    context = {
        'alunos_list' : alunos_list,
        'num_alunos': num_alunos,
        'num_alunos_comp': num_alunos_comp,
        'num_alunos_mxt': num_alunos_mxt,
        'num_alunos_mec': num_alunos_mec,
        'configuracao': configuracao,
        'tabela_alunos': tabela_alunos,
    }
    return render(request, 'users/alunos.html', context=context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def alunos_inscrevendo(request):
    configuracao = Configuracao.objects.all().first()

    # PARA O FUTURO IMPLEMENTAR
    # if configuracao.semestre==1:
    #     ano = configuracao.ano
    #     semestre = 2
    # else:
    #     ano = configuracao.ano+1
    #     semestre = 1

    # Alunos se inscrevendo atualmente
    ano = configuracao.ano
    semestre = configuracao.semestre

    alunos_se_inscrevendo = Aluno.objects.filter(trancado=False).filter(anoPFE=ano).filter(semestrePFE=semestre).order_by("user__first_name")
    alunos = alunos_se_inscrevendo.filter(user__tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0]) # Conta soh alunos
    num_alunos = alunos.count()
    num_alunos_comp = alunos.filter(curso__exact='C').count() # Conta alunos computacao
    num_alunos_mxt = alunos.filter(curso__exact='X').count() # Conta alunos mecatrônica
    num_alunos_mec = alunos.filter(curso__exact='M').count() # Conta alunos mecânica

    inscritos = 0
    ninscritos = 0
    opcoes = []
    for aluno in alunos:
        opcao = Opcao.objects.filter(aluno=aluno).filter(projeto__ano=ano).filter(projeto__semestre=semestre)
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
    }
    return render(request, 'users/alunos_inscrevendo.html', context=context)

# TROCAR O NOME DESSA FUNÇAO
@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def aluno(request, pk):
    aluno = Aluno.objects.filter(pk=pk).first()
    configuracao = Configuracao.objects.all().first()
    context = {
        'configuracao': configuracao,
        'aluno': aluno,
    }
    return render(request, 'users/aluno_detail.html', context=context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def professor_detail(request, pk):
    professor = Professor.objects.filter(pk=pk).first()
    projetos = Projeto.objects.filter(orientador=professor).all()
    context = {
        'professor': professor,
        'projetos': projetos,
    }
    return render(request, 'users/professor_detail.html', context=context)

# class AlunoListView(LoginRequiredMixin, generic.ListView):
#     model = Aluno
#     paginate_by = 2
#     #{% if aluno_list %}
#     # {% for aluno in aluno_list %}
#     #   <li>
#     #     <a href="{{ aluno.get_absolute_url }}">{{ aluno.login }}</a> ({{aluno.nome_completo}})
#     #   </li>
#     # {% endfor %}

# # Visualiza informaçõs da empresa e permite editar
# @login_required
# def empresa(request, empresa_id):
#     try:
#         empresa = Empresa.objects.get(login=empresa_id)
#     except Empresa.DoesNotExist:
#         raise Http404("Empresa nao encontrado")
#     return render(request, 'empresa.html', {'empresa': empresa})

# # Visualiza informaçõs do professor e permite editar
# @login_required
# def professor(request, professor_id):
#     try:
#         professor = Professor.objects.get(login=professor_id)
#     except Professor.DoesNotExist:
#         raise Http404("Professor nao encontrado")
#     return render(request, 'professor.html', {'professor': professor})
