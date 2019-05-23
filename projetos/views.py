# Desenvolvido para o Projeto Final de Engenharia
# Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
# Data: 15 de Maio de 2019

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

from .resources import ProjetoResource

def email(aluno, message):
    subject = 'PFE : '+aluno.user.username
    email_from = settings.EMAIL_HOST_USER
    recipient_list = ['pfeinsper@gmail.com',aluno.user.email,]
    return send_mail( subject, message, email_from, recipient_list, html_message=message, fail_silently=True, )

def create_message(aluno):
        message = '<br>\n'
        message += '&nbsp;&nbsp;Caro aluno: <b>'+aluno.user.first_name+" "+aluno.user.last_name+" ("+aluno.user.username+')</b>\n\n'
        message += '<br><br>\n\n'
        message += '&nbsp;&nbsp;Suas opções de projeto foram:<br>\n'
        message += '<ul>'
        for o in Opcao.objects.filter(aluno=aluno):
            message += ("&nbsp;"*4)+"<li>"+o.projeto.titulo+" ("+o.projeto.empresa.nome_empresa+")</li>\n"
        message += '</ul>'
        message += '<br>\n'+("&nbsp;"*12)+"atenciosamente, comitê PFE"
        message += '&nbsp;<br>\n'
        message += '&nbsp;<br>\n'
        return message

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
        if(len(check_values)<5): return HttpResponse("Selecione ao menos 5 projetos")
        aluno = Aluno.objects.get(pk=request.user.pk)
        for p in Projeto.objects.all():
            if str(p.pk) in check_values:
                if len(aluno.opcoes.filter(pk=p.pk))==0:
                    Opcao.objects.create(aluno=aluno, projeto=p)
            else:
                if len(aluno.opcoes.filter(pk=p.pk))!=0:
                    Opcao.objects.filter(aluno=aluno, projeto=p).delete()
        message = create_message(aluno)
        x = email(aluno,message)
        if(x!=1): message = "Algum problema de conexão, contacte: lpsoares@insper.edu.br"
        context= {'message': message,}    
        return render(request, 'projetos/submissao.html', context)
        #return HttpResponse("Dados submetidos<br><br><br>"+message)
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

# Exporta dados direto para o navegador no formato CSV
@login_required
def export(request):
    projeto_resource = ProjetoResource()
    dataset = projeto_resource.export()
    response = HttpResponse(dataset.csv, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="projetos.csv"'
    return response

# Exporta dados direto para o navegador no formato XLS
@login_required
def exportXLS(request):
    projeto_resource = ProjetoResource()
    dataset = projeto_resource.export()
    response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="projetos.xls"'
    return response

# 
@login_required
@permission_required('user.can_view_professor', login_url='/projetos/')
def histograma(request):
    projeto_list = Projeto.objects.all()
    opcoes_list = []
    for p in projeto_list:
        opcoes = Opcao.objects.filter(projeto=p)
        opcoes_list.append(len(opcoes))
    mylist = zip(projeto_list, opcoes_list)
    mylist = sorted(mylist, key=lambda x: x[1],reverse=True)

    context= {'mylist': mylist }    
    return render(request, 'projetos/histograma.html', context)

@login_required
@permission_required('user.can_view_professor', login_url='/projetos/')
def administracao(request):
    num_projetos = Projeto.objects.count()  # The 'all()' is implied by default.
    context = {
        'num_projetos': num_projetos,
    }
    return render(request, 'index_admin.html', context=context)
