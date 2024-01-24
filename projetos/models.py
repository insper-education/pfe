#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

import datetime
import string
import random
import re

from urllib.parse import quote

from django.db import models
from django.db.models import F

from django.urls import reverse  # To generate URLS by reversing URL patterns
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib import admin
from django.template.defaultfilters import slugify
from django.utils.encoding import force_text
from django.shortcuts import get_object_or_404

from .support import get_upload_path

from estudantes.models import Relato
from operacional.models import Curso
from academica.models import Exame
import users.models

from .tipos import TIPO_EVENTO

#from professores.support import converte_conceitos
def converte_conceitos(nota):
    if( nota >= 9.5 ): return ("A+")
    if( nota >= 9.0 ): return ("A")
    if( nota >= 8.0 ): return ("B+")
    if( nota >= 7.0 ): return ("B")
    if( nota >= 6.0 ): return ("C+")
    if( nota >= 5.0 ): return ("C")
    if( nota >= 4.0 ): return ("D+")
    if( nota >= 3.0 ): return ("D")
    if( nota >= 2.0 ): return ("D-")
    if( nota >= 0.0 ): return ("I")
    return "inválida"

### PROBLEMA DE CIRCULARIDADE ###

# REMOVER
from .tipos import TIPO_DE_DOCUMENTO

from documentos.models import TipoDocumento

class Organizacao(models.Model):
    """Dados das organizações que propõe projetos para o PFE."""

    nome = models.CharField("Nome Fantasia", max_length=100, unique=True,
                            help_text='Nome fantasia da organização parceira')
    sigla = models.CharField("Sigla", max_length=20, unique=True,
                             help_text='Sigla usada pela organização parceira')
    endereco = models.TextField("Endereço", max_length=200, null=True, blank=True,
                                help_text='Endereço da organização parceira')
    website = models.URLField("website", max_length=250, null=True, blank=True,
                              help_text='website da organização parceira')
    informacoes = models.TextField("Informações", max_length=1000, null=True, blank=True,
                                   help_text='Informações sobre a organização parceira')
    logotipo = models.ImageField("Logotipo", upload_to=get_upload_path, null=True, blank=True,
                                 help_text='Logotipo da organização parceira')
    cnpj = models.CharField("CNPJ", max_length=14, null=True, blank=True, 
                            help_text='Código de CNPJ da empresa')
    inscricao_estadual = models.CharField("Inscrição Estadual", max_length=15,
                                          null=True, blank=True,
                                          help_text='Código da inscrição estadual')
    razao_social = models.CharField("Razão Social", max_length=100, null=True, blank=True,
                                    help_text='Razão social da organização parceira')
    ramo_atividade = models.TextField("Ramo de Atividade", max_length=1000, null=True, blank=True,
                                      help_text='Ramo de atividade da organização parceira')

    estrelas = models.PositiveSmallIntegerField(default=0, help_text='Interesse para o semestre')

    area_curso = models.ManyToManyField("operacional.Curso", blank=True,
                                        help_text="Curso que mais se identifica com a área da organização")


    class Meta:
        ordering = [ "nome",]
        verbose_name = "Organização"
        verbose_name_plural = "Organizações"

    @classmethod
    def create(cls):
        """Cria um objeto (entrada) em Organizacao."""
        organizacao = cls()
        return organizacao

    def __str__(self):
        """Retorno padrão textual."""
        return self.nome

    def sigla_limpa(self):
        """Retorna o texto da sigla sem caracteres especiais ou espaço."""
        sigla = force_text(self.sigla).strip().replace(' ', '_')
        sigla = re.sub(r'(?u)[^-\w.]', '', sigla)
        return sigla


class Projeto(models.Model):
    """Dados dos projetos para o PFE."""

    titulo = models.CharField("Título", max_length=160,
                              help_text='Título Provisório do projeto')
    titulo_final = models.CharField("Título Final", max_length=160, null=True,
                                    blank=True,
                                    help_text='Título Final do projeto')

    # MANTER COM UMA DESCRIÇÃO ATUALIZADA
    descricao = models.TextField("Descrição", max_length=3000, null=True, blank=True,
                                 help_text='Descricao do projeto')

    # CAMPO ANTIGO, MANTIDO SÓ POR HISTÓRICO
    areas = models.TextField("Áreas", max_length=1000,
                             help_text='Áreas da engenharia envolvidas no projeto')

    organizacao = models.ForeignKey(Organizacao, null=True, blank=True, on_delete=models.SET_NULL,
                                    help_text='Organização parceira que propôs projeto')

    avancado = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL,
                                 help_text='projeto original em caso de avançado')

    ano = models.PositiveIntegerField("Ano",
                                      validators=[MinValueValidator(2018), MaxValueValidator(3018)],
                                      help_text='Ano que o projeto comeca')

    semestre = models.PositiveIntegerField("Semestre",
                                           validators=[MinValueValidator(1), MaxValueValidator(2)],
                                           help_text='Semestre que o projeto comeca')

    orientador = models.ForeignKey('users.Professor', null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='professor_orientador',
                                   help_text='professor orientador do projeto')

    proposta = models.ForeignKey('Proposta', null=True, blank=True, on_delete=models.SET_NULL,
                                 help_text='Proposta original do projeto')

    time_misto = models.BooleanField("Time Misto", default=False,
                                        help_text='Caso o projeto conte com membros externos a instituição')

    class Meta:
        ordering = [ "organizacao", "ano", "semestre"]
        permissions = (("altera_empresa", "Empresa altera valores"),
                       ("altera_professor", "Professor altera valores"), )

    @classmethod
    def create(cls, proposta):
        """Cria um Projeto (entrada) na Banca."""
        projeto = cls(proposta=proposta)
        return projeto
    
    # Methods
    @property
    def procura_de_alunos(self):
        """Retorna só 4."""
        return 4  # REFAZER (OU ABANDONAR DE VEZ)

    def get_absolute_url(self):
        """Returns the url to access a particular instance of MyModelName."""
        return reverse('projeto-detail', args=[str(self.id)])

    def get_titulo(self):
        """Caso tenha titulo atualizado, retorna esse, senão retorna o original e único."""
        if self.titulo_final:
            return self.titulo_final
        if not self.titulo:
            return "PROBLEMA NA IDENTIFICAÇÃO DO TÍTULO DO PROJETO"
        return self.titulo

    def certificado_orientador(self):
        """Retorna link do certificado."""
        certificado = Certificado.objects.filter(usuario=self.orientador.user, projeto=self, tipo_de_certificado=101)
        return certificado

    def __str__(self):
        """Retorno padrão textual."""
        texto = ""

        if self.organizacao and self.organizacao.sigla:
            texto = self.organizacao.sigla
        else:
            texto = "SEM ORGANIZAÇÃO DEFINIDA"

        if self.ano and self.semestre:
            texto += " (" + str(self.ano) + "." + str(self.semestre) + ") "
        else:
            texto += " (SEM PERÍODO DEFINIDO)"

        return texto + self.get_titulo()

    def tem_relatos(self):
        """Retorna todos os possiveis relatos quinzenais para o projeto."""
        
        # Antes de 2022 os relatores era realizados no Blackboard
        # Essa função em hardcode não é ideal, mas resolve o problema
        if self.ano < 2022:
            return Evento.objects.none()
        
        if self.semestre == 1:
            eventos = Evento.objects.filter(tipo_de_evento=20, endDate__year=self.ano, endDate__month__lt=7)
        else:
            eventos = Evento.objects.filter(tipo_de_evento=20, endDate__year=self.ano, endDate__month__gt=6)

        return eventos

    # @property
    def get_relatos(self):
        """Retorna todos os possiveis relatos quinzenais para o projeto."""
        
        proximo = datetime.date.today() + datetime.timedelta(days=14)

        eventos = self.tem_relatos().filter(startDate__lt=proximo).order_by("endDate")

        relatos = []
        avaliados = []  # se o orientador fez alguma avaliação dos relatos

        for index in range(len(eventos)):
        
            if not index: # index == 0:
                relato = Relato.objects.filter(alocacao__projeto=self, momento__lte=eventos[0].endDate + datetime.timedelta(days=1))

            else:
                relato = Relato.objects.filter(alocacao__projeto=self, momento__gt=eventos[index-1].endDate + datetime.timedelta(days=1), momento__lte=eventos[index].endDate + datetime.timedelta(days=1))

            avaliado = []
            for r in relato:
                if r.avaliacao > 0:
                    avaliado.append([True, r.alocacao.aluno])
                if r.avaliacao == 0:
                    avaliado.append([False, r.alocacao.aluno])
                    
            avaliados.append(avaliado)

            relatos.append([u[0] for u in relato.order_by().values('alocacao').distinct().values_list('alocacao_id')])
    
        return zip(eventos, relatos, avaliados)

    @property
    def get_planos_de_orientacao(self):
        """Retorna todos os planos de orientação do projeto."""
        # (28, 'Plano de Orientação'),
        tipo_documento = TipoDocumento.objects.get(nome="Plano de Orientação")
        documentos = Documento.objects.filter(tipo_documento=tipo_documento, projeto=self)
        return documentos

    @property
    def has_relatos(self):
        """Retorna se houver algum relato quinzenal para o projeto."""            
        return Relato.objects.filter(alocacao__projeto=self).exists()

    @property
    def media_falconi(self):
        exame = Exame.objects.get(titulo="Falconi")
        aval_banc_falconi = Avaliacao2.objects.filter(projeto=self, exame=exame)  # Falc.
        nota_banca_falconi, _, _ = users.models.Aluno.get_banca(None, aval_banc_falconi)
        return nota_banca_falconi

    @property
    def media_bancas(self):
        exames = Exame.objects.filter(titulo="Banca Final") | Exame.objects.filter(titulo="Banca Intermediária")
        aval_bancas = Avaliacao2.objects.filter(projeto=self, exame__in=exames)  # Bancas.
        nota_bancas, _, _ = users.models.Aluno.get_banca(None, aval_bancas)
        return nota_bancas

    @property
    def media_orientador(self):
        alocacoes = users.models.Alocacao.objects.filter(projeto=self)
        if alocacoes:
            primeira = alocacoes.first()
            medias = primeira.get_media

            nota = 0
            peso = 0
            if ("peso_grupo_inter" in medias) and (medias["peso_grupo_inter"] is not None) and (medias["peso_grupo_inter"] > 0):
                nota += medias["nota_grupo_inter"]
                peso += medias["peso_grupo_inter"]
                
            if ("peso_grupo_final" in medias) and (medias["peso_grupo_final"] is not None) and (medias["peso_grupo_final"] > 0):
                nota += medias["nota_grupo_final"]
                peso += medias["peso_grupo_final"]
                
            if peso:
                return nota/peso
            return 0.0

        else:
            return 0.0


    @property
    def medias(self):
        notas = [0,0,0,0]
        notas[0] = self.media_orientador
        notas[1] = self.media_bancas
        notas[2] = self.media_falconi
        notas[3] = (notas[0] + notas[1] + notas[2])/3
        return notas

    
    def periodo(self):
        configuracao = get_object_or_404(Configuracao)
        if self.ano >= configuracao.ano:
            return "Atuais"
        if self.ano == configuracao.ano and self.semestre >= configuracao.semestre:
            return "Atuais"
        return "Anteriores"
    
    
    @property
    def get_edicao(self):
        return str(self.ano)+"."+str(self.semestre)


class Proposta(models.Model):
    """Dados da Proposta de Projeto para o PFE."""

    slug = models.SlugField("slug", unique=True, max_length=64, null=True, blank=True,
                            help_text="Slug para o endereço da proposta")

    nome = models.CharField("Nome", max_length=127,
                            help_text='Nome(s) de quem submeteu o projeto')
    email = models.CharField("e-mail", max_length=80, null=True, blank=True,
                             help_text='e-mail(s) de quem está dando o Feedback')
    website = models.URLField("website", max_length=250, null=True, blank=True,
                              help_text='website da organização')

    nome_organizacao = models.CharField("Organização", max_length=120, null=True, blank=True,
                                        help_text='Nome da Organização/Empresa')

    endereco = models.TextField("Endereço", max_length=400, null=True, blank=True,
                                help_text='Endereço da Instituiçã')

    contatos_tecnicos = models.TextField("Contatos Técnicos", max_length=400,
                                         help_text='Contatos Técnicos')

    contatos_administrativos = models.TextField("Contatos Administrativos", max_length=400,
                                                null=True, blank=True,
                                                help_text='Contatos Administrativos')

    descricao_organizacao = models.TextField("Descrição da Organização", max_length=3000,
                                             null=True, blank=True,
                                             help_text='Descrição da Organização')

    departamento = models.TextField("Descrição do Depart.", max_length=3000, null=True, blank=True,
                                    help_text='Descrição do departamento que propôs o projeto')

    titulo = models.CharField("Título", max_length=160,
                              help_text='Título Provisório do projeto')

    descricao = models.TextField("Descrição", max_length=3000,
                                 help_text='Descricao do projeto')

    expectativas = models.TextField("Expectativas", max_length=3000,
                                    help_text='Expectativas em relação ao projeto')

    recursos = models.TextField("Recursos", max_length=1000, null=True, blank=True,
                                help_text='Recursos a serem disponibilizados aos Alunos')

    observacoes = models.TextField("Outras Observações", max_length=3000, null=True, blank=True,
                                   help_text='Outras Observações')

    anexo = models.FileField("Anexo", upload_to=get_upload_path, null=True, blank=True,
                             help_text='Documento Anexo')

    # O principal interesse da empresa com o projeto é:
    TIPO_INTERESSE = (
        (10, 'aprimorar o entendimento de uma tecnologia/solução com foco no médio prazo, sem interesse a curto prazo.'),
        (20, 'realizar uma prova de conceito, podendo finalizar o desenvolvimento internamente dependendo do resultado.'),
        (30, 'iniciar o desenvolvimento de um projeto que, potencialmente, será continuado internamente no curto prazo.'),
        (40, 'identificar talentos, com intenção de contratá-los para continuar esse ou outros projetos internamente.'),
        (50, 'mentorar estudantes para que empreendam com um produto ou tecnologia da empresa, podendo estabelecer uma parceria ou contrato de fornecimento caso seja criada uma startup a partir desse projeto.'),
    )
    aprimorar = models.BooleanField(default=False, help_text=TIPO_INTERESSE[0][1])
    realizar = models.BooleanField(default=False, help_text=TIPO_INTERESSE[1][1])
    iniciar = models.BooleanField(default=False, help_text=TIPO_INTERESSE[2][1])
    identificar = models.BooleanField(default=False, help_text=TIPO_INTERESSE[3][1])
    mentorar = models.BooleanField(default=False, help_text=TIPO_INTERESSE[4][1])
    
    # ESSE ESTA OBSOLETO
    # tipo_de_interesse = models.PositiveSmallIntegerField(choices=TIPO_INTERESSE,
    #                                                      null=True, blank=True,
    #                                                      help_text='O principal interesse da empresa com o projeto é')

    internacional = models.BooleanField("Internacional", default=False,
                                        help_text='Caso a proposta venha de um parceiro internacional, o que afeta a lingua de comunicação do projeto')

    intercambio = models.BooleanField("Intercâmbio", default=False,
                                        help_text='Caso a proposta venha de um intercâmbio')

    # Preenchidos automaticamente
    ano = models.PositiveIntegerField("Ano",
                                      validators=[MinValueValidator(2018), MaxValueValidator(3018)],
                                      help_text='Ano que o projeto comeca')
    semestre = models.PositiveIntegerField("Semestre",
                                           validators=[MinValueValidator(1), MaxValueValidator(2)],
                                           help_text='Semestre que o projeto comeca')

    organizacao = models.ForeignKey(Organizacao, on_delete=models.SET_NULL, null=True, blank=True,
                                    help_text='Organização parceira que propôs projeto')

    disponivel = models.BooleanField("Disponível", default=False,
                                     help_text='Se projeto está atualmente disponível para alunos')

    autorizado = models.ForeignKey("users.PFEUser", null=True, blank=True,
                                   on_delete=models.SET_NULL,
                                   help_text='Quem autorizou a ser publicado para os alunos')

    fechada = models.BooleanField(default=False, help_text='Se a proposta virou um projeto')

    perfil1 = models.ManyToManyField("operacional.Curso", help_text="Perfil de curso desejado para estudante", related_name="perfil1")
    perfil2 = models.ManyToManyField("operacional.Curso", help_text="Perfil de curso desejado para estudante", related_name="perfil2")
    perfil3 = models.ManyToManyField("operacional.Curso", help_text="Perfil de curso desejado para estudante", related_name="perfil3")
    perfil4 = models.ManyToManyField("operacional.Curso", help_text="Perfil de curso desejado para estudante", related_name="perfil4")

    data = models.DateTimeField(default=datetime.datetime.now,
                                help_text='data e hora da criação da proposta de projeto')

    colaboracao = models.ForeignKey(Organizacao, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='colaboracao',
                                    help_text='Organização colaborando para a proposta de projeto')


    # Conformidade de Proposta

    habilidades = models.BooleanField(default=False, help_text='A proposta de projeto requer conhecimentos e habilidades adquiridos em anos anteriores do curso de engenharia?')
    #Does the project proposal require knowledge and skills acquired from previous years of engineering course work?

    design = models.BooleanField(default=False, help_text='A proposta do projeto exige que os alunos apliquem um processo sistemático de projeto de engenharia para um sistema, componente ou processo para atender às necessidades desejadas?')
    #Does the project proposal require students to apply a systematic engineering design process for a system, component, or process to meet desired needs?

    realistico = models.BooleanField(default=False, help_text='A proposta do projeto representa uma experiência do mundo real ou da indústria real que é solicitada formalmente por uma organização externa?')
    #Does the project proposal represent a have a real-world or real-industry experience that are formally requested by an external organization?

    normas = models.BooleanField(default=False, help_text='A proposta do projeto tem oportunidade de incorporar padrões de engenharia apropriados que podem ser referenciados posteriormente nos relatórios do projeto?')
    #Does the project proposal have opportunity to incorporates appropriate engineering standards that can be further referenced in the project reports?

    restricoes = models.BooleanField(default=False, help_text='A proposta do projeto possui um desafio de design que incorpora várias restrições realistas, como econômica, ambiental, social, política, ética, saúde e segurança, capacidade de fabricação e/ou sustentabilidade?')
    #Does the project proposal design challenge incorporate multiple realistic constraints, such as economic, environmental, social, political, ethical, health and safety, manufacturability, and/or sustainability?

    experimentacao = models.BooleanField(default=False, help_text='A proposta do projeto requer experimentação e habilidades práticas?')
    #Does the project proposal require experimentation and hands-on skills?

    equipe = models.BooleanField(default=False, help_text='A proposta do projeto permite o trabalho em equipe entre alunos de um ou mais cursos de engenharia?')
    #Does the project proposal allow teamwork among students in one or more engineering programs?

    duracao = models.BooleanField(default=False, help_text='A proposta do projeto possui uma complexidade adequada a um semestre letivo (cerca de 4,5 meses)?')
    #Does the project proposal complexity is appropriate to one academic semester (around 4.5 months)?

    carga = models.BooleanField(default=False, help_text='A proposta do projeto é de complexidade suficiente para permitir que cada membro da equipe contribua com cerca de 360 horas entre aula, laboratório, reuniões e fora do horário de aula?')
    #Does the project proposal is sufficient complexity to allow each team member to contribute about 360 hours among class, laboratory, meetings, and outside class time?

    mensuravel = models.BooleanField(default=False, help_text='A proposta do projeto tem objetivos concretos e mensuráveis?')
    #Does the project proposal have concrete and measurable goals?


    class Meta:
        ordering = [ "organizacao", "ano", "semestre",]
        verbose_name = "Proposta"
        verbose_name_plural = "Propostas"

    @classmethod
    def create(cls):
        """Cria um objeto (entrada) em Propostas."""
        proposta = cls()
        return proposta

    def __str__(self):
        """Retorno padrão textual."""
        if self.organizacao:
            return self.organizacao.sigla+" ("+str(self.ano)+"."+str(self.semestre)+") "+self.titulo
        if self.nome_organizacao:
            return self.nome_organizacao+" ("+str(self.ano)+"."+str(self.semestre)+") "+self.titulo
        return "ORG. NÃO DEFINIDA"+" ("+str(self.ano)+"."+str(self.semestre)+") "+self.titulo

    # pylint: disable=arguments-differ
    def save(self, *args, **kwargs):
        if (not self.id) or (not self.slug):
            senha = ''.join(random.SystemRandom().\
                                   choice(string.ascii_uppercase + string.digits) for _ in range(6))
            self.slug = slugify(str(self.ano)+"-"+str(self.semestre)+"-"+self.titulo[:50]+"-"+senha)

        super(Proposta, self).save(*args, **kwargs)

    def get_absolute_url(self):
        """Caminho para editar uma proposta."""
        return reverse('proposta_editar', kwargs={'slug': self.slug})

    def get_interesses(self):
        interesses = [
            ["aprimorar", Proposta.TIPO_INTERESSE[0][1], self.aprimorar],
            ["realizar", Proposta.TIPO_INTERESSE[1][1], self.realizar],
            ["iniciar", Proposta.TIPO_INTERESSE[2][1], self.iniciar],
            ["identificar", Proposta.TIPO_INTERESSE[3][1], self.identificar],
            ["mentorar", Proposta.TIPO_INTERESSE[4][1], self.mentorar],
        ]
        return interesses
    
    def get_interesses_selecionados(self):
        interesses = []
        if self.aprimorar: interesses += [["aprimorar", Proposta.TIPO_INTERESSE[0][1], self.aprimorar]]
        if self.realizar: interesses += [["realizar", Proposta.TIPO_INTERESSE[1][1], self.realizar]]
        if self.iniciar: interesses += [["iniciar", Proposta.TIPO_INTERESSE[2][1], self.iniciar]]
        if self.identificar: interesses += [["identificar", Proposta.TIPO_INTERESSE[3][1], self.identificar]]
        if self.mentorar: interesses += [["mentorar", Proposta.TIPO_INTERESSE[4][1], self.mentorar]]
        return interesses

    def get_nativamente(self):
        """Retorna em string com curso mais nativo da proposta."""

        count = {}
        total = 0

        for curso in Curso.objects.all():
            count[curso] = 0

        for ferfil in [self.perfil1, self.perfil3, self.perfil3, self.perfil4]:
            for curso in ferfil.all(): 
                count[curso] += 1
                total += 1

        if total == 0:
            return " "

        keymax = max(count, key= lambda x: count[x])
        if count[keymax] > total//2:
            return keymax
        return "?"

    def get_anexo(self):
        """Nome do arquivo do anexo."""
        return self.anexo.name.split('/')[-1]

class Configuracao(models.Model):
    """Armazena os dados básicos de funcionamento do sistema."""

    ano = models.PositiveIntegerField("Ano",
                                      validators=[MinValueValidator(2018), MaxValueValidator(3018)],
                                      help_text='Ano que o projeto comeca')
    semestre = models.PositiveIntegerField("Semestre",
                                           validators=[MinValueValidator(1), MaxValueValidator(2)],
                                           help_text='Semestre que o projeto comeca')

    recipient_reembolso = models.CharField(max_length=127, blank=True,
                                           help_text='Separar lista por ponto e virgula')

    liberadas_propostas = models.BooleanField(default=False,
                                              help_text='Para estudantes visualizarem propostas')

    min_props = models.PositiveIntegerField("Mínimo de Propostas para Estudantes Selecionarem", default=5,
        help_text='Quantidade mínima de propostas a serem selecionas pelos estudantes')
    
    maxMB_filesize = models.PositiveIntegerField("Tamanho máximo de arquivo", default=2000,
        help_text='Tamanho máximo de arquivo em MB')

    coordenacao = models.ForeignKey('users.Administrador', null=True, blank=True, on_delete=models.SET_NULL,
                                    help_text='responsável pela coordenação do PFE')

    lingua = models.CharField(max_length=2, blank=True, default="pt",
                              help_text='Língua do sistema')

    prazo_preencher_banca = models.PositiveIntegerField("Prazo para banca", default=30,
                                           help_text='Prazo máximo para membros de uma banca colocarem suas avaliações')

    coordenador = models.CharField(max_length=64, null=True, blank=True,
                                           help_text='Nome para assinatura do coordenador do PFE')

    assinatura = models.ImageField("Assinatura", upload_to=get_upload_path, null=True, blank=True,
                                   help_text="Assinatura do coordenador do PFE")

    ###----------------------Mensagens----------------------###

    msg_aval_pares = models.TextField("Mensagem Avaliação de Pares", max_length=1000, null=True, blank=True,
                                   help_text="Mensagem que descreve como será a Avaliação de Pares")

    msg_email_automatico = models.TextField("Mensagem de Envio Automático", max_length=1000, null=True, blank=True,
                                   help_text="Mensagem de Envio Automático de e-mail")
    
    ###-----------------------------------------------------###

    class Meta:
        verbose_name = "Configuração"
        verbose_name_plural = "Configurações"

    def coordenador_email(self):
        return quote(self.coordenador)
    
    def periodo(self):
        return str(self.ano) + '.' + str(self.semestre)
    
    def proximo_periodo(self):
        if self.semestre == 1:
            semestre = 2
            ano = self.ano
        else:
            ano = self.ano + 1
            semestre = 1

        return str(ano) + '.' + str(semestre)

class ConfiguracaoAdmin(admin.ModelAdmin):
    """Usado para configurar a classe Configuracao."""

    def has_add_permission(self, request):
        # se já existe uma entrada não é possível adicionar outra.
        count = Configuracao.objects.all().count()
        if count == 0:
            return True
        return False


class Disciplina(models.Model):
    """Disciplinas que os alunos podem cursar."""

    nome = models.CharField(max_length=100, help_text='nome')

    def __str__(self):
        """Retorno padrão textual."""
        return self.nome


class Cursada(models.Model):
    """Relacionamento entre um aluno e uma disciplina cursada por ele."""

    disciplina = models.ForeignKey(Disciplina, null=True, blank=True, on_delete=models.SET_NULL,
                                   help_text='disciplina cursada pelo aluno')
    aluno = models.ForeignKey('users.Aluno', null=True, blank=True, on_delete=models.SET_NULL,
                              help_text='aluno que cursou a disciplina')
    nota = models.PositiveSmallIntegerField(validators=[MaxValueValidator(10)],
                                            help_text='nota obtida pelo aluno na disciplina')

    class Meta:
        """Classe Meta."""
        ordering = ["nota"]

    def __str__(self):
        """Retorno padrão textual."""
        return self.aluno.user.username+" >>> "+self.disciplina.nome


class Recomendada(models.Model):
    """Disciplinas recomendadas que um aluno ja tenha cursado para fazer o projeto."""

    disciplina = models.ForeignKey(Disciplina, null=True, on_delete=models.SET_NULL,
                                   help_text='disciplina recomendada para o projeto')
    proposta = models.ForeignKey(Proposta, null=True, on_delete=models.SET_NULL,
                                 help_text='proposta que recomenda a disciplina')

    def __str__(self):
        """Retorno padrão textual."""
        titulo = "???"
        if self.proposta:
            titulo = self.proposta.titulo
        nome = "???"
        if self.disciplina:
            nome = self.disciplina.nome
        return titulo + " >>> " + nome

    @classmethod
    def create(cls):
        """Cria um objeto (entrada) em Recomendada."""
        recomendada = cls()
        return recomendada


class Evento(models.Model):
    """Eventos para a agenda do PFE."""

    location = models.CharField(blank=True, max_length=80,
                                help_text="Onde Ocorrerá o Evento")
    startDate = models.DateField(default=datetime.date.today, blank=True,
                                 help_text="Inicio do Evento")
    endDate = models.DateField(default=datetime.date.today, blank=True,
                               help_text="Fim do Evento")

    tipo_de_evento = models.PositiveSmallIntegerField(choices=[subl[:2] for subl in TIPO_EVENTO],
                                                      null=True, blank=True,
                                                      help_text="Define o tipo do evento a ocorrer")

    descricao = models.CharField(max_length=200, blank=True,
                                 help_text="Descrição do evento")

    observacao = models.CharField(max_length=160, blank=True,
                                  help_text="Qualquer observação relavante")
    
    responsavel = models.ForeignKey("users.PFEUser", null=True, blank=True,
                                   on_delete=models.SET_NULL,
                                   help_text="Responsável pelo evento, por exemplo professor que ministrou a aula")

    def get_title(self):
        """Retorna em string o nome do evento."""
        return self.get_tipo_de_evento_display()
  
    def get_color(self):
        """Retorna uma cor característica do evento para desenhar no calendário."""
        for entry in TIPO_EVENTO:
            if self.tipo_de_evento == entry[0]:
                return entry[2]
        return None

    def get_semester(self):
        """Retorna o semestre do evento."""
        if self.startDate.month <= 6:
            return 1
        return 2

    def get_data(self):
        """Retorna a data do evento."""
        return self.startDate

    def em_prazo(self):
        """Se ainda em prazo."""
        return datetime.date.today() <= self.endDate

    @classmethod
    def create(cls):
        """Cria um objeto (entrada) em Evento."""
        evento = cls()
        return evento

    def __str__(self):
        """Retorno padrão textual."""
        texto = self.get_title()
        if self.startDate:
            texto += " (" + self.startDate.strftime("%d/%m/%Y") + ")"
        return texto

    class Meta:
        ordering = ["startDate"]


class Banca(models.Model):
    """Bancas do PFE."""

    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text='projeto')

    slug = models.SlugField("slug", unique=True, max_length=64, null=True, blank=True,
                            help_text="Slug para o endereço da banca")

    location = models.CharField(null=True, blank=True, max_length=50,
                                help_text='sala em que vai ocorrer banca')
    startDate = models.DateTimeField(default=datetime.datetime.now, null=True, blank=True,
                                     help_text='Inicio da Banca')
    endDate = models.DateTimeField(default=datetime.datetime.now, null=True, blank=True,
                                   help_text='Fim da Banca')
    color = models.CharField(max_length=20, null=True, blank=True,
                             help_text='Cor a usada na apresentação da banca na interface gráfica')
    membro1 = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL,
                                related_name='membro1', help_text='membro da banca')
    membro2 = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL,
                                related_name='membro2', help_text='membro da banca')
    membro3 = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL,
                                related_name='membro3', help_text='membro da banca')
    TIPO_DE_BANCA = ( # não mudar a ordem dos números
        (0, 'Final'),
        (1, 'Intermediária'),
        (2, 'Certificação Falconi'),
    )
    tipo_de_banca = models.PositiveSmallIntegerField(choices=TIPO_DE_BANCA, default=0)
    link = models.CharField(max_length=512, blank=True,
                            help_text='Link para transmissão pela internet se houver')
    def __str__(self):
        return self.projeto.titulo

    @classmethod
    def create(cls, projeto):
        """Cria um objeto (entrada) na Banca."""
        banca = cls(projeto=projeto)
        return banca

    # pylint: disable=arguments-differ
    def save(self, *args, **kwargs):
        if not self.id:
            senha = ''.join(random.SystemRandom().\
                                   choice(string.ascii_uppercase + string.digits) for _ in range(6))

            ano = self.startDate.strftime("%y")
            mes = int(self.startDate.strftime("%m"))

            if mes > 7:
                semestre = "2"
            else:
                semestre = "1"

            self.slug = slugify(ano+semestre+str(self.tipo_de_banca)+senha)

        super(Banca, self).save(*args, **kwargs)

    def get_absolute_url(self):
        """Caminho para avaliar uma banca."""
        return reverse("banca_avaliar", kwargs={"slug": self.slug})

    class Meta:
        ordering = ["startDate"]

    def get_tipo(self):
        """Retorna o tipo da banca."""
        return self.get_tipo_de_banca_display()
    
    def periodo(self):
        configuracao = get_object_or_404(Configuracao)
        if self.startDate.year >= configuracao.ano:
            if configuracao.semestre == 1 and self.startDate.month < 7:
                return "Atuais"
            if configuracao.semestre == 2 and self.startDate.month > 7:
                return "Atuais"
        return "Anteriores"
    
    def get_observacoes_estudantes(self):
        """Retorna as observações dos estudantes."""
        if self.tipo_de_banca == 0:
            observacoes = Observacao.objects.filter(projeto=self.projeto, observacoes_estudantes__isnull=False, exame__titulo="Banca Final")
        elif self.tipo_de_banca == 1:
            observacoes = Observacao.objects.filter(projeto=self.projeto, observacoes_estudantes__isnull=False, exame__titulo="Banca Intermediária")
        elif self.tipo_de_banca == 2:
            observacoes = Observacao.objects.filter(projeto=self.projeto, observacoes_estudantes__isnull=False, exame__titulo="Falconi")
        else:
            observacoes = Observacao.objects.none()
        return observacoes
    
    def get_avaliacoes(self):
        if self.tipo_de_banca == 0:
            avaliacoes = Avaliacao2.objects.filter(projeto=self.projeto, exame__titulo="Banca Final")
        elif self.tipo_de_banca == 1:
            avaliacoes = Avaliacao2.objects.filter(projeto=self.projeto, exame__titulo="Banca Intermediária")
        elif self.tipo_de_banca == 2:
            avaliacoes = Avaliacao2.objects.filter(projeto=self.projeto, exame__titulo="Falconi")
        else:
            avaliacoes = Avaliacao2.objects.none()

        objetivos = {}
        nota = 0
        peso = 0
        pesos = {}
        for avaliacao in avaliacoes:
            if avaliacao.objetivo in objetivos:
                objetivos[avaliacao.objetivo] += avaliacao.nota
                pesos[avaliacao.objetivo] += 1
            else:
                objetivos[avaliacao.objetivo] = avaliacao.nota
                pesos[avaliacao.objetivo] = 1
            nota += float(avaliacao.nota) * float(avaliacao.peso)
            peso += float(avaliacao.peso)
        
        for objetivo in objetivos:
            objetivos[objetivo] = converte_conceitos(objetivos[objetivo]/pesos[objetivo])

        avaliacao = {}
        avaliacao["objetivos"] = objetivos
        avaliacao["nota"] = nota/peso if peso > 0 else 0
        avaliacao["peso"] = peso

        return avaliacao


class Encontro(models.Model):
    """Encontros (para dinâmicas de grupos)."""

    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text='projeto')
    location = models.CharField(blank=True, max_length=280,
                                help_text='sala em que vai ocorrer a dinâmica')
    startDate = models.DateTimeField(default=datetime.datetime.now,
                                     help_text='Inicio da Dinâmica')
    endDate = models.DateTimeField(default=datetime.datetime.now,
                                   help_text='Fim da Dinâmica')
    facilitador = models.ForeignKey('users.PFEUser', null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name='facilitador',
                                    help_text='facilitador da dinâmica')

    def hora_fim(self):
        """Mostra só a hora final do encontro."""
        return self.endDate.strftime("%H:%M")
    hora_fim.short_description = 'Hora Fim'

    def url_location(self):
        """Checa se link."""
        if self.location[:4] == "http":
            return True
        return False

    @classmethod
    def create(cls, startDate, endDate):
        """Cria um objeto (entrada) no Encontro."""
        encontro = cls(startDate=startDate, endDate=endDate)
        return encontro

    def __str__(self):
        return str(self.startDate)


class Anotacao(models.Model):
    """Anotacoes de comunicações com as organizações pareceiras."""

    momento = models.DateTimeField(default=datetime.datetime.now, blank=True,
                                   help_text='Data e hora da comunicação') # hora ordena para dia
    organizacao = models.ForeignKey(Organizacao, null=True, blank=True, on_delete=models.SET_NULL,
                                    help_text='Organização parceira')
    autor = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL,
                              related_name='professor_orientador', help_text='quem fez a anotação')
    texto = models.TextField(max_length=2000, help_text='Anotação')

    TIPO_DE_RETORNO = ( # não mudar a ordem dos números
        (0, "Contactada para enviar proposta"),
        (1, "Interessada em enviar proposta"),
        (2, "Enviou proposta de projeto"),
        (3, "Não vai enviar proposta de projeto"),
        (4, "Confirmamos estudantes para o(s) projeto(s) proposto(s)"),
        (5, "Notificamos que não conseguimos montar projeto"),
        (6, "Contrato fechado para projeto"),
        (7, "Envio de Relatório Final"),
        (10, "Autorizou a publicação do Relatório Final"),
        (11, "Negou a publicação do Relatório Final"),
        (254, "outros"),
    )

    tipo_de_retorno = models.PositiveSmallIntegerField(choices=TIPO_DE_RETORNO, default=0)

    def __str__(self):
        return str(self.momento)

    @classmethod
    def create(cls, organizacao):
        """Cria um objeto (entrada) em Anotação."""
        anotacao = cls(organizacao=organizacao)
        return anotacao

    class Meta:
        verbose_name = 'Anotação'
        verbose_name_plural = 'Anotações'


class Documento(models.Model):
    """Documentos, em geral PDFs, e seus relacionamentos com o PFE."""

    organizacao = models.ForeignKey(Organizacao, null=True, blank=True, on_delete=models.SET_NULL,
                                    help_text="Organização referente o documento")
    usuario = models.ForeignKey("users.PFEUser", null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="Usuário do documento")
    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="Documento do Projeto")
    documento = models.FileField(null=True, blank=True, max_length=160,
                                 upload_to=get_upload_path,
                                 help_text="Documento PDF")
    link = models.URLField("link", max_length=250, null=True, blank=True,
                           help_text="website da organização parceira")
    anotacao = models.CharField(null=True, blank=True, max_length=64,
                                help_text="qualquer anotação sobre o documento em questão")
    data = models.DateTimeField(null=True, blank=True,
                            help_text="Data e hora do documento")
    
    ### REMOVER  ##############################################
    tipo_de_documento = models.PositiveSmallIntegerField(choices=TIPO_DE_DOCUMENTO, default=0)
    ### ######################################################

    tipo_documento = models.ForeignKey("documentos.TipoDocumento", null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="Tipo de documento")

    confidencial = models.BooleanField(default=True, help_text="Documento confidêncial")

    LINGUA_DO_DOCUMENTO = ( # não mudar a ordem dos números
        (0, "Português"),
        (1, "Inglês"),
    )

    lingua_do_documento = models.PositiveSmallIntegerField(choices=LINGUA_DO_DOCUMENTO, default=0)

    def __str__(self):
        return str(self.tipo_documento)

    @classmethod
    def create(cls):
        """Cria um objeto (entrada) em Documento."""
        documento = cls()
        return documento


class Banco(models.Model):
    """Lista dos Bancos Existentes no Brasil."""

    nome = models.CharField(max_length=50,
                            help_text='nome do banco')
    codigo = models.PositiveSmallIntegerField(validators=[MaxValueValidator(999)],
                                              help_text='código do banco')

    @classmethod
    def create(cls, nome, codigo):
        """Cria um objeto (entrada) no Banco."""
        banco = cls(nome=nome, codigo=codigo)
        return banco

    def __str__(self):
        return str(self.nome)


class Reembolso(models.Model):
    """Armazena os reembolsos pedidos pelos alunos do PFE."""

    usuario = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL,
                                help_text='usuário pedindo reembolso')
    banco = models.ForeignKey(Banco, null=True, on_delete=models.SET_NULL,
                              help_text='banco a se fazer o reembolso')
    agencia = models.CharField(max_length=6, null=True, blank=True,
                               help_text='agência no banco')
    conta = models.CharField(max_length=16, null=True, blank=True,
                             help_text='conta no banco')
    descricao = models.TextField(max_length=2000,
                                 help_text='desrição do pedido de reembolso')
    valor = models.DecimalField(max_digits=5, decimal_places=2,
                                help_text='valor a ser reembolsado')
    data = models.DateTimeField(default=datetime.datetime.now,
                                help_text='data e hora da criação do pedido de reembolso')
    nota = models.FileField(upload_to=get_upload_path, null=True, blank=True,
                            help_text='Nota(s) Fiscal(is)')

    @classmethod
    def create(cls, usuario):
        """Cria um objeto (entrada) no Reembolso."""
        reembolso = cls(usuario=usuario)
        return reembolso

    def __str__(self):
        return str(str(self.usuario)+str(self.data))


class Aviso(models.Model):
    """Avisos para a Coordenação do PFE."""

    titulo = models.CharField(max_length=120, null=True, blank=True,
                              help_text="Título do Aviso")

    tipo_de_evento = models.\
        PositiveSmallIntegerField(choices=[subl[:2] for subl in TIPO_EVENTO],
                                  null=True, blank=True,
                                  help_text="Define o tipo do evento de referência")

    delta = models.SmallIntegerField(default=0,
                                     help_text="dias passados do evento definido")
    mensagem = models.TextField(max_length=4096, null=True, blank=True,
                                help_text="mensagem a ser enviar no texto")
    
    ### NÃO DEVE SER MAIS USADO ##############################################
    realizado = models.BooleanField(default=False, help_text='Se já realizado no período')  # NAO MAIS USADO
    data_realizado = models.DateField(default=datetime.date.today, blank=True,
                                      help_text='Data de quando o evento foi realizado pela última vez')
    ##########################################################################
    
    datas_realizado = models.TextField(max_length=4096, default="[]",
                                      help_text="Datas de quando o evento foi realizado")
    

    coordenacao = \
        models.BooleanField(default=False, help_text="Para coordenação do PFE")
    comite_pfe = \
        models.BooleanField(default=False, help_text="Para os membros do comitê do PFE")
    todos_alunos = \
        models.BooleanField(default=False, help_text="Para todos os alunos do semestre")
    todos_orientadores = \
        models.BooleanField(default=False, help_text="Para todos os orientadores do semestre")
    contatos_nas_organizacoes = \
        models.BooleanField(default=False, help_text="Para contatos nas organizações parceiras")

    # Usar get_tipo_de_evento_display em vez disso
    def get_evento(self):
        """Retorna em string o nome do evento."""
        for entry in TIPO_EVENTO:
            if self.tipo_de_evento == entry[0]:
                return entry[1]
        return "Sem evento"

    def __str__(self):
        return str(self.titulo)

    @classmethod
    def create(cls):
        """Cria um objeto (entrada) em Aviso."""
        aviso = cls()
        return aviso


class Entidade(models.Model):
    """Todas as entidades estudantis do Insper."""

    nome = models.CharField(max_length=100,
                            help_text='nome da entidade estudantil')

    def __str__(self):
        return self.nome

class Acompanhamento(models.Model):
    """Acompanhamento das organizacoes parceiras."""

    data = models.DateField(default=datetime.date.today, blank=True,
                            help_text='Data da Resposta')
    autor = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL,
                              help_text='quem enviou a observação de acompanhamento')
    texto = models.TextField(max_length=1000, help_text='Feedback Outros')

    def __str__(self):
        return str(self.data)

    @classmethod
    def create(cls):
        """Cria um objeto (entrada) em Acompanhamento."""
        acompanhamento = cls()
        return acompanhamento


class Feedback(models.Model):
    """Feedback das organizacoes parceiras."""

    data = models.DateField(default=datetime.date.today, blank=True,
                            help_text='Data do Feedback')
    nome = models.CharField(max_length=120, null=True, blank=True,
                            help_text='Nome de quem está dando o Feedback')
    email = models.EmailField(max_length=80, null=True, blank=True,
                              help_text='e-mail de quem está dando o Feedback')
    #isso esta bem baguncado
    empresa = models.CharField(max_length=120, null=True, blank=True,
                               help_text='Empresa de quem está dando o Feedback')
    tecnico = models.TextField(max_length=1000, null=True, blank=True,
                               help_text='Feedback Técnico')
    comunicacao = models.TextField(max_length=1000, null=True, blank=True,
                                   help_text='Feedback Comunicação')
    organizacao = models.TextField(max_length=1000, null=True, blank=True,
                                   help_text='Feedback Organização')
    outros = models.TextField(max_length=1000, null=True, blank=True,
                              help_text='Feedback Outros')

    nps = models.PositiveIntegerField("NPS", null=True, blank=True,
                                      validators=[MinValueValidator(0), MaxValueValidator(10)],
                                      help_text='Valor Net Promoter Score')

    def __str__(self):
        return str(self.data)

    @classmethod
    def create(cls):
        """Cria um objeto (entrada) em Feedback."""
        feedback = cls()
        return feedback



class FeedbackEstudante(models.Model):
    """Feedback dos estudantes."""

    momento = models.DateTimeField(default=datetime.datetime.now, blank=True,
                                help_text='Data e hora do feedback')

    estudante = models.ForeignKey('users.Aluno', null=True, blank=True, on_delete=models.SET_NULL,
                              help_text='estudante que fez o feedback')

    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text='projeto que estava no feedback')

    TIPO_RECOMENDARIA = ( # não mudar a ordem dos números
        (1, 'Não recomendo'),
        (2, 'Recomendo com ressalvas'),
        (3, 'Recomendo fortemente'),
    )
    recomendaria = models.PositiveSmallIntegerField(choices=TIPO_RECOMENDARIA, null=True, blank=True,
                                                    help_text='O quanto você recomendaria fazermos um projeto de PFE nos próximos semestres com a Empresa Parceira?')


    primeira_opcao = models.BooleanField("Primeira Opção", null=True, blank=True,
                                         help_text='Agora que você conhece mais da Empresa Parceira, essa seria uma das primeiras opções para você fazer estágio ou ser contratado de forma efetiva?')

    TIPO_PROPOSTA = ( # não mudar a ordem dos números
        (1, 'Recebi convite e apliquei'),
        (2, 'Não recebi convite, mas apliquei'),
        (3, 'Recebi convite, mas não apliquei'),
        (4, 'Não recebi, nem apliquei'),
        (5, 'Não haviam vagas em aberto'),
    )
    proposta = models.PositiveSmallIntegerField(choices=TIPO_PROPOSTA, null=True, blank=True,
                                                    help_text='Tendo ou não buscado alguma proposta da Empresa Parceira para estágio ou contrato de trabalho.')


    TIPO_TRABALHANDO = ( # não mudar a ordem dos números
        (1, 'Empresa do Projeto do PFE'),
        (2, 'Outra'),
        (3, 'Ainda não'),
        (4, 'Prefiro não responder'),
    )
    trabalhando = models.PositiveSmallIntegerField(choices=TIPO_TRABALHANDO, null=True, blank=True,
                                                    help_text='Você já está trabalhando (ou em vias de trabalhar) em alguma empresa?')


    outros = models.TextField(max_length=1000, null=True, blank=True,
                              help_text='Feedback Outros')

    def __str__(self):
        return str(self.momento) + " - " + str(self.estudante) + " : " + str(self.projeto)

    @classmethod
    def create(cls):
        """Cria um objeto (entrada) em FeedbackEstudante."""
        feedback = cls()
        return feedback


class Conexao(models.Model):
    """Controla como um usuário se conecta a um projeto."""

    parceiro = models.ForeignKey("users.Parceiro", null=True, blank=True,
                                 on_delete=models.SET_NULL,
                                 help_text="parceiro que se conecta ao projeto")

    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="projeto que possui vínculo da conexão")
    observacao = models.TextField(max_length=256, null=True, blank=True,
                                  help_text="qualquer observação relevante")
    
    papel = {
       "gestor_responsavel": ["Gestor Responsável", "GR"],
       "mentor_tecnico": ["Mentoria Técnica", "MT"],
       "recursos_humanos" : ["Área Administrativa", "AA"],
       "colaboracao" : ["Colaboração Externa", "CE"],
    }
    gestor_responsavel = models.BooleanField(papel["gestor_responsavel"], default=False)
    mentor_tecnico = models.BooleanField(papel["mentor_tecnico"], default=False)
    recursos_humanos = models.BooleanField(papel["recursos_humanos"], default=False)
    colaboracao = models.BooleanField(papel["colaboracao"], default=False)

    def get_papeis(self):
        texto = []
        for field in Conexao.papel:
            if getattr(self, field):
                texto += [Conexao.papel[field]]
        return texto
    
    def __str__(self):
        texto = ""
        if self.parceiro:
            texto += self.parceiro.user.get_full_name()
        texto += " >>> "
        if self.projeto and self.projeto.organizacao:
            texto += self.projeto.organizacao.sigla+" - "+self.projeto.get_titulo()+\
                " ("+str(self.projeto.ano)+"."+str(self.projeto.semestre)+")"
        return texto

    class Meta:
        verbose_name = 'Conexão'
        verbose_name_plural = 'Conexões'


class Coorientador(models.Model):
    """Controla lista de coorientadores por projeto."""

    usuario = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL,
                                help_text='coorientador de um projeto')
    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text='projeto que foi coorientado')
    observacao = models.TextField(max_length=256, null=True, blank=True,
                                  help_text='qualquer observação relevante')

    def __str__(self):
        mensagem = ""
        if self.usuario:
            mensagem += self.usuario.get_full_name()
        else:
            mensagem += "USUÁRIO NÃO DEFINIDO"
        mensagem += " >>> "
        if self.projeto:
            mensagem += self.projeto.get_titulo()+\
                " ("+str(self.projeto.ano)+"."+str(self.projeto.semestre)+")"
        else:
            mensagem += "PROJETO NÃO DEFINIDO"
        return mensagem

    class Meta:
        verbose_name = "Coorientador"
        verbose_name_plural = "Coorientadores"

class ObjetivosDeAprendizagem(models.Model):
    """Objetidos de Aprendizagem do curso."""

    titulo = models.TextField("Título", max_length=128, null=True, blank=True,
                              help_text="Título do objetivo de aprendizagem")

    titulo_en = models.TextField("Título Inglês", max_length=128, null=True, blank=True,
                                 help_text="Título do objetivo de aprendizagem em inglês")

    sigla = models.CharField("sigla", max_length=3, null=True, blank=True,
                             help_text="Sigla do objetivo de aprendizagem")
    
    sigla_en = models.CharField("sigla", max_length=3, null=True, blank=True,
                                help_text="Sigla do objetivo de aprendizagem em inglês")

    objetivo = models.TextField(max_length=256, null=True, blank=True,
                                help_text="Descrição do objetivo de aprendizagem")

    objetivo_en = models.TextField(max_length=256, null=True, blank=True,
                                   help_text="Descrição do objetivo de aprendizagem")


    # Rubricas de Grupo Intermediárias e Finais
    rubrica_intermediaria_I = models.TextField(max_length=1024, null=True, blank=True,
                                               help_text="Rubrica intermediária do conceito I")
    rubrica_final_I = models.TextField(max_length=1024, null=True, blank=True,
                                       help_text="Rubrica final do conceito I")
    rubrica_intermediaria_D = models.TextField(max_length=1024, null=True, blank=True,
                                               help_text='Rubrica intermediária do conceito D')
    rubrica_final_D = models.TextField(max_length=1024, null=True, blank=True,
                                       help_text='Rubrica final do conceito D')
    rubrica_intermediaria_C = models.TextField(max_length=1024, null=True, blank=True,
                                               help_text='Rubrica intermediária do conceito C')
    rubrica_final_C = models.TextField(max_length=1024, null=True, blank=True,
                                       help_text='Rubrica final do conceito C')
    rubrica_intermediaria_B = models.TextField(max_length=1024, null=True, blank=True,
                                               help_text='Rubrica intermediária do conceito B')
    rubrica_final_B = models.TextField(max_length=1024, null=True, blank=True,
                                       help_text='Rubrica final do conceito B')
    rubrica_intermediaria_A = models.TextField(max_length=1024, null=True, blank=True,
                                               help_text='Rubrica intermediária do conceito A')
    rubrica_final_A = models.TextField(max_length=1024, null=True, blank=True,
                                       help_text='Rubrica final do conceito A')



    # Rubricas de Individuais Intermediárias e Finais
    rubrica_intermediaria_individual_I = models.TextField(max_length=1024, null=True, blank=True,
                                                         help_text='Rubrica intermediária do conceito I')
    rubrica_final_individual_I = models.TextField(max_length=1024, null=True, blank=True,
                                                 help_text='Rubrica final do conceito I')
    rubrica_intermediaria_individual_D = models.TextField(max_length=1024, null=True, blank=True,
                                                         help_text='Rubrica intermediária do conceito D')
    rubrica_final_individual_D = models.TextField(max_length=1024, null=True, blank=True,
                                                 help_text='Rubrica final do conceito D')
    rubrica_intermediaria_individual_C = models.TextField(max_length=1024, null=True, blank=True,
                                                         help_text='Rubrica intermediária do conceito C')
    rubrica_final_individual_C = models.TextField(max_length=1024, null=True, blank=True,
                                                 help_text='Rubrica final do conceito C')
    rubrica_intermediaria_individual_B = models.TextField(max_length=1024, null=True, blank=True,
                                                         help_text='Rubrica intermediária do conceito B')
    rubrica_final_individual_B = models.TextField(max_length=1024, null=True, blank=True,
                                                 help_text='Rubrica final do conceito B')
    rubrica_intermediaria_individual_A = models.TextField(max_length=1024, null=True, blank=True,
                                                         help_text='Rubrica intermediária do conceito A')
    rubrica_final_individual_A = models.TextField(max_length=1024, null=True, blank=True,
                                                 help_text='Rubrica final do conceito A')



    # Rubricas de Grupo Intermediárias e Finais em Inglês
    rubrica_intermediaria_I_en = models.TextField(max_length=1024, null=True, blank=True,
                                               help_text='Rubrica intermediária do conceito I')
    rubrica_final_I_en = models.TextField(max_length=1024, null=True, blank=True,
                                       help_text='Rubrica final do conceito I')
    rubrica_intermediaria_D_en = models.TextField(max_length=1024, null=True, blank=True,
                                               help_text='Rubrica intermediária do conceito D')
    rubrica_final_D_en = models.TextField(max_length=1024, null=True, blank=True,
                                       help_text='Rubrica final do conceito D')
    rubrica_intermediaria_C_en = models.TextField(max_length=1024, null=True, blank=True,
                                               help_text='Rubrica intermediária do conceito C')
    rubrica_final_C_en = models.TextField(max_length=1024, null=True, blank=True,
                                       help_text='Rubrica final do conceito C')
    rubrica_intermediaria_B_en = models.TextField(max_length=1024, null=True, blank=True,
                                               help_text='Rubrica intermediária do conceito B')
    rubrica_final_B_en = models.TextField(max_length=1024, null=True, blank=True,
                                       help_text='Rubrica final do conceito B')
    rubrica_intermediaria_A_en = models.TextField(max_length=1024, null=True, blank=True,
                                               help_text='Rubrica intermediária do conceito A')
    rubrica_final_A_en = models.TextField(max_length=1024, null=True, blank=True,
                                       help_text='Rubrica final do conceito A')



    # Rubricas de Individuais Intermediárias e Finais em Inglês
    rubrica_intermediaria_individual_I_en = models.TextField(max_length=1024, null=True, blank=True,
                                                         help_text='Rubrica intermediária do conceito I')
    rubrica_final_individual_I_en = models.TextField(max_length=1024, null=True, blank=True,
                                                 help_text='Rubrica final do conceito I')
    rubrica_intermediaria_individual_D_en = models.TextField(max_length=1024, null=True, blank=True,
                                                         help_text='Rubrica intermediária do conceito D')
    rubrica_final_individual_D_en = models.TextField(max_length=1024, null=True, blank=True,
                                                 help_text='Rubrica final do conceito D')
    rubrica_intermediaria_individual_C_en = models.TextField(max_length=1024, null=True, blank=True,
                                                         help_text='Rubrica intermediária do conceito C')
    rubrica_final_individual_C_en = models.TextField(max_length=1024, null=True, blank=True,
                                                 help_text='Rubrica final do conceito C')
    rubrica_intermediaria_individual_B_en = models.TextField(max_length=1024, null=True, blank=True,
                                                         help_text='Rubrica intermediária do conceito B')
    rubrica_final_individual_B_en = models.TextField(max_length=1024, null=True, blank=True,
                                                 help_text='Rubrica final do conceito B')
    rubrica_intermediaria_individual_A_en = models.TextField(max_length=1024, null=True, blank=True,
                                                         help_text='Rubrica intermediária do conceito A')
    rubrica_final_individual_A_en = models.TextField(max_length=1024, null=True, blank=True,
                                                 help_text='Rubrica final do conceito A')





    avaliacao_aluno = models.BooleanField("Avaliação do Aluno", default=False,
                                          help_text='Avaliação do Aluno (AA)')

    avaliacao_banca = models.BooleanField("Avaliação da Banca", default=False,
                                          help_text='Avaliação da Banca (AB)')

    avaliacao_grupo = models.BooleanField("Avaliação do Grupo", default=False,
                                          help_text='Avaliação do Grupo (AG)')

    avaliacao_falconi = models.BooleanField("Avaliação Falconi", default=False,
                                            help_text='Avaliação Falconi (AF)')

    data_inicial = models.DateField("Data Inicial", null=True, blank=True,
                                    help_text='Data Inicial de Uso')

    data_final = models.DateField("Data Final", null=True, blank=True,
                                  help_text='Data Final de Uso')


    ### ESSES PESOS PODEM SER REMOVIDOS, NÃO DEVEM SER MAIS USADOS
    peso_intermediario_individual = models.FloatField(default=0,
                                                      help_text='peso intermediário individual')

    peso_intermediario_grupo = models.FloatField(default=0,
                                                 help_text='peso intermediário grupo')

    peso_final_individual = models.FloatField(default=0,
                                              help_text='peso final individual')

    peso_final_grupo = models.FloatField(default=0,
                                         help_text='peso final grupo')

    peso_banca_intermediaria = models.FloatField(default=0,
                                                 help_text='peso para banca intermediária')

    peso_banca_final = models.FloatField(default=0,
                                         help_text='peso para banca final')

    peso_banca_falconi = models.FloatField(default=0,
                                           help_text='peso para banca falconi')
    ##############################################################


    ordem = models.PositiveSmallIntegerField(help_text='ordem para aparecer nas listas')


    def __str__(self):
        texto = str(self.titulo) + "  [ "
        if self.data_inicial:
            texto += str(self.data_inicial)
        texto += " -> "
        if self.data_final:
            texto += str(self.data_final)
        else:
            texto += "hoje"
        texto += " ]"
        return texto

    class Meta:
        verbose_name = 'ObjetivosDeAprendizagem'
        verbose_name_plural = 'ObjetivosDeAprendizagem'


# NAO USAR MAIS, ESTA OBSOLETO, REMOVER !!!!
# Usado em Avaliacao e Observacao
# TIPO_DE_AVALIACAO = ( # não mudar a ordem dos números
#     (0, 'Não definido'),
#     (1, 'Banca Intermediária'),
#     (2, 'Banca Final'),
#     (10, 'Relatório de Planejamento'),      # avaliado até 2020.1
#     (11, 'Relatório Intermediário de Grupo'),
#     (12, 'Relatório Final de Grupo'),
#     (21, 'Relatório Intermediário Individual'),
#     (22, 'Relatório Final Individual'),

#     (50, 'Planejamento Primeira Fase'),     # usado até 2019.1
#     (51, 'Avaliação Parcial Individual'),   # usado até 2019.1
#     (52, 'Avaliação Final Individual'),     # usado até 2019.1
#     (53, 'Avaliação Parcial de Grupo'),     # usado até 2019.1
#     (54, 'Avaliação Final de Grupo'),       # usado até 2019.1
#     (99, 'Falconi'),
#     (200, "Relato Quinzenal"),
# )



class Avaliacao2(models.Model):
    """Avaliações realizadas durante o projeto."""

    # NÃO USAR MAIS TIPO DE AVALIAÇÃO, USAR EXAME
    # tipo_de_avaliacao = models.PositiveSmallIntegerField(choices=TIPO_DE_AVALIACAO, default=0)

    # DEFINE O TIPO DE AVALIAÇÃO
    exame = models.ForeignKey("academica.Exame", null=True, blank=True, on_delete=models.SET_NULL,
                                 help_text="Tipo de avaliação")

    momento = models.DateTimeField(default=datetime.datetime.now, blank=True,
                                   help_text="Data e hora da comunicação") # hora ordena para dia

    peso = models.FloatField("Peso", validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True,
                             help_text="Peso da avaliação na média em % (varia de 0 a 100)")

    # A nota será convertida para rubricas se necessário
    nota = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    # Somente útil para Bancas
    avaliador = models.ForeignKey("users.PFEUser", null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name="avaliador",
                                  help_text="avaliador do projeto")

    # Para Bancas e Entregas em Grupo (quando avaliando o grupo inteiro)
    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="projeto que foi avaliado")

    # Para Alocações dos estudantes (caso um aluno reprove ele teria duas alocações)
    alocacao = models.ForeignKey("users.Alocacao", null=True, blank=True,
                                 on_delete=models.SET_NULL,
                                 related_name="projeto_alocado_avaliacao",
                                 help_text="relacao de alocação entre projeto e estudante")

    objetivo = models.ForeignKey(ObjetivosDeAprendizagem, related_name="objetivo_avaliacao",
                                 on_delete=models.SET_NULL, null=True, blank=True,
                                 help_text="Objetivo de Aprendizagem")

    na = models.BooleanField("Não Avaliado", default=False,
                             help_text="Caso o avaliador não tenha avaliado esse quesito")

    def __str__(self):
        texto = ""
        texto += str(self.exame.titulo)[0:8]
        texto += " > "
        texto += str(self.projeto)[0:12]
        texto += " > "
        texto += str(self.avaliador)
        
        return texto
        return "Avaliação Não Definida"

    @classmethod
    def create(cls, projeto=None, alocacao=None):
        """Cria um objeto (entrada) em Avaliação."""
        avaliacao = cls(projeto=projeto, alocacao=alocacao)
        return avaliacao

    class Meta:
        verbose_name = 'Avaliação2'
        verbose_name_plural = 'Avaliações2'
        ordering = ['momento',]

    def get_conceito(self):
        # Está duplicado, mas é para não quebrar o código
        if( self.nota >= 9.5 ): return ("A+")
        if( self.nota >= 8.5 ): return ("A")
        if( self.nota >= 7.5 ): return ("B+")
        if( self.nota >= 6.5 ): return ("B")
        if( self.nota >= 5.5 ): return ("C+")
        if( self.nota >= 4.5 ): return ("C")
        if( self.nota >= 3.5 ): return ("D+")
        if( self.nota >= 2.5 ): return ("D")
        if( self.nota >= 1.5 ): return ("D-")
        return ("I")


class Avaliacao_Velha(models.Model):
    """Quando avaliações de banca são refeitas, as antigas vem para essa base de dados."""

    # NÃO USAR MAIS TIPO DE AVALIAÇÃO, USAR EXAME
    # tipo_de_avaliacao = models.PositiveSmallIntegerField(choices=TIPO_DE_AVALIACAO, default=0)

    # DEFINE O TIPO DE AVALIAÇÃO
    exame = models.ForeignKey("academica.Exame", null=True, blank=True, on_delete=models.SET_NULL,
                                 help_text="Tipo de avaliação")

    momento = models.DateTimeField(default=datetime.datetime.now, blank=True,
                                   help_text='Data e hora da comunicação') # hora ordena para dia

    peso = models.FloatField("Peso", validators=[MinValueValidator(0), MaxValueValidator(100)],
                             null=True, blank=True,
                             help_text='Pesa da avaliação na média (bancas compartilham peso)',
                             default=10) # 10% para as bancas

    # A nota será convertida para rubricas se necessário
    nota = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    # Somente útil para Bancas
    avaliador = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL,
                                  help_text='avaliador do projeto')

    # Para Bancas e Entregas em Grupo (quando avaliando o grupo inteiro)
    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text='projeto que foi avaliado')

    # Para Alocações dos estudantes (caso um aluno reprove ele teria duas alocações)
    alocacao = models.ForeignKey('users.Alocacao', null=True, blank=True,
                                 on_delete=models.SET_NULL,
                                 related_name='projeto_alocado_avaliacao_velha',
                                 help_text='relacao de alocação entre projeto e estudante')

    objetivo = models.ForeignKey(ObjetivosDeAprendizagem, related_name='objetivo_avaliacao_velha',
                                 on_delete=models.SET_NULL, null=True, blank=True,
                                 help_text='Objetivo de Aprendizagem')

    na = models.BooleanField("Não Avaliado", default=False,
                             help_text='Caso o avaliador não tenha avaliado esse quesito')

    def __str__(self):
        texto = ""
        texto += str(self.exame.titulo)[0:8]
        texto += " > "
        texto += str(self.projeto)[0:12]
        texto += " > "
        texto += str(self.avaliador)
        return texto

    @classmethod
    def create(cls, projeto=None, alocacao=None):
        """Cria um objeto (entrada) em Avaliação Velha."""
        avaliacao = cls(projeto=projeto, alocacao=alocacao)
        return avaliacao

    class Meta:
        verbose_name = 'Avaliação Velha'
        verbose_name_plural = 'Avaliações Velhas'
        ordering = ['momento',]


class Reprovacao(models.Model):
    """Reprovações controladas por falha em Objetivos de Aprendizagem."""

    # Para Alocações dos estudantes (caso um aluno reprove ele teria duas alocações)
    alocacao = models.ForeignKey('users.Alocacao', null=True,
                                 on_delete=models.SET_NULL,
                                 related_name='projeto_alocado_reprovacao',
                                 help_text='alocação que sofreu reprovação')

    # A nota será convertida para rubricas se necessário
    nota = models.DecimalField(max_digits=4, decimal_places=2)

    def __str__(self):
        return str(self.alocacao) + "Nota: " + str(self.nota)

    @classmethod
    def create(cls, alocacao):
        """Cria um objeto (entrada) em Reprovação."""
        reprovacao = cls(alocacao=alocacao)
        return reprovacao

    class Meta:
        verbose_name = 'Reprovação'
        verbose_name_plural = 'Reprovações'


class Observacao(models.Model):
    """Observações realizadas durante avaliações."""

    # DEFINE O TIPO DE AVALIAÇÃO
    exame = models.ForeignKey("academica.Exame", null=True, blank=True, on_delete=models.SET_NULL,
                                 help_text="Tipo de avaliação")
    
    momento = models.DateTimeField(default=datetime.datetime.now, blank=True,
                                   help_text='Data e hora da comunicação') # hora ordena para dia

    # Somente útil para Bancas
    avaliador = models.ForeignKey("users.PFEUser", null=True, blank=True, on_delete=models.SET_NULL,
                                  help_text="avaliador do projeto")

    # Para Bancas e Entregas em Grupo
    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="projeto que foi avaliado")

    # Para Alocações dos estudantes (caso um aluno reprove ele teria duas alocações)
    alocacao = models.ForeignKey("users.Alocacao", null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name="observacao_alocado",
                                 help_text="relacao de alocação entre projeto e estudante")

    # Se houver, usando pois no Blackboard alguns estão dessa forma
    objetivo = models.ForeignKey(ObjetivosDeAprendizagem, related_name='objetivo_observacao',
                                 on_delete=models.SET_NULL, null=True, blank=True,
                                 help_text="Objetivo de Aprendizagem")

    observacoes_orientador = models.TextField(max_length=2048, null=True, blank=True,
                                   help_text="Observações a serem compartilhadas somente com o orientador do projeto")

    observacoes_estudantes = models.TextField(max_length=2048, null=True, blank=True,
                                   help_text="Observações a serem compartilhadas com os estudantes do projeto")

    @classmethod
    def create(cls, projeto):
        """Cria um objeto (entrada) em Observacao."""
        observacao = cls(projeto=projeto)
        return observacao

    def __str__(self):
        return "Obs. tipo: " + str(self.exame) + " = " + str(self.observacoes_orientador)[:6] + "..."

    class Meta:
        verbose_name = 'Observação'
        verbose_name_plural = 'Observações'
        #ordering = [,]


class Observacao_Velha(models.Model):
    """Quando Observações de banca são refeitas, as antigas vem para essa base de dados."""

    # NÃO USAR MAIS TIPO DE AVALIAÇÃO, USAR EXAME
    # tipo_de_avaliacao = models.PositiveSmallIntegerField(choices=TIPO_DE_AVALIACAO, default=0)

    # DEFINE O TIPO DE AVALIAÇÃO
    exame = models.ForeignKey("academica.Exame", null=True, blank=True, on_delete=models.SET_NULL,
                                 help_text="Tipo de avaliação")
    
    momento = models.DateTimeField(default=datetime.datetime.now, blank=True,
                                   help_text='Data e hora da comunicação') # hora ordena para dia

    # Somente útil para Bancas
    avaliador = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL,
                                  help_text='avaliador do projeto')

    # Para Bancas e Entregas em Grupo
    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text='projeto que foi avaliado')

    # Para Alocações dos estudantes (caso um aluno reprove ele teria duas alocações)
    alocacao = models.ForeignKey('users.Alocacao', null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name='observacao_velha_alocado',
                                 help_text='relacao de alocação entre projeto e estudante')

    # Se houver, usando pois no Blackboard alguns estão dessa forma
    objetivo = models.ForeignKey(ObjetivosDeAprendizagem, related_name='objetivo_observacao_velha',
                                 on_delete=models.SET_NULL, null=True, blank=True,
                                 help_text='Objetivo de Aprendizagem')

    observacoes = models.TextField(max_length=2048, null=True, blank=True,
                                   help_text='qualquer observação relevante')

    @classmethod
    def create(cls, projeto):
        """Cria um objeto (entrada) em Observacao Velha."""
        observacao = cls(projeto=projeto)
        return observacao

    def __str__(self):
        return "Observação velha tipo : " + str(self.exame)

    class Meta:
        verbose_name = 'Observação Velha'
        verbose_name_plural = 'Observações Velhas'
        


class Certificado(models.Model):
    """Certificados das Premiações do PFE."""

    usuario = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL,
                                help_text='pessoa premiada com certificado')
    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text='projeto relacionado ao certificado')
    data = models.DateField(default=datetime.date.today, blank=True,
                            help_text='data do certificado')

    TIPO_DE_CERTIFICADO = (  # não mudar a ordem dos números
        (0, 'Não definido'),
        (1, 'Estudante destaque'),
        (2, 'Equipe destaque'),
        (11, 'Destaque Falconi'),
        (12, 'Excelência Falconi'),
        (101, "Orientação de Projeto"),
        (102, "Coorientação de Projeto"),
        (103, "Membro de Banca Intermediária"),
        (104, "Membro de Banca Final"),
        (105, "Membro da Banca Falconi"),
        (106, "Mentoria Profissional"),  # antigo mentor na Falconi
        (107, "Mentoria Técnica"),  # mentor da empresa
    )
    tipo_de_certificado = models.PositiveSmallIntegerField(choices=TIPO_DE_CERTIFICADO, default=0)

    observacao = models.TextField(max_length=256, null=True, blank=True,
                                  help_text='qualquer observação relevante')

    documento = models.FileField("Documento", upload_to=get_upload_path, null=True, blank=True,
                                 help_text='Documento Digital')

    # Usar get_tipo_de_certificado_display
    def get_certificado(self):
        """Retorna em string o nome do certificado."""
        for entry in Certificado.TIPO_DE_CERTIFICADO:
            if self.tipo_de_certificado == entry[0]:
                return entry[1]
        return None

    @classmethod
    def create(cls):
        """Cria um objeto (entrada) em Certificado."""
        certificado = cls()
        return certificado

    def __str__(self):
        texto = self.usuario.get_full_name() + " >>> "
        if self.projeto:
            texto += self.projeto.get_titulo()
            texto += " (" + str(self.projeto.ano) + "." + str(self.projeto.semestre) + ")"
        return texto

    def file_name(self):
        return self.documento.name.split('/')[-1]
    
    class Meta:
        verbose_name = 'Certificado'
        verbose_name_plural = 'Certificados'

class Area(models.Model):
    """Projeto em que o aluno está alocado."""

    titulo = models.CharField("Título", max_length=48, null=True, blank=True,
                              help_text='Titulo da área de interesse')

    descricao = models.CharField("Descrição", max_length=512, null=True, blank=True,
                                 help_text='Descrição da área de interesse')

    ativa = models.BooleanField("Ativa", default=True,
                                help_text='Se a área de interesse está sendo usada atualmente')

    def __str__(self):
        return self.titulo

    @classmethod
    def create(cls, titulo):
        """Cria uma Área nova."""
        area = cls(titulo=titulo)
        return area

    class Meta:
        verbose_name = 'Área'
        verbose_name_plural = 'Áreas'

class AreaDeInteresse(models.Model):
    """Usado para fazer o mapeando da proposta ou da pessoa para área de interesse."""

    # As áreas são de interesse ou do usuário ou da proposta (que passa para o projeto)
    usuario = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL,
                                help_text='área dde interessada da pessoa')
    proposta = models.ForeignKey(Proposta, null=True, blank=True, on_delete=models.SET_NULL,
                                 help_text='área de interesse da proposta')

    # Campo para especificar uma outra área que não a da lista de áreas controladas
    outras = models.CharField("Outras", max_length=128, null=True, blank=True,
                              help_text='Outras áreas de interesse')

    area = models.ForeignKey(Area, null=True, blank=True, on_delete=models.SET_NULL,
                             help_text='área de interesse')

    class Meta:
        verbose_name = 'Área de Interesse'
        verbose_name_plural = 'Áreas de Interesse'

    def __str__(self):
        if self.usuario:
            if self.outras:
                return self.usuario.get_full_name()+" >>> "+self.outras
            return self.usuario.get_full_name()+" >>> "+str(self.area)
        if self.proposta:
            if self.outras:
                return self.proposta.titulo+" >>> "+self.outras
            return self.proposta.titulo+" >>> "+str(self.area)
        if self.outras:
            return self.outras
        return str(self.area)

    @classmethod
    def create(cls):
        """Cria uma Área de Interesse nova."""
        area_de_interesse = cls()
        return area_de_interesse

    @classmethod
    def create_estudante_area(cls, estudante, area):
        """Cria uma Área de Interesse nova."""
        area_de_interesse = cls(usuario=estudante.user, area=area)
        return area_de_interesse

    @classmethod
    def create_estudante_outras(cls, estudante, outras):
        """Cria uma Área de Interesse nova."""
        area_de_interesse = cls(usuario=estudante.user, outras=outras)
        return area_de_interesse

    @classmethod
    def create_proposta_area(cls, proposta, area):
        """Cria uma Área de Interesse nova."""
        area_de_interesse = cls(proposta=proposta, area=area)
        return area_de_interesse

    @classmethod
    def create_proposta_outras(cls, proposta, outras):
        """Cria uma Área de Interesse nova."""
        area_de_interesse = cls(proposta=proposta, outras=outras)
        return area_de_interesse

    @classmethod
    def create_usuario_area(cls, usuario, area):
        """Cria uma Área de Interesse nova."""
        area_de_interesse = cls(usuario=usuario, area=area)
        return area_de_interesse
