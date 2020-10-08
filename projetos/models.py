#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

import datetime
import string
import random
from django.db import models
from django.urls import reverse  # To generate URLS by reversing URL patterns
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib import admin
from django.template.defaultfilters import slugify

def get_upload_path(instance, filename):
    """Caminhos para armazenar os arquivos."""
    caminho = ""
    if isinstance(instance, Documento):
        if instance.organizacao:
            caminho += slugify(instance.organizacao.sigla) + "/"
        if instance.usuario:
            caminho += slugify(instance.usuario.username) + "/"
        if caminho == "":
            caminho = "documentos/"
    elif isinstance(instance, Projeto):
        caminho += slugify(instance.organizacao.sigla) + "/"
        caminho += "projeto" + str(instance.pk) + "/"
    elif isinstance(instance, Organizacao):
        caminho += slugify(instance.sigla) + "/logotipo/"
    elif isinstance(instance, Certificado):
        if instance.projeto.organizacao:
            caminho += slugify(instance.projeto.organizacao.sigla) + "/"
            caminho += "projeto" + str(instance.projeto.pk) + "/"
        if instance.usuario:
            caminho += slugify(instance.usuario.username) + "/"
    return "{0}/{1}".format(caminho, filename)

class Organizacao(models.Model):
    """Dados das organizações que propõe projetos para o PFE."""

    nome = models.CharField("Nome Fantasia", max_length=80,
                            help_text='Nome fantasia da organização parceira')
    sigla = models.CharField("Sigla", max_length=20,
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

    class Meta:
        ordering = ['sigla']
        verbose_name = 'Organização'
        verbose_name_plural = 'Organizações'

    @classmethod
    def create(cls):
        """Cria um objeto (entrada) em Organizacao."""
        organizacao = cls()
        return organizacao

    def __str__(self):
        return self.nome
    #def documento(self):
    #    return os.path.split(self.contrato.name)[1]

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

    avancado = models.BooleanField("Avançado", default=False,
                                   help_text='Se for um projeto de PFE Avançado')

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

    class Meta:
        ordering = ['organizacao', 'ano', 'semestre']
        permissions = (("altera_empresa", "Empresa altera valores"),
                       ("altera_professor", "Professor altera valores"), )

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
        else:
            return self.titulo

    def __str__(self):
        return self.organizacao.sigla+" ("+str(self.ano)+"."+str(self.semestre)+") "+\
            self.get_titulo()

    @classmethod
    def create(cls, proposta):
        """Cria um Projeto (entrada) na Banca."""
        projeto = cls(proposta=proposta)
        return projeto

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

    endereco = models.TextField("Endereço", max_length=400,
                                help_text='Endereço da Instituiçã')

    contatos_tecnicos = models.TextField("Contatos Técnicos", max_length=400,
                                         help_text='Contatos Técnicos')

    contatos_administrativos = models.TextField("Contatos Administrativos", max_length=400,
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

    areas_de_interesse = models.ForeignKey('users.Areas', on_delete=models.SET_NULL,
                                           null=True, blank=True,
                                           help_text='Áreas de interesse esperadas dos alunos')

    recursos = models.TextField("Recursos", max_length=1000, null=True, blank=True,
                                help_text='Recursos a serem disponibilizados aos Alunos')

    observacoes = models.TextField("Outras Observações", max_length=3000, null=True, blank=True,
                                   help_text='Outras Observações')

    anexo = models.FileField("Anexo", upload_to=get_upload_path, null=True, blank=True,
                             help_text='Documento PDF')

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

    autorizado = models.ForeignKey('users.PFEUser', null=True, blank=True,
                                   on_delete=models.SET_NULL,
                                   help_text='Quem autorizou a ser publicado para os alunos')

    fechada = models.BooleanField(default=False, help_text='Se a proposta virou um projeto')

    perfil_aluno1_computacao = \
        models.BooleanField(default=False, help_text='Perfil desejado de computação para aluno 1')
    perfil_aluno1_mecatronica = \
        models.BooleanField(default=False, help_text='Perfil desejado de mecatrônica para aluno 1')
    perfil_aluno1_mecanica = \
        models.BooleanField(default=False, help_text='Perfil desejado de mecânica para aluno 1')
    perfil_aluno2_computacao = \
        models.BooleanField(default=False, help_text='Perfil desejado de computação para aluno 2')
    perfil_aluno2_mecatronica = \
        models.BooleanField(default=False, help_text='Perfil desejado de mecatrônica para aluno 2')
    perfil_aluno2_mecanica = \
        models.BooleanField(default=False, help_text='Perfil desejado de mecânica para aluno 2')
    perfil_aluno3_computacao = \
        models.BooleanField(default=False, help_text='Perfil desejado de computação para aluno 3')
    perfil_aluno3_mecatronica = \
        models.BooleanField(default=False, help_text='Perfil desejado de mecatrônica para aluno 3')
    perfil_aluno3_mecanica = \
        models.BooleanField(default=False, help_text='Perfil desejado de mecânica para aluno 3')
    perfil_aluno4_computacao = \
        models.BooleanField(default=False, help_text='Perfil desejado de computação para aluno 4')
    perfil_aluno4_mecatronica = \
        models.BooleanField(default=False, help_text='Perfil desejado de mecatrônica para aluno 4')
    perfil_aluno4_mecanica = \
        models.BooleanField(default=False, help_text='Perfil desejado de mecânica para aluno 4')

    data = models.DateTimeField(default=datetime.datetime.now,
                                help_text='data e hora da criação da proposta de projeto')

    class Meta:
        ordering = ['organizacao', 'ano', 'semestre']

    @classmethod
    def create(cls):
        """Cria um objeto (entrada) em Propostas."""
        proposta = cls()
        return proposta

    def __str__(self):
        if self.organizacao:
            return self.organizacao.sigla+" ("+str(self.ano)+"."+str(self.semestre)+") "+self.titulo
        elif self.nome_organizacao:
            return self.nome_organizacao+" ("+str(self.ano)+"."+str(self.semestre)+") "+self.titulo
        else:
            return "ORG. NÃO DEFINIDA"+" ("+str(self.ano)+"."+str(self.semestre)+") "+self.titulo

    # pylint: disable=arguments-differ
    def save(self, *args, **kwargs):
        if not self.id:
            senha = ''.join(random.SystemRandom().\
                                   choice(string.ascii_uppercase + string.digits) for _ in range(6))
            self.slug = slugify(str(self.ano)+"-"+str(self.semestre)+"-"+self.titulo[:50]+"-"+senha)

        super(Proposta, self).save(*args, **kwargs)

    def get_absolute_url(self):
        """Caminha para editar uma proposta."""
        return reverse('proposta_editar', kwargs={'slug': self.slug})

class Configuracao(models.Model):
    """Armazena os dados básicos de funcionamento do sistema."""
    ano = models.PositiveIntegerField("Ano",
                                      validators=[MinValueValidator(2018), MaxValueValidator(3018)],
                                      help_text='Ano que o projeto comeca')
    semestre = models.PositiveIntegerField("Semestre",
                                           validators=[MinValueValidator(1), MaxValueValidator(2)],
                                           help_text='Semestre que o projeto comeca')
    manutencao = models.BooleanField(default=False,
                                     help_text='Mostra mensagem de site em manutencao na entrada')
    prazo = models.DateTimeField("Prazo", default=datetime.datetime.now, blank=True,
                                 help_text='Prazo para os alunos se inscreverem nos projetos')
    t0 = models.DateField(default=datetime.date.today, blank=True,
                          help_text='Inicio do Semestre Letivo')
    recipient_reembolso = models.CharField(max_length=127, blank=True,
                                           help_text='Separar lista por ponto e virgula')
    liberados_projetos = models.BooleanField(default=False,
                                             help_text='Para que alunos vejam projetos alocados')
    liberadas_propostas = models.BooleanField(default=False,
                                              help_text='Para alunos verem propostas disponiveis')

    class Meta:
        verbose_name = 'Configuração'
        verbose_name_plural = 'Configurações'

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
        ordering = ['nota']
    def __str__(self):
        return self.aluno.user.username+" >>> "+self.disciplina.nome

class Recomendada(models.Model):
    """Disciplinas recomendadas que um aluno ja tenha cursado para fazer o projeto."""
    disciplina = models.ForeignKey(Disciplina, null=True, blank=True, on_delete=models.SET_NULL,
                                   help_text='disciplina recomendada para o projeto')
    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text='projeto que recomenda a disciplina')
    proposta = models.ForeignKey(Proposta, null=True, blank=True, on_delete=models.SET_NULL,
                                 help_text='proposta que recomenda a disciplina')
    def __str__(self):
        return self.projeto.titulo+" >>> "+self.disciplina.nome

class Evento(models.Model):
    """Eventos para a agenda do PFE."""
    #name = models.CharField(max_length=50, blank=True)
    location = models.CharField(blank=True, max_length=50,
                                help_text='Onde Ocorrerá o Evento')
    startDate = models.DateField(default=datetime.date.today, blank=True,
                                 help_text='Inicio do Evento')
    endDate = models.DateField(default=datetime.date.today, blank=True,
                               help_text='Fim do Evento')
    #color = models.CharField(max_length=20, blank=True)

    TIPO_EVENTO = (
        (0, 'Feriado', 'lightgrey'),
        (1, 'Aula cancelada', 'lightgrey'),

        (10, 'Início das aulas', 'red'),
        (11, 'Evento de abertura do PFE', 'orange'),
        (12, 'Aula PFE', 'lightgreen'),
        (13, 'Evento de encerramento do PFE', 'brown'),
        (14, 'Banca intermediária', 'violet'),
        (15, 'Bancas finais', 'yellow'),
        (16, 'Apresentação formal final na organização', 'beige'),
        (17, 'Apresentação opcional intermediária na organização', 'oldlace'),

        (20, 'Relato Quinzenal (Individual)', 'aquamarine'),
        (21, 'Entrega de Relatório Preliminar (Grupo)', 'lightblue'), # esse era o antigo relatório de planejamento
        (22, 'Entrega do Relatório Intermediário (Grupo e Individual)', 'teal'),
        (23, 'Entrega do Relatório Final (Grupo e Individual)', 'aqua'),
        (24, 'Entrega do Relatório Revisado (Grupo)', 'deepskyblue'),
        (25, 'Entrega do Banner (Grupo)', 'chocolate'),
        (26, 'Entrega do Vídeo (Grupo)', 'lavender'),

        (30, 'Feedback dos Alunos sobre PFE', 'orange'),
        (31, 'Avaliação de Pares Intermediária', 'pink'),
        (32, 'Avaliação de Pares Final', 'pink'),

        (40, 'Laboratório', 'orange'),
        (41, 'Semana de provas', 'red'),

        (50, 'Apresentação para Certificação Falconi', 'darkorange'),


        (101, 'Apólice Seguro Acidentes Pessoais', 'aquamarine'),

        (111, 'Bate-papo com estudante que farão PFE no próximo semestre', 'lightcyan'),
        (112, 'Alunos demonstrarem interesse em adiar PFE para 9º semestre', 'limegreen'),
        (113, 'Apresentação dos projetos disponíveis para estudantes', 'darkslategray'),

        (120, 'Limite para submissão de propostas de projetos pelas organizações', 'lime'),
        (121, 'Pré seleção de propostas de projetos', 'chartreuse'),

        (123, 'Indicação de interesse nos projetos do próximo semestre pelos estudante', 'pink'),
        (124, 'Notificação para estudantes dos grupos formados', 'paleturquoise'),
        (125, 'Notificação para organizações dos projetos fechados', 'moccasin'),
        (126, 'Professores tiram dúvidas sobre projetos para alunos', 'lightsalmon'),


        (130, 'Validação dos projetos pelo comitê', 'peru'),

        (140, 'Reunião de orientações aos orientadores', 'maroon'),

    )

    tipo_de_evento = models.PositiveSmallIntegerField(choices=[subl[:2] for subl in TIPO_EVENTO],
                                                      null=True, blank=True,
                                                      help_text='Define o tipo do evento a ocorrer')

    def get_title(self):
        """Retorna em string o nome do evento."""
        for entry in Evento.TIPO_EVENTO:
            if self.tipo_de_evento == entry[0]:
                return entry[1]
        return None

    def get_color(self):
        """Retorna uma cor característica do evento para desenhar no calendário."""
        for entry in Evento.TIPO_EVENTO:
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

    def __str__(self):
        return self.get_title()+" ("+self.startDate.strftime("%d/%m/%Y")+")"
    class Meta:
        ordering = ['startDate']

class Banca(models.Model):
    """Bancas do PFE."""
    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text='projeto')
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
        (0, 'final'),
        (1, 'intermediaria'),
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

    class Meta:
        ordering = ['startDate']

class Encontro(models.Model):
    """Encontros (para dinâmicas de grupos)."""
    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text='projeto')
    location = models.CharField(blank=True, max_length=50,
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
        (0, 'Contactada para enviar proposta'),
        (1, 'Enviou proposta de projeto'),
        (2, 'Interessada em enviar proposta'),
        (3, 'Recusou enviar proposta de projeto'),
        (4, 'Confirmamos um grupo de alunos para o projeto'),
        (5, 'Notificamos que não conseguimos montar projeto'),
        (254, 'outros'),
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
                                    help_text='Organização referente o documento')
    usuario = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL,
                                help_text='Usuário do documento')
    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text='Documento do Projeto')
    documento = models.FileField(upload_to=get_upload_path,
                                 help_text='Documento PDF')
    anotacao = models.CharField(null=True, blank=True, max_length=50,
                                help_text='qualquer anotação sobre o documento em questão')
    data = models.DateField(null=True, blank=True,
                            help_text='Data do documento')
    TIPO_DE_DOCUMENTO = ( # não mudar a ordem dos números
        (0, 'contrato com empresa'),
        (1, 'contrato entre empresa e aluno'),
        (2, 'contrado de confidencialidade'),
        (3, 'relatório final'),
        (4, 'autorização de publicação empresa'),
        (5, 'autorização de publicação aluno'),
        (6, 'regulamento PFE'),
        (7, 'plano de aprendizado'),
        (8, 'manual do aluno'),
        (9, 'manual do orientador'),
        (10, 'manual da organização parceira'),
        (11, 'manual do carreiras'),
        (12, 'manual de relatórios'),
        (13, 'manual de planejamentos'),
        (14, 'termo de parceria'),
        (15, 'seguros'),
        (16, 'outros_antigo'),
        (17, 'template de relatórios'),
        (255, 'outros'),
    )
    tipo_de_documento = models.PositiveSmallIntegerField(choices=TIPO_DE_DOCUMENTO, default=0)
    def __str__(self):
        return str(self.TIPO_DE_DOCUMENTO[self.tipo_de_documento][1])

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
                              help_text='Título do Aviso')

    tipo_de_evento = models.\
        PositiveSmallIntegerField(choices=[subl[:2] for subl in Evento.TIPO_EVENTO],
                                  null=True, blank=True,
                                  help_text='Define o tipo do evento de referência')

    delta = models.SmallIntegerField(default=0,
                                     help_text='dias passados do evento definido')
    mensagem = models.TextField(max_length=4096, null=True, blank=True,
                                help_text='mensagem a ser enviar no texto')
    realizado = models.BooleanField(default=False, help_text='Se já realizado no período')
    coordenacao = \
        models.BooleanField(default=False, help_text='Para organização do PFE')
    comite_pfe = \
        models.BooleanField(default=False, help_text='Para os membros do comitê do PFE')
    todos_alunos = \
        models.BooleanField(default=False, help_text='Para todos os alunos do semestre')
    todos_orientadores = \
        models.BooleanField(default=False, help_text='Para todos os orientadores do semestre')
    contatos_nas_organizacoes = \
        models.BooleanField(default=False, help_text='Para contatos nas organizações parceiras')

    def get_data(self):
        """Retorna a data do aviso do semestre."""
        configuracao = Configuracao.objects.all().first()
        delta_days = datetime.timedelta(days=self.delta)
        if self.tipo_de_evento:
            eventos = Evento.objects.filter(tipo_de_evento=self.tipo_de_evento).\
                                     filter(startDate__year=configuracao.ano)
            if configuracao.semestre == 1:
                evento = eventos.filter(startDate__month__lt=7).last()
            else:
                evento = eventos.filter(startDate__month__gt=6).last()

            if evento:
                return evento.startDate + delta_days

        return configuracao.t0 + delta_days

    def get_evento(self):
        """Retorna em string o nome do evento."""
        for entry in Evento.TIPO_EVENTO:
            if self.tipo_de_evento == entry[0]:
                return entry[1]
        return "Sem evento"

    def __str__(self):
        return str(self.titulo)

class Entidade(models.Model):
    """Todas as entidades estudantis do Insper"""
    nome = models.CharField(max_length=100,
                            help_text='nome da entidade estudantil')
    def __str__(self):
        return self.nome

class Feedback(models.Model):
    """Feedback das organizacoes parceiras."""
    data = models.DateField(default=datetime.date.today, blank=True,
                            help_text='Data do Feedback')
    #organizacao_parceira=models.ForeignKey(Empresa,null=True,blank=True,on_delete=models.SET_NULL,
    #                                help_text='Organização parceira')
    #autor = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL,
    #                          related_name='professor_orientador', help_text='quem fez a anotação')
    nome = models.CharField(max_length=120, null=True, blank=True,
                            help_text='Nome de quem está dando o Feedback')
    email = models.EmailField(max_length=80, null=True, blank=True,
                              help_text='e-mail de quem está dando o Feedback')
    #isso esta bem baguncado
    empresa = models.CharField(max_length=120, null=True, blank=True,
                               help_text='Empresa de quem está dando o Feedback')
    tecnico = models.TextField(max_length=1000, help_text='Feedback Técnico')
    comunicacao = models.TextField(max_length=1000, help_text='Feedback Comunicação')
    organizacao = models.TextField(max_length=1000, help_text='Feedback Organização')
    outros = models.TextField(max_length=1000, help_text='Feedback Outros')

    def __str__(self):
        return str(self.data)

    @classmethod
    def create(cls):
        """Cria um objeto (entrada) em Feedback."""
        feedback = cls()
        return feedback

class Conexao(models.Model):
    """Controla como um usuário se conecta a um projeto."""

    parceiro = models.ForeignKey('users.Parceiro', null=True, blank=True,
                                 on_delete=models.SET_NULL,
                                 help_text='parceiro que se conecta ao projeto')

    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text='projeto que possui vínculo da conexão')
    observacao = models.TextField(max_length=256, null=True, blank=True,
                                  help_text='qualquer observação relevante')
    gestor_responsavel = models.BooleanField("Gestor Responsável", default=False)
    mentor_tecnico = models.BooleanField("Mentor Técnico", default=False)
    recursos_humanos = models.BooleanField("Recursos Humanos", default=False)
    colaboracao = models.BooleanField("Colaboração", default=False)

    def __str__(self):
        return self.parceiro.user.get_full_name()+" >>> "+\
               self.projeto.organizacao.sigla+" - "+self.projeto.get_titulo()+\
               " ("+str(self.projeto.ano)+"."+str(self.projeto.semestre)+")"

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
        return self.usuario.get_full_name()+" >>> "+\
               self.projeto.get_titulo()+\
               " ("+str(self.projeto.ano)+"."+str(self.projeto.semestre)+")"

    class Meta:
        verbose_name = 'Coorientador'
        verbose_name_plural = 'Coorientadores'

class ObjetivosDeAprendizagem(models.Model):
    """Objetidos de Aprendizagem do curso."""

    titulo = models.TextField(max_length=128, null=True, blank=True,
                              help_text='Título do objetivo de aprendizagem')

    objetivo = models.TextField(max_length=256, null=True, blank=True,
                                help_text='Descrição do objetivo de aprendizagem')

    rubrica_I = models.TextField(max_length=1024, null=True, blank=True,
                                 help_text='Rubrica do conceito I')
    rubrica_D = models.TextField(max_length=1024, null=True, blank=True,
                                 help_text='Rubrica do conceito D')
    rubrica_C = models.TextField(max_length=1024, null=True, blank=True,
                                 help_text='Rubrica do conceito C')
    rubrica_B = models.TextField(max_length=1024, null=True, blank=True,
                                 help_text='Rubrica do conceito B')
    rubrica_A = models.TextField(max_length=1024, null=True, blank=True,
                                 help_text='Rubrica do conceito A')

    avaliacao_aluno = models.BooleanField("Avaliação do Aluno", default=False,
                                          help_text='Avaliação do Aluno (AA)')

    avaliacao_banca = models.BooleanField("Avaliação da Banca", default=False,
                                          help_text='Avaliação da Banca (AB)')

    avaliacao_grupo = models.BooleanField("Avaliação do Grupo", default=False,
                                          help_text='Avaliação do Grupo (AG)')

    def __str__(self):
        return str(self.titulo)

    class Meta:
        verbose_name = 'ObjetivosDeAprendizagem'
        verbose_name_plural = 'ObjetivosDeAprendizagem'

# Usado em Avaliacao e Observacao
TIPO_DE_AVALIACAO = ( # não mudar a ordem dos números
    ( 0, 'Não definido'),
    ( 1, 'Banca Intermediária'),
    ( 2, 'Banca Final'),
    (10, 'Relatório de Planejamento'),
    (11, 'Relatório Intermediário de Grupo'),
    (12, 'Relatório Final de Grupo'),
    (21, 'Relatório Intermediário Individual'),
    (22, 'Relatório Final Individual'),
    (50, 'Planejamento Primeira Fase'),
    (51, 'Avaliação Parcial Individual'),
    (52, 'Avaliação Final Individual'),
)

class Avaliacao2(models.Model):
    """Avaliações realizadas durante o projeto."""

    tipo_de_avaliacao = models.PositiveSmallIntegerField(choices=TIPO_DE_AVALIACAO, default=0)

    momento = models.DateTimeField(default=datetime.datetime.now, blank=True,
                                   help_text='Data e hora da comunicação') # hora ordena para dia
  
    peso = models.FloatField("Peso",
                                       validators=[MinValueValidator(0), MaxValueValidator(100)],
                                       help_text='Pesa da avaliação na média (bancas compartilham peso)',
                                       default=10) # 10% para as bancas

    # A nota será convertida para rubricas se necessário
    nota = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    # Somente útil para Bancas
    avaliador = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL,
                                  help_text='avaliador do projeto')

    # Para Bancas e Entregas em Grupo
    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text='projeto que foi avaliado')

    # Para Alocações dos estudantes (caso um aluno reprove ele teria duas alocações)
    alocacao = models.ForeignKey('users.Alocacao', null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name='projeto_alocado_avaliacao',
                                 help_text='relacao de alocação entre projeto e estudante')

    objetivo = models.ForeignKey(ObjetivosDeAprendizagem, related_name='objetivo_avaliacao',
                                 on_delete=models.SET_NULL, null=True, blank=True,
                                 help_text='Objetivo de Aprendizagem')

    def __str__(self):
        for i,j in TIPO_DE_AVALIACAO:
            if self.tipo_de_avaliacao==i:
                return j
        return "Avaliação Não Definida"

    @classmethod
    def create(cls, projeto):
        """Cria um objeto (entrada) em Avaliação."""
        avaliacao = cls(projeto=projeto)
        return avaliacao

    class Meta:
        verbose_name = 'Avaliação2'
        verbose_name_plural = 'Avaliações2'
        ordering = ['momento',]

class Observacao(models.Model):
    """Observações realizadas durante avaliações."""

    tipo_de_avaliacao = models.PositiveSmallIntegerField(choices=TIPO_DE_AVALIACAO, default=0)

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
                                 on_delete=models.SET_NULL, related_name='observacao_alocado',
                                 help_text='relacao de alocação entre projeto e estudante')

    # Se houver, usando pois no Blackboard alguns estão dessa forma
    objetivo = models.ForeignKey(ObjetivosDeAprendizagem, related_name='objetivo_observacao',
                                 on_delete=models.SET_NULL, null=True, blank=True,
                                 help_text='Objetivo de Aprendizagem')

    observacoes = models.TextField(max_length=512, null=True, blank=True,
                                help_text='qualquer observação relevante')

    @classmethod
    def create(cls, projeto):
        """Cria um objeto (entrada) em Observacao."""
        observacao = cls(projeto=projeto)
        return observacao

    def __str__(self):
        return "Avaliação tipo : " + str(self.tipo_de_avaliacao)

    class Meta:
        verbose_name = 'Observação'
        verbose_name_plural = 'Observações'
        #ordering = [,]


class Certificado(models.Model):
    """Certificados das Premiações do PFE."""
    usuario = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL,
                                help_text='pessoa premiada com certificado')
    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text='projeto relacionado ao certificado')
    data = models.DateField(default=datetime.date.today, blank=True,
                            help_text='data do certificado')

    TIPO_DE_CERTIFICADO = ( # não mudar a ordem dos números
        (0, 'Não definido'),
        (1, 'Estudante destaque'),
        (2, 'Equipe destaque'),
    )
    tipo_de_certificado = models.PositiveSmallIntegerField(choices=TIPO_DE_CERTIFICADO, default=0)

    observacao = models.TextField(max_length=256, null=True, blank=True,
                                  help_text='qualquer observação relevante')

    documento = models.FileField("Documento", upload_to=get_upload_path, null=True, blank=True,
                                 help_text='Documento Digital')

    def get_certificado(self):
        """Retorna em string o nome do certificado."""
        for entry in Certificado.TIPO_DE_CERTIFICADO:
            if self.tipo_de_certificado == entry[0]:
                return entry[1]
        return None

    def __str__(self):
        return self.usuario.get_full_name()+" >>> "+\
               self.projeto.get_titulo()+\
               " ("+str(self.projeto.ano)+"."+str(self.projeto.semestre)+")"

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
        """ Cria uma Área nova. """
        area = cls(titulo=titulo)
        return area

    class Meta:
        verbose_name = 'Área'
        verbose_name_plural = 'Áreas'

class AreaDeInteresse(models.Model):
    """ Usado para fazer o mapeando da proposta ou da pessoa para área de interesse. """

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
            else:
                return self.usuario.get_full_name()+" >>> "+str(self.area)
        elif self.proposta:
            if self.outras:
                return self.proposta.titulo+" >>> "+self.outras
            else:
                return self.proposta.titulo+" >>> "+str(self.area)
        else:
            if self.outras:
                return self.outras
            else:
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
