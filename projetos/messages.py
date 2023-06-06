#!/usr/bin/env python

"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 18 de Outubro de 2019
"""

from django.conf import settings
from django.core.mail import send_mail
from users.models import Opcao
from .models import AreaDeInteresse
from .models import Area

def htmlizar(text):
    """Coloca <br> nas quebras de linha."""
    return text.replace('\n', '<br>\n')

def email(subject, recipient_list, message):
    """Envia um e-mail para o HOST_USER."""
    email_from = settings.EMAIL_USER + " <" + settings.EMAIL_HOST_USER + ">"
    auth_user = settings.EMAIL_HOST_USER
    return send_mail(subject, message, email_from, recipient_list,
                     fail_silently=True, auth_user=auth_user, html_message=message)

def create_message(estudante, ano, semestre):
    """Cria mensagem quando o estudante termina de preencher o formulário de seleção de propostas"""
    message = '<br>\n'
    message += '&nbsp;&nbsp;Estudante: <b>'+estudante.user.first_name+" "+estudante.user.last_name
    message += " ("+estudante.user.username+')</b>\n\n'
    message += '&nbsp;<br><br>\n\n'
    message += '&nbsp;&nbsp;Suas opções de propostas de projetos foram:<br>\n'
    message += '<ul>'
    opcoes = Opcao.objects.filter(aluno=estudante)
    if not opcoes:
        message += "NÃO FORAM ENCONTRADAS OPÇÕES DE ESCOLHA DE PROPOSTAS DE PROJETOS!"
    for opcao in opcoes:
        if opcao.proposta.disponivel:
            # Mostra somente as propostas do próximo ano, não outras em caso de estudante DP
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

    todas_areas = Area.objects.filter(ativa=True)
    alguma = False
    for area in todas_areas:
        if AreaDeInteresse.objects.filter(usuario=estudante.user, area=area):
            message += "<li>"+area.titulo+"</li>\n"
            alguma = True
    if not alguma:
        message += "<br>\nNENHUMA ÁREA DE INTERESSE SELECIONADA!<br>\n<br>\n"

    if AreaDeInteresse.objects.filter(area=None, usuario=estudante.user).exists():
        outras = AreaDeInteresse.objects.get(area=None, usuario=estudante.user).outras
        message += "Outras: <u>"+outras+"</u><br>\n"

    message += '</ul>'
    message += '<br>\n'
    message += '&nbsp;&nbsp;Suas informações adicionais são:<br>\n'
    message += '<br>\n'
    message += ("&nbsp;" * 4)
    message += 'Você já trabalhou/trabalha ou estagiou/estagia em alguma empresa de engenharia?<br>\n'
    message += ("&nbsp;" * 4)
    message += 'Se sim, qual/quais?<br>\n'
    if estudante.trabalhou:
        message += ("&nbsp;" * 4) + '<i>'+estudante.trabalhou+'</i>'
    else:
        message += ("&nbsp;" * 4) + '<i>'+'CAMPO NÃO DEFINIDO'+'</i>'
    message += '<br><br>\n\n'
    message += ("&nbsp;" * 4) + 'Você já participou de atividades sociais?<br>\n'
    message += ("&nbsp;" * 4) + 'Se sim, qual/quais?<br>\n'
    if estudante.social:
        message += ("&nbsp;"*4)+'<i>'+estudante.social+'</i>'
    else:
        message += ("&nbsp;"*4)+'<i>'+'CAMPO NÃO DEFINIDO'+'</i>'
    message += '<br><br>\n\n'
    message += ("&nbsp;"*4)+'Você já participou de alguma entidade estudantil do Insper?<br>\n'
    message += ("&nbsp;"*4)+'Liste as que você já participou?<br>\n'
    if estudante.entidade:
        message += ("&nbsp;"*4)+'<i>'+estudante.entidade+'</i>'
    else:
        message += ("&nbsp;"*4)+'<i>'+'CAMPO NÃO DEFINIDO'+'</i>'
    message += '<br><br>\n\n'
    message += ("&nbsp;"*4)+'Você possui familiares em algum empresa que está aplicando?'
    message += 'Ou empresa concorrente direta?<br>\n'
    message += ("&nbsp;"*4)+'Se sim, qual/quais? Qual seu grau de relacionamento.<br>\n'
    if estudante.familia:
        message += ("&nbsp;"*4)+'<i>'+estudante.familia+'</i>'
    else:
        message += ("&nbsp;"*4)+'<i>'+'CAMPO NÃO DEFINIDO'+'</i>'
    message += '<br><br>\n\n'
    if estudante.user.linkedin:
        message += ("&nbsp;"*4)+'<i>LinkedIn:</i> <a href='+estudante.user.linkedin+'>'
        message += estudante.user.linkedin+'</a>'
        message += '<br><br>\n\n'
    message += '<br>\n'+("&nbsp;"*12)+"atenciosamente, comitê PFE"
    message += '&nbsp;<br>\n'
    message += '&nbsp;<br>\n'
    return message

def message_reembolso(usuario, projeto, reembolso, cpf):
    """Emite menssagem de reembolso."""
    message = '<br>\n'
    message += '&nbsp;&nbsp;Caro <b>Dept. de Carreiras</b>\n\n'
    message += '<br><br>\n\n'
    message += '&nbsp;&nbsp;Por favor, encaminhem o pedido de reembolso de: '
    message += usuario.first_name+" "+usuario.last_name+" ("+usuario.username+')<br>\n'
    message += '&nbsp;&nbsp;CPF: '+cpf[:3]+'.'+cpf[3:6]+'.'+cpf[6:9]+'-'+cpf[9:11]+'<br>\n'
    # if usuario.aluno.curso == "C":
    #     curso = "Computação"
    # elif usuario.aluno.curso == "M":
    #     curso = "Mecânica"
    # else:
    #     curso = "Mecatrônica"
    curso = str(usuario.aluno.curso2)
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
    message += '&nbsp;&nbsp;&nbsp;Obs: você deverá entregar todas as notas fiscais originais, '
    message += 'ou senão imprimir, diretamente no departamento de carreiras,'
    message += 'sem isso o processo não avançará.<br>\n'

    return message

def message_agendamento(encontro, cancelado):
    """Emite menssagem de agendamento de dinâmica."""
    message = '<br>\n'
    message += '&nbsp;&nbsp;Grupo do Projeto <b>'
    message += str(encontro.projeto)
    message += '</b>\n\n'
    message += '<br><br>\n\n'
    message += '&nbsp;&nbsp;Marcada dinâmica do PFE: '
    message += 'dia ' + str(encontro.startDate.strftime("%d/%m/%Y")) + ' das ' + str(encontro.startDate.strftime("%H:%M")) + ' às ' + str(encontro.endDate.strftime("%H:%M"))
    message += '<br>\n'
    if encontro.location:
        message += '&nbsp;&nbsp;Local: '
        message += str(encontro.location)
        message += '<br>\n'
    if encontro.facilitador:
        message += '&nbsp;&nbsp;Com: '
        message += str(encontro.facilitador)
        message += '<br>\n'

    if cancelado:
        message += '<br>\n'
        message += '&nbsp;&nbsp;<font color="red">Obs: horário previamente agendado ' + cancelado + ' foi cancelado.</font><br>\n'
        message += '<br>\n'

    return message
