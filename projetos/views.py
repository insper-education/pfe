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

from django.core.mail import send_mail
from django.conf import settings

from .models import Projeto, Empresa
from users.models import Aluno, Professor, Funcionario, Opcao

def email(aluno):
    subject = 'PFE : '+aluno.user.username
    message = ' '
    for o in Opcao.objects.filter(aluno=aluno):
        message += o.projeto.titulo+"\n"
    email_from = settings.EMAIL_HOST_USER
    recipient_list = ['pfeinsper@gmail.com',]
    send_mail( subject, message, email_from, recipient_list )

@login_required
def index(request):
    num_projetos = Projeto.objects.count()  # The 'all()' is implied by default.
    num_visits = request.session.get('num_visits', 0)     # Number of visits to this view, as counted in the session variable.
    request.session['num_visits'] = num_visits + 1
    context = {
        'num_projetos': num_projetos,
        'num_visits': num_visits,
    }
    return render(request, 'index.html', context=context)

class ProjetoDetailView(LoginRequiredMixin, generic.DetailView):
    model = Projeto

@login_required
def selecao(request):
    if request.method == 'POST':
        check_values = request.POST.getlist('selection')
        #if(len(check_values)<=5): return HttpResponse("Selecione ao menos 5 projetos")
        a = Aluno.objects.get(pk=request.user.pk)
        for p in Projeto.objects.all():
            if str(p.pk) in check_values:
                if len(a.opcoes.filter(pk=p.pk))==0:
                    Opcao.objects.create(aluno=a, projeto=p)
            else:
                if len(a.opcoes.filter(pk=p.pk))!=0:
                    Opcao.objects.filter(aluno=a, projeto=p).delete()
        email(a)
        return HttpResponse("Dados submetidos")
    else:
        return HttpResponse("Chamada irregular")

@login_required
def projetos(request):
    projeto_list = Projeto.objects.all()
    opcoes = Opcao.objects.filter(aluno=Aluno.objects.get(pk=request.user.pk)) 
    opcoes_list = []
    for i in opcoes:
        opcoes_list.append(i.projeto.pk)    
    context= {'projeto_list': projeto_list, 'opcoes_list': opcoes_list, }    
    return render(request, 'projetos/projetos.html', context)