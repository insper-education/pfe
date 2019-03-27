import datetime
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.template import loader
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .forms import AlunoForm, AlunoForm2

from .models import Projeto, Opcao, Empresa
from users.models import Aluno, Professor, Funcionario

# Tela de login (precisa ser refeita com sessões)
@login_required
def index(request):
    num_projetos = Projeto.objects.count()  # The 'all()' is implied by default.
    
    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_projetos': num_projetos,
        'num_visits': num_visits,
    }
    return render(request, 'index.html', context=context)

# Checa informação passada com credenciais do usuário
@login_required
def login(request):
    if request.POST['funcao']=="estudante":
        return HttpResponseRedirect(reverse('aluno', args={request.POST['uname']}))
    elif request.POST['funcao']=="empresa": 
        return HttpResponseRedirect(reverse('empresa', args={request.POST['uname']}))
    elif request.POST['funcao']=="professor": 
        return HttpResponseRedirect(reverse('professor', args={request.POST['uname']}))
    else:
        return HttpResponse("Algum erro")

@login_required
def alunos(request):
    # Conta alunos
    num_alunos = Aluno.objects.all().count()
    
    # Conta alunos computacao
    num_alunos_comp = Aluno.objects.filter(curso__exact='C').count()
    
    context = {
        'num_alunos': num_alunos,
        'num_alunos_comp': num_alunos_comp,
    }

    return render(request, 'alunos.html', context=context)

class AlunoListView(LoginRequiredMixin, generic.ListView):
    model = Aluno
    paginate_by = 2     # http://127.0.0.1:8000/projetos/alunos/?page=2
    #context_object_name = 'my_book_list'   # your own name for the list as a template variable
    #queryset = Book.objects.filter(title__icontains='war')[:5] # Get 5 books containing the title war
    #template_name = 'books/my_arbitrary_template_name_list.html'  # Specify your own template name/location
    #def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        #context = super(BookListView, self).get_context_data(**kwargs)
        # Create any data and add it to the context
        #context['some_data'] = 'This is just some data'
        #return context

class AlunoDetailView(LoginRequiredMixin, generic.DetailView):
    model = Aluno

# Visualiza informaçõs do aluno e permite editar
@login_required
def aluno(request, aluno_id):
    try:
        aluno = Aluno.objects.get(login=aluno_id)
    except Aluno.DoesNotExist:
        raise Http404("Aluno nao encontrado")
    return render(request, 'aluno.html', {'aluno': aluno})

# Visualiza informaçõs da empresa e permite editar
@login_required
def empresa(request, empresa_id):
    try:
        empresa = Empresa.objects.get(login=empresa_id)
    except Empresa.DoesNotExist:
        raise Http404("Empresa nao encontrado")
    return render(request, 'empresa.html', {'empresa': empresa})

# Visualiza informaçõs do professor e permite editar
@login_required
def professor(request, professor_id):
    try:
        professor = Professor.objects.get(login=professor_id)
    except Professor.DoesNotExist:
        raise Http404("Professor nao encontrado")
    return render(request, 'professor.html', {'professor': professor})

# Visualiza informaçõs do projeto e permite editar
@login_required
def projeto(request):
    if request.POST['acao']=="editar":
        projeto_id = request.POST['projeto']
        try:
            projeto = Projeto.objects.get(pk=projeto_id)
        except Projeto.DoesNotExist:
            raise Http404("Projeto nao encontrado")
        return render(request, 'projeto.html', {'projeto': projeto})
    else:
        return render(request, 'projeto.html')

class ProjetoDetailView(LoginRequiredMixin, generic.DetailView):
    model = Projeto



class ProjetosByUserListView(PermissionRequiredMixin, LoginRequiredMixin,generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = Projeto
    permission_required = ('projetos.altera_empresa', 'projetos.altera_professor')
    template_name ='projetos/projeto_list_user.html'
    paginate_by = 10
    
    def get_queryset(self):
        return Projeto.objects.filter(usuario=self.request.user).filter(disponivel__exact=True).order_by('titulo')


# por enquanto o que está abaixo ainda é lixo
@login_required
def detalhes_aluno(request, aluno_id):
    return HttpResponse("dados do aluno %s." % aluno_id)

@login_required
@permission_required('projetos.altera_empresa')
@permission_required('projetos.altera_professor')
def projetos_aluno(request, aluno_id):
    response = "Projetos do aluno %s.<BR>" % aluno_id
    projetos = Projeto.objects.all()
    output = ', '.join([p.abreviacao for p in projetos])
    return HttpResponse(response+output)

@login_required
def detalhes(request):
    alunos_list = Aluno.objects.all()
    projetos_list = Projeto.objects.all()
    context = {
        'alunos_list': alunos_list,
        'projetos_list': projetos_list,
    }
    return render(request, 'index.html', context)

@login_required
def cria_usuarios(request):
    # Create user and save to the database
    user = User.objects.create_user('myusername', 'myemail@crazymail.com', 'mypassword')

    # Update fields and then save again
    user.first_name = 'John'
    user.last_name = 'Citizen'
    user.save()


def nascimento(request, pk):
    aluno_instance = get_object_or_404(Aluno, login=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = AlunoForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            aluno_instance.nascimento = form.cleaned_data['nascimento']
            aluno_instance.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('my-proj') )

    # If this is a GET (or any other method) create the default form.
    else:
        #proposed_nascimento_date = datetime.date.today() - datetime.timedelta(weeks=3)
        proposed_nascimento_date = aluno_instance.nascimento
        #form = AlunoForm(initial={'nascimento': proposed_nascimento_date})
        form = AlunoForm2(initial={'nascimento': proposed_nascimento_date})
        

    context = {
        'form': form,
        'aluno_instance': aluno_instance,
    }

    return render(request, 'projetos/alunos_nascimento.html', context)


class ProjetoCreate(CreateView):
    model = Projeto
    fields = '__all__'
    initial = {'ano': 2019}

class ProjetoUpdate(UpdateView):
    model = Projeto
    fields = ['titulo', 'abreviacao', 'descricao', 'ano']

class ProjetoDelete(DeleteView):
    model = Projeto
    success_url = reverse_lazy('my-proj')

