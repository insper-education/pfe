#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Junho de 2023
"""

import subprocess
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.middleware.csrf import get_token
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

from administracao.models import Carta

# Get an instance of a logger
logger = logging.getLogger("django")

def index(request):
    """Página principal do sistema."""
    if request.user.is_authenticated:
        return render(request, "index.html")
    else:
        info = get_object_or_404(Carta, template="Informação")
        return render(request, "info.html", {"info": info})

def info(request):
    """Página com informações."""
    info = get_object_or_404(Carta, template="Informação")
    return render(request, "info.html", {"info": info})

def manutencao(request):
    """Página de Manutenção do sistema."""
    return render(request, "manutencao.html")

def custom_400(request, exception):
    mensagem = "<h1>Bad Request (400)</h1>"
    if (exception):
        mensagem += str(exception) + "<br>"
    mensagem += "Em caso de dúvida " + settings.CONTATO
    #t = loader.get_template("400.html")
    #t.render(Context({"exception_value": value,})
    return HttpResponse(mensagem)

@login_required
@user_passes_test(lambda u: u.is_superuser)
@permission_required("users.view_administrador", raise_exception=True)
def reiniciar_sistema(request):
    """Reinicia o sistema do Capstone pela interface web."""
    if not request.user.eh_admin:
        return HttpResponse("Acesso Negado", status=403)
    if request.method == "POST":
        try:
            result = subprocess.run(["./restart.sh"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if result.returncode == 0:
                logger.info("Sistema reiniciado com sucesso.")
                logger.info(f"Output: {result.stdout}")
                page = f"""
                <html><head><title>Reiniciar Sistema</title>
                <meta http-equiv="refresh" content="15;url=/"></head>
                <body><h1>Reiniciar Sistema</h1>
                <p>Sistema está reiniciando...</p>
                <p><a href="/">Voltar para a página principal</a></p>
                </body></html>
                """
                return HttpResponse(page)
            else:
                logger.error(f"Erro ao reiniciar o sistema:\n output: {result.stdout}\n error: {result.stderr}")
                return HttpResponse(f"Erro ao reiniciar o sistema:<br> output: {result.stdout}<br> error: {result.stderr}", status=500)
        except Exception as e:
            logger.error(f"Erro ao executar o comando: {str(e)}")
            return HttpResponse(f"Erro: {str(e)}", status=500)
        
        # try:
        #     os.system("./restart.sh")
        #     page = f"""
        #     <html><head><title>Reiniciar Sistema</title>
        #     <meta http-equiv="refresh" content="15;url=/"></head>
        #     <body><h1>Reiniciar Sistema</h1>
        #     <p>Sistema está reiniciando...</p>
        #     <p><a href="/">Voltar para a página principal</a></p>
        #     </body></html>
        #     """
        #     return HttpResponse(page)
        # except Exception as e:
        #     return HttpResponse(f"Erro: {str(e)}", status=500)    
    page = f"""
    <html><head><title>Reiniciar Sistema</title></head>
    <body><h1>Reiniciar Sistema</h1><form method="post">
    <input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">
    <input type="submit"></form></body></html>
    """
    return HttpResponse(page)

@login_required
@permission_required("users.view_administrador", raise_exception=True)
def migracao(request):
    """temporário."""
    message = "Nada Feito"
    return HttpResponse(message)
