# Desenvolvido para o Projeto Final de Engenharia
# Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
# Data: 18 de Outubro de 2019

from django.conf import settings
from django.core.mail import send_mail
from users.models import PFEUser, Aluno, Professor, Parceiro, Opcao

def email(subject, recipient_list, message):
    #subject = 'PFE : '+aluno.user.username
    email_from = settings.EMAIL_HOST_USER
    #recipient_list = ['pfeinsper@gmail.com',aluno.user.email,]
    return send_mail( subject, message, email_from, recipient_list, html_message=message, fail_silently=True, )

def create_message(aluno):
        message = '<br>\n'
        message += '&nbsp;&nbsp;Caro aluno: <b>'+aluno.user.first_name+" "+aluno.user.last_name+" ("+aluno.user.username+')</b>\n\n'
        message += '<br><br>\n\n'
        message += '&nbsp;&nbsp;Suas opções de projetos foram:<br>\n'
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
        message += '<br><br>\n\n'
        message += '&nbsp;&nbsp;Suas informações adicionais são:<br>\n'
        message += '<br>\n'
        message += ("&nbsp;"*4)+'Você já trabalhou e/ou estagiou em alguma empresa de engenharia?<br>\n'
        message += ("&nbsp;"*4)+'Se sim, qual/quais?<br>\n'
        message += ("&nbsp;"*4)+'<i>'+aluno.trabalhou+'</i>'
        message += '<br><br>\n\n'
        message += ("&nbsp;"*4)+'Você já participou de atividades sociais?<br>\n'
        message += ("&nbsp;"*4)+'Se sim, qual/quais?<br>\n'
        message += ("&nbsp;"*4)+'<i>'+aluno.social+'</i>'
        message += '<br><br>\n\n'
        message += ("&nbsp;"*4)+'Você já participou de alguma entidade estudantil do Insper?<br>\n'
        message += ("&nbsp;"*4)+'Liste as que você já participou?<br>\n'
        message += ("&nbsp;"*4)+'<i>'+aluno.entidade+'</i>'
        message += '<br><br>\n\n'
        message += ("&nbsp;"*4)+'Você possui familiares em algum empresa que está aplicando? Ou empresa concorrente direta?<br>\n'
        message += ("&nbsp;"*4)+'Se sim, qual/quais? Qual seu grau de relacionamento.<br>\n'
        message += ("&nbsp;"*4)+'<i>'+aluno.familia+'</i>'
        message += '<br><br>\n\n'
        message += '<br>\n'+("&nbsp;"*12)+"atenciosamente, comitê PFE"
        message += '&nbsp;<br>\n'
        message += '&nbsp;<br>\n'
        return message
