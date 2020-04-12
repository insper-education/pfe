#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 18 de Outubro de 2019
"""

from django.conf import settings
from django.core.mail import send_mail
from users.models import Opcao

def htmlizar(text):
    """Coloca <br> nas quebras de linha."""
    return text.replace('\\n', '<br>\\n')

def email(subject, recipient_list, message):
    """Envia um e-mail para o HOST_USER."""
    email_from = settings.EMAIL_HOST_USER
    return send_mail(subject, message, email_from, recipient_list, html_message=message, fail_silently=True)

def create_message(aluno, ano, semestre):
    """Cria mensagem quando o aluno termina de preencher o formulário de seleção de projetos"""
    message = '<br>\n'
    message += '&nbsp;&nbsp;Caro aluno: <b>'+aluno.user.first_name+" "+aluno.user.last_name+" ("+aluno.user.username+')</b>\n\n'
    message += '<br><br>\n\n'
    message += '&nbsp;&nbsp;Suas opções de projetos foram:<br>\n'
    message += '<ul>'
    for opcao in Opcao.objects.filter(aluno=aluno):
        if opcao.projeto.ano == ano and opcao.projeto.semestre == semestre and opcao.projeto.disponivel:
            message += ("&nbsp;"*4)+"<p>"+str(opcao.prioridade)+" - "+opcao.projeto.titulo+" ("+opcao.projeto.empresa.nome_empresa+")</p>\n"
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
    message += ("&nbsp;" * 4) + 'Você já trabalhou e/ou estagiou em alguma empresa de engenharia?<br>\n'
    message += ("&nbsp;" * 4) + 'Se sim, qual/quais?<br>\n'
    if aluno.trabalhou:
        message += ("&nbsp;" * 4) + '<i>'+aluno.trabalhou+'</i>'
    else:
        message += ("&nbsp;" * 4) + '<i>'+'CAMPO NÃO DEFINIDO'+'</i>'
    message += '<br><br>\n\n'
    message += ("&nbsp;" * 4) + 'Você já participou de atividades sociais?<br>\n'
    message += ("&nbsp;" * 4) + 'Se sim, qual/quais?<br>\n'
    if aluno.social:
        message += ("&nbsp;"*4)+'<i>'+aluno.social+'</i>'
    else:
        message += ("&nbsp;"*4)+'<i>'+'CAMPO NÃO DEFINIDO'+'</i>'
    message += '<br><br>\n\n'
    message += ("&nbsp;"*4)+'Você já participou de alguma entidade estudantil do Insper?<br>\n'
    message += ("&nbsp;"*4)+'Liste as que você já participou?<br>\n'
    if aluno.entidade:
        message += ("&nbsp;"*4)+'<i>'+aluno.entidade+'</i>'
    else:
        message += ("&nbsp;"*4)+'<i>'+'CAMPO NÃO DEFINIDO'+'</i>'
    message += '<br><br>\n\n'
    message += ("&nbsp;"*4)+'Você possui familiares em algum empresa que está aplicando?'
    message += 'Ou empresa concorrente direta?<br>\n'
    message += ("&nbsp;"*4)+'Se sim, qual/quais? Qual seu grau de relacionamento.<br>\n'
    if aluno.familia:
        message += ("&nbsp;"*4)+'<i>'+aluno.familia+'</i>'
    else:
        message += ("&nbsp;"*4)+'<i>'+'CAMPO NÃO DEFINIDO'+'</i>'
    message += '<br><br>\n\n'
    message += '<br>\n'+("&nbsp;"*12)+"atenciosamente, comitê PFE"
    message += '&nbsp;<br>\n'
    message += '&nbsp;<br>\n'
    return message

def message_reembolso(usuario, projeto, reembolso):
    message = '<br>\n'
    message += '&nbsp;&nbsp;Caro <b>Dept. de Carreiras</b>\n\n'
    message += '<br><br>\n\n'
    message += '&nbsp;&nbsp;Por favor, encaminhem o pedido de reembolso de: '
    message += usuario.first_name+" "+usuario.last_name+" ("+usuario.username+')<br>\n'
    cpf = str(usuario.cpf)
    message += '&nbsp;&nbsp;CPF: '+cpf[:3]+'.'+cpf[3:6]+'.'+cpf[6:9]+'-'+cpf[9:11]+'<br>\n'
    if usuario.aluno.curso == "C":
        curso = "Computação"
    elif usuario.aluno.curso == "M":
        curso = "Mecânica"
    else:
        curso = "Mecatrônica"
    message += '&nbsp;&nbsp;Curso: '+curso+'<br>\n'
    if projeto:
        message += '<br>\n'
        message += '&nbsp;&nbsp;Participante do projeto: '+projeto.titulo+'<br>\n'
    message += '<br>\n'
    message += '&nbsp;&nbsp;Descrição: '+reembolso.descricao+'<br>\n'
    message += '<br>\n'
    message += '&nbsp;&nbsp;Banco: '
    message += reembolso.banco.nome+' ('+str(reembolso.banco.codigo)+')'+'<br>\n'
    message += '&nbsp;&nbsp;Conta: ' + reembolso.conta+'<br>\n'
    message += '&nbsp;&nbsp;Agência: ' + reembolso.agencia+'<br>\n'
    message += '<br>\n'
    message += '&nbsp;&nbsp;Valor do reembolso: ' + reembolso.valor+'<br>\n'
    message += '<br>\n'
    message += '<br>\n'
    message += '&nbsp;&nbsp;Para isso use o Centro de Custo: '
    message += '200048 - PROJETO FINAL DE ENGENHARIA<br>\n'
    message += '&nbsp;&nbsp;Com a conta contábil: '
    message += '400339 - INSUMOS PARA EQUIPAMENTOS DOS LABORATÓRIOS<br>\n'
    message += '<br>\n'+("&nbsp;"*12)+"atenciosamente, coordenação do PFE"
    message += '&nbsp;<br>\n'
    message += '&nbsp;<br>\n'
    message += '&nbsp;&nbsp;&nbsp;Obs: O aluno deverá entregar todos as notas fiscais originais, '
    message += 'ou senão imprimir, diretamente no departamento de carreiras,'
    message += 'sem isso o processo não deverá avançar.<br>\n'

    return message
