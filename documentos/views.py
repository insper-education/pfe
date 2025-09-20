#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""

import os
import re
import zipfile
import tempfile
import random
import string
import json
from datetime import datetime

from django.http import FileResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.utils.html import escape


from .support import atualiza_certificado, generate_unique_arcname, checa_documentos_certificado

from academica.models import Exame, ExibeNota

from administracao.models import TipoCertificado, GrupoCertificado, Estrutura

from documentos.models import TipoDocumento

from operacional.models import Curso

from professores.support import recupera_avaliadores_bancas

from projetos.models import Documento, Configuracao, Projeto, Certificado, Coorientador, Encontro, Conexao
from projetos.messages import email, prepara_mensagem_email
from users.support import get_edicoes


#@login_required
def index_documentos(request):
    """Lista os documentos armazenados no servidor."""
    context = {
        "titulo": {"pt": "Documentações", "en": "Documentation"},
        "documentos": Documento.objects.all(),
        "areas": Estrutura.loads(nome="Index Documentos"),
    }

    if "/documentos/documentos" in request.path:
        return render(request, "documentos/documentos.html", context=context)
    else:
        return render(request, "documentos/index_documentos.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def biblioteca_link(request, primarykey=None):
    """Edita uma banca de avaliação para o projeto."""

    if primarykey is None:
        return HttpResponseNotFound("<h1>Erro!</h1>")
    if not request.user.eh_admin:
        return HttpResponse("Sem privilégios necessários", status=401)
    
    relatorio = get_object_or_404(Documento, pk=primarykey)

    if request.is_ajax() and request.method == "POST":
        link = request.POST.get("link", "").strip()
        if link:
            relatorio.link = link
            relatorio.save()
            return JsonResponse({"atualizado": True, "link": relatorio.link})
        return HttpResponse("Atualização não realizada.", status=401)

    context = {
        "Documento": Documento,
        "relatorio": relatorio,
        "url": request.get_full_path(),
    }
    return render(request, "documentos/biblioteca_link.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def certificados_submetidos(request, edicao=None, tipos=None, gerados=None):
    """Lista os Certificados Emitidos."""

    if request.is_ajax() and "edicao" in request.POST:
        edicao = request.POST["edicao"]
        if edicao == "todas":
            context = { "certificados": Certificado.objects.all()}
        else:
            ano, semestre = request.POST["edicao"].split('.')
            context = { "certificados": Certificado.objects.filter(projeto__ano=ano, projeto__semestre=semestre)}

    elif request.method == "POST":
        aviso = ""
        # pega todas os certificados marcados
        dados = request.POST.getlist("certificado")
        for primarykey in dados:
            certificado = get_object_or_404(Certificado, pk=primarykey)
            assunto, para, message = prepara_mensagem_email(request, "certificado", primarykey)
            
            recipient_list = para.split(';')
            configuracao = get_object_or_404(Configuracao)
            recipient_list.append(configuracao.coordenacao.user.email)

            email(assunto, recipient_list, message)
            aviso += "Mensagem de Certificado de " + str(certificado.tipo_certificado) + " para " + str(certificado.get_projeto()) + " enviado para: " + escape(para) + "<br>"

        mensagem = {
            "pt": "Mensagens de Certificados enviadas.<br><br>" + aviso,
            "en": "Certificate messages sent.<br><br>" + aviso,
        }
        context = {
            "voltar": True,
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, "generic_ml.html", context=context)

    else:   
        context = {
            "titulo": {"pt": "Certificados Emitidos", "en": "Issued Certificates"},
            "grupos_certificados": GrupoCertificado.objects.all(),
            "edicoes": get_edicoes(Certificado)[0],
            "selecionada_edicao": edicao,
            "tipos": tipos.split(',') if tipos else None,
            "gerados": gerados,
        }

    return render(request, "documentos/certificados_submetidos.html", context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def selecao_geracao_certificados(request):
    """Recupera um certificado pelos dados."""
    configuracao = get_object_or_404(Configuracao)
    context = {
        "titulo": {"pt": "Seleção de Geração de Certificados", "en": "Certificate Generation Selection"},
        "edicoes": get_edicoes(Projeto)[0],
        "selecionada_edicao": f"{configuracao.ano}.{configuracao.semestre}",
        "grupos": GrupoCertificado.objects.all(),
        }
    return render(request, "documentos/selecao_geracao_certificados.html", context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def gerar_certificados(request):
    """Recupera um certificado pelos dados."""

    # Verifica se arquivo com assinatura e papel timbrado estão disponíveis
    erro = checa_documentos_certificado()
    if erro:
        return erro

    if "edicao" not in request.POST:
        return HttpResponse("Algum erro não identificado.", status=401)
    ano, semestre = request.POST["edicao"].split('.')

    tipos = []
    qcertificados = 0
    for grupo in ["O", "C", "MP", "MT", "B"]:
        if grupo in request.POST:
            tipos_cert = TipoCertificado.objects.filter(grupo_certificado__sigla=grupo)
            tipos.append(grupo)
            for tipo in tipos_cert:
                if grupo == "O":
                    for projeto in Projeto.objects.filter(ano=ano, semestre=semestre, orientador__isnull=False):
                        qcertificados += atualiza_certificado(projeto.orientador.user, projeto, tipo)
                if grupo == "C":
                    for coorientador in Coorientador.objects.filter(projeto__ano=ano, projeto__semestre=semestre):    
                        qcertificados += atualiza_certificado(coorientador.usuario, coorientador.projeto, tipo)
                if grupo == "MP":
                    for encontro in Encontro.objects.filter(projeto__ano=ano, projeto__semestre=semestre):
                        qcertificados += atualiza_certificado(encontro.facilitador, encontro.get_projeto(), tipo, contexto={"dinamica": encontro})
                if grupo == "MT":
                    for conexao in Conexao.objects.filter(projeto__ano=ano, projeto__semestre=semestre, mentor_tecnico=True):
                        qcertificados += atualiza_certificado(conexao.parceiro.user, conexao.get_projeto(), tipo)
                if grupo == "B":        
                    for membro, banca in recupera_avaliadores_bancas(tipo.exame, ano, semestre):
                        qcertificados += atualiza_certificado(membro, banca.get_projeto(), tipo, contexto={"banca": banca}, alocacao=banca.alocacao)

    if not tipos:
        return HttpResponse("Nenhum tipo de certificado selecionado.", status=401)
    return redirect("certificados_submetidos", edicao=request.POST["edicao"], tipos=",".join(tipos), gerados=qcertificados)


# @login_required
def materias_midia(request):
    """Exibe Matérias que houveram na mídia."""
    tipo_documento = TipoDocumento.objects.get(sigla="MMPA")  # Matéria na Mídia e Publicação Acadêmica
    documentos = Documento.objects.filter(tipo_documento=tipo_documento)
    
    cabecalhos = [{"pt": "Data", "en": "Date"},
                  {"pt": "Anotações", "en": "Notes"},
                  {"pt": "Projeto", "en": "Project"},
                  {"pt": "Documento", "en": "Document"},
                  {"pt": "URLs", "en": "URLs"},
                ]

    context = {
        "titulo": {"pt": "Matérias na Mídia e Publicações Acadêmicas", "en": "Media Coverage and Academic Publications"},
        "documentos": documentos,
        "tipo": tipo_documento,
        "cabecalhos": cabecalhos,
        }
    return render(request, "documentos/materias_midia.html", context)


# @login_required
def relatorios_publicos(request, edicao=None):
    """Exibe relatórios públicos."""

    if request.is_ajax():
        
        projetos = Projeto.objects.all()
        if "edicao" not in request.POST:
            return HttpResponse("Erro ao carregar dados!", status=401)
        edicao = request.POST["edicao"]
        if edicao != "todas":
            ano_semestre = request.POST["edicao"].split('.')
            if len(ano_semestre) != 2:  # Fazendo isso por que algum engracadinho tentar quebrar o servidor
                return HttpResponse("Erro ao carregar dados!", status=401)
            try:
                ano, semestre = int(ano_semestre[0]), int(ano_semestre[1])
            except ValueError:
                return HttpResponse("Erro ao carregar dados!", status=401)
            projetos = projetos.filter(ano=ano, semestre=semestre)
        if "orientador" in request.GET:
            orientador = request.GET.get("orientador", "").strip()
            if orientador.isdigit():
                projetos = projetos.filter(orientador__id=int(orientador))
            else:
                return HttpResponse("Erro ao carregar dados!", status=401)
        
        cabecalhos = [{"pt": "Projeto", "en": "Project"},
                      {"pt": "Estudantes", "en": "Students"},
                      {"pt": "Orientador", "en": "Advisor"},
                      {"pt": "Organização", "en": "Company"},
                      {"pt": "Banca Final", "en": "Examination Board"},
                      {"pt": "Período", "en": "Semester"},
                      {"pt": "Documentos", "en": "Documents"},]
            
        captions = [
            {"sigla": "B", "pt": "Biblioteca", "en": "Library"},
            {"sigla": "S", "pt": "Servidor", "en": "Server"},
        ]

        context = {
            "projetos": projetos,
            "edicao": edicao,
            "cabecalhos": cabecalhos,
            "captions": captions,
        }

    else:

        # Se estiver logado, exibe todos os relatórios públicos e for administrador
        if request.user.is_authenticated and request.user.eh_admin:
            edicoes = get_edicoes(Projeto)[0]  # Administradores podem ver todas as edições
        else:
            relatorios = Documento.objects.filter(tipo_documento__sigla="RPU", confidencial=False)\
                    .order_by("projeto__ano", "projeto__semestre")  # Relatório Publicado
            relatorios = relatorios.values_list("projeto__ano", "projeto__semestre").distinct()
            edicoes = [f"{ano}.{semestre}" for ano, semestre in relatorios]

        selecionada_edicao = edicao
        get_edicao = request.GET.get("edicao", None)
        if get_edicao and get_edicao in edicoes:
            selecionada_edicao = get_edicao

        selecionada_lingua = request.GET.get("lingua", None)
        selecionado_orientador = request.GET.get("orientador", None)

        base_url = reverse("relatorios_publicos")
        endpoints = [
            {"path": f"{base_url}/todas", "method": "GET", "description": "Lista todos os projetos com relatórios públicos."},
            {"path": f"{base_url}?edicao={{valor}}", "method": "GET", "description": "Filtra projetos pela edição. Exemplo: edicao=2025.2"},
            {"path": f"{base_url}?lingua={{valores}}", "method": "GET", "description": "Filtra projetos pelas línguas. Exemplo: lingua=pt ou lingua=en"},
            {"path": f"{base_url}?orientador={{id}}", "method": "GET", "description": "Filtra projetos pelo orientador. Exemplo: orientador=31"}
        ]

        context = {
            "titulo": {"pt": "Documentos Públicos", "en": "Public Documents"},
            "edicoes": edicoes,  #relatorios publicos
            "selecionada_edicao": selecionada_edicao,
            "selecionada_lingua": selecionada_lingua,
            "selecionado_orientador": selecionado_orientador,
            "endpoints": json.dumps(endpoints),
        }
    
    return render(request, "documentos/relatorios_publicos.html", context) 


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def tabela_documentos(request):
    """Exibe tabela com todos os documentos armazenados."""
    cursos_insper = Curso.objects.filter(curso_do_insper=True).order_by("id")
    cursos_externos = Curso.objects.filter(curso_do_insper=False).order_by("id")

    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]

            if edicao == "todas":
                projetos = Projeto.objects.all()
            else:
                ano, semestre = request.POST["edicao"].split('.')
                projetos = Projeto.objects.filter(ano=ano, semestre=semestre)

            if "curso" in request.POST:
                curso = request.POST["curso"]
            else:
                return HttpResponse("Algum erro não identificado.", status=401)

            # Filtra para projetos com estudantes de um curso específico
            if curso != "TE":
                if curso != 'T':
                    projetos = projetos.filter(alocacao__aluno__curso2__sigla_curta=curso).distinct()
                else:
                    projetos = projetos.filter(alocacao__aluno__curso2__in=cursos_insper).distinct()

        cabecalhos = [{"pt": "Projeto", "en": "Project"},
                        {"pt": "Estudantes", "en": "Students"},
                        {"pt": "Orientador", "en": "Advisor"},
                        {"pt": "Período", "en": "Semester"},
                        {"pt": "Organização", "en": "Company"},
                        {"pt": "Banca Final", "en": "Examination Board"},
                        {"pt": "Documentos", "en": "Documents"},]

        context = {
            "projetos": projetos,
            "edicao": edicao,
            "cabecalhos": cabecalhos,
        }

    else:
    
        informacoes = [
            (".tit_ori", "Título Original", "Original Title"),
            (".curso", "Curso", "Program"),
            (".coorientadores", "Coorientadores", "Co-advisors"),
            (".confidencial", "Confidenciais", "Confidential"),
        ]

        context = {
            "titulo": { "pt": "Documentação dos Projetos", "en": "Project Documents"},
            "edicoes": get_edicoes(Projeto)[0],
            "informacoes": informacoes,
            "cursos": cursos_insper,
            "cursos_externos": cursos_externos,
        }

    return render(request, "documentos/tabela_documentos.html", context)



@login_required
@permission_required("users.altera_professor", raise_exception=True)
def exportar_documentos_projetos(request):
    """Exibe tabela com todos os documentos armazenados."""
    cursos_insper = Curso.objects.filter(curso_do_insper=True).order_by("id")
    cursos_externos = Curso.objects.filter(curso_do_insper=False).order_by("id")
    
    tipos_documentos = TipoDocumento.objects.filter(projeto=True)

    context = {
        "titulo": {"pt": "Exportar Documentos dos Projetos", "en": "Export Project Documents"},
        "edicoes": get_edicoes(Projeto)[0],
        "cursos": cursos_insper,
        "cursos_externos": cursos_externos,
        "lista": tipos_documentos,
    }

    if "edicao" in request.POST:
        edicao = request.POST["edicao"]

        if edicao == "todas":
            projetos = Projeto.objects.all()
        else:
            ano, semestre = request.POST["edicao"].split('.')
            projetos = Projeto.objects.filter(ano=ano, semestre=semestre)

        if "curso" in request.POST:
            curso = request.POST["curso"]
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        # Filtra para projetos com estudantes de um curso específico
        curso_sigla = ""
        if curso != "TE":
            if curso != 'T':
                projetos = projetos.filter(alocacao__aluno__curso2__sigla_curta=curso).distinct()
                curso_sigla = Curso.objects.get(sigla_curta=curso).sigla + "_"
            else:
                projetos = projetos.filter(alocacao__aluno__curso2__in=cursos_insper).distinct()

        context["projetos"] = projetos
        context["edicao"] = edicao

        if request.is_ajax():
            pass

        elif request.method == "POST":  # Significa que o usuário clicou no botão de exportar

            selecionados = request.POST.getlist("selection")
            tipos_documentos_selecionados = TipoDocumento.objects.filter(sigla__in=selecionados)

            # Return all the objects that point to files
            documentos = Documento.objects.filter(projeto__in=projetos, tipo_documento__in=tipos_documentos_selecionados)
            
            # Create a zip file
            nome_arquivo = "documentos_" + curso_sigla + edicao.replace('.', '_') + ".zip"
            # Random sequence of characters to avoid name conflicts
            sequencia_aleatoria = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            
            zip_path = os.path.join(settings.MEDIA_ROOT + "/tmp", "documentos_" + sequencia_aleatoria + ".zip")
            with zipfile.ZipFile(zip_path, "w") as zip_file:
                
                # Loop over all documents
                for documento in documentos:
                    projeto_titulo = documento.projeto.get_titulo_org_periodo_seguro()
                    
                    if documento.usuario and documento.usuario.username:
                        username = re.sub(r'\W+', '', documento.usuario.username.replace(' ', '_'))
                    else:
                        username = "sem_usuario"

                    if documento.tipo_documento and documento.tipo_documento.nome:
                        tipo_documento = re.sub(r"\W+", "", documento.tipo_documento.nome.replace(' ', '_'))
                    else:
                        tipo_documento = "sem_tipo_documento"

                    # Get the path of the file
                    if documento.documento:
                        local_path = os.path.join(settings.MEDIA_ROOT, "{0}".format(documento.documento))
                        file_path = os.path.abspath(local_path)
                        if ".." in file_path:
                            raise PermissionDenied
                        if os.path.exists(file_path):
                            # Add the file to the zip file
                            virtual_path = projeto_titulo
                            if documento.tipo_documento and documento.tipo_documento.individual:
                                virtual_path = virtual_path + "/" + username
                            
                            basename = os.path.basename(file_path)
                            _, extension = os.path.splitext(basename)
                            filename = tipo_documento + extension
                            arcname = os.path.join(virtual_path, filename)
                            unique_arcname = generate_unique_arcname(zip_file, arcname)
                            zip_file.write(file_path, arcname=unique_arcname)

                    if documento.link:
                        # Documento does not have a file, create a temporary text file
                        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                            redirect_content = "<html><head><meta http-equiv='refresh' content='0; url={0}'></head></html>".format(documento.link)
                            temp_file.write(redirect_content.encode("utf-8"))
                            temp_file_path = temp_file.name
                        
                        virtual_path = projeto_titulo
                        if documento.tipo_documento and documento.tipo_documento.individual:
                            virtual_path = virtual_path + "/" + username
                        
                        filename = tipo_documento + ".html"
                        arcname = os.path.join(virtual_path, filename)
                        unique_arcname = generate_unique_arcname(zip_file, arcname)
                        zip_file.write(temp_file_path, arcname=unique_arcname)
                        # The file is no longer needed, removing it
                        os.remove(temp_file_path)

            # Open the zip file and return it as a response
            return FileResponse(open(zip_path, "rb"), as_attachment=True, filename=nome_arquivo)

    return render(request, "documentos/exportar_documentos_projetos.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def exibir_ocultar_notas(request):
    """Controla que notas exibir ou ocultar para os alunos."""

    exames = Exame.objects.all()
    context = {
        "titulo": {"pt": "Exibir ou Ocultar Notas", "en": "Show or Hide Grades"},
        "edicoes": get_edicoes(Projeto)[0],
        "lista": exames,
    }

    if "edicao" in request.POST:
        edicao = request.POST["edicao"]

        if edicao == "todas":
            return HttpResponse("Erro, sem suporte para todas as edições.", status=401)
        else:
            ano, semestre = request.POST["edicao"].split('.')

        context["edicao"] = edicao
        context["selecionada_edicao"] = edicao

        if request.is_ajax():
            pass

        elif request.method == "POST":  # Significa que o usuário clicou no botão de exportar
            selecionados = request.POST.getlist("selection")
            for exame in exames:
                (exibe, _created)  = ExibeNota.objects.get_or_create(exame=exame, ano=ano, semestre=semestre)
                exibe.exibe = exame.sigla in selecionados
                exibe.save()

    return render(request, "documentos/exibir_ocultar_notas.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def tabela_seguros(request):
    """Exibe tabela com todos os seguros armazenados."""
    tipo_documento = TipoDocumento.objects.get(nome="Seguros")
    seguros = Documento.objects.filter(tipo_documento=tipo_documento)
    context = {
        "titulo": {"pt": "Seguros Emitidos", "en": "Insurance Documents"},
        "seguros": seguros,
        }
    return render(request, "documentos/tabela_seguros.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def tabela_atas(request):
    """Exibe tabela com todos os seguros armazenados."""
    try:
        tipo_ata = TipoDocumento.objects.get(nome="Ata do Comitê")
        atas = Documento.objects.filter(tipo_documento=tipo_ata).order_by("-data")
    except TipoDocumento.DoesNotExist:
        return HttpResponse("Tipo de Documento para Ata do Comitê não encontrado.", status=401)

    try:
        tipo_template = TipoDocumento.objects.get(sigla="TAC")  # Template Ata Comitê
        template = Documento.objects.filter(tipo_documento=tipo_template).last()
    except TipoDocumento.DoesNotExist:
        return HttpResponse("Tipo de Documento para Template de Ata do Comitê não encontrado.", status=401)

    context = {
        "titulo": {"pt": "Atas do Comitê Capstone", "en": "Capstone Committee Minutes"},
        "atas": atas,
        "template": template,
        "tipo": tipo_ata,
    }
    return render(request, "documentos/tabela_atas.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def tabela_imagens(request):
    """Exibe tabela com todos as imagens (vídeos e fotos) produzidos no semestre."""
    try:
        tipo_imagens = TipoDocumento.objects.get(nome="Imagens do Semestre")
        imagens = Documento.objects.filter(tipo_documento=tipo_imagens).order_by("-data")
    except TipoDocumento.DoesNotExist:
        return HttpResponse("Tipo de Documento para Imagens do Semestre não encontrado.", status=401)

    context = {
        "titulo": {"pt": "Vídeos e Fotos do Semestre", "en": "Semester Videos and Photos"},
        "documentos": imagens,
        "tipo": tipo_imagens,
    }
    return render(request, "documentos/tabela_imagens.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def contratos_assinados(request):
    """Exibe tabela com todos os documentos armazenados."""

    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]

            if edicao == "todas":
                projetos = Projeto.objects.all()
            else:
                ano, semestre = request.POST["edicao"].split('.')
                projetos = Projeto.objects.filter(ano=ano, semestre=semestre)


        cabecalhos = [{"pt": "Organização", "en": "Organization"},
                        {"pt": "Projeto", "en": "Project"},
                        {"pt": "Conexões", "en": "Connections"},
                        {"pt": "Estudantes", "en": "Students"},
                        {"pt": "Orientador", "en": "Advisor"},
                        {"pt": "Período", "en": "Period"},
                        {"pt": "Contrato(s)", "en": "Contract(s)"},
                        ]
        
        context = {
            "projetos": projetos,
            "edicao": edicao,
            "cabecalhos": cabecalhos
        }

    else:

        context = {
            "titulo": {"pt": "Contratos Assinados", "en": "Signed Contracts"},
            "edicoes": get_edicoes(Projeto)[0],
            }

    return render(request, "documentos/contratos_assinados.html", context)


@login_required
@permission_required("users.view_administrador", raise_exception=True)
def duplicar_publicar(request, relatorio_id):
    """Duplica um relatório final de revisão, tornando-o público."""
    if not request.user.is_authenticated or not request.user.eh_admin:
        return HttpResponse("Sem privilégios necessários", status=401)

    relatorio = get_object_or_404(Documento, pk=relatorio_id)
    if relatorio.tipo_documento.sigla != "RFR":
        return HttpResponse("Apenas Relatórios Finais de Revisão podem ser duplicados.", status=401)

    novo_relatorio = Documento()
    novo_relatorio.projeto = relatorio.projeto
    novo_relatorio.tipo_documento = get_object_or_404(TipoDocumento, sigla="RPU")  # Relatório Público
    novo_relatorio.usuario = relatorio.usuario
    novo_relatorio.confidencial = False
    novo_relatorio.data = datetime.now().date()
    novo_relatorio.anotacao = "Duplicado de " + str(relatorio.tipo_documento) +  ( (" - " + relatorio.anotacao ) if relatorio.anotacao else "")
    if relatorio.documento:
        novo_relatorio.documento = relatorio.documento
    if relatorio.link:
        novo_relatorio.link = relatorio.link
    novo_relatorio.save()

    mensagem = {
        "pt": "Relatório Final de Revisão duplicado como Relatório Público.",
        "en": "Final Review Report duplicated as Public Report.",
    }
    context = {
        "voltar": True,
        "area_principal": True,
        "mensagem": mensagem,
    }
    return render(request, "generic_ml.html", context=context)

