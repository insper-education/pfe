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

@login_required
@transaction.atomic
def update_profile(request):
    if request.method == 'POST':
        pfeuser_form = PFEUserForm(request.POST, instance=request.user)
        aluno_form = AlunoForm(request.POST, instance=request.user.profile)
        if pfeuser_form.is_valid() and aluno_form.is_valid():
            pfeuser_form.save()
            aluno_form.save()
            messages.success(request, _('Your profile was successfully updated!'))
            return redirect('signup')
        else:
            messages.error(request, _('Please correct the error below.'))
    else:
        pfeuser_form = PFEUserForm(instance=request.user)
        aluno_form = AlunoForm(instance=request.user.profile)
    return render(request, 'users/profile.html', {
        'pfeuser_form': pfeuser_form,
        'aluno_form': aluno_form
    })

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
