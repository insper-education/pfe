#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

import os
import datetime
import string
import random
import re

from django.db import models
from django.conf import settings

from django.urls import reverse  # To generate URLS by reversing URL patterns
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib import admin
from django.template.defaultfilters import slugify
from django.utils.encoding import force_text
from django.shortcuts import get_object_or_404

from .support import get_upload_path

from .tipos import TIPO_EVENTO

from academica.support_notas import converte_letra


class Organizacao(models.Model):
    """Dados das organizações que propõe projetos."""

    nome = models.CharField("Nome Fantasia", max_length=100, unique=True,
                            help_text="Nome fantasia da organização parceira")
    
    sigla = models.CharField("Sigla", max_length=20, unique=True,
                             help_text="Sigla usada pela organização parceira")
    
    endereco = models.TextField("Endereço", max_length=200, null=True, blank=True,
                                help_text="Endereço da organização parceira")
    
    website = models.URLField("website", max_length=300, null=True, blank=True,
                              help_text="website da organização parceira")
    
    informacoes = models.TextField("Informações", max_length=1000, null=True, blank=True,
                                   help_text="Informações sobre a organização parceira")
    
    logotipo = models.ImageField("Logotipo", upload_to=get_upload_path, null=True, blank=True,
                                 help_text="Logotipo da organização parceira")
    
    cnpj = models.CharField("CNPJ", max_length=14, null=True, blank=True, 
                            help_text="Código de CNPJ da empresa")
    
    inscricao_estadual = models.CharField("Inscrição Estadual", max_length=15,
                                          null=True, blank=True,
                                          help_text="Código da inscrição estadual")
    
    razao_social = models.CharField("Razão Social", max_length=100, null=True, blank=True,
                                    help_text="Razão social da organização parceira")
    
    ramo_atividade = models.TextField("Ramo de Atividade", max_length=1000, null=True, blank=True,
                                      help_text="Ramo de atividade da organização parceira")

    estrelas = models.PositiveSmallIntegerField(default=0, help_text="Interesse para o semestre")

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
    """Dados dos projetos."""
    
    titulo_final = models.CharField("Título Final", max_length=160, null=True,
                                    blank=True, help_text="Título Final do projeto")

    resumo = models.TextField("Resumo", max_length=6000, null=True, blank=True,
                                 help_text="Resumo final para o projeto criado pelos estudantes")
    
    abstract = models.TextField("Abstract", max_length=6000, null=True, blank=True,
                                 help_text="Resumo final em inglês para o projeto criado pelos estudantes")
    
    palavras_chave = models.CharField("Palavras-chave", max_length=1000, null=True, blank=True,
                                 help_text="Palavras-chave para os documentos do projeto")
    
    pastas_do_projeto = models.TextField("Pastas do Projeto", max_length=2000, null=True, blank=True,
                                help_text="Links para repositórios com dados/códigos dos projeto (para orientador acessar)")

    organizacao_velho = models.ForeignKey(Organizacao, null=True, blank=True, on_delete=models.SET_NULL,
                                    help_text="Organização parceira que propôs projeto")

    avancado = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL,
                                 help_text="projeto original em caso de avançado")

    ano = models.PositiveIntegerField("Ano",
                                      validators=[MinValueValidator(2018), MaxValueValidator(3018)],
                                      help_text="Ano que o projeto começa")

    semestre = models.PositiveIntegerField("Semestre",
                                           validators=[MinValueValidator(1), MaxValueValidator(2)],
                                           help_text="Semestre que o projeto começa")

    orientador = models.ForeignKey("users.Professor", null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name="professor_orientador",
                                   help_text="professor orientador do projeto")

    proposta = models.ForeignKey("Proposta", null=True, blank=True, on_delete=models.SET_NULL,
                                 help_text="Proposta original do projeto")

    time_misto = models.BooleanField("Time Misto", default=False,
                                     help_text="Caso o projeto conte com membros externos a instituição")

    site = models.URLField("site", max_length=300, null=True, blank=True,
                           help_text="site do projeto desenvolvido pelos estudantes")
    
    atualizacao_estudantes = models.DateTimeField("Atualização Estudantes", null=True, blank=True,
                           help_text="Data da última atualização dos dados do projeto pelos estudantes")
    class Meta:
        ordering = [ "ano", "semestre", "proposta__organizacao" ]  # Não mudar a ordem
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
        return reverse("projeto-detail", args=[str(self.id)])

    def get_titulo(self):
        """Caso tenha titulo atualizado, retorna esse, senão retorna o original e único."""
        if self.titulo_final:
            return self.titulo_final
        if not self.proposta.titulo:
            return "PROBLEMA NA IDENTIFICAÇÃO DO TÍTULO DO PROJETO"
        return self.proposta.titulo

    # def certificado_orientador(self):
    #     """Retorna link do certificado."""
    #     tipo_certificado = get_object_or_404(TipoCertificado, titulo="Orientação de Projeto")
    #     certificado = Certificado.objects.filter(usuario=self.orientador.user, projeto=self, tipo_certificado=tipo_certificado)
    #     return certificado

    @property
    def organizacao(self):
        """Retorna a organização que foi definida na proposta."""
        return self.proposta.organizacao

    def __str__(self):
        """Retorno padrão textual."""
        texto = ""

        if self.proposta.organizacao and self.proposta.organizacao.sigla:
            texto = "[" + self.proposta.organizacao.sigla + "] "
        else:
            texto = "[SEM ORGANIZAÇÃO DEFINIDA] "

        texto += self.get_titulo()

        if self.ano and self.semestre:
            texto += " (" + str(self.ano) + "." + str(self.semestre) + ") "
        else:
            texto += " (SEM PERÍODO DEFINIDO)"

        return texto

    def tem_relatos(self):
        """Retorna todos os possiveis relatos quinzenais para o projeto."""
        # Antes de 2022 os relatos quinzenais era realizados no Blackboard
        # Essa função em hardcode não é ideal, mas resolve o problema
        if self.ano < 2022:
            return Evento.objects.none()
        else:
            return Evento.get_eventos(sigla="RQ", ano=self.ano, semestre=self.semestre)
    
    def periodo(self):
        configuracao = get_object_or_404(Configuracao)
        if self.ano >= configuracao.ano:
            return {"pt": "Atuais", "en": "Current"}
        if self.ano == configuracao.ano and self.semestre >= configuracao.semestre:
            return {"pt": "Atuais", "en": "Current"}
        return {"pt": "Anteriores", "en": "Previous"}
        
    @property
    def get_edicao(self):
        return str(self.ano)+"."+str(self.semestre)
    
    def get_site(self):
        return "/sites/"+str(self.id)+"/" if os.path.exists(settings.SITE_ROOT + "/projeto"+str(self.id)) else None
    
    # Retorna os coorientadores do projeto
    @property
    def get_coorientadores_ids(self):
        return Coorientador.objects.filter(projeto=self).values_list("usuario", flat=True)
    
    def get_banca_final(self):
        banca = Banca.objects.filter(projeto=self, composicao__exame__titulo="Banca Final").last()
        return banca
        
        
class Proposta(models.Model):
    """Dados da Proposta de Projeto."""

    slug = models.SlugField("slug", unique=True, max_length=64, null=True, blank=True,
                            help_text="Slug para o endereço da proposta")

    nome = models.CharField("Nome", max_length=127,
                            help_text="Nome(s) de quem submeteu o projeto")
    email = models.CharField("e-mail", max_length=80, null=True, blank=True,
                             help_text="e-mail(s) de quem está dando o Feedback")
    website = models.URLField("website", max_length=300, null=True, blank=True,
                              help_text="website da organização")

    nome_organizacao = models.CharField("Organização", max_length=120, null=True, blank=True,
                                        help_text="Nome da Organização/Empresa")

    endereco = models.TextField("Endereço", max_length=400, null=True, blank=True,
                                help_text="Endereço da Instituição")

    contatos_tecnicos = models.TextField("Contatos Técnicos", max_length=400,
                                         help_text="Contatos Técnicos")

    contatos_administrativos = models.TextField("Contatos Administrativos", max_length=400,
                                                null=True, blank=True,
                                                help_text="Contatos Administrativos")

    descricao_organizacao = models.TextField("Descrição da Organização", max_length=3000,
                                             null=True, blank=True,
                                             help_text="Descrição da Organização")

    departamento = models.TextField("Descrição do Depart.", max_length=3000, null=True, blank=True,
                                    help_text="Descrição do departamento que propôs o projeto")

    titulo = models.CharField("Título", max_length=160,
                              help_text="Título Provisório do projeto")

    descricao = models.TextField("Descrição", max_length=3000,
                                 help_text="Descricao da Proposta de Projeto")

    expectativas = models.TextField("Expectativas", max_length=3000,
                                    help_text="Expectativas em relação ao projeto")

    recursos = models.TextField("Recursos", max_length=1000, null=True, blank=True,
                                help_text="Recursos a serem disponibilizados para estudantes")

    observacoes = models.TextField("Outras Observações", max_length=3000, null=True, blank=True,
                                   help_text="Outras Observações")

    anexo = models.FileField("Anexo", upload_to=get_upload_path, null=True, blank=True,
                             help_text="Documento Anexo")

    # O principal interesse da empresa com o projeto é:
    TIPO_INTERESSE = (
        (10, "aprimorar o entendimento de uma tecnologia/solução com foco no médio prazo, sem interesse a curto prazo."),
        (20, "realizar uma prova de conceito, podendo finalizar o desenvolvimento internamente dependendo do resultado."),
        (30, "iniciar o desenvolvimento de um projeto que, potencialmente, será continuado internamente no curto prazo."),
        (40, "identificar talentos, com intenção de contratá-los para continuar esse ou outros projetos internamente."),
        (50, "mentorar estudantes para que empreendam com um produto ou tecnologia da empresa, podendo estabelecer uma parceria ou contrato de fornecimento caso seja criada uma startup a partir desse projeto."),
    )
    aprimorar = models.BooleanField(default=False, help_text=TIPO_INTERESSE[0][1])
    realizar = models.BooleanField(default=False, help_text=TIPO_INTERESSE[1][1])
    iniciar = models.BooleanField(default=False, help_text=TIPO_INTERESSE[2][1])
    identificar = models.BooleanField(default=False, help_text=TIPO_INTERESSE[3][1])
    mentorar = models.BooleanField(default=False, help_text=TIPO_INTERESSE[4][1])
    
    internacional = models.BooleanField("Internacional", default=False,
                                        help_text="Caso a proposta venha de um parceiro internacional, o que afeta a lingua de comunicação do projeto")

    intercambio = models.BooleanField("Intercâmbio", default=False,
                                        help_text="Caso a proposta venha de um intercâmbio")

    empreendendo = models.BooleanField("Empreendendo", default=False,
                                        help_text="Proposta de grupo de estudantes regulares empreendendo em próprio projeto")

    # Preenchidos automaticamente
    ano = models.PositiveIntegerField("Ano",
                                      validators=[MinValueValidator(2018), MaxValueValidator(3018)],
                                      help_text="Ano que o projeto começa")
    semestre = models.PositiveIntegerField("Semestre",
                                           validators=[MinValueValidator(1), MaxValueValidator(2)],
                                           help_text="Semestre que o projeto começa")

    organizacao = models.ForeignKey(Organizacao, on_delete=models.SET_NULL, null=True, blank=True,
                                    help_text="Organização parceira que propôs projeto")

    disponivel = models.BooleanField("Disponível", default=False,
                                     help_text="Se projeto está atualmente disponível para alunos")

    autorizado = models.ForeignKey("users.PFEUser", null=True, blank=True,
                                   on_delete=models.SET_NULL,
                                   help_text="Quem autorizou a ser publicado para os alunos")

    perfil1 = models.ManyToManyField("operacional.Curso", help_text="Perfil de curso desejado para estudante", related_name="perfil1", blank=True)
    perfil2 = models.ManyToManyField("operacional.Curso", help_text="Perfil de curso desejado para estudante", related_name="perfil2", blank=True)
    perfil3 = models.ManyToManyField("operacional.Curso", help_text="Perfil de curso desejado para estudante", related_name="perfil3", blank=True)
    perfil4 = models.ManyToManyField("operacional.Curso", help_text="Perfil de curso desejado para estudante", related_name="perfil4", blank=True)

    data = models.DateTimeField(default=datetime.datetime.now,
                                help_text="Data e hora da criação da proposta de projeto")

    colaboracao = models.ForeignKey(Organizacao, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="colaboracao",
                                    help_text="Organização colaborando para a proposta de projeto")


    # Conformidade de Proposta

    habilidades = models.BooleanField(default=False, help_text="A proposta de projeto requer conhecimentos e habilidades adquiridos em anos anteriores dos curso de graduação?")
    #Does the project proposal require knowledge and skills acquired from previous years of undergrad course work?

    design = models.BooleanField(default=False, help_text="A proposta do projeto exige que os alunos apliquem um processo sistemático de projeto em tecnologia para um sistema, componente ou processo para atender às necessidades desejadas?")
    #Does the project proposal require students to apply a systematic technical design process for a system, component, or process to meet desired needs?

    realistico = models.BooleanField(default=False, help_text="A proposta do projeto representa uma experiência do mundo real ou da indústria real que é solicitada formalmente por uma organização externa?")
    #Does the project proposal represent a have a real-world or real-industry experience that are formally requested by an external organization?

    normas = models.BooleanField(default=False, help_text="A proposta do projeto tem oportunidade de incorporar normas técnicas apropriadas que podem ser referenciados posteriormente nos relatórios do projeto?")
    #Does the project proposal have opportunity to incorporates appropriate technical standards that can be further referenced in the project reports?

    restricoes = models.BooleanField(default=False, help_text="A proposta do projeto possui um desafio de design que incorpora várias restrições realistas, como econômica, ambiental, social, política, ética, saúde e segurança, capacidade de fabricação e/ou sustentabilidade?")
    #Does the project proposal design challenge incorporate multiple realistic constraints, such as economic, environmental, social, political, ethical, health and safety, manufacturability, and/or sustainability?

    experimentacao = models.BooleanField(default=False, help_text="A proposta do projeto requer experimentação e habilidades práticas?")
    #Does the project proposal require experimentation and hands-on skills?

    equipe = models.BooleanField(default=False, help_text="A proposta do projeto permite o trabalho em equipe entre estudantes de um ou mais cursos de graduação?")
    #Does the project proposal allow teamwork among students in one or more undegrad programs?

    duracao = models.BooleanField(default=False, help_text="A proposta do projeto possui uma complexidade adequada a um semestre letivo (cerca de 4,5 meses)?")
    #Does the project proposal complexity is appropriate to one academic semester (around 4.5 months)?

    carga = models.BooleanField(default=False, help_text="A proposta do projeto é de complexidade suficiente para permitir que cada membro da equipe contribua com cerca de 360 horas entre aula, laboratório, reuniões e fora do horário de aula?")
    #Does the project proposal is sufficient complexity to allow each team member to contribute about 360 hours among class, laboratory, meetings, and outside class time?

    mensuravel = models.BooleanField(default=False, help_text="A proposta do projeto tem objetivos concretos e mensuráveis?")
    #Does the project proposal have concrete and measurable goals?

    class Meta:
        ordering = [ "ano", "semestre", "organizacao" ]
        verbose_name = "Proposta"
        verbose_name_plural = "Propostas"

    @classmethod
    def create(cls):
        """Cria um objeto (entrada) em Propostas."""
        proposta = cls()
        return proposta

    def perfis(self):
        perfis = [getattr(self, f"perfil{i}") for i in range(1, 5)]
        return perfis

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
        return reverse("proposta_editar", kwargs={"slug": self.slug})

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

    @property
    def get_edicao(self):
        if self.ano and self.semestre:
            return str(self.ano)+"."+str(self.semestre)
        return "ERRO AO IDENTIFICAR PERÍODO"

    def get_anexo(self):
        """Nome do arquivo do anexo."""
        return self.anexo.name.split('/')[-1]

    def get_anexo(self):
        """Nome do arquivo do anexo."""
        return self.anexo.name.split('/')[-1]

class Configuracao(models.Model):
    """Armazena os dados básicos de funcionamento do sistema."""

    ano = models.PositiveIntegerField("Ano",
                                      validators=[MinValueValidator(2018), MaxValueValidator(3018)],
                                      help_text="Ano de operação do sistema")
    semestre = models.PositiveIntegerField("Semestre",
                                           validators=[MinValueValidator(1), MaxValueValidator(2)],
                                           help_text="Semestre de operação do sistema")

    recipient_reembolso = models.CharField(max_length=127, blank=True,
                                           help_text="Separar lista por ponto e virgula")

    min_props = models.PositiveIntegerField("Mínimo de Propostas para Estudantes Selecionarem", default=5,
        help_text="Quantidade mínima de propostas a serem selecionas pelos estudantes")
    
    maxMB_filesize = models.PositiveIntegerField("Tamanho máximo de arquivo", default=2000,
        help_text="Tamanho máximo de arquivo em MB")

    coordenacao = models.ForeignKey("users.Administrador", null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="coordenacao",
                                    help_text="responsável pela coordenação do Capstone")
    
    operacao = models.ForeignKey("users.PFEUser", null=True, blank=True, on_delete=models.SET_NULL,
                                 related_name="operacao",
                                 help_text="responsável pela operação do Capstone")
    
    lingua = models.CharField(max_length=2, blank=True, default="pt",
                              help_text="Língua do sistema")

    prazo_avaliar = models.PositiveIntegerField("Prazo para avaliar", default=10,
                                           help_text="Prazo máximo para orientadores avaliarem entregas")
    
    prazo_preencher_banca = models.PositiveIntegerField("Prazo para banca", default=30,
                                           help_text="Prazo máximo para membros de uma banca colocarem suas avaliações")
    
    periodo_relato = models.PositiveIntegerField("Período Relato Quinzenal", default=10,
                                           help_text="Período para Relato Quinzenal ser preenchido antes do prazo")

    estudates_por_grupo = models.PositiveIntegerField("Estudantes por Grupo", default=4,
                                           help_text="Quantidade padrão de estudantes por grupo de projeto")

    #LIMITE_DE_SALAS_P_BANCAS
    limite_salas_bancas = models.PositiveIntegerField("Limite de Salas para Bancas", default=2,
                                           help_text="Limite de Salas para Bancas Simultâneas")

    ###---------------------- JSON -------------------------###
    index_documentos = models.TextField("Index Documentos", max_length=4096, null=True, blank=True,
                                   help_text="Documentos a serem mostrados no Index Documentos")
    
    horarios_semanais = models.TextField("Horarios Semanais", max_length=512, null=True, blank=True,
                                   help_text="Horários de Trabalho Semanais dos Estudantes")

    ###-----------------------------------------------------###



    ###----------------------Mensagens----------------------###

    msg_aval_pares = models.TextField("Mensagem Avaliação de Pares", max_length=1000, null=True, blank=True,
                                   help_text="Mensagem que descreve como será a Avaliação de Pares")

    msg_email_automatico = models.TextField("Mensagem de Envio Automático", max_length=1000, null=True, blank=True,
                                   help_text="Mensagem de Envio Automático de e-mail")
    
    ###-----------------------------------------------------###

    class Meta:
        verbose_name = "Configuração"
        verbose_name_plural = "Configurações"
    
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

    nome = models.CharField(max_length=100, help_text="nome")

    def __str__(self):
        """Retorno padrão textual."""
        return self.nome


class Cursada(models.Model):
    """Relacionamento entre um aluno e uma disciplina cursada por ele."""

    disciplina = models.ForeignKey(Disciplina, null=True, blank=True, on_delete=models.SET_NULL,
                                   help_text="disciplina cursada pelo aluno")
    aluno = models.ForeignKey("users.Aluno", null=True, blank=True, on_delete=models.SET_NULL,
                              help_text="aluno que cursou a disciplina")
    nota = models.PositiveSmallIntegerField(validators=[MaxValueValidator(10)],
                                            help_text="nota obtida pelo aluno na disciplina")

    class Meta:
        """Classe Meta."""
        ordering = ["nota"]

    def __str__(self):
        """Retorno padrão textual."""
        return self.aluno.user.username+" >>> "+self.disciplina.nome


class Recomendada(models.Model):
    """Disciplinas recomendadas que um aluno ja tenha cursado para fazer o projeto."""

    disciplina = models.ForeignKey(Disciplina, null=True, on_delete=models.SET_NULL,
                                   help_text="disciplina recomendada para o projeto")
    proposta = models.ForeignKey(Proposta, null=True, on_delete=models.SET_NULL,
                                 help_text="proposta que recomenda a disciplina")

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
    """Eventos para a agenda."""

    location = models.CharField(blank=True, null=True, max_length=80,
                                help_text="Onde ocorrerá o evento")
    startDate = models.DateField(default=datetime.date.today, blank=True,
                                 help_text="Inicio do Evento")
    endDate = models.DateField(default=datetime.date.today, blank=True,
                               help_text="Fim do Evento")

    # REMOVER TIPO DE EVENTO
    tipo_de_evento = models.PositiveSmallIntegerField(choices=[subl[:2] for subl in TIPO_EVENTO],
                                                      null=True, blank=True,
                                                      help_text="Define o tipo do evento a ocorrer")
    # ˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆ
    
    tipo_evento = models.ForeignKey("administracao.TipoEvento", null=True, blank=True, on_delete=models.SET_NULL,
                                      help_text="Tipo de evento")

    atividade = models.CharField(max_length=200, blank=True,
                                 help_text="nome da atividade do evento")

    observacao = models.CharField(max_length=160, blank=True,
                                  help_text="Qualquer observação relavante")
    
    descricao = models.CharField(max_length=512, blank=True,
                                 help_text="Descrição do evento")
    
    responsavel = models.ForeignKey("users.PFEUser", null=True, blank=True,
                                   on_delete=models.SET_NULL,
                                   help_text="Responsável pelo evento, por exemplo professor que ministrou a aula")

    documento = models.ForeignKey("projetos.Documento", null=True, blank=True, on_delete=models.SET_NULL,
                                  help_text="Material do evento, em caso de aulas, os slides da aula")

    documento2 = models.ForeignKey("projetos.Documento", null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name="documento2",
                                  help_text="Material axuliar do evento, em caso de aulas, os slides da aula")


    # PRECISA COLOCAR EM TIPO DE EVENTO (para os avisos)
    # coordenacao = \
    #     models.BooleanField(default=True, help_text="Para coordenação do Capstone")
    # operacional = \
    #     models.BooleanField(default=False, help_text="Para equipe operacional do Capstone")
    # comite_pfe = \
    #     models.BooleanField(default=False, help_text="Para os membros do comitê do Capstone")
    # todos_alunos = \
    #     models.BooleanField(default=False, help_text="Para todos os estudantes do semestre")
    # todos_orientadores = \
    #     models.BooleanField(default=False, help_text="Para todos os orientadores do semestre")
    # contatos_nas_organizacoes = \
    #     models.BooleanField(default=False, help_text="Para contatos nas organizações parceiras")

    def get_title(self):
        """Retorna em string o nome do evento."""
        return self.tipo_evento.nome
  
    def get_color(self):
        """Retorna uma cor característica do evento para desenhar no calendário."""
        return "#"+self.tipo_evento.cor

    def get_semester(self):
        """Retorna o semestre do evento."""
        return 1 if self.startDate.month <= 6 else 2

    def get_data(self):
        """Retorna a data do evento."""
        return self.startDate

    def em_prazo(self):
        """Se ainda em prazo."""
        return datetime.date.today() <= self.endDate
    
    def data_inicio_aval(self):
        """Data para avaliação de relatórios de bancas é especial. (para professores avaliarem)"""
        # (22, "Entrega do Relatório Intermediário (Grupo e Individual)", "#008080"),
        # (23, "Entrega do Relatório Final (Grupo e Individual)", "#00FFFF"),
        # (14, "Bancas Intermediárias", "#EE82EE"),
        # (15, "Bancas Finais", "#FFFF00"),
        if self.tipo_evento.sigla in ["ERI", "ERF"]:
            if self.tipo_evento.sigla == "ERI":
                evento = Evento.objects.filter(tipo_evento__sigla="BI", startDate__gt=self.endDate).order_by("startDate").first()
                return evento.startDate if evento else None
            else: # 23
                evento = Evento.objects.filter(tipo_evento__sigla="BF", startDate__gt=self.endDate).order_by("startDate").first()
                return evento.startDate if evento else None
        return self.startDate

    def data_aval(self):
        """Data para avaliação de relatórios de bancas é especial. (para professores avaliarem)"""
        # (22, "Entrega do Relatório Intermediário (Grupo e Individual)", "#008080"),
        # (23, "Entrega do Relatório Final (Grupo e Individual)", "#00FFFF"),
        # (14, "Bancas Intermediárias", "#EE82EE"),
        # (15, "Bancas Finais", "#FFFF00"),
        if self.tipo_evento.sigla in ["ERI", "ERF"]:
            if self.tipo_evento.sigla == "ERI":
                evento = Evento.objects.filter(tipo_evento__sigla="BI", startDate__gt=self.endDate).order_by("startDate").first()
                return evento.endDate if evento else None
            else: # 23 "ERF"
                evento = Evento.objects.filter(tipo_evento__sigla="BF", startDate__gt=self.endDate).order_by("startDate").first()
                return evento.endDate if evento else None
        return self.endDate

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

    def periodo(self):
        configuracao = get_object_or_404(Configuracao)
        if self.startDate.year >= configuracao.ano:
            if configuracao.semestre == 1 and self.startDate.month < 7:
                return {"pt": "Atuais", "en": "Current"}
            if configuracao.semestre == 2 and self.startDate.month > 7:
                return {"pt": "Atuais", "en": "Current"}
        return {"pt": "Anteriores", "en": "Previous"}
    
    def documentos(self):
        """Retorna os documentos do evento."""
        return [self.documento, self.documento2]

    @staticmethod
    def get_evento(sigla=None, tipo=None, nome=None, configuracao=None, ano=None, semestre=None):
        """Retorna o último evento do ano/semestre conforme tipo de evento."""
        return Evento.get_eventos(sigla=sigla, tipo=tipo, nome=nome, configuracao=configuracao, ano=ano, semestre=semestre).last()

    @staticmethod
    def get_eventos(sigla=None, tipo=None, nome=None, configuracao=None, ano=None, semestre=None):
        """Retorna todos os eventos de um ano e semestre conforme tipo de evento selecionado."""

        if configuracao:
            ano = configuracao.ano
            semestre = configuracao.semestre
        elif ano and semestre:
            pass
        else:
            configuracao = get_object_or_404(Configuracao)
            ano = configuracao.ano
            semestre = configuracao.semestre

        if semestre == 1:
            eventos = Evento.objects.filter(startDate__year=ano, startDate__month__lt=7)
        else:
            eventos = Evento.objects.filter(startDate__year=ano, startDate__month__gte=7)

        if sigla:
            eventos = eventos.filter(tipo_evento__sigla=sigla)
        elif tipo:
            eventos = eventos.filter(tipo_evento=tipo)
        elif nome:
            eventos = eventos.filter(tipo_evento__nome=nome)
        
        return eventos.order_by("endDate", "startDate")
            

    class Meta:
        ordering = ["startDate"]


class Banca(models.Model):
    """Bancas de Avaliação."""

    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="projeto")

    alocacao = models.ForeignKey("users.Alocacao", null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="alocação do estudante (para bancas de probation que são individuais)")

    slug = models.SlugField("slug", unique=True, max_length=64, null=True, blank=True,
                            help_text="Slug para o endereço da banca")

    location = models.CharField(null=True, blank=True, max_length=124,
                                help_text="sala em que vai ocorrer banca")
    startDate = models.DateTimeField(default=datetime.datetime.now, null=True, blank=True,
                                     help_text="Inicio da Banca")
    endDate = models.DateTimeField(default=datetime.datetime.now, null=True, blank=True,
                                   help_text="Fim da Banca")
    
    membro1 = models.ForeignKey("users.PFEUser", null=True, blank=True, on_delete=models.SET_NULL,
                                related_name="membro1", help_text="membro da banca")
    membro2 = models.ForeignKey("users.PFEUser", null=True, blank=True, on_delete=models.SET_NULL,
                                related_name="membro2", help_text="membro da banca")
    membro3 = models.ForeignKey("users.PFEUser", null=True, blank=True, on_delete=models.SET_NULL,
                                related_name="membro3", help_text="membro da banca")

    ### REMOVER TIPO DE BANCA
    TIPO_DE_BANCA = ( # não mudar a ordem dos números
        (0, "Final"),
        (1, "Intermediária"),
        (2, "Falconi"),
        (3, "Probation"),
    )
    tipo_de_banca = models.PositiveSmallIntegerField(choices=TIPO_DE_BANCA, default=0)
    #### ˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆ


    link = models.CharField(max_length=512, blank=True,
                            help_text="Link para transmissão pela internet se houver")
    
    composicao = models.ForeignKey("academica.Composicao", null=True, blank=True, on_delete=models.SET_NULL,
                                   help_text="tipo de composição para exame de avaliação da banca")

    def get_sigla(self):
        """Retorna a sigla do tipo de banca."""
        return self.composicao.exame.sigla

    def __str__(self):
        """Retorno padrão textual."""
        texto = "Banca " + self.composicao.exame.titulo + ": "
        if self.alocacao:
            texto += "(" + self.alocacao.aluno.user.get_full_name() + ") "
        texto +=  "[" + self.get_projeto().organizacao.sigla + "] " + self.get_projeto().get_titulo()
        return texto

    @classmethod
    def create(cls, projeto=None):
        """Cria um objeto (entrada) na Banca."""
        if projeto is None:
            banca = cls()
        else:
            banca = cls(projeto=projeto)
        return banca

    # pylint: disable=arguments-differ
    def save(self, *args, **kwargs):
        if not self.id:
            senha = ''.join(random.SystemRandom().\
                                   choice(string.ascii_uppercase + string.digits) for _ in range(6))

            ano = self.startDate.strftime("%y")
            mes = int(self.startDate.strftime("%m"))
            semestre = "2" if mes > 7 else "1"
            self.slug = slugify(ano+semestre+str(self.composicao.exame.sigla)+senha)

        super(Banca, self).save(*args, **kwargs)

    def get_absolute_url(self):
        """Caminho para avaliar uma banca."""
        return reverse("banca_avaliar", kwargs={"slug": self.slug})

    def membros(self):
        """Retorna os membros da banca."""
        selecao = []
        if self.composicao.exame.sigla in ["BI", "BF"]: # Banca Final ou Intermediária também precisam da avaliação do orientador
            selecao += [self.projeto.orientador.user]
        selecao += [ m for m in [self.membro1, self.membro2, self.membro3] if m is not None]
        return selecao
    
    class Meta:
        ordering = ["startDate"]

    def get_tipo(self):
        """Retorna o tipo da banca."""
        return self.composicao.exame
    
    @property
    def periodo(self):
        if datetime.datetime.now() < self.startDate + datetime.timedelta(days=30):
            return {"pt": "Atuais", "en": "Current"}
        return {"pt": "Anteriores", "en": "Previous"}

    def get_observacoes_estudantes(self):
        """Retorna as observações dos estudantes."""
        if self.alocacao:  # Não estão sendo preenchidas as observações para estudantes de bancas de probation
            return Observacao.objects.filter(alocacao=self.alocacao, observacoes_estudantes__isnull=False, exame=self.composicao.exame)
        return Observacao.objects.filter(projeto=self.projeto, observacoes_estudantes__isnull=False, exame=self.composicao.exame)
    
    def get_avaliacoes_bancas(self):
        """Retorna as avaliações da banca (com algumas condições)."""
        prazo_horas = 24  # prazo para publicar as notas depois que todos avaliaram
        if self.composicao.exame.sigla == "F":
            prazo_horas = 24*14
        elif self.composicao.exame.sigla == "P":
            prazo_horas = 48
        
        avaliacoes = Avaliacao2.objects.filter(projeto=self.projeto, exame=self.composicao.exame)

        now = datetime.datetime.now()
        checa_banca = True

        # Evento de encerramento
        if self.alocacao is None:  # Não é banca de probation
            evento = Evento.get_evento(sigla="EE", ano=self.projeto.ano, semestre=self.projeto.semestre)                
            if evento and now.date() > evento.endDate:  # Após o evento de encerramento liberar todas as notas
                checa_banca = False

        # Verifica se todos avaliaram a pelo menos 24 horas atrás
        if checa_banca:

            for membro in self.membros():
                avaliacao = avaliacoes.filter(avaliador=membro).last()
                if not avaliacao:
                    return None
                if now - avaliacao.momento < datetime.timedelta(hours=prazo_horas):
                    return None
        
        objetivos = {}
        nota = 0
        peso = 0
        pesos = {}
        for avaliacao in avaliacoes:
            if (avaliacao.nota is not None) and (avaliacao.peso is not None):
                if avaliacao.objetivo in objetivos:
                    objetivos[avaliacao.objetivo] += avaliacao.nota
                    pesos[avaliacao.objetivo] += 1
                else:
                    objetivos[avaliacao.objetivo] = avaliacao.nota
                    pesos[avaliacao.objetivo] = 1
                nota += float(avaliacao.nota) * float(avaliacao.peso)
                peso += float(avaliacao.peso)

        for objetivo in objetivos:
            objetivos[objetivo] = (objetivos[objetivo]/pesos[objetivo], converte_letra(objetivos[objetivo]/pesos[objetivo]))

        avaliacao = {}
        avaliacao["objetivos"] = objetivos
        avaliacao["nota"] = nota/peso if peso > 0 else 0
        avaliacao["peso"] = peso

        return avaliacao
    
    def get_cor(self):
        return f"#{self.composicao.exame.cor}"

    def get_avaliadores(self):
        objetivos = ObjetivosDeAprendizagem.objects.all()
        avaliadores = {}
        projeto = self.get_projeto()
        exame = self.composicao.exame
        for objetivo in objetivos:
        
            if self.alocacao:  # Probation
                avaliacoes = Avaliacao2.objects.filter(alocacao=self.alocacao, objetivo=objetivo, exame=exame).order_by("avaliador", "-momento")
            else:
                avaliacoes = Avaliacao2.objects.filter(projeto=projeto, objetivo=objetivo, exame=exame).order_by("avaliador", "-momento")

            for banca in avaliacoes:
                if banca.avaliador not in avaliadores:
                    avaliadores[banca.avaliador] = {}
                if objetivo not in avaliadores[banca.avaliador]:
                    avaliadores[banca.avaliador][objetivo] = banca
                    avaliadores[banca.avaliador]["momento"] = banca.momento
        
        if self.alocacao:
            observacoes = Observacao.objects.filter(alocacao=self.alocacao, exame=exame).order_by("avaliador", "-momento")
        else:
            observacoes = Observacao.objects.filter(projeto=projeto, exame=exame).order_by("avaliador", "-momento")

        for observacao in observacoes:
            if observacao.avaliador not in avaliadores:
                avaliadores[observacao.avaliador] = {}
            if "observacoes_estudantes" not in avaliadores[observacao.avaliador]:
                avaliadores[observacao.avaliador]["observacoes_estudantes"] = observacao.observacoes_estudantes
            if "observacoes_orientador" not in avaliadores[observacao.avaliador]:
                avaliadores[observacao.avaliador]["observacoes_orientador"] = observacao.observacoes_orientador

        return avaliadores

    def get_projeto(self):
        """Retorna o projeto da banca."""
        if self.alocacao:
            return self.alocacao.projeto
        if self.projeto:
            return self.projeto
        return None
    
    @staticmethod
    def get_bancas_com_membro(membro):
        bancas = (Banca.objects.filter(membro1=membro) |
                  Banca.objects.filter(membro2=membro) |
                  Banca.objects.filter(membro3=membro))

        # Orientador é automaticamente membro de banca final e intermediária
        if hasattr(membro, "Professor"):
            bancas = bancas | Banca.objects.filter(projeto__orientador=membro.professor, composicao__exame__sigla__in=("BI", "BF"))
        return bancas


class Encontro(models.Model):
    """Encontros (para dinâmicas de grupos)."""

    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="projeto")
    location = models.CharField(blank=True, max_length=280,
                                help_text="sala em que vai ocorrer a dinâmica")
    startDate = models.DateTimeField(default=datetime.datetime.now,
                                     help_text="Inicio da Dinâmica")
    endDate = models.DateTimeField(default=datetime.datetime.now,
                                   help_text="Fim da Dinâmica")
    facilitador = models.ForeignKey("users.PFEUser", null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name="facilitador",
                                    help_text="facilitador da dinâmica")

    def hora_fim(self):
        """Mostra só a hora final do encontro."""
        return self.endDate.strftime("%H:%M")
    hora_fim.short_description = "Hora Fim"

    def url_location(self):
        """Checa se link."""
        if self.location[:4] == "http":
            return True
        return False
    
    def periodo(self):
        configuracao = get_object_or_404(Configuracao)
        if self.startDate.year >= configuracao.ano:
            if configuracao.semestre == 1 and self.startDate.month < 7:
                return {"pt": "Atuais", "en": "Current"}
            if configuracao.semestre == 2 and self.startDate.month > 7:
                return {"pt": "Atuais", "en": "Current"}
        return {"pt": "Anteriores", "en": "Previous"}
    
    def get_projeto(self):
        """Retorna o projeto do encontro."""
        return self.projeto

    @classmethod
    def create(cls, startDate, endDate):
        """Cria um objeto (entrada) no Encontro."""
        encontro = cls(startDate=startDate, endDate=endDate)
        return encontro

    def __str__(self):
        return str(self.startDate)


class TipoRetorno(models.Model):
    """Tipos de retorno de comunicações com as organizações parceiras."""

    nome = models.CharField(max_length=64, help_text="nome do tipo de retorno")
    descricao = models.CharField(max_length=512, blank=True, help_text="descrição do tipo de retorno")
    cor = models.CharField(max_length=6, default="FFFFFF", help_text="cor do tipo de retorno")
    
    # REMOVER TMP_ID
    tmp_id = models.PositiveIntegerField(null=True, blank=True, help_text="id temporário")

    GRUPO_DE_RETORNO = ( # não mudar a ordem dos números
        (1, "Prospecção"),
        (2, "Retorno"),
        (3, "Contratação"),
        (4, "Relatório"),
        (5, "outros"),
    )

    grupo_de_retorno = models.PositiveSmallIntegerField(choices=GRUPO_DE_RETORNO, default=0)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Tipo de Retorno"
        verbose_name_plural = "Tipos de Retorno"
        ordering = ["-grupo_de_retorno", "nome"]

class Anotacao(models.Model):
    """Anotacoes de comunicações com as organizações pareceiras."""

    momento = models.DateTimeField(default=datetime.datetime.now, blank=True,
                                   help_text="Data e hora da comunicação") # hora ordena para dia
    organizacao = models.ForeignKey(Organizacao, null=True, blank=True, on_delete=models.SET_NULL,
                                    help_text="Organização parceira")
    autor = models.ForeignKey("users.PFEUser", null=True, blank=True, on_delete=models.SET_NULL,
                              related_name="professor_orientador", help_text="quem fez a anotação")
    texto = models.TextField(max_length=2000, help_text="Anotação")

    # Obsoleto - não usar
    TIPO_DE_RETORNO = ( # não mudar a ordem dos números
        (0, "Contactada para enviar proposta", "Prospecção"),
        (1, "Interessada em enviar proposta", "Prospecção"),
        (2, "Enviou proposta de projeto", "Prospecção"),
        (3, "Não enviará proposta de projeto", "Prospecção"),
        (4, "Confirmamos estudantes para o(s) projeto(s) proposto(s)", "Retorno"),
        (5, "Notificamos que não conseguimos montar projeto", "Retorno"),
        (6, "Contrato fechado para projeto", "Contratação"),
        (7, "Envio de Relatório Final", "Relatório"),
        (10, "Autorizou a publicação do Relatório Final", "Relatório"),
        (11, "Negou a publicação do Relatório Final (público)", "Relatório"),
        (12, "Contrato em análise", "Contratação"),
        (13, "Acionada para assinatura de contrato", "Contratação"),
        (254, "outros", ""),
    )

    # Obsoleto - não usar
    tipo_de_retorno = models.PositiveSmallIntegerField(choices=[subl[:2] for subl in TIPO_DE_RETORNO], default=0)
    # ˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆˆ

    tipo_retorno = models.ForeignKey(TipoRetorno, null=True, blank=True, on_delete=models.SET_NULL,
                                    help_text="Tipo de retorno")

    def __str__(self):
        return str(self.momento)

    @classmethod
    def create(cls, organizacao):
        """Cria um objeto (entrada) em Anotação."""
        anotacao = cls(organizacao=organizacao)
        return anotacao

    class Meta:
        verbose_name = "Anotação"
        verbose_name_plural = "Anotações"


class Documento(models.Model):
    """Documentos em geral."""

    organizacao = models.ForeignKey(Organizacao, null=True, blank=True, on_delete=models.SET_NULL,
                                    help_text="Organização referente o documento")
    usuario = models.ForeignKey("users.PFEUser", null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="Usuário do documento")
    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="Documento do Projeto")
    documento = models.FileField(null=True, blank=True, max_length=256,
                                 upload_to=get_upload_path,
                                 help_text="Link para o arquivo no servidor")
    link = models.URLField("link", max_length=320, null=True, blank=True,
                           help_text="Link do documento na internets")
    anotacao = models.CharField(null=True, blank=True, max_length=64,
                                help_text="Qualquer anotação sobre o documento em questão")
    data = models.DateTimeField(null=True, blank=True,
                            help_text="Data e hora do documento")
    tipo_documento = models.ForeignKey("documentos.TipoDocumento", null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="Tipo de documento")
    confidencial = models.BooleanField(default=True, help_text="Documento confidêncial")

    LINGUA_DO_DOCUMENTO = ( # não mudar a ordem dos números
        (0, "Português"),
        (1, "Inglês"),
    )

    lingua_do_documento = models.PositiveSmallIntegerField(choices=LINGUA_DO_DOCUMENTO, default=0)

    def __str__(self):
        texto = ""
        texto += str(self.tipo_documento) + " "
        if self.data:
            texto += " [" + str(self.data) + "]"
        if self.anotacao:
            texto += " ("+str(self.anotacao)+")"
        return texto
    
    def filename(self):
        if self.documento:
            return os.path.basename(self.documento.name)
        else:
            return self.link
    
    def extensao(self):
        return os.path.splitext(self.filename())[1][1:].upper()

    # Remove o arquivo apontado pelo documento se o documento for deletado
    def delete(self, using=None, keep_parents=False):
        self.documento.delete()
        super().delete()

    @classmethod
    def create(cls):
        """Cria um objeto (entrada) em Documento."""
        documento = cls()
        return documento

    class Meta:
        ordering = ["-data"]


class Banco(models.Model):
    """Lista dos Bancos Existentes no Brasil."""

    nome = models.CharField(max_length=50,
                            help_text="nome do banco")
    codigo = models.PositiveSmallIntegerField(validators=[MaxValueValidator(999)],
                                              help_text="código do banco")

    @classmethod
    def create(cls, nome, codigo):
        """Cria um objeto (entrada) no Banco."""
        banco = cls(nome=nome, codigo=codigo)
        return banco

    def __str__(self):
        return str(self.nome)


class Reembolso(models.Model):
    """Armazena os reembolsos pedidos."""

    usuario = models.ForeignKey("users.PFEUser", null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="usuário pedindo reembolso")
    banco = models.ForeignKey(Banco, null=True, on_delete=models.SET_NULL,
                              help_text="banco a se fazer o reembolso")
    agencia = models.CharField(max_length=6, null=True, blank=True,
                               help_text="agência no banco")
    conta = models.CharField(max_length=16, null=True, blank=True,
                             help_text="conta no banco")
    descricao = models.TextField(max_length=2000,
                                 help_text="desrição do pedido de reembolso")
    valor = models.DecimalField(max_digits=5, decimal_places=2,
                                help_text="valor a ser reembolsado")
    data = models.DateTimeField(default=datetime.datetime.now,
                                help_text="data e hora da criação do pedido de reembolso")
    nota = models.FileField(upload_to=get_upload_path, null=True, blank=True,
                            help_text="Nota(s) Fiscal(is)")

    @classmethod
    def create(cls, usuario):
        """Cria um objeto (entrada) no Reembolso."""
        reembolso = cls(usuario=usuario)
        return reembolso

    def __str__(self):
        return str(str(self.usuario)+str(self.data))


class Aviso(models.Model):
    """Avisos para a Coordenação do Capstone."""

    titulo = models.CharField(max_length=120, null=True, blank=True,
                              help_text="Título do Aviso")

    tipo_de_evento = models.\
        PositiveSmallIntegerField(choices=[subl[:2] for subl in TIPO_EVENTO],
                                  null=True, blank=True,
                                  help_text="Define o tipo do evento de referência")
    
    tipo_evento = models.ForeignKey("administracao.TipoEvento", null=True, blank=True, on_delete=models.SET_NULL,
                                    help_text="Tipo de evento")

    delta = models.SmallIntegerField(default=0,
                                     help_text="dias passados do evento definido")
    mensagem = models.TextField(max_length=4096, null=True, blank=True,
                                help_text="mensagem a ser enviar no texto")
    
    ### NÃO DEVE SER MAIS USADO ##############################################
    realizado = models.BooleanField(default=False, help_text="Se já realizado no período")  # NAO MAIS USADO
    data_realizado = models.DateField(default=datetime.date.today, blank=True,
                                      help_text="Data de quando o evento foi realizado pela última vez")
    ##########################################################################
    
    datas_realizado = models.TextField(max_length=4096, default="[]",
                                      help_text="Datas de quando o evento foi realizado")
    

    # Quem deve receber o aviso (REPETIDO EM TIPO DE EVENTO)
    coordenacao = \
        models.BooleanField(default=True, help_text="Para coordenação do Capstone")
    operacional = \
        models.BooleanField(default=False, help_text="Para equipe operacional do Capstone")
    comite_pfe = \
        models.BooleanField(default=False, help_text="Para os membros do comitê do Capstone")
    todos_alunos = \
        models.BooleanField(default=False, help_text="Para todos os estudantes do semestre")
    todos_orientadores = \
        models.BooleanField(default=False, help_text="Para todos os orientadores do semestre")
    contatos_nas_organizacoes = \
        models.BooleanField(default=False, help_text="Para contatos nas organizações parceiras")

    def get_evento(self):
        """Retorna em string o nome do evento."""
        if self.tipo_evento:
            return self.tipo_evento.nome
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
                            help_text="nome da entidade estudantil")

    def __str__(self):
        return self.nome

class Acompanhamento(models.Model):
    """Acompanhamento das organizacoes parceiras."""

    data = models.DateField(default=datetime.date.today, blank=True,
                            help_text="Data da Resposta")
    autor = models.ForeignKey("users.PFEUser", null=True, blank=True, on_delete=models.SET_NULL,
                              help_text="quem enviou a observação de acompanhamento")
    texto = models.TextField(max_length=1000, help_text="Feedback Outros")

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
                            help_text="Data do Feedback")
    nome = models.CharField(max_length=120, null=True, blank=True,
                            help_text="Nome de quem está dando o Feedback")
    email = models.EmailField(max_length=80, null=True, blank=True,
                              help_text="e-mail de quem está dando o Feedback")
    #isso esta bem baguncado
    empresa = models.CharField(max_length=120, null=True, blank=True,
                               help_text="Empresa de quem está dando o Feedback")
    tecnico = models.TextField(max_length=1000, null=True, blank=True,
                               help_text="Feedback Técnico")
    comunicacao = models.TextField(max_length=1000, null=True, blank=True,
                                   help_text="Feedback Comunicação")
    organizacao = models.TextField(max_length=1000, null=True, blank=True,
                                   help_text="Feedback Organização")
    outros = models.TextField(max_length=1000, null=True, blank=True,
                              help_text="Feedback Outros")

    nps = models.PositiveIntegerField("NPS", null=True, blank=True,
                                      validators=[MinValueValidator(0), MaxValueValidator(10)],
                                      help_text="Valor Net Promoter Score")

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
                                help_text="Data e hora do feedback")

    estudante = models.ForeignKey("users.Aluno", null=True, blank=True, on_delete=models.SET_NULL,
                              help_text="estudante que fez o feedback")

    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="projeto que estava no feedback")

    TIPO_RECOMENDARIA = ( # não mudar a ordem dos números
        (1, "Não recomendo"),
        (2, "Recomendo com ressalvas"),
        (3, "Recomendo fortemente"),
    )
    recomendaria = models.PositiveSmallIntegerField(choices=TIPO_RECOMENDARIA, null=True, blank=True,
                                                    help_text="O quanto você recomendaria fazermos um projeto de Casptone nos próximos semestres com a Empresa Parceira?")


    primeira_opcao = models.BooleanField("Primeira Opção", null=True, blank=True,
                                         help_text="Agora que você conhece mais da Empresa Parceira, essa seria uma das primeiras opções para você fazer estágio ou ser contratado de forma efetiva?")

    TIPO_PROPOSTA = ( # não mudar a ordem dos números
        (1, "Recebi convite e apliquei"),
        (2, "Não recebi convite, mas apliquei"),
        (3, "Recebi convite, mas não apliquei"),
        (4, "Não recebi, nem apliquei"),
        (5, "Não haviam vagas em aberto"),
    )
    proposta = models.PositiveSmallIntegerField(choices=TIPO_PROPOSTA, null=True, blank=True,
                                                    help_text="Tendo ou não buscado alguma proposta da Empresa Parceira para estágio ou contrato de trabalho.")


    TIPO_TRABALHANDO = ( # não mudar a ordem dos números
        (1, "Empresa do Projeto do PFE"),
        (2, "Outra"),
        (3, "Ainda não"),
        (4, "Prefiro não responder"),
    )
    trabalhando = models.PositiveSmallIntegerField(choices=TIPO_TRABALHANDO, null=True, blank=True,
                                                    help_text="Você já está trabalhando (ou em vias de trabalhar) em alguma empresa?")


    outros = models.TextField(max_length=1000, null=True, blank=True,
                              help_text="Feedback Outros")

    def __str__(self):
        return str(self.momento) + " - " + str(self.estudante) + " : " + str(self.projeto)

    @classmethod
    def create(cls):
        """Cria um objeto (entrada) em FeedbackEstudante."""
        feedback = cls()
        return feedback


class Conexao(models.Model):
    """Controla como um usuário se conecta a um projeto."""

    parceiro = models.ForeignKey("users.Parceiro", null=True,
                                 on_delete=models.SET_NULL,
                                 help_text="parceiro que se conecta ao projeto")

    projeto = models.ForeignKey(Projeto, null=True, on_delete=models.SET_NULL,
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
    
    def get_projeto(self):
        """Retorna o projeto da conexão."""
        return self.projeto
    
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
        verbose_name = "Conexão"
        verbose_name_plural = "Conexões"


class Coorientador(models.Model):
    """Controla lista de coorientadores por projeto."""

    usuario = models.ForeignKey("users.PFEUser", null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="coorientador de um projeto")
    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="projeto que foi coorientado")
    observacao = models.TextField(max_length=256, null=True, blank=True,
                                  help_text="qualquer observação relevante")

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

    # def certificado_coorientador(self):
    #     """Se o coorientador pode emitir certificado."""
    #     tipo_certificado = get_object_or_404(TipoCertificado, titulo="Coorientação de Projeto")
    #     certificado = Certificado.objects.filter(projeto=self.projeto, usuario=self.usuario, tipo_certificado=tipo_certificado)
    #     return certificado

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
                                               help_text="Rubrica intermediária do conceito D")
    rubrica_final_D = models.TextField(max_length=1024, null=True, blank=True,
                                       help_text="Rubrica final do conceito D")
    rubrica_intermediaria_C = models.TextField(max_length=1024, null=True, blank=True,
                                               help_text="Rubrica intermediária do conceito C")
    rubrica_final_C = models.TextField(max_length=1024, null=True, blank=True,
                                       help_text="Rubrica final do conceito C")
    rubrica_intermediaria_B = models.TextField(max_length=1024, null=True, blank=True,
                                               help_text="Rubrica intermediária do conceito B")
    rubrica_final_B = models.TextField(max_length=1024, null=True, blank=True,
                                       help_text="Rubrica final do conceito B")
    rubrica_intermediaria_A = models.TextField(max_length=1024, null=True, blank=True,
                                               help_text="Rubrica intermediária do conceito A")
    rubrica_final_A = models.TextField(max_length=1024, null=True, blank=True,
                                       help_text="Rubrica final do conceito A")



    # Rubricas de Individuais Intermediárias e Finais
    rubrica_intermediaria_individual_I = models.TextField(max_length=1024, null=True, blank=True,
                                                         help_text="Rubrica intermediária do conceito I")
    rubrica_final_individual_I = models.TextField(max_length=1024, null=True, blank=True,
                                                 help_text="Rubrica final do conceito I")
    rubrica_intermediaria_individual_D = models.TextField(max_length=1024, null=True, blank=True,
                                                         help_text="Rubrica intermediária do conceito D")
    rubrica_final_individual_D = models.TextField(max_length=1024, null=True, blank=True,
                                                 help_text="Rubrica final do conceito D")
    rubrica_intermediaria_individual_C = models.TextField(max_length=1024, null=True, blank=True,
                                                         help_text="Rubrica intermediária do conceito C")
    rubrica_final_individual_C = models.TextField(max_length=1024, null=True, blank=True,
                                                 help_text="Rubrica final do conceito C")
    rubrica_intermediaria_individual_B = models.TextField(max_length=1024, null=True, blank=True,
                                                         help_text="Rubrica intermediária do conceito B")
    rubrica_final_individual_B = models.TextField(max_length=1024, null=True, blank=True,
                                                 help_text="Rubrica final do conceito B")
    rubrica_intermediaria_individual_A = models.TextField(max_length=1024, null=True, blank=True,
                                                         help_text="Rubrica intermediária do conceito A")
    rubrica_final_individual_A = models.TextField(max_length=1024, null=True, blank=True,
                                                 help_text="Rubrica final do conceito A")



    # Rubricas de Grupo Intermediárias e Finais em Inglês
    rubrica_intermediaria_I_en = models.TextField(max_length=1024, null=True, blank=True,
                                               help_text="Rubrica intermediária do conceito I")
    rubrica_final_I_en = models.TextField(max_length=1024, null=True, blank=True,
                                       help_text="Rubrica final do conceito I")
    rubrica_intermediaria_D_en = models.TextField(max_length=1024, null=True, blank=True,
                                               help_text="Rubrica intermediária do conceito D")
    rubrica_final_D_en = models.TextField(max_length=1024, null=True, blank=True,
                                       help_text="Rubrica final do conceito D")
    rubrica_intermediaria_C_en = models.TextField(max_length=1024, null=True, blank=True,
                                               help_text="Rubrica intermediária do conceito C")
    rubrica_final_C_en = models.TextField(max_length=1024, null=True, blank=True,
                                       help_text="Rubrica final do conceito C")
    rubrica_intermediaria_B_en = models.TextField(max_length=1024, null=True, blank=True,
                                               help_text="Rubrica intermediária do conceito B")
    rubrica_final_B_en = models.TextField(max_length=1024, null=True, blank=True,
                                       help_text="Rubrica final do conceito B")
    rubrica_intermediaria_A_en = models.TextField(max_length=1024, null=True, blank=True,
                                               help_text="Rubrica intermediária do conceito A")
    rubrica_final_A_en = models.TextField(max_length=1024, null=True, blank=True,
                                       help_text="Rubrica final do conceito A")



    # Rubricas de Individuais Intermediárias e Finais em Inglês
    rubrica_intermediaria_individual_I_en = models.TextField(max_length=1024, null=True, blank=True,
                                                         help_text="Rubrica intermediária do conceito I")
    rubrica_final_individual_I_en = models.TextField(max_length=1024, null=True, blank=True,
                                                 help_text="Rubrica final do conceito I")
    rubrica_intermediaria_individual_D_en = models.TextField(max_length=1024, null=True, blank=True,
                                                         help_text="Rubrica intermediária do conceito D")
    rubrica_final_individual_D_en = models.TextField(max_length=1024, null=True, blank=True,
                                                 help_text="Rubrica final do conceito D")
    rubrica_intermediaria_individual_C_en = models.TextField(max_length=1024, null=True, blank=True,
                                                         help_text="Rubrica intermediária do conceito C")
    rubrica_final_individual_C_en = models.TextField(max_length=1024, null=True, blank=True,
                                                 help_text="Rubrica final do conceito C")
    rubrica_intermediaria_individual_B_en = models.TextField(max_length=1024, null=True, blank=True,
                                                         help_text="Rubrica intermediária do conceito B")
    rubrica_final_individual_B_en = models.TextField(max_length=1024, null=True, blank=True,
                                                 help_text="Rubrica final do conceito B")
    rubrica_intermediaria_individual_A_en = models.TextField(max_length=1024, null=True, blank=True,
                                                         help_text="Rubrica intermediária do conceito A")
    rubrica_final_individual_A_en = models.TextField(max_length=1024, null=True, blank=True,
                                                 help_text="Rubrica final do conceito A")





    avaliacao_aluno = models.BooleanField("Avaliação do Aluno", default=False,
                                          help_text="Avaliação do Aluno (AA)")

    avaliacao_banca = models.BooleanField("Avaliação da Banca", default=False,
                                          help_text="Avaliação da Banca (AB)")

    avaliacao_grupo = models.BooleanField("Avaliação do Grupo", default=False,
                                          help_text="Avaliação do Grupo (AG)")

    avaliacao_falconi = models.BooleanField("Avaliação Falconi", default=False,
                                            help_text="Avaliação Falconi (AF)")

    data_inicial = models.DateField("Data Inicial", null=True, blank=True,
                                    help_text="Data Inicial de Uso")

    data_final = models.DateField("Data Final", null=True, blank=True,
                                  help_text="Data Final de Uso")


    ### ESSES PESOS PODEM SER REMOVIDOS, NÃO DEVEM SER MAIS USADOS
    peso_intermediario_individual = models.FloatField(default=0,
                                                      help_text="peso intermediário individual")

    peso_intermediario_grupo = models.FloatField(default=0,
                                                 help_text="peso intermediário grupo")

    peso_final_individual = models.FloatField(default=0,
                                              help_text="peso final individual")

    peso_final_grupo = models.FloatField(default=0,
                                         help_text="peso final grupo")

    peso_banca_intermediaria = models.FloatField(default=0,
                                                 help_text="peso para banca intermediária")

    peso_banca_final = models.FloatField(default=0,
                                         help_text="peso para banca final")

    peso_banca_falconi = models.FloatField(default=0,
                                           help_text="peso para banca falconi")
    ##############################################################


    ordem = models.PositiveSmallIntegerField(help_text="ordem para aparecer nas listas")


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
        verbose_name = "ObjetivosDeAprendizagem"
        verbose_name_plural = "ObjetivosDeAprendizagem"
        ordering = ["ordem", "data_inicial"]


class Avaliacao2(models.Model):
    """Avaliações realizadas durante o projeto."""

    # NÃO USAR MAIS TIPO DE AVALIAÇÃO, USAR EXAME
    # tipo_de_avaliacao = models.PositiveSmallIntegerField(choices=TIPO_DE_AVALIACAO, default=0)

    # DEFINE O TIPO DE AVALIAÇÃO
    exame = models.ForeignKey("academica.Exame", null=True, blank=True, on_delete=models.SET_NULL,
                                 help_text="Tipo de avaliação")

    momento = models.DateTimeField(default=datetime.datetime.now, blank=True,
                                   help_text="Data e hora da avaliação") # hora ordena para dia

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
        verbose_name = "Avaliação2"
        verbose_name_plural = "Avaliações2"
        ordering = ["momento",]

    def get_conceito(self):
        return converte_letra(self.nota)

    def get_conceitoX(self):
        return converte_letra(self.nota, mais="X")


class Avaliacao_Velha(models.Model):
    """Quando avaliações de banca são refeitas, as antigas vem para essa base de dados."""

    # NÃO USAR MAIS TIPO DE AVALIAÇÃO, USAR EXAME
    # tipo_de_avaliacao = models.PositiveSmallIntegerField(choices=TIPO_DE_AVALIACAO, default=0)

    # DEFINE O TIPO DE AVALIAÇÃO
    exame = models.ForeignKey("academica.Exame", null=True, blank=True, on_delete=models.SET_NULL,
                                 help_text="Tipo de avaliação")

    momento = models.DateTimeField(default=datetime.datetime.now, blank=True,
                                   help_text="Data e hora da comunicação") # hora ordena para dia

    peso = models.FloatField("Peso", validators=[MinValueValidator(0), MaxValueValidator(100)],
                             null=True, blank=True,
                             help_text="Pesa da avaliação na média (bancas compartilham peso)",
                             default=10) # 10% para as bancas

    # A nota será convertida para rubricas se necessário
    nota = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    # Somente útil para Bancas
    avaliador = models.ForeignKey("users.PFEUser", null=True, blank=True, on_delete=models.SET_NULL,
                                  help_text="avaliador do projeto")

    # Para Bancas e Entregas em Grupo (quando avaliando o grupo inteiro)
    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="projeto que foi avaliado")

    # Para Alocações dos estudantes (caso um aluno reprove ele teria duas alocações)
    alocacao = models.ForeignKey("users.Alocacao", null=True, blank=True,
                                 on_delete=models.SET_NULL,
                                 related_name="projeto_alocado_avaliacao_velha",
                                 help_text="relacao de alocação entre projeto e estudante")

    objetivo = models.ForeignKey(ObjetivosDeAprendizagem, related_name="objetivo_avaliacao_velha",
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

    @classmethod
    def create(cls, projeto=None, alocacao=None):
        """Cria um objeto (entrada) em Avaliação Velha."""
        avaliacao = cls(projeto=projeto, alocacao=alocacao)
        return avaliacao

    class Meta:
        verbose_name = "Avaliação Velha"
        verbose_name_plural = "Avaliações Velhas"
        ordering = ["momento",]


class Reprovacao(models.Model):
    """Reprovações controladas por falha em Objetivos de Aprendizagem."""

    # Para Alocações dos estudantes (caso um aluno reprove ele teria duas alocações)
    alocacao = models.ForeignKey("users.Alocacao", null=True,
                                 on_delete=models.SET_NULL,
                                 related_name="projeto_alocado_reprovacao",
                                 help_text="alocação que sofreu reprovação")

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
        verbose_name = "Reprovação"
        verbose_name_plural = "Reprovações"


class Observacao(models.Model):
    """Observações realizadas durante avaliações."""

    # DEFINE O TIPO DE AVALIAÇÃO
    exame = models.ForeignKey("academica.Exame", null=True, blank=True, on_delete=models.SET_NULL,
                                 help_text="Tipo de avaliação")
    
    momento = models.DateTimeField(default=datetime.datetime.now, blank=True,
                                   help_text="Data e hora da comunicação") # hora ordena para dia

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
    objetivo = models.ForeignKey(ObjetivosDeAprendizagem, related_name="objetivo_observacao",
                                 on_delete=models.SET_NULL, null=True, blank=True,
                                 help_text="Objetivo de Aprendizagem")

    observacoes_orientador = models.TextField(max_length=5000, null=True, blank=True,
                                   help_text="Observações a serem compartilhadas somente com o orientador do projeto")

    observacoes_estudantes = models.TextField(max_length=5000, null=True, blank=True,
                                   help_text="Observações a serem compartilhadas com os estudantes do projeto")

    def __str__(self):
        return "Obs. tipo: " + str(self.exame) + " = " + str(self.observacoes_orientador)[:6] + "..."

    class Meta:
        verbose_name = "Observação"
        verbose_name_plural = "Observações"


class Observacao_Velha(models.Model):
    """Quando Observações de banca são refeitas, as antigas vem para essa base de dados."""

    # NÃO USAR MAIS TIPO DE AVALIAÇÃO, USAR EXAME
    # tipo_de_avaliacao = models.PositiveSmallIntegerField(choices=TIPO_DE_AVALIACAO, default=0)

    # DEFINE O TIPO DE AVALIAÇÃO
    exame = models.ForeignKey("academica.Exame", null=True, blank=True, on_delete=models.SET_NULL,
                                 help_text="Tipo de avaliação")
    
    momento = models.DateTimeField(default=datetime.datetime.now, blank=True,
                                   help_text="Data e hora da comunicação") # hora ordena para dia

    # Somente útil para Bancas
    avaliador = models.ForeignKey("users.PFEUser", null=True, blank=True, on_delete=models.SET_NULL,
                                  help_text="avaliador do projeto")

    # Para Bancas e Entregas em Grupo
    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="projeto que foi avaliado")

    # Para Alocações dos estudantes (caso um aluno reprove ele teria duas alocações)
    alocacao = models.ForeignKey("users.Alocacao", null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name="observacao_velha_alocado",
                                 help_text="relacao de alocação entre projeto e estudante")

    # Se houver, usando pois no Blackboard alguns estão dessa forma
    objetivo = models.ForeignKey(ObjetivosDeAprendizagem, related_name="objetivo_observacao_velha",
                                 on_delete=models.SET_NULL, null=True, blank=True,
                                 help_text="Objetivo de Aprendizagem")

    observacoes_orientador = models.TextField(max_length=5000, null=True, blank=True,
                                   help_text="Observações a serem compartilhadas somente com o orientador do projeto")

    observacoes_estudantes = models.TextField(max_length=5000, null=True, blank=True,
                                   help_text="Observações a serem compartilhadas com os estudantes do projeto")

    @classmethod
    def create(cls, projeto):
        """Cria um objeto (entrada) em Observacao Velha."""
        observacao = cls(projeto=projeto)
        return observacao

    def __str__(self):
        return "Observação velha tipo : " + str(self.exame)

    class Meta:
        verbose_name = "Observação Velha"
        verbose_name_plural = "Observações Velhas"
        

class Certificado(models.Model):
    """Certificados."""

    usuario = models.ForeignKey("users.PFEUser", null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="pessoa que recebeu o certificado")
    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="projeto relacionado ao certificado")
    alocacao = models.ForeignKey("users.Alocacao", null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="alocação relacionada ao certificado")
    data = models.DateField(default=datetime.date.today, blank=True,
                            help_text="data do certificado")

    tipo_certificado = models.ForeignKey("administracao.TipoCertificado", null=True, blank=True, on_delete=models.SET_NULL,
                                         help_text="Tipo de certificado")

    observacao = models.TextField(max_length=256, null=True, blank=True,
                                  help_text="qualquer observação relevante")

    documento = models.FileField("Documento", upload_to=get_upload_path, null=True, blank=True,
                                 help_text="Documento Digital")

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

    # Usado para envio de email dos certificados
    def get_banca(self):
        """Retorna banca relacionada ao certificado."""
        if self.projeto:
            if self.tipo_certificado.titulo == "Membro de Banca Intermediária": 
                return Banca.objects.filter(projeto=self.projeto, composicao__exame__sigla="BI").last()  # (1, "Intermediária"),
            if self.tipo_certificado.titulo == "Membro de Banca Final":
                return Banca.objects.filter(projeto=self.projeto, composicao__exame__sigla="BF").last()  # (0, "Final"),
            if self.tipo_certificado.titulo == "Membro da Banca Falconi":
                return Banca.objects.filter(projeto=self.projeto, composicao__exame__sigla="F").last()  # (2, "Certificação Falconi"),
            if self.tipo_certificado.titulo == "Membro de Banca de Probation":
                return Banca.objects.filter(projeto=self.projeto, composicao__exame__sigla="P").last()  # (3, "Probation"),
        return None
    
    def get_projeto(self):
        """Retorna o projeto do certificado."""
        if self.alocacao:
            return self.alocacao.projeto
        if self.projeto:
            return self.projeto
        return None

    class Meta:
        verbose_name = "Certificado"
        verbose_name_plural = "Certificados"

class Area(models.Model):
    """Projeto em que o aluno está alocado."""

    titulo = models.CharField("Título", max_length=48, null=True, blank=True,
                              help_text="Titulo da área de interesse")

    descricao = models.CharField("Descrição", max_length=512, null=True, blank=True,
                                 help_text="Descrição da área de interesse")

    ativa = models.BooleanField("Ativa", default=True,
                                help_text="Se a área de interesse está sendo usada atualmente")

    def __str__(self):
        return self.titulo

    @classmethod
    def create(cls, titulo):
        """Cria uma Área nova."""
        area = cls(titulo=titulo)
        return area

    class Meta:
        verbose_name = "Área"
        verbose_name_plural = "Áreas"

class AreaDeInteresse(models.Model):
    """Usado para fazer o mapeando da proposta ou da pessoa para área de interesse."""

    # As áreas são de interesse ou do usuário ou da proposta (que passa para o projeto)
    usuario = models.ForeignKey("users.PFEUser", null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="área dde interessada da pessoa")
    proposta = models.ForeignKey(Proposta, null=True, blank=True, on_delete=models.SET_NULL,
                                 help_text="área de interesse da proposta")

    # Campo para especificar uma outra área que não a da lista de áreas controladas
    outras = models.CharField("Outras", max_length=128, null=True, blank=True,
                              help_text="Outras áreas de interesse")

    area = models.ForeignKey(Area, null=True, blank=True, on_delete=models.SET_NULL,
                             help_text="área de interesse")

    class Meta:
        verbose_name = "Área de Interesse"
        verbose_name_plural = "Áreas de Interesse"

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
