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
from professores.support import recupera_bancas_falconi
from professores.support import recupera_mentorias
from professores.support import recupera_mentorias_técnica

from projetos.models import Documento, Configuracao, Projeto, Certificado
from projetos.models import get_upload_path

# from users.models import Aluno
from users.models import PFEUser
from users.support import get_edicoes

from .support import render_pdf_file


@login_required
def index_documentos(request):
    """Lista os documentos armazenados no servidor."""
    # Regulamento PFE
    regulamento = Documento.objects.filter(tipo_de_documento=6).last()

    # Plano de Aprendizado
    plano_de_aprend = Documento.objects.filter(tipo_de_documento=7).last()

    # manual do aluno
    manual_aluno = Documento.objects.filter(tipo_de_documento=8).last()

    # manual do orientador
    manual_orientador = Documento.objects.filter(tipo_de_documento=9).last()

    # manual de avaliações
    manual_avaliacoes = Documento.objects.filter(tipo_de_documento=24).last()

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

    # manual para apresentação na banca
    manual_apresentacao = Documento.objects.filter(tipo_de_documento=22).last()

    # manual de participação em bancas
    manual_bancas = Documento.objects.filter(tipo_de_documento=23).last()

    context = {
        "MEDIA_URL": settings.MEDIA_URL,
        "regulamento": regulamento,
        "plano_de_aprendizagem": plano_de_aprend,
        "manual_aluno": manual_aluno,
        "manual_planejamento": manual_planejamento,
        "manual_relatorio": manual_relatorio,
        "termo_parceria": termo_parceria,
        "template_relatorio": template_relatorio,
        "manual_apresentacao": manual_apresentacao,
        "manual_bancas": manual_bancas,
        "manual_orientador": manual_orientador,
        "manual_avaliacoes": manual_avaliacoes,
    }

    return render(request, "documentos/index_documentos.html", context)


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

    configuracao = get_object_or_404(Configuracao)
    coordenacao = configuracao.coordenacao
    #coordenacoes = PFEUser.objects.filter(coordenacao=True)

    context = {
        "certificados": certificados,
        "edicoes": edicoes,
        "coordenacao": coordenacao,
        #"coordenacoes": coordenacoes,
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

    if projeto and not certificado.documento:
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
        elif tipo_cert == 105:
            context['usuario'] = usuario
            context['banca'] = banca
            tipo = "_banca_falconi"
        elif tipo_cert == 106:
            context['usuario'] = usuario
            context['dinamica'] = banca
            tipo = "_mentoria_profissional"
        elif tipo_cert == 107:
            context['usuario'] = usuario
            context['count_projetos'] = banca
            tipo = "_mentoria_tecnica"
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
def selecao_geracao_certificados(request):
    """Recupera um certificado pelos dados."""

    edicoes, _, _ = get_edicoes(Projeto)
    

    context = {
        'edicoes': edicoes,
    }

    return render(request, 'documentos/selecao_geracao_certificados.html', context)



@login_required
@transaction.atomic
@permission_required('users.altera_professor', login_url='/')
def gerar_certificados(request):
    """Recupera um certificado pelos dados."""
    if not os.path.exists("arquivos/signature.png"):
        return HttpResponse("Arquivo de assinatura não encontrado.", status=401)
    if not os.path.exists("arquivos/papel_timbrado.pdf"):
        return HttpResponse("Papel timbrado não encontrado.", status=401)

    if 'edicao' in request.POST:
        ano, semestre = request.POST['edicao'].split('.')
    else:
        return HttpResponse("Algum erro não identificado.", status=401)

    certificados = []
    if 'orientador' in request.POST:
        # (101, "Orientação de Projeto"),
        orientadores = recupera_orientadores(ano, semestre)
        arquivo = "documentos/certificado_orientador.html"
        for orientador in orientadores:
            for projeto in orientador[1]:
                certificado = atualiza_certificado(orientador[0].user,
                                                   projeto,
                                                   101,
                                                   arquivo)
                if certificado:
                    certificados.append(certificado)

    if 'coorientador' in request.POST:
        # (102, "Coorientação de Projeto"),
        coorientadores = recupera_coorientadores(ano, semestre)
        arquivo = "documentos/certificado_coorientador.html"
        for coorientador in coorientadores:
            for projeto in coorientador[1]:
                certificado = atualiza_certificado(coorientador[0].user,
                                                   projeto,
                                                   102,
                                                   arquivo)
                if certificado:
                    certificados.append(certificado)

    if 'banca' in request.POST:
        # (103, "Membro de Banca Intermediária"),
        membro_banca = recupera_bancas_intermediarias(ano, semestre)
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

    if 'banca' in request.POST:
        # (104, "Membro de Banca Final"),
        membro_banca = recupera_bancas_finais(ano, semestre)
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

    if 'banca' in request.POST:
        # (105, "Membro de Banca Falconi"),
        membro_banca = recupera_bancas_falconi(ano, semestre)
        arquivo = "documentos/certificado_banca_falconi.html"
        for membro in membro_banca:
            for banca in membro[1]:
                certificado = atualiza_certificado(membro[0].user,
                                                   banca.projeto,
                                                   105,
                                                   arquivo,
                                                   banca=banca)
                if certificado:
                    certificados.append(certificado)

    if 'mentoria_profissional' in request.POST:
        # (106, "Mentoria de Grupo"),  # mentor na Profissional (antiga Mentoria Falconi)
        membro_banca = recupera_mentorias(ano, semestre)
    
        arquivo = "documentos/certificado_mentoria.html"
        for membro in membro_banca:
            for banca in membro[1]:
                certificado = atualiza_certificado(membro[0],
                                                   banca.projeto,
                                                   106,
                                                   arquivo,
                                                   banca=banca)
                if certificado:
                    certificados.append(certificado)

    if 'mentoria_tecnica' in request.POST:
        # (107, "Mentoria Técnica"),  # mentor da empresa
        membros = recupera_mentorias_técnica(ano, semestre)
        arquivo = "documentos/certificado_mentoria_tecnica.html"
        for membro in membros:
            for banca in membro[1]:
                certificado = atualiza_certificado(membro[0],
                                                   banca.projeto,
                                                   107,
                                                   arquivo,
                                                   banca=banca)
                if certificado:
                    certificados.append(certificado)

    configuracao = get_object_or_404(Configuracao)
    coordenacao = configuracao.coordenacao

    context = {
        'certificados': certificados,
        "coordenacao": coordenacao,
    }

    return render(request, 'documentos/gerar_certificados.html', context)


# @login_required
def relatorios_publicos(request):
    """Exibe relatórios públicos."""
    relatorios = Documento.objects.filter(tipo_de_documento=25, confidencial=False)\
        .order_by("-projeto__ano", "-projeto__semestre")

    context = {
        'relatorios': relatorios,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, 'documentos/relatorios_publicos.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def tabela_documentos(request):
    """Exibe tabela com todos os documentos armazenados."""

    if request.is_ajax():
        if 'edicao' in request.POST:
            edicao = request.POST['edicao']

            if edicao == 'todas':
                projetos = Projeto.objects.all()
            else:
                ano, semestre = request.POST['edicao'].split('.')
                projetos = Projeto.objects.filter(ano=ano, semestre=semestre)


            if 'curso' in request.POST:
                curso = request.POST['curso']    
            else:
                return HttpResponse("Algum erro não identificado.", status=401)

            if curso != 'T':
                projetos = projetos.filter(alocacao__aluno__curso=curso).distinct()


        context = {
            "projetos": projetos,
            "edicao": edicao,
            "MEDIA_URL": settings.MEDIA_URL,
        }

    else:
    
        edicoes, _, _ = get_edicoes(Projeto)
        context = {
            "edicoes": edicoes,
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

@login_required
@permission_required('users.altera_professor', login_url='/')
def tabela_atas(request):
    """Exibe tabela com todos os seguros armazenados."""
    atas = Documento.objects.filter(tipo_de_documento=21).order_by("-data")
    context = {
        'atas': atas,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, 'documentos/tabela_atas.html', context)
