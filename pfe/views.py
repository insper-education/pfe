#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Junho de 2023
"""

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.http import HttpResponse


@login_required
def index(request):
    """Página principal do sistema do Projeto Final de Engenharia."""
    # num_visits = request.session.get('num_visits', 0) # Visitas a página.
    # request.session['num_visits'] = num_visits + 1
    return render(request, 'index.html')


def manutencao(request):
    """Página de Manutenção do Projeto Final de Engenharia."""
    return render(request, 'manutencao.html')


def custom_400(request, exception):
    mensagem = "<h1>Bad Request (400)</h1>"
    if (exception):
        mensagem += str(exception) + "<br>"
    mensagem += "Em caso de dúvida " + settings.CONTATO
    #t = loader.get_template('400.html')
    #t.render(Context({'exception_value': value,})
    return HttpResponse(mensagem)


from projetos.models import Proposta
from operacional.models import Curso

@login_required
@permission_required("users.view_administrador", raise_exception=True)
def migracao(request):
    """temporário."""
    message = "Feito"

    propostas = Proposta.objects.all()

    comp = Curso.objects.get(sigla_curta="C")
    mec = Curso.objects.get(sigla_curta="M")
    mxt = Curso.objects.get(sigla_curta="X")

    for proposta in propostas:
    
        if proposta.perfil_aluno1_computacao:
            proposta.perfil1.add(comp)
        if proposta.perfil_aluno1_mecanica:
            proposta.perfil1.add(mec)
        if proposta.perfil_aluno1_mecatronica:
            proposta.perfil1.add(mxt)

        if proposta.perfil_aluno2_computacao:
            proposta.perfil2.add(comp)
        if proposta.perfil_aluno2_mecanica:
            proposta.perfil2.add(mec)
        if proposta.perfil_aluno2_mecatronica:
            proposta.perfil2.add(mxt)

        if proposta.perfil_aluno3_computacao:
            proposta.perfil3.add(comp)
        if proposta.perfil_aluno3_mecanica:
            proposta.perfil3.add(mec)
        if proposta.perfil_aluno3_mecatronica:
            proposta.perfil3.add(mxt)

        if proposta.perfil_aluno4_computacao:
            proposta.perfil4.add(comp)
        if proposta.perfil_aluno4_mecanica:
            proposta.perfil4.add(mec)
        if proposta.perfil_aluno4_mecatronica:
            proposta.perfil4.add(mxt)

        proposta.save()

    return HttpResponse(message)