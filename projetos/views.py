# Desenvolvido para o Projeto Final de Engenharia
# Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
# Data: 15 de Maio de 2019

from django.utils import timezone

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

from .models import Projeto, Empresa, Configuracao, Disciplina, Evento
from users.models import PFEUser, Aluno, Professor, Parceiro, Opcao

from .resources import ProjetosResource, OrganizacoesResource, OpcoesResource, UsuariosResource, AlunosResource, ProfessoresResource, ConfiguracaoResource, DisciplinasResource

import re #regular expression (para o import)
from tablib import Dataset, Databook
import os
import tablib
from import_export import resources


# Para gerar o PDF
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

from django.core.exceptions import PermissionDenied

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

    configuracao = Configuracao.objects.all().first
    context = {
        'num_projetos': num_projetos,
        'num_visits': num_visits,
        'configuracao': configuracao,
    }
    return render(request, 'index_aluno.html', context=context)
    

class ProjetoDetailView(LoginRequiredMixin, generic.DetailView):
    model = Projeto

@login_required
def projetos(request):
    warnings=""
    projeto_list = Projeto.objects.all()
    if request.method == 'POST':
        configuracao = Configuracao.objects.all().first()
        if timezone.now() > configuracao.prazo:
           return HttpResponse("Prazo para seleção de projetos vencido!") #<br>Hora atual:  "+str(timezone.now())+"<br>Hora limite:"+str(configuracao.prazo)
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
            return render(request, 'projetos/confirmacao.html', context)
        else:
            context= {'warnings': warnings,}    
            return render(request, 'projetos/projetosincompleto.html', context)
    else:
        opcoes_list = Opcao.objects.filter(aluno=Aluno.objects.get(pk=request.user.pk)) 
        configuracao = Configuracao.objects.all().first
        context= {
            'projeto_list': projeto_list,
            'opcoes_list': opcoes_list,
            'configuracao': configuracao,
            'warnings': warnings,
        }
        return render(request, 'projetos/projetos.html', context)

# 
@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def histograma(request):
    configuracao = Configuracao.objects.all().first()
    opcoes_list = []
    projeto_list = Projeto.objects.all()
    for p in projeto_list:
        opcoes = Opcao.objects.filter(projeto=p)
        opcoes_alunos = opcoes.filter(aluno__user__tipo_de_usuario=1)
        opcoes_validas = opcoes_alunos.filter(aluno__anoPFE=configuracao.ano).filter(aluno__semestrePFE=configuracao.semestre)
        count = 0
        for o in opcoes_validas:
            if o.prioridade <= 5:
                count += 1
        opcoes_list.append(count)
    mylist = zip(projeto_list, opcoes_list)
    mylist = sorted(mylist, key=lambda x: x[1],reverse=True)
    context= {'mylist': mylist }    
    return render(request, 'projetos/histograma.html', context)

#Busca proxima opcao do aluno
def getNextOpcao(n,opcoes):
    n+=1
    lopcoes = opcoes.filter(prioridade=n)
    num_total_projetos = Projeto.objects.all().count() # Depois filtrar melhor
    while (len(lopcoes)==0) and (n<=num_total_projetos):
        n+=1
        lopcoes = opcoes.filter(prioridade=n)
    if len(lopcoes)>0:
        return n
    else:
        return 0

#Pega a opcao de preferencia do aluno se possivel
def getOpcao(n,opcoes, min_group, max_group, projetos_ajustados):
    configuracao = Configuracao.objects.all().first()
    opcao = opcoes.get(prioridade=n)
    while True:
        opcoesp = Opcao.objects.filter(projeto=opcao.projeto)
        opcoesp_alunos = opcoesp.filter(aluno__user__tipo_de_usuario=1)
        opcoesp_validas = opcoesp_alunos.filter(aluno__anoPFE=configuracao.ano).filter(aluno__semestrePFE=configuracao.semestre)
        if len(opcoesp_validas) >= min_group: #Verifica se o projeto tem numero minimo de alunos aplicando
            # checa se alunos no projeto ja tem CR maior dos que ja estao no momento no projeto
            crh = 0  
            for ov in projetos_ajustados[opcao.projeto]:
                if ov.aluno.cr > opcao.aluno.cr:
                    crh += 1 #conta cada aluno com cr maior que o aluno sendo alocado
            if crh < max_group:
                break #se tudo certo retorna esse projeto mesmo
        # Nao achou tentando outra opcao
        nx = getNextOpcao(n,opcoes)
        if(nx!=0):
            opcao = opcoes.get(prioridade=nx)
            break
        else:  # caso nao encontre mais nenhuma opcao valida
            return None
    return opcao

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def propor(request):
    ############################################
    ## COLOCAR ESSE VALOR ACESSIVEL NO SISTEMA #
    ############################################
    pref_pri_cr = 0.1  # Ficar longe da prioridade tem um custo de 5% na selecao do projeto

    configuracao = Configuracao.objects.all().first()
    projeto_list = []
    opcoes_list = []
    projetos = Projeto.objects.all()
    if request.method == 'POST':
        min_group = int(request.POST.get('min',0))
        max_group = int(request.POST.get('max',5))
        projetos_ajustados = {}
        alunos = Aluno.objects.filter(user__tipo_de_usuario=1).filter(anoPFE=configuracao.ano).filter(semestrePFE=configuracao.semestre)
        
        #Checa se o CR de todos os alunos esta coreto
        for aluno in alunos:
            if(aluno.cr < 5.0):
                return HttpResponse("Aluno: "+aluno.user.first_name+" "+aluno.user.last_name+" ("+aluno.user.username+') com CR = '+str(aluno.cr))

        #Cria Lista para todos os projetos
        for p in projetos:
            projetos_ajustados[p]=[]

        #Posiciona os alunos nas suas primeiras opcoes (supondo projeto permitir)
        for aluno in alunos:
            opcoes = Opcao.objects.filter(aluno=aluno)
            if len(opcoes) >= 5: # checa se aluno preencheu formulario
                opcoes1 = getOpcao(1,opcoes,min_group,max_group,projetos_ajustados) #busca nas opcoes do aluno
                projetos_ajustados[opcoes1.projeto].append(opcoes1)
        
        #Posiciona os alunos nas suas melhores opcoes sem estourar o tamanho do grupo
        balanceado = False
        count = 200
        menor_grupo=1 # usado para elimnar primeiro grupos de 1, depois de 2, etc
        while (not(balanceado)) and (count>0):
            balanceado = True
            
            balanceado_max = False
            # Removendo alunos de grupos superlotados
            while (not(balanceado_max)) and (count>0):
                count -= 1 # para nao correr o risco de um loop infinito
                balanceado_max = True
                for pr, ops in projetos_ajustados.items():
                    if len(ops) > max_group: # Checa se projeto esta superlotado
                        remove_opcao = None
                        for o in range(len(ops)):
                            if(ops[o].prioridade < 5): #Nao move aluno para prioridade menor que 5 (REVER)
                                if(remove_opcao is None):
                                    remove_opcao = ops[o]
                                elif( (ops[o].aluno.cr * (1-((ops[o].prioridade-1)*pref_pri_cr)))  <  (remove_opcao.aluno.cr * (1-((remove_opcao.prioridade-1)*pref_pri_cr) ) ) ):
                                    remove_opcao = ops[o]
                        if remove_opcao is not None:
                            opcoes = Opcao.objects.filter(aluno=remove_opcao.aluno)
                            no = getNextOpcao(remove_opcao.prioridade,opcoes)
                            if no != 0:
                                op2 = getOpcao(no,opcoes,min_group,max_group,projetos_ajustados) #busca nas opcoes do aluno
                                if op2 != None:
                                    balanceado_max = False
                                    balanceado = False
                                    menor_grupo=1
                                    projetos_ajustados[pr].remove(remove_opcao)
                                    projetos_ajustados[op2.projeto].append(op2)
                                    #print("Movendo(a) "+remove_opcao.aluno.user.first_name.lower()+" (DE): "+pr.titulo+" (PARA):"+op2.projeto.titulo)
            
            # Realocando alunos de grupos muito pequenos (um aluno por vez)
            for pr, ops in projetos_ajustados.items():
                remove_opcao = None
                remove_projeto = None
                if (len(ops) > 0) and (len(ops) <= menor_grupo ):
                    for o in range(len(ops)):
                        if(remove_opcao is None):
                            if(ops[o].prioridade < 5):  # So para não tirar aluno com prioridade maior que 5
                                remove_opcao = ops[o]
                                remove_projeto = pr
                        elif(ops[o].aluno.cr < remove_opcao.aluno.cr) and (ops[o].prioridade < 5):
                            remove_opcao = ops[o]
                            remove_projeto = pr
                if remove_opcao is not None:
                    opcoes = Opcao.objects.filter(aluno=remove_opcao.aluno)
                    no = getNextOpcao(remove_opcao.prioridade,opcoes)
                    if no != 0:
                        op2 = getOpcao(no,opcoes,min_group,max_group,projetos_ajustados) #busca nas opcoes do aluno
                        if op2 != None:
                            balanceado = False
                            menor_grupo=1
                            projetos_ajustados[remove_projeto].remove(remove_opcao)
                            projetos_ajustados[op2.projeto].append(op2)
                            #print("Movendo(b) "+remove_opcao.aluno.user.first_name.lower()+" (DE): "+remove_projeto.titulo+" (PARA):"+op2.projeto.titulo)

            if (menor_grupo<min_group) and balanceado:  # caso todos os grupos com menor_grupo ja foram
                menor_grupo += 1
                balanceado = False


        #Cria lista para enviar para o template html
        for pr, ops in projetos_ajustados.items():
            if len(ops) > 0 :
                projeto_list.append(pr)
                opcoes_list.append(ops)
        mylist = zip(projeto_list, opcoes_list)
    else:
        for p in projetos:
            opcoes = Opcao.objects.filter(projeto=p)
            opcoes_alunos = opcoes.filter(aluno__user__tipo_de_usuario=1)
            opcoes_validas = opcoes_alunos.filter(aluno__anoPFE=configuracao.ano).filter(aluno__semestrePFE=configuracao.semestre)
            opcoes1 = opcoes_validas.filter(prioridade=1)
            if len(opcoes1) > 0 :
                projeto_list.append(p)
                opcoes_list.append(opcoes1)
        mylist = zip(projeto_list, opcoes_list)
    context= {
        'mylist': mylist,
        'length': len(projeto_list),
    }
    return render(request, 'projetos/propor.html', context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def administracao(request):
    return render(request, 'index_admin.html')

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def professor(request):
    return render(request, 'index_professor.html')

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def completo(request, pk):
    projeto = Projeto.objects.filter(pk=pk).first()  # acho que tem de ser get
    opcoes = Opcao.objects.filter(projeto=projeto) 
    configuracao = Configuracao.objects.all().first
    context = {
        'projeto': projeto,
        'opcoes': opcoes,
        'configuracao': configuracao,
    }
    return render(request, 'projetos/projeto_completo.html', context=context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
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
@permission_required("users.altera_professor", login_url='/projetos/')
def organizacoes(request):
    organizacoes_list = Empresa.objects.all()
    context= {'organizacoes_list': organizacoes_list,}
    return render(request, 'projetos/organizacoes.html', context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def organizacao(request, login): #acertar isso para pk
    organization = Empresa.objects.filter(login=login).first()  # acho que tem de ser get
    context = {
        'organization': organization,
    }
    return render(request, 'projetos/organizacao_completo.html', context=context)

# Exporta dados direto para o navegador nos formatos CSV, XLS e JSON
@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
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
@permission_required("users.altera_professor", login_url='/projetos/')
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
@permission_required("users.altera_professor", login_url='/projetos/')
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
@permission_required("users.altera_professor", login_url='/projetos/')
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


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result)
    if not pdf.err:
        return result
        #return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

# Gera relatorios
@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def relatorio(request, modelo, formato):
    configuracao = Configuracao.objects.all().first()
    
    if(modelo=="projetos"):
        context = {
            'projetos': Projeto.objects.all(),
            'configuracao': configuracao,
        }
        if(formato=="html" or formato=="HTML"):
            return render(request, 'projetos/relatorio_projetos.html', context)
        elif(formato=="pdf" or formato=="PDF"):
            pdf = render_to_pdf('projetos/relatorio_projetos.html', context)
            return HttpResponse(pdf.getvalue(), content_type='application/pdf')

    elif(modelo=="alunos"):
        context = {
            'alunos': Aluno.objects.all().filter(user__tipo_de_usuario=1).filter(anoPFE=configuracao.ano).filter(semestrePFE=configuracao.semestre),
            'configuracao': configuracao,
        }
        if(formato=="html" or formato=="HTML"):
            return render(request, 'projetos/relatorio_alunos.html', context)
        elif(formato=="pdf" or formato=="PDF"):
            pdf = render_to_pdf('projetos/relatorio_alunos.html', context)
            return HttpResponse(pdf.getvalue(), content_type='application/pdf')
    else:
        return HttpResponse("Chamada irregular : Base de dados desconhecida = "+modelo)

    return HttpResponse("Chamada irregular : Formato desconhecido = "+formato)



@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def relatorio_backup(request):
    subject = 'RELATÓRIOS PFE'
    message = "Relatórios PFE"
    email_from = settings.EMAIL_HOST_USER
    recipient_list = ['pfeinsper@gmail.com','lpsoares@gmail.com',]
    mail = EmailMessage(subject, message, email_from, recipient_list)
    configuracao = Configuracao.objects.all().first()
    context = {
        'projetos': Projeto.objects.all(),
        'alunos': Aluno.objects.all().filter(user__tipo_de_usuario=1).filter(anoPFE=configuracao.ano).filter(semestrePFE=configuracao.semestre),
        'configuracao': configuracao,
    }
    pdf_proj = render_to_pdf('projetos/relatorio_projetos.html', context)
    pdf_alun = render_to_pdf('projetos/relatorio_alunos.html', context)
    mail.attach("projetos.pdf", pdf_proj.getvalue(), 'application/pdf')
    mail.attach("alunos.pdf", pdf_alun.getvalue(), 'application/pdf')
    mail.send()
    return HttpResponse("E-mail enviado.")

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def fechados(request):
    configuracao = Configuracao.objects.all().first()
    projetos = []
    alunos_list = []
    prioridade_list = []
    nalunos = 0
    qtd_prioridades = [0,0,0,0,0,0]   # para grafico de pizza no final

    for p in Projeto.objects.all():
        #alunosPFE = Aluno.objects.filter(alocado=p)
        alunosPFE = Aluno.objects.filter(alocacao__projeto=p)
        if len(alunosPFE) > 0 :
            projetos.append(p)
            alunos_list.append(alunosPFE)
            nalunos += len(alunosPFE)
            alunos = []
            prioridades = []
            for aluno in alunosPFE:
                opcoes = Opcao.objects.filter(projeto=p)
                opcoes_alunos = opcoes.filter(aluno__user__tipo_de_usuario=1)
                opcoes1 = opcoes_alunos.filter(aluno__alocado=p)
                opcoes2 = opcoes1.filter(aluno=aluno)
                if len(opcoes2)==1:
                    prioridade = opcoes2.first().prioridade
                    prioridades.append(prioridade)
                    qtd_prioridades[prioridade-1] += 1
                else:
                    prioridades.append(0)
            prioridade_list.append( zip(alunosPFE,prioridades) )
    mylist = zip(projetos, prioridade_list)
    context= {
        'mylist': mylist,
        'length': len(projetos),
        'nalunos': nalunos,
        'qtd_prioridades': qtd_prioridades,
    }
    return render(request, 'projetos/fechados.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def todos(request):
    configuracao = Configuracao.objects.all().first()
    projetos = []
    alunos_list = []
    prioridade_list = []
    nalunos = 0
    qtd_prioridades = [0,0,0,0,0,0]   # para grafico de pizza no final

    for p in Projeto.objects.all():
        alunosPFE = Aluno.objects.filter(alocado=p)
        if len(alunosPFE) > 0 :
            projetos.append(p)
            alunos_list.append(alunosPFE)
            nalunos += len(alunosPFE)
            alunos = []
            prioridades = []
            for aluno in alunosPFE:
                opcoes = Opcao.objects.filter(projeto=p)
                opcoes_alunos = opcoes.filter(aluno__user__tipo_de_usuario=1)
                opcoes_validas = opcoes_alunos.filter(aluno__anoPFE=configuracao.ano).filter(aluno__semestrePFE=configuracao.semestre)
                opcoes1 = opcoes_validas.filter(aluno__alocado=p)
                opcoes2 = opcoes1.filter(aluno=aluno)
                if len(opcoes2)==1:
                    prioridade = opcoes2.first().prioridade
                    prioridades.append(prioridade)
                    qtd_prioridades[prioridade-1] += 1
                else:
                    prioridades.append(0)
            prioridade_list.append( zip(alunosPFE,prioridades) )
    mylist = zip(projetos, prioridade_list)
    context= {
        'mylist': mylist,
        'length': len(projetos),
        'nalunos': nalunos,
        'qtd_prioridades': qtd_prioridades,
    }
    return render(request, 'projetos/todos.html', context)


# https://simpleisbetterthancomplex.com/packages/2016/08/11/django-import-export.html
@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def carrega(request, dado):
    if request.method == 'POST':
        
        dataset = tablib.Dataset()

        if dado=="disciplinas":
            resource = DisciplinasResource()
        if dado=="alunos":
            resource = AlunosResource()
        else:
            raise Http404

        new_data = request.FILES['arquivo'].readlines()
        entradas = ""
        for i in new_data:
            string = i.decode("utf-8")
            entradas += re.sub('[^A-Za-z0-9À-ÿ, \r\n@._]+','', string) # Limpa caracteres especiais

        imported_data = dataset.load(entradas,format='csv')
        dataset.insert_col(0, col=lambda row: None, header="id")

        result = resource.import_data(dataset, dry_run=True, raise_errors=True)

        if not result.has_errors():
            resource.import_data(dataset, dry_run=False)  # Actually import now
            string_html = "Importado: <br>"
            for row_values in dataset:
                string_html += str(row_values) + "<br>"
            return HttpResponse(string_html)
        else:
            return HttpResponse("Erro ao carregar arquivo."+str(result))

    return render(request, 'projetos/import.html')

@login_required
def calendario(request):
    eventos = Evento.objects.exclude(name="Aula PFE")
    aulas = Evento.objects.filter(name="Aula PFE")
    context= {
        'eventos': eventos,
        'aulas': aulas,
    }
    return render(request, 'projetos/calendario.html', context)

@login_required
def submissao(request):
    context= {
    }
    return render(request, 'projetos/submissao.html', context)

@login_required
def documentos(request):
    return render(request, 'index_documentos.html')

@login_required
def download(request, path):
    file_path = os.path.abspath(os.path.join(settings.ARQUIVOS, os.path.split(path)[1]) )
    if ".." in file_path: raise PermissionDenied
    if "\\" in file_path: raise PermissionDenied
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/pdf")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def contrato(request, organizacao, path):
    file_path = os.path.abspath(os.path.join(settings.ARQUIVOS, "{0}/{1}".format(organizacao, path) ) )
    if ".." in file_path: raise PermissionDenied
    if "\\" in file_path: raise PermissionDenied
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/pdf")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def projetos_lista(request):
    configuracao = Configuracao.objects.all().first()
    projetos = Projeto.objects.all()
    context= {'projetos': projetos }    
    return render(request, 'projetos/projetos_lista.html', context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def exportar(request):
    return render(request, 'projetos/exportar.html')

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def relatorios(request):
    return render(request, 'projetos/relatorios.html')

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def carregar(request):
    return render(request, 'projetos/carregar.html')

@login_required
def meuprojeto(request):
    user = PFEUser.objects.get(pk=request.user.pk)
    if user.tipo_de_usuario != 1 and user.tipo_de_usuario != 2:
       return HttpResponse("Você não está cadastrado como aluno ou professor") 
    aluno = Aluno.objects.get(pk=request.user.pk) # com professor ainda esta errado
    projeto = aluno.alocado
    if not projeto:
        return HttpResponse("Você não está alocado em nenhum projeto.")
    alunos = Aluno.objects.filter(alocado=projeto)
    context = {
        'projeto': projeto,
        'alunos': alunos,
    }
    return render(request, 'projetos/meuprojeto.html', context=context)