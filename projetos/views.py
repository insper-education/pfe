from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from django.http import Http404
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import Aluno, Projeto, Opcao, Empresa, Professor, Funcionario

# Tela de login (precisa ser refeita com sessões)
def index(request):
    return render(request, 'index.html')

# Checa informação passada com credenciais do usuário
def login(request):
    if request.POST['funcao']=="estudante":
        return HttpResponseRedirect(reverse('aluno', args={request.POST['uname']}))
    elif request.POST['funcao']=="empresa": 
        return HttpResponseRedirect(reverse('empresa', args={request.POST['uname']}))
    elif request.POST['funcao']=="professor": 
        return HttpResponseRedirect(reverse('professor', args={request.POST['uname']}))
    else:
        return HttpResponse("Algum erro")


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


# Visualiza informaçõs do aluno e permite editar
def aluno(request, aluno_id):
    try:
        aluno = Aluno.objects.get(login=aluno_id)
    except Aluno.DoesNotExist:
        raise Http404("Aluno nao encontrado")
    return render(request, 'aluno.html', {'aluno': aluno})

# Visualiza informaçõs da empresa e permite editar
def empresa(request, empresa_id):
    try:
        empresa = Empresa.objects.get(login=empresa_id)
    except Empresa.DoesNotExist:
        raise Http404("Empresa nao encontrado")
    return render(request, 'empresa.html', {'empresa': empresa})

# Visualiza informaçõs do professor e permite editar
def professor(request, professor_id):
    try:
        professor = Professor.objects.get(login=professor_id)
    except Professor.DoesNotExist:
        raise Http404("Professor nao encontrado")
    return render(request, 'professor.html', {'professor': professor})

# Visualiza informaçõs do projeto e permite editar
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



# por enquanto o que está abaixo ainda é lixo
def detalhes_aluno(request, aluno_id):
    return HttpResponse("dados do aluno %s." % aluno_id)

def projetos_aluno(request, aluno_id):
    response = "Projetos do aluno %s.<BR>" % aluno_id
    projetos = Projeto.objects.all()
    output = ', '.join([p.abreviacao for p in projetos])
    return HttpResponse(response+output)

def detalhes(request):
    alunos_list = Aluno.objects.all()
    projetos_list = Projeto.objects.all()
    context = {
        'alunos_list': alunos_list,
        'projetos_list': projetos_list,
    }
    return render(request, 'index.html', context)


