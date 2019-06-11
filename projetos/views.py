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

from django.shortcuts import redirect

from django.core.mail import send_mail, EmailMessage
from django.conf import settings

from .models import Projeto, Empresa, Configuracao
from users.models import Aluno, Professor, Funcionario, Opcao

from .resources import ProjetosResource, OrganizacoesResource, OpcoesResource, UsuariosResource, AlunosResource, ProfessoresResource, ConfiguracaoResource

from tablib import Dataset, Databook

from django import template
register = template.Library()  # para o template



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
            message += ("&nbsp;"*4)+"<p>"+str(o.prioridade)+" - "+o.projeto.titulo+" ("+o.projeto.empresa.nome_empresa+")</p>\n"
        message += '</ul>'
        message += '<br><br>\n\n'
        message += '&nbsp;&nbsp;Suas áreas de interesse são:<br>\n'
        message += '<ul>'

        if aluno.inovacao_social: message += (("&nbsp;"*4)+"<li>Inovação Social</li>\n") 
        if aluno.ciencia_dos_dados: message += (("&nbsp;"*4)+"<li>Ciência de Dados</li>\n")
        if aluno.modelagem_3D: message += (("&nbsp;"*4)+"<li>Modelagem 3D</li>\n")
        if aluno.manufatura: message += (("&nbsp;"*4)+"<li>Manufatura</li>\n")
        if aluno.resistencia_dos_materiais: message += (("&nbsp;"*4)+"<li>Resistência dos Materiais</li>\n")
        if aluno.modelagem_de_sistemas: message += (("&nbsp;"*4)+"<li>Modelagem de Sistemas</li>\n")
        if aluno.controle_e_automacao: message += (("&nbsp;"*4)+"<li>Controle e Automação</li>\n")
        if aluno.termodinamica: message += (("&nbsp;"*4)+"<li>Termodinâmica</li>\n")
        if aluno.fluidodinamica: message += (("&nbsp;"*4)+"<li>Fluidodinâmica</li>\n")
        if aluno.eletronica_digital: message += (("&nbsp;"*4)+"<li>Eletrônica Digital</li>\n")
        if aluno.programacao: message += (("&nbsp;"*4)+"<li>Programação</li>\n")
        if aluno.inteligencia_artificial: message += (("&nbsp;"*4)+"<li>Inteligência Artificial</li>\n")
        if aluno.banco_de_dados: message += (("&nbsp;"*4)+"<li>Banco de Dados</li>\n")
        if aluno.computacao_em_nuvem: message += (("&nbsp;"*4)+"<li>Computação em Nuvem</li>\n")
        if aluno.visao_computacional: message += (("&nbsp;"*4)+"<li>Visão Computacional</li>\n")
        if aluno.computacao_de_alto_desempenho: message += (("&nbsp;"*4)+"<li>Computação de Alto Desempenho</li>\n")
        if aluno.robotica: message += (("&nbsp;"*4)+"<li>Robótica</li>\n")
        if aluno.realidade_virtual_aumentada: message += (("&nbsp;"*4)+"<li>Realidade Virtual e Aumentada</li>\n")
        if aluno.protocolos_de_comunicacao: message += (("&nbsp;"*4)+"<li>Protocolos de Comunicação</li>\n")
        if aluno.eficiencia_energetica: message += (("&nbsp;"*4)+"<li>Eficiência Energética</li>\n")
        if aluno.administracao_economia_financas: message += (("&nbsp;"*4)+"<li>Administração, Economia e Finanças</li>\n")

        message += '</ul>'
        message += '<br>\n'
        message += '<br>\n'+("&nbsp;"*12)+"atenciosamente, comitê PFE"
        message += '&nbsp;<br>\n'
        message += '&nbsp;<br>\n'
        return message

@login_required
def index(request):
    if Configuracao.objects.all().first().manutencao:
        return render(request, 'projetos/manutencao.html')
    num_projetos = Projeto.objects.count()  # The 'all()' is implied by default.
    num_visits = request.session.get('num_visits', 0)     # Number of visits to this view, as counted in the session variable.
    request.session['num_visits'] = num_visits + 1
    context = {
        'num_projetos': num_projetos,
        'num_visits': num_visits,
    }
    return render(request, 'index_aluno.html', context=context)
    

class ProjetoDetailView(LoginRequiredMixin, generic.DetailView):
    model = Projeto

@login_required
def projetos(request):
    warnings=""
    projeto_list = Projeto.objects.all()
    if request.method == 'POST':
        prioridade = {}
        for p in projeto_list:
            check_values = request.POST.get('selection'+str(p.pk),0)
            prioridade[p.pk] = check_values
        for i in range(1,len(Projeto.objects.all())+1):
            if i<6 and list(prioridade.values()).count(str(i))==0:
                warnings += "Nenhum projeto com prioridade "+str(i)+"\n"
            if list(prioridade.values()).count(str(i))>1:
                warnings += "Mais de um projeto com prioridade "+str(i)+"\n"
        if warnings=="":
            aluno = Aluno.objects.get(pk=request.user.pk)
            for p in projeto_list:
                if prioridade[p.pk]!="0":
                    if len(aluno.opcoes.filter(pk=p.pk))==0:
                        Opcao.objects.create(aluno=aluno, projeto=p, prioridade=int(prioridade[p.pk]))
                    elif Opcao.objects.get(aluno=aluno, projeto=p).prioridade != int(prioridade[p.pk]):
                        opc = Opcao.objects.get(aluno=aluno, projeto=p)
                        opc.prioridade = int(prioridade[p.pk])
                        opc.save()
                else:
                    if len(aluno.opcoes.filter(pk=p.pk))!=0:
                        Opcao.objects.filter(aluno=aluno, projeto=p).delete()
            message = create_message(aluno)
            x = email(aluno,message)
            if(x!=1): message = "Algum problema de conexão, contacte: lpsoares@insper.edu.br"
            context= {'message': message,}    
            return render(request, 'projetos/submissao.html', context)
        else:
            context= {'warnings': warnings,}    
            return render(request, 'projetos/projetosincompleto.html', context)
    else:
        opcoes_list = Opcao.objects.filter(aluno=Aluno.objects.get(pk=request.user.pk)) 
        # opcoes = Opcao.objects.filter(aluno=Aluno.objects.get(pk=request.user.pk)) 
        # opcoes_list = []
        # for i in opcoes:
        #     opcoes_list.append(i.projeto.pk)
        configuracao = Configuracao.objects.all().first
        context= {
            'projeto_list': projeto_list,
            'opcoes_list': opcoes_list,
            # 'opcoes_list': opcoes_list,
            'configuracao': configuracao,
            'warnings': warnings,
        }
        return render(request, 'projetos/projetos.html', context)

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
    return render(request, 'index_admin.html')

@login_required
@permission_required('user.can_view_professor', login_url='/projetos/')
def professor(request):
    return render(request, 'index_professor.html')

@login_required
@permission_required('user.can_view_professor', login_url='/projetos/')
def completo(request, pk):
    projeto = Projeto.objects.filter(pk=pk).first()  # acho que tem de ser get
    opcoes = Opcao.objects.filter(projeto=projeto) 
    context = {
        'projeto': projeto,
        'opcoes': opcoes,
    }
    return render(request, 'projetos/projeto_completo.html', context=context)

@login_required
@permission_required('user.can_view_professor', login_url='/projetos/')
def areas(request):

    inovacao_social = Aluno.objects.filter(inovacao_social=True).count()
    ciencia_dos_dados = Aluno.objects.filter(ciencia_dos_dados=True).count()
    modelagem_3D = Aluno.objects.filter(modelagem_3D=True).count()
    manufatura = Aluno.objects.filter(manufatura=True).count()
    resistencia_dos_materiais = Aluno.objects.filter(resistencia_dos_materiais=True).count()
    modelagem_de_sistemas = Aluno.objects.filter(modelagem_de_sistemas=True).count()
    controle_e_automacao = Aluno.objects.filter(controle_e_automacao=True).count()
    termodinamica = Aluno.objects.filter(termodinamica=True).count()
    fluidodinamica = Aluno.objects.filter(fluidodinamica=True).count()
    eletronica_digital = Aluno.objects.filter(eletronica_digital=True).count()
    programacao = Aluno.objects.filter(programacao=True).count()
    inteligencia_artificial = Aluno.objects.filter(inteligencia_artificial=True).count()
    banco_de_dados = Aluno.objects.filter(banco_de_dados=True).count()
    computacao_em_nuvem = Aluno.objects.filter(computacao_em_nuvem=True).count()
    visao_computacional = Aluno.objects.filter(visao_computacional=True).count()
    computacao_de_alto_desempenho = Aluno.objects.filter(computacao_de_alto_desempenho=True).count()
    robotica = Aluno.objects.filter(robotica=True).count()
    realidade_virtual_aumentada = Aluno.objects.filter(realidade_virtual_aumentada=True).count()
    protocolos_de_comunicacao = Aluno.objects.filter(protocolos_de_comunicacao=True).count()
    eficiencia_energetica = Aluno.objects.filter(eficiencia_energetica=True).count()
    administracao_economia_financas =Aluno.objects.filter(administracao_economia_financas=True).count()

    context= {
        'inovacao_social':inovacao_social,
        'ciencia_dos_dados':ciencia_dos_dados,
        'modelagem_3D':modelagem_3D,
        'manufatura':manufatura,
        'resistencia_dos_materiais':resistencia_dos_materiais,
        'modelagem_de_sistemas':modelagem_de_sistemas,
        'controle_e_automacao':controle_e_automacao,
        'termodinamica':termodinamica,
        'fluidodinamica': fluidodinamica,
        'eletronica_digital':eletronica_digital,
        'programacao':programacao,
        'inteligencia_artificial':inteligencia_artificial,
        'banco_de_dados':banco_de_dados,
        'computacao_em_nuvem':computacao_em_nuvem,
        'visao_computacional': visao_computacional,
        'computacao_de_alto_desempenho':computacao_de_alto_desempenho,
        'robotica':robotica,
        'realidade_virtual_aumentada':realidade_virtual_aumentada,
        'protocolos_de_comunicacao':protocolos_de_comunicacao,
        'eficiencia_energetica':eficiencia_energetica,
        'administracao_economia_financas':administracao_economia_financas,
    }
    return render(request, 'projetos/areas.html', context)

@login_required
@permission_required('user.can_view_professor', login_url='/projetos/')
def organizacoes(request):
    organizacoes_list = Empresa.objects.all()
    context= {'organizacoes_list': organizacoes_list,}
    return render(request, 'projetos/organizacoes.html', context)

@login_required
@permission_required('user.can_view_professor', login_url='/projetos/')
def organizacao(request, login): #acertar isso para pk
    organization = Empresa.objects.filter(login=login).first()  # acho que tem de ser get
    context = {
        'organization': organization,
    }
    return render(request, 'projetos/organizacao_completo.html', context=context)

# Exporta dados direto para o navegador nos formatos CSV, XLS e JSON
@login_required
@permission_required('user.can_view_professor', login_url='/projetos/')
def export(request, modelo, formato):
    if(modelo=="projetos"):
        resource = ProjetosResource()
    elif(modelo=="organizacoes"):
        resource = OrganizacoesResource()
    elif(modelo=="opcoes"):
        resource = OpcoesResource()
    elif(modelo=="usuarios"):
        resource = UsuariosResource()
    elif(modelo=="alunos"):
        resource = AlunosResource()
    elif(modelo=="professores"):
        resource = ProfessoresResource()
    elif(modelo=="configuracao"):
        resource = ConfiguracaoResource()
    else:
        return HttpResponse("Chamada irregular : Base de dados desconhecida = "+modelo)
    dataset = resource.export()
    if(formato=="xls" or formato=="xlsx"):
        response = HttpResponse(dataset.xlsx, content_type='application/ms-excel')
        formato="xlsx"
    elif(formato=="json"):
        response = HttpResponse(dataset.json, content_type='application/json')
    elif(formato=="csv"):
        response = HttpResponse(dataset.csv, content_type='text/csv')
    else:
        return HttpResponse("Chamada irregular : Formato desconhecido = "+formato)
    response['Content-Disposition'] = 'attachment; filename="'+modelo+'.'+formato+'"'
    return response

def create_backup():
    databook = Databook()

    data_projetos = ProjetosResource().export()
    data_projetos.title = "Projetos"
    databook.add_sheet(data_projetos)

    data_organizacoes = OrganizacoesResource().export()
    data_organizacoes.title = "Organizacoes"
    databook.add_sheet(data_organizacoes)

    data_opcoes = OpcoesResource().export()
    data_opcoes.title = "Opcoes"
    databook.add_sheet(data_opcoes)

    data_usuarios = UsuariosResource().export()
    data_usuarios.title = "Usuarios"
    databook.add_sheet(data_usuarios)

    data_alunos = AlunosResource().export()
    data_alunos.title = "Alunos"
    databook.add_sheet(data_alunos)

    data_professores = ProfessoresResource().export()
    data_professores.title = "Professores"
    databook.add_sheet(data_professores)

    data_configuracao = ConfiguracaoResource().export()
    data_configuracao.title = "Configuracao"
    databook.add_sheet(data_configuracao)

    return databook

@login_required
@permission_required('user.can_view_professor', login_url='/projetos/')
def backup(request, formato):
    databook = create_backup()
    if(formato=="xls" or formato=="xlsx"):
        response = HttpResponse(databook.xlsx, content_type='application/ms-excel')
        formato="xlsx"
    elif(formato=="json"):
        response = HttpResponse(databook.json, content_type='application/json')
    else:
        return HttpResponse("Chamada irregular : Formato desconhecido = "+formato)
    response['Content-Disposition'] = 'attachment; filename="backup.'+formato+'"'
    return response

@login_required
@permission_required('user.can_view_professor', login_url='/projetos/')
def email_backup(request):
    subject = 'BACKUP PFE'
    message = "Backup PFE"
    email_from = settings.EMAIL_HOST_USER
    recipient_list = ['pfeinsper@gmail.com','lpsoares@gmail.com',]
    mail = EmailMessage(subject, message, email_from, recipient_list)
    databook = create_backup()
    mail.attach("backup.xlsx", databook.xlsx, 'application/ms-excel')
    mail.attach("backup.json", databook.json, 'application/json')
    mail.send()
    return HttpResponse("E-mail enviado.")

@login_required
@permission_required('user.can_view_professor', login_url='/projetos/')
def servico(request):
    configuracao = Configuracao.objects.all().first()
    if request.method == 'POST':
        check_values = request.POST.getlist('selection')
        if 'manutencao' in check_values:
            print("true")
            configuracao.manutencao = True;
        else:
            print("false")
            configuracao.manutencao = False;
        configuracao.save()
        return redirect('/projetos/administracao/')
    else:
        context= {'manutencao': configuracao.manutencao,}    
        return render(request, 'projetos/servico.html', context)
