# Desenvolvido para o Projeto Final de Engenharia
# Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
# Data: 15 de Maio de 2019

from django.shortcuts import render
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.urls import reverse_lazy
from django.views import generic
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.db import transaction

from .forms import PFEUserCreationForm, PFEUserForm, AlunoForm
from .models import PFEUser, Aluno, Professor, Funcionario

from tablib import Dataset

from django.shortcuts import render_to_response
from django.template import RequestContext

#from django.http import HttpResponse
from .resources import AlunoResource

def export(request):
    aluno_resource = AlunoResource()
    dataset = aluno_resource.export()
    response = HttpResponse(dataset.csv, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="alunos.csv"'
    return response

def exportXLS(request):
    aluno_resource = AlunoResource()
    dataset = aluno_resource.export()
    response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="alunos.xls"'
    return response

@login_required
@transaction.atomic
def update_profile(request):
    if request.method == 'POST':
        pfeuser_form = PFEUserForm(request.POST, instance=request.user)
        aluno_form = AlunoForm(request.POST, instance=request.user.aluno)
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
        #return HttpResponse("Dados atualizados<br><br><br>")
    else:
        pfeuser_form = PFEUserForm(instance=request.user)
        aluno_form = AlunoForm(instance=request.user)
    return render(request, 'users/profile.html', {
        'pfeuser_form': pfeuser_form,
        'aluno_form': aluno_form
    })





### CODIGO NAO PRONTO ABAIXO ###
def simple_upload(request):
    if request.method == 'POST':
        aluno_resource = AlunoResource()
        dataset = Dataset()
        new_alunos = request.FILES['myfile']

        imported_data = dataset.load(new_alunos.read())
        result = aluno_resource.import_data(dataset, dry_run=True)  # Test the data import

        if not result.has_errors():
            aluno_resource.import_data(dataset, dry_run=False)  # Actually import now

    return render(request, 'users/import.html')

class SignUp(generic.CreateView):
    form_class = PFEUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'

class Usuario(generic.DetailView):
    model = Aluno

def show_profile(request, pk):
    user = PFEUser.objects.get(pk=pk)
    user.profile.bio = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit...'
    user.profile.location = 'Sao Paulo'
    user.save()
    return HttpResponse("Tudo certo!")


# # Checa informação passada com credenciais do usuário
# @login_required
# def login(request):
#     if request.POST['funcao']=="estudante":
#         return HttpResponseRedirect(reverse('aluno', args={request.POST['uname']}))
#     elif request.POST['funcao']=="empresa": 
#         return HttpResponseRedirect(reverse('empresa', args={request.POST['uname']}))
#     elif request.POST['funcao']=="professor": 
#         return HttpResponseRedirect(reverse('professor', args={request.POST['uname']}))
#     else:
#         return HttpResponse("Algum erro")


# @login_required
# def alunos(request):
#     num_alunos = Aluno.objects.all().count() # Conta alunos
#     num_alunos_comp = Aluno.objects.filter(curso__exact='C').count() # Conta alunos computacao
#     context = {
#         'num_alunos': num_alunos,
#         'num_alunos_comp': num_alunos_comp,
#     }
#     # Nao existe mais
#     return render(request, 'alunos.html', context=context)
#     #<li><strong>Alunos:</strong> {{ num_alunos }}</li>
#     #<li><strong>Alunos de Computacao:</strong> {{ num_alunos_comp }}</li>

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
