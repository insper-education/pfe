#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""


from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic

from projetos.models import Configuracao, Projeto
from .forms import PFEUserCreationForm
from .models import PFEUser, Aluno, Professor, Parceiro, Opcao

@login_required
def perfil(request):
    """Retorna a página conforme o perfil do usuário."""
    user = PFEUser.objects.get(pk=request.user.pk)
    if user.tipo_de_usuario == 1: #aluno
        aluno = Aluno.objects.get(pk=request.user.pk)
        context = {'aluno' : aluno,}
        return render(request, 'users/profile_detail.html', context=context)
    if user.tipo_de_usuario == 2: #professor
        professor = Professor.objects.get(pk=request.user.pk)
        context = {'professor' : professor,}
        return render(request, 'users/profile_detail.html', context=context)
    if user.tipo_de_usuario == 3: #parceiro
        parceiro = Parceiro.objects.get(pk=request.user.pk)
        context = {'parceiro' : parceiro,}
        return render(request, 'users/profile_detail.html', context=context)
    return HttpResponse("Seu perfil não foi encontrado!")

@login_required
@transaction.atomic
def areas_interesse(request):
    """Para aluno definir suas áreas de interesse."""
    if request.method == 'POST':

        configuracao = Configuracao.objects.all().first()
        if timezone.now() > configuracao.prazo:
            #<br>Hora atual:  "+str(timezone.now())+"<br>Hora limite:"+str(configuracao.prazo)
            return HttpResponse("Prazo para seleção de áreas vencido!")

        check_values = request.POST.getlist('selection')
        aluno = Aluno.objects.get(pk=request.user.pk)

        aluno.inovacao_social = "inovacao_social" in check_values
        aluno.ciencia_dos_dados = "ciencia_dos_dados" in check_values
        aluno.modelagem_3D = "modelagem_3D" in check_values
        aluno.manufatura = "manufatura" in check_values
        aluno.resistencia_dos_materiais = "resistencia_dos_materiais" in check_values
        aluno.modelagem_de_sistemas = "modelagem_de_sistemas" in check_values
        aluno.controle_e_automacao = "controle_e_automacao" in check_values
        aluno.termodinamica = "termodinamica" in check_values
        aluno.fluidodinamica = "fluidodinamica" in check_values
        aluno.eletronica_digital = "eletronica_digital" in check_values
        aluno.programacao = "programacao" in check_values
        aluno.inteligencia_artificial = "inteligencia_artificial" in check_values
        aluno.banco_de_dados = "banco_de_dados" in check_values
        aluno.computacao_em_nuvem = "computacao_em_nuvem" in check_values
        aluno.visao_computacional = "visao_computacional" in check_values
        aluno.computacao_de_alto_desempenho = "computacao_de_alto_desempenho" in check_values
        aluno.robotica = "robotica" in check_values
        aluno.realidade_virtual_aumentada = "realidade_virtual_aumentada" in check_values
        aluno.protocolos_de_comunicacao = "protocolos_de_comunicacao" in check_values
        aluno.eficiencia_energetica = "eficiencia_energetica" in check_values
        aluno.administracao_economia_financas = "administracao_economia_financas" in check_values
        aluno.save()
        return render(request, 'users/atualizado.html',)
    return render(request, 'users/areas_interesse.html',)

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
    """Gera lista com todos os alunos já registrados."""
    configuracao = Configuracao.objects.all().first()
    alunos_list = Aluno.objects.filter(user__tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0])\
        .order_by("user__first_name", "user__last_name", ) # Conta soh alunos
    num_alunos = alunos_list.count()
    num_alunos_comp = alunos_list.filter(curso__exact='C').count() # Conta alunos computacao
    num_alunos_mxt = alunos_list.filter(curso__exact='X').count() # Conta alunos mecatrônica
    num_alunos_mec = alunos_list.filter(curso__exact='M').count() # Conta alunos mecânica

    tabela_alunos = {}

    totais = {}
    totais["computação"] = 0
    totais["mecânica"] = 0
    totais["mecatrônica"] = 0

    ano = 2018
    semestre = 2
    while True:
        alunos_semestre = alunos_list.\
            filter(alocacao__projeto__ano=ano, alocacao__projeto__semestre=semestre).distinct()
        if ano not in tabela_alunos:
            tabela_alunos[ano] = {}
        if semestre not in tabela_alunos[ano]:
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

        if ((ano == configuracao.ano) and (semestre == configuracao.semestre)):
            break

        if semestre == 1:
            semestre = 2
        else:
            ano += 1
            semestre = 1

    totais["total"] = totais["computação"] + totais["mecânica"] + totais["mecatrônica"] 

    context = {
        'alunos_list' : alunos_list,
        'num_alunos': num_alunos,
        'num_alunos_comp': num_alunos_comp,
        'num_alunos_mxt': num_alunos_mxt,
        'num_alunos_mec': num_alunos_mec,
        'configuracao': configuracao,
        'tabela_alunos': tabela_alunos,
        'totais': totais,
    }
    return render(request, 'users/alunos_lista.html', context=context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def alunos_inscrevendo(request):
    """Mostra todos os alunos que estão se inscrevendo em projetos."""
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

    alunos_se_inscrevendo = Aluno.objects.filter(trancado=False).\
                                          filter(anoPFE=ano, semestrePFE=semestre).\
                                          order_by("user__first_name")

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
                              filter(projeto__ano=ano, projeto__semestre=semestre)
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

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def aluno_detail(request, primarykey):
    """Mostra detalhes sobre o aluno."""
    aluno = Aluno.objects.filter(pk=primarykey).first()
    configuracao = Configuracao.objects.all().first()
    context = {
        'configuracao': configuracao,
        'aluno': aluno,
    }
    return render(request, 'users/aluno_detail.html', context=context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def professor_detail(request, primarykey):
    """Mostra detalhes sobre o professor."""
    professor = Professor.objects.filter(pk=primarykey).first()
    projetos = Projeto.objects.filter(orientador=professor).all()
    context = {
        'professor': professor,
        'projetos': projetos,
    }
    return render(request, 'users/professor_detail.html', context=context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def parceiro_detail(request, primarykey):
    """Mostra detalhes sobre o parceiro."""
    parceiro = Parceiro.objects.filter(pk=primarykey).first()
    configuracao = Configuracao.objects.all().first()
    context = {
        'configuracao': configuracao,
        'parceiro': parceiro,
    }
    return render(request, 'users/parceiro_detail.html', context=context)


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
