#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""

import os

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

from professores.support import recupera_orientadores
from professores.support import recupera_coorientadores
from professores.support import recupera_bancas_intermediarias
from professores.support import recupera_bancas_finais

from projetos.models import Documento, Configuracao, Projeto, Certificado
from projetos.models import get_upload_path

from users.models import Aluno
from users.support import get_edicoes

from .support import render_pdf_file


@login_required
def index_documentos(request):
    """Lista os documentos armazenados no servidor."""
    # Regulamento PFE
    regulamento = Documento.objects.filter(tipo_de_documento=6).last()

    # Plano de Aprend
    plano_de_aprend = Documento.objects.filter(tipo_de_documento=7).last()

    # manual do aluno
    manual_aluno = Documento.objects.filter(tipo_de_documento=8).last()

    # manual do orientador
    # = Documento.objects.filter(tipo_de_documento=9).last()

    # manual da organização parceira
    # = Documento.objects.filter(tipo_de_documento=10).last()

    # manual de planej
    manual_planejamento = Documento.objects.filter(tipo_de_documento=13).last()

    # manual de relatórios
    manual_relatorio = Documento.objects.filter(tipo_de_documento=12).last()

    # template de relat.
    template_relatorio = Documento.objects.filter(tipo_de_documento=17).last()

    # termo de parceria
    termo_parceria = Documento.objects.filter(tipo_de_documento=14).last()

    context = {
        'MEDIA_URL': settings.MEDIA_URL,
        'regulamento': regulamento,
        'plano_de_aprendizagem': plano_de_aprend,
        'manual_aluno': manual_aluno,
        'manual_planejamento': manual_planejamento,
        'manual_relatorio': manual_relatorio,
        'termo_parceria': termo_parceria,
        'template_relatorio': template_relatorio,
    }

    return render(request, 'documentos/index_documentos.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def certificados_submetidos(request):
    """Lista os Certificados Emitidos."""
    edicoes = []

    if request.is_ajax():
        if 'edicao' in request.POST:
            edicao = request.POST['edicao']
            if edicao == 'todas':
                certificados = Certificado.objects.all()
            else:
                ano, semestre = request.POST['edicao'].split('.')
                certificados = Certificado.objects\
                    .filter(projeto__ano=ano, projeto__semestre=semestre)
        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        edicoes, ano, semestre = get_edicoes(Certificado)
        certificados = Certificado.objects\
            .filter(projeto__ano=ano, projeto__semestre=semestre)

    context = {
        'certificados': certificados,
        'edicoes': edicoes,
    }

    return render(request, 'documentos/certificados_submetidos.html', context)


def atualiza_certificado(usuario, projeto, tipo_cert, arquivo, banca=None):
    """Atualiza os certificados."""
    (certificado, _created) = \
        Certificado.objects.get_or_create(usuario=usuario,
                                          projeto=projeto,
                                          tipo_de_certificado=tipo_cert)

    context = {
        'projeto': projeto,
    }

    if not certificado.documento:
        if tipo_cert == 101:
            tipo = "_orientacao"
        elif tipo_cert == 102:
            context['usuario'] = usuario
            tipo = "_coorientacao"
        elif tipo_cert == 103:
            context['usuario'] = usuario
            context['banca'] = banca
            tipo = "_banca_intermediaria"
        elif tipo_cert == 104:
            context['usuario'] = usuario
            context['banca'] = banca
            tipo = "_banca_final"
        else:
            tipo = ""

        path = get_upload_path(certificado, "")

        full_path = settings.MEDIA_ROOT + "/" + path
        os.makedirs(full_path, mode=0o777, exist_ok=True)

        filename = full_path + "certificado" + tipo + ".pdf"

        pdf = render_pdf_file(arquivo, context, filename)

        if (not pdf) or pdf.err:
            return HttpResponse("Erro ao gerar certificados.", status=401)

        certificado.documento = path + "certificado" + tipo + ".pdf"
        certificado.save()

        return certificado

    return None


@login_required
@transaction.atomic
@permission_required('users.altera_professor', login_url='/')
def gerar_certificados(request):
    """Recupera um certificado pelos dados."""
    configuracao = get_object_or_404(Configuracao)
    # try:
    #     configuracao = Configuracao.objects.get()
    # except Configuracao.DoesNotExist:
    #     return HttpResponse("Falha na configuracao do sistema.", status=401)

    certificados = []

    # (101, "Orientação de Projeto"),
    orientadores = recupera_orientadores(configuracao.ano,
                                         configuracao.semestre)
    arquivo = "documentos/certificado_orientador.html"
    for orientador in orientadores:
        for projeto in orientador[1]:
            certificado = atualiza_certificado(orientador[0].user,
                                               projeto,
                                               101,
                                               arquivo)
            if certificado:
                certificados.append(certificado)

    # (102, "Coorientação de Projeto"),
    coorientadores = recupera_coorientadores(configuracao.ano,
                                             configuracao.semestre)
    arquivo = "documentos/certificado_coorientador.html"
    for coorientador in coorientadores:
        for projeto in coorientador[1]:
            certificado = atualiza_certificado(coorientador[0].user,
                                               projeto,
                                               102,
                                               arquivo)
            if certificado:
                certificados.append(certificado)

    # (103, "Membro de Banca Intermediária"),
    membro_banca = recupera_bancas_intermediarias(configuracao.ano,
                                                  configuracao.semestre)
    arquivo = "documentos/certificado_banca_intermediaria.html"
    for membro in membro_banca:
        for banca in membro[1]:
            certificado = atualiza_certificado(membro[0].user,
                                               banca.projeto,
                                               103,
                                               arquivo,
                                               banca=banca)
            if certificado:
                certificados.append(certificado)

    # (104, "Membro de Banca Final"),
    membro_banca = recupera_bancas_finais(configuracao.ano,
                                          configuracao.semestre)
    arquivo = "documentos/certificado_banca_final.html"
    for membro in membro_banca:
        for banca in membro[1]:
            certificado = atualiza_certificado(membro[0].user,
                                               banca.projeto,
                                               104,
                                               arquivo,
                                               banca=banca)
            if certificado:
                certificados.append(certificado)

    context = {
        'certificados': certificados,
    }

    return render(request, 'documentos/gerar_certificados.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def tabela_documentos(request):
    """Exibe tabela com todos os documentos armazenados."""
    configuracao = get_object_or_404(Configuracao)

    projetos = Projeto.objects.all().order_by("ano", "semestre")

    documentos = []
    for projeto in projetos:

        contrato = {}

        # Contratos   -   (0, 'contrato com empresa')
        contratos = []
        for doc in Documento.objects.filter(organizacao=projeto.organizacao)\
                .filter(tipo_de_documento=0):
            contratos.append((doc.documento, doc.anotacao, doc.data))
        contrato["contratos"] = contratos

        # Contrato alunos  -  (1, 'contrato entre empresa e aluno')
        contratos_alunos = []
        alunos = Aluno.objects.filter(alocacao__projeto=projeto)
        for aluno in alunos:
            documento = Documento.objects.filter(usuario=aluno.user).\
                                          filter(tipo_de_documento=1).last()
            if documento:
                contratos_alunos.append((documento.documento,
                                         aluno.user.first_name + " " +
                                         aluno.user.last_name))
            else:
                contratos_alunos.append(("",
                                         aluno.user.first_name + " " +
                                         aluno.user.last_name))
        contrato["contratos_alunos"] = contratos_alunos

        # relatorio_final   -   (3, 'relatório final')
        documento = Documento.objects.filter(projeto=projeto)\
            .filter(tipo_de_documento=3).last()
        if documento:
            contrato["relatorio_final"] = documento.documento
        else:
            contrato["relatorio_final"] = ""

        # Autor. de Public. da Empresa (4, 'autorização de publicação empresa')
        documento = Documento.objects.filter(projeto=projeto)\
            .filter(tipo_de_documento=4).last()
        if documento:
            contrato["autorizacao_publicacao_empresa"] = documento.documento
        else:
            contrato["autorizacao_publicacao_empresa"] = ""

        documentos.append(contrato)

        # Autor. de Public do Estudante (5, 'autorização de publicação aluno')
        autorizacao_publicacao_aluno = []
        alunos = Aluno.objects.filter(alocacao__projeto=projeto)
        for aluno in alunos:
            documento = Documento.objects.filter(usuario=aluno.user).\
                                          filter(tipo_de_documento=5).last()
            if documento:
                autorizacao_publicacao_aluno.\
                    append((documento.documento,
                            aluno.user.first_name+" "+aluno.user.last_name))
            else:
                autorizacao_publicacao_aluno.\
                    append(("",
                            aluno.user.first_name+" "+aluno.user.last_name))
        contrato["autorizacao_publicacao_aluno"] = autorizacao_publicacao_aluno

        # Outros   -   (14, 'outros')
        outros = []
        for doc in Documento.objects.filter(organizacao=projeto.organizacao)\
                .filter(tipo_de_documento=14):
            outros.append((doc.documento, doc.anotacao, doc.data))
        contrato["outros"] = outros
    mylist = zip(projetos, documentos)

    # Outros documentos
    seguros = Documento.objects.filter(tipo_de_documento=15)

    context = {
        'configuracao': configuracao,
        'mylist': mylist,
        'seguros': seguros,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, 'documentos/tabela_documentos.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def tabela_seguros(request):
    """Exibe tabela com todos os seguros armazenados."""
    seguros = Documento.objects.filter(tipo_de_documento=15)

    context = {
        'seguros': seguros,
        'MEDIA_URL': settings.MEDIA_URL,
    }

    return render(request, 'documentos/tabela_seguros.html', context)
