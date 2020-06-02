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
    return text.replace('\n', '<br>\n')

def email(subject, recipient_list, message):
    """Envia um e-mail para o HOST_USER."""
    email_from = settings.EMAIL_HOST_USER
    return send_mail(subject, message, email_from, recipient_list,
                     html_message=message, fail_silently=True)

def create_message(aluno, ano, semestre):
    """Cria mensagem quando o aluno termina de preencher o formulário de seleção de propostas"""
    message = '<br>\n'
    message += '&nbsp;&nbsp;Estudante: <b>'+aluno.user.first_name+" "+aluno.user.last_name
    message += " ("+aluno.user.username+')</b>\n\n'
    message += '&nbsp;<br><br>\n\n'
    message += '&nbsp;&nbsp;Suas opções de propostas de projetos foram:<br>\n'
    message += '<ul>'
    opcoes = Opcao.objects.filter(aluno=aluno)
    if not opcoes:
        message += "NÃO FORAM ENCONTRADAS OPÇÕES DE ESCOLHA DE PROPOSTAS DE PROJETOS!"
    for opcao in opcoes:
        if opcao.proposta.disponivel:
            # Mostra somente as propostas do próximo ano, não outras em caso de aluno DP
            if opcao.proposta.ano == ano and\
               opcao.proposta.semestre == semestre:
                message += "<p>"+str(opcao.prioridade)+" - "
                message += opcao.proposta.titulo+" ("
                if opcao.proposta.nome_organizacao:
                    message += opcao.proposta.nome_organizacao
                elif opcao.proposta.organizacao and opcao.proposta.organizacao.nome:
                    message += opcao.proposta.organizacao.nome
                else:
                    message += "ORGANIZAÇÃO INDEFINIDA"
                message += ")</p>\n"
    message += '</ul>'
    message += '<br>\n'

    message += '&nbsp;&nbsp;Suas áreas de interesse são:<br>\n'
    message += '<ul>'

    if aluno.areas_de_interesse.inovacao_social:
        message += "<li>Inovação Social</li>\n"
    if aluno.areas_de_interesse.ciencia_dos_dados:
        message += "<li>Ciência de Dados</li>\n"
    if aluno.areas_de_interesse.modelagem_3D:
        message += "<li>Modelagem 3D</li>\n"
    if aluno.areas_de_interesse.manufatura:
        message += "<li>Manufatura</li>\n"
    if aluno.areas_de_interesse.resistencia_dos_materiais:
        message += "<li>Resistência dos Materiais</li>\n"
    if aluno.areas_de_interesse.modelagem_de_sistemas:
        message += "<li>Modelagem de Sistemas</li>\n"
    if aluno.areas_de_interesse.controle_e_automacao:
        message += "<li>Controle e Automação</li>\n"
    if aluno.areas_de_interesse.termodinamica:
        message += "<li>Termodinâmica</li>\n"
    if aluno.areas_de_interesse.fluidodinamica:
        message += "<li>Fluidodinâmica</li>\n"
    if aluno.areas_de_interesse.eletronica_digital:
        message += "<li>Eletrônica Digital</li>\n"
    if aluno.areas_de_interesse.programacao:
        message += "<li>Programação</li>\n"
    if aluno.areas_de_interesse.inteligencia_artificial:
        message += "<li>Inteligência Artificial</li>\n"
    if aluno.areas_de_interesse.banco_de_dados:
        message += "<li>Banco de Dados</li>\n"
    if aluno.areas_de_interesse.computacao_em_nuvem:
        message += "<li>Computação em Nuvem</li>\n"
    if aluno.areas_de_interesse.visao_computacional:
        message += "<li>Visão Computacional</li>\n"
    if aluno.areas_de_interesse.computacao_de_alto_desempenho:
        message += "<li>Computação de Alto Desempenho</li>\n"
    if aluno.areas_de_interesse.robotica:
        message += "<li>Robótica</li>\n"
    if aluno.areas_de_interesse.realidade_virtual_aumentada:
        message += "<li>Realidade Virtual e Aumentada</li>\n"
    if aluno.areas_de_interesse.protocolos_de_comunicacao:
        message += "<li>Protocolos de Comunicação</li>\n"
    if aluno.areas_de_interesse.eficiencia_energetica:
        message += "<li>Eficiência Energética</li>\n"
    if aluno.areas_de_interesse.administracao_economia_financas:
        message += "<li>Administração, Economia e Finanças</li>\n"

    alguma = aluno.areas_de_interesse.inovacao_social or \
             aluno.areas_de_interesse.ciencia_dos_dados or \
             aluno.areas_de_interesse.modelagem_3D or \
             aluno.areas_de_interesse.manufatura or \
             aluno.areas_de_interesse.resistencia_dos_materiais or \
             aluno.areas_de_interesse.modelagem_de_sistemas or \
             aluno.areas_de_interesse.controle_e_automacao or \
             aluno.areas_de_interesse.termodinamica or \
             aluno.areas_de_interesse.fluidodinamica or \
             aluno.areas_de_interesse.eletronica_digital or \
             aluno.areas_de_interesse.programacao or \
             aluno.areas_de_interesse.inteligencia_artificial or \
             aluno.areas_de_interesse.banco_de_dados or \
             aluno.areas_de_interesse.computacao_em_nuvem or \
             aluno.areas_de_interesse.visao_computacional or \
             aluno.areas_de_interesse.computacao_de_alto_desempenho or \
             aluno.areas_de_interesse.robotica or \
             aluno.areas_de_interesse.realidade_virtual_aumentada or \
             aluno.areas_de_interesse.protocolos_de_comunicacao or \
             aluno.areas_de_interesse.eficiencia_energetica or \
             aluno.areas_de_interesse.administracao_economia_financas

    if not alguma:
        message += "<br>\nNENHUMA ÁREA DE INTERESSE SELECIONADA!<br>\n<br>\n"

    if aluno.areas_de_interesse.outras:
        message += "Outras: <u>"+aluno.areas_de_interesse.outras+"</u><br>\n"

    message += '</ul>'
    message += '<br>\n'
    message += '&nbsp;&nbsp;Suas informações adicionais são:<br>\n'
    message += '<br>\n'
    message += ("&nbsp;" * 4)
    message += 'Você já trabalhou e/ou estagiou em alguma empresa de engenharia?<br>\n'
    message += ("&nbsp;" * 4)
    message += 'Se sim, qual/quais?<br>\n'
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
    if aluno.user.linkedin:
        message += ("&nbsp;"*4)+'<i>LinkedIn:</i> <a href='+aluno.user.linkedin+'>'
        message += aluno.user.linkedin+'</a>'
        message += '<br><br>\n\n'
    message += '<br>\n'+("&nbsp;"*12)+"atenciosamente, comitê PFE"
    message += '&nbsp;<br>\n'
    message += '&nbsp;<br>\n'
    return message

def message_reembolso(usuario, projeto, reembolso):
    """ Emite menssagem de reembolso. """
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
