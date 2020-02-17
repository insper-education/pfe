#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

#import os
import datetime
from django.db import models
from django.urls import reverse  # To generate URLS by reversing URL patterns
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib import admin
#from datetime import datetime
#from django.conf import settings
#import users.models

def get_upload_path(instance, filename):
    """Caminhos para armazenar os arquivos."""
    caminho = ""
    if isinstance(instance, Documento):
        if instance.organizacao:
            caminho += instance.organizacao.sigla + "/"
        if instance.usuario:
            caminho += instance.usuario.username + "/"
        if caminho == "":
            caminho = "documentos/"
    elif isinstance(instance, Projeto):
        caminho += instance.empresa.sigla + "/"
        caminho += "projeto" + str(instance.pk) + "/"
    elif isinstance(instance, Empresa):
        caminho += instance.sigla + "/logotipo/"
    file_path = caminho
    # ISSO DO FILE_PATH NAO FAZ SENTIDO, REMOVER
    return "{0}/{1}".format(file_path, filename)

class Empresa(models.Model):
    """Dados das empresas que propõe projetos para o PFE."""
    #RENOMEAR PARA ORGANIZACAO
    login = models.CharField(primary_key=True, max_length=20)
    #login = models.CharField(max_length=20)     # em algum momento concertar isso
    nome_empresa = models.CharField("Nome Fantasia", max_length=80,
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
    ramo_atividade = models.CharField("Ramo de Atividade", max_length=120, null=True, blank=True,
                                      help_text='Ramo de atividade da organização parceira')

    class Meta:
        ordering = ['sigla']
        permissions = (("altera_empresa", "Empresa altera valores"),
                       ("altera_professor", "Professor altera valores"), )
    def __str__(self):
        return self.nome_empresa
    #def documento(self):
    #    return os.path.split(self.contrato.name)[1]

class Projeto(models.Model):
    """Dados dos projetos para o PFE."""
    titulo = models.CharField("Título", max_length=127,
                              help_text='Título Provisório do projeto')
    titulo_final = models.CharField("Título Final", max_length=127, null=True,
                                    blank=True,
                                    help_text='Título Final do projeto')
    descricao = models.TextField("Descrição", max_length=3000,
                                 help_text='Descricao do projeto')
    expectativas = models.TextField("Expectativas", max_length=3000,
                                    help_text='Expectativas em relação ao projeto')
    areas = models.TextField("Áreas", max_length=1000,
                             help_text='Áreas da engenharia envolvidas no projeto')
    recursos = models.TextField("Recursos", max_length=1000,
                                help_text='Recursos a serem disponibilizados aos Alunos')
    anexo = models.FileField("Anexo", upload_to=get_upload_path, null=True, blank=True,
                             help_text='Documento PDF')
    imagem = models.ImageField(null=True, blank=True,
                               help_text='Imagem que representa projeto (se houver)')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE,
                                help_text='Organização parceira que propôs projeto')
    departamento = models.TextField("Departamento", max_length=1000, null=True, blank=True,
                                    help_text='Descrição do departamento que propôs o projeto')
    avancado = models.BooleanField("Avançado", default=False,
                                   help_text='Se for um projeto de PFE Avançado')
    ano = models.PositiveIntegerField("Ano",
                                      validators=[MinValueValidator(2018), MaxValueValidator(3018)],
                                      help_text='Ano que o projeto comeca')
    semestre = models.PositiveIntegerField("Semestre",
                                           validators=[MinValueValidator(1), MaxValueValidator(2)],
                                           help_text='Semestre que o projeto comeca')
    disponivel = models.BooleanField("Disponível", default=False,
                                     help_text='Se projeto está atualmente disponível para alunos')
    orientador = models.ForeignKey('users.Professor', null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='professor_orientador',
                                   help_text='professor orientador do projeto')
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

    areas_de_interesse = models.ForeignKey('users.Areas', on_delete=models.CASCADE,
                                           null=True, blank=True,
                                           help_text='Áreas de interesse esperas dos alunos')

    class Meta:
        ordering = ['empresa', 'ano', 'semestre']
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
        return self.empresa.sigla+" ("+str(self.ano)+"."+str(self.semestre)+") "+self.get_titulo()

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
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE,
                                   help_text='disciplina cursada pelo aluno')
    aluno = models.ForeignKey('users.Aluno', on_delete=models.CASCADE,
                              help_text='aluno que cursou a disciplina')
    nota = models.PositiveSmallIntegerField(validators=[MaxValueValidator(10)],
                                            help_text='nota obtida pelo aluno na disciplina')
    class Meta:
        ordering = ['nota']
    def __str__(self):
        return self.aluno.user.username+" >>> "+self.disciplina.nome

class Recomendada(models.Model):
    """Disciplinas recomendadas que um aluno ja tenha cursado para fazer o projeto."""
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE,
                                   help_text='disciplina recomendada para o projeto')
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE,
                                help_text='projeto que recomenda a disciplina')
    def __str__(self):
        return self.projeto.titulo+" >>> "+self.disciplina.nome

class Evento(models.Model):
    """Eventos para a agenda do PFE."""
    name = models.CharField(max_length=50)
    location = models.CharField(blank=True, max_length=50)
    startDate = models.DateField(default=datetime.date.today, blank=True,
                                 help_text='Inicio do Evento')
    endDate = models.DateField(default=datetime.date.today, blank=True,
                               help_text='Fim do Evento')
    color = models.CharField(max_length=20)
    def __str__(self):
        return self.name
    class Meta:
        ordering = ['startDate']

class Banca(models.Model):
    """Bancas do PFE."""
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE,
                                help_text='projeto')
    location = models.CharField(blank=True, max_length=50,
                                help_text='sala em que vai ocorrer banca')
    startDate = models.DateTimeField(default=datetime.datetime.now, blank=True,
                                     help_text='Inicio da Banca')
    endDate = models.DateTimeField(default=datetime.datetime.now, blank=True,
                                   help_text='Fim da Banca')
    color = models.CharField(max_length=20, blank=True,
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
    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.CASCADE,
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
    def __str__(self):
        return str(self.startDate)

class Anotacao(models.Model):
    """Anotacoes de comunicações com as organizações pareceiras."""
    data = models.DateField(default=datetime.date.today, blank=True,
                            help_text='Data da comunicação')
    organizacao = models.ForeignKey(Empresa, null=True, blank=True, on_delete=models.CASCADE,
                                    help_text='Organização parceira')
    autor = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL,
                              related_name='professor_orientador', help_text='quem fez a anotação')
    texto = models.TextField(max_length=2000, help_text='Anotação')
    def __str__(self):
        return str(self.data)
    @classmethod
    def create(cls, organizacao):
        """Cria um objeto (entrada) em Anotação."""
        anotacao = cls(organizacao=organizacao)
        return anotacao

class Documento(models.Model):
    """Documentos, em geral PDFs, e seus relacionamentos com o PFE."""
    organizacao = models.ForeignKey(Empresa, null=True, blank=True, on_delete=models.SET_NULL,
                                    help_text='Empresa que propôs projeto')
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
        (16, 'outros'),
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
    delta = models.SmallIntegerField(default=0,
                                     help_text='dias passados do início do semestre')
    mensagem = models.TextField(max_length=4096, null=True, blank=True,
                                help_text='mensagem a ser enviar no texto')
    comite_pfe = \
        models.BooleanField(default=False, help_text='Lista todos os membros do comitê do PFE')
    todos_alunos = \
        models.BooleanField(default=False, help_text='Lista todos os alunos do semestre')
    aluno_p_projeto = \
        models.BooleanField(default=False, help_text='Lista alunos por projetos do semestre')
    todos_orientadores = \
        models.BooleanField(default=False, help_text='Lista todos os alunos do semestre')
    orientadores_p_projeto = \
        models.BooleanField(default=False, help_text='Lista orientadores por projetos do semestre')
    contatos_nas_organizacoes = \
        models.BooleanField(default=False, help_text='Lista contatos nas organizações parceiras')

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
    #organizacao_parceira=models.ForeignKey(Empresa,null=True,blank=True,on_delete=models.CASCADE,
    #                                help_text='Organização parceira')
    #autor = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL,
    #                          related_name='professor_orientador', help_text='quem fez a anotação')
    nome = models.CharField(max_length=120, null=True, blank=True,
                            help_text='Nome de quem está dando o Feedback')
    email = models.EmailField(max_length=80, null=True, blank=True,
                              help_text='e-mail de quem está dando o Feedback')
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
    usuario = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL,
                                help_text='usuário que se conecta ao projeto')
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE,
                                help_text='projeto que possui vínculo da conexão')
    observacao = models.TextField(max_length=256, null=True, blank=True,
                                  help_text='qualquer observação relevante')
    gestor_responsavel = models.BooleanField(default=False)
    mentor_tecnico = models.BooleanField(default=False)
    recursos_humanos = models.BooleanField(default=False)

    def __str__(self):
        return self.usuario.get_full_name()+" >>> "+\
               self.projeto.empresa.sigla+" - "+self.projeto.get_titulo()+\
               " ("+str(self.projeto.ano)+"."+str(self.projeto.semestre)+")"

class Coorientador(models.Model):
    """Controla lista de coorientadores por projeto."""
    usuario = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL,
                                help_text='coorientador de um projeto')
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE,
                                help_text='projeto que foi coorientado')
    observacao = models.TextField(max_length=256, null=True, blank=True,
                                  help_text='qualquer observação relevante')

    def __str__(self):
        return self.usuario.get_full_name()+" >>> "+\
               self.projeto.get_titulo()+\
               " ("+str(self.projeto.ano)+"."+str(self.projeto.semestre)+")"
