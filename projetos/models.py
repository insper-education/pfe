# Desenvolvido para o Projeto Final de Engenharia
# Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
# Data: 15 de Maio de 2019

from django.db import models
from django.urls import reverse  # To generate URLS by reversing URL patterns
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib import admin
from datetime import datetime

import datetime 
import os

from django.conf import settings

import users.models

# Caminhos para armazenar os arquivos
def get_upload_path(instance, filename):
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
    file_path = caminho
    # ISSO DO FILE_PATH NAO FAZ SENTIDO, REMOVER
    return "{0}/{1}".format(file_path, filename)

# RENOMEAR PARA ORGANIZACAO
class Empresa(models.Model):
    login = models.CharField(primary_key=True, max_length=20)
    #login = models.CharField(max_length=20)     # em algum momento concertar isso
    nome_empresa = models.CharField(max_length=80)
    sigla = models.CharField(max_length=20)
    endereco = models.TextField(max_length=200, help_text='Endereço da Empresa')
    website = models.URLField(max_length=250, null=True, blank=True)
    informacoes = models.TextField(max_length=1000, null=True, blank=True, help_text='Informações sobre a empresa')

    class Meta:
        ordering = ['sigla']
        permissions = (("altera_empresa", "Empresa altera valores"), ("altera_professor", "Professor altera valores"), )
    def __str__(self):
        return self.nome_empresa
    def documento(self):
        return os.path.split(self.contrato.name)[1]

class Projeto(models.Model):
    titulo = models.CharField(max_length=127, help_text='Título Provisório do projeto')
    titulo_final = models.CharField(max_length=127, null=True, blank=True, help_text='Título Final do projeto')
    descricao = models.TextField(max_length=2000, help_text='Descricao do projeto')
    expectativas = models.TextField(max_length=2000, help_text='Expectativas em relação ao projeto')
    areas = models.TextField(max_length=1000, help_text='Áreas da engenharia envolvidas no projeto')
    recursos = models.TextField(max_length=1000, help_text='Recursos a serem disponibilizados aos Alunos')
    anexo = models.FileField(upload_to=get_upload_path, null=True, blank=True, help_text='Documento PDF')
    imagem = models.ImageField(null=True, blank=True, help_text='Imagem que representa projeto (se houver)')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, help_text='Organização parceira que propôs projeto')
    departamento = models.TextField(max_length=1000, null=True, blank=True, help_text='Descrição do departamento que propôs o projeto')
    avancado = models.BooleanField(default=False, help_text='Se for um projeto de PFE Avançado')
    ano = models.PositiveIntegerField(validators=[MinValueValidator(2018),MaxValueValidator(3018)], help_text='Ano que o projeto comeca')
    semestre = models.PositiveIntegerField(validators=[MinValueValidator(1),MaxValueValidator(2)], help_text='Semestre que o projeto comeca')
    disponivel = models.BooleanField(default=False, help_text='Se o projeto está atualmente disponível para os alunos')
    orientador = models.ForeignKey('users.Professor', null=True, blank=True, on_delete=models.SET_NULL, related_name='professor_orientador', help_text='professor orientador do projeto')
    perfil_aluno1_computacao = models.BooleanField(default=False, help_text='Perfil desejado para o primeiro aluno se for de computação')
    perfil_aluno1_mecatronica = models.BooleanField(default=False, help_text='Perfil desejado para o primeiro aluno se for de mecatrônica')
    perfil_aluno1_mecanica = models.BooleanField(default=False, help_text='Perfil desejado para o primeiro aluno se for de mecânica')
    perfil_aluno2_computacao = models.BooleanField(default=False, help_text='Perfil desejado para o segundo aluno se for de computação')
    perfil_aluno2_mecatronica = models.BooleanField(default=False, help_text='Perfil desejado para o segundo aluno se for de mecatrônica')
    perfil_aluno2_mecanica = models.BooleanField(default=False, help_text='Perfil desejado para o segundo aluno se for de mecânica')
    perfil_aluno3_computacao = models.BooleanField(default=False, help_text='Perfil desejado para o terceiro aluno se for de computação')
    perfil_aluno3_mecatronica = models.BooleanField(default=False, help_text='Perfil desejado para o terceiro aluno se for de mecatrônica')
    perfil_aluno3_mecanica = models.BooleanField(default=False, help_text='Perfil desejado para o terceiro aluno se for de mecânica')
    perfil_aluno4_computacao = models.BooleanField(default=False, help_text='Perfil desejado para o quarto aluno se for de computação')
    perfil_aluno4_mecatronica = models.BooleanField(default=False, help_text='Perfil desejado para o quarto aluno se for de mecatrônica')
    perfil_aluno4_mecanica = models.BooleanField(default=False, help_text='Perfil desejado para o quarto aluno se for de mecânica')
    
    class Meta:
        ordering = ['titulo']
        permissions = (("altera_empresa", "Empresa altera valores"), ("altera_professor", "Professor altera valores"), )

    # Methods
    @property
    def procura_de_alunos(self):
        return 4  # REFAZER (OU ABANDONAR DE VEZ)

    def get_absolute_url(self):
        """Returns the url to access a particular instance of MyModelName."""
        return reverse('projeto-detail', args=[str(self.id)])

    def __str__(self):
        return self.titulo+" ("+str(self.ano)+"."+str(self.semestre)+")"

class Configuracao(models.Model):
    ano = models.PositiveIntegerField(validators=[MinValueValidator(2018),MaxValueValidator(3018)], help_text='Ano que o projeto comeca')
    semestre = models.PositiveIntegerField(validators=[MinValueValidator(1),MaxValueValidator(2)], help_text='Semestre que o projeto comeca')
    manutencao = models.BooleanField(default=False, help_text='Mostra mensagem de site em manutencao na entrada')
    prazo = models.DateTimeField(default=datetime.datetime.now, blank=True, help_text='Prazo para os alunos se inscreverem nos projetos')
    t0 = models.DateField(default=datetime.date.today, blank=True, help_text='Inicio do Semestre Letivo')
    recipient_reembolso = models.CharField(max_length=127, blank=True, help_text='Separar lista por ponto e virgula')

class ConfiguracaoAdmin(admin.ModelAdmin):
  def has_add_permission(self, request):
    # if there's already an entry, do not allow adding
    count = Configuracao.objects.all().count()
    if count == 0:
      return True
    return False

class Disciplina(models.Model):
    nome = models.CharField(max_length=100, help_text='nome')
    def __str__(self):
        return self.nome

class Cursada(models.Model):
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE, help_text='disciplina cursada pelo aluno')
    aluno = models.ForeignKey('users.Aluno', on_delete=models.CASCADE, help_text='aluno que cursou a disciplina')
    nota = models.PositiveSmallIntegerField()
    class Meta:
        ordering = ['nota']
    def __str__(self):
        return self.aluno.user.username+" >>> "+self.disciplina.nome

# Para listas as disciplinas recomendadas que um aluno ja tenha cursado para fazer o projeto
class Recomendada(models.Model):
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE, help_text='disciplina recomendada para o projeto')
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, help_text='projeto que recomenda a disciplina')
    def __str__(self):
        return self.projeto.titulo+" >>> "+self.disciplina.nome

# Eventos para a agenda do PFE
class Evento(models.Model):
    name = models.CharField(max_length=50)
    location = models.CharField(blank=True, max_length=50)
    startDate = models.DateField(default=datetime.date.today, blank=True, help_text='Inicio do Evento')
    endDate = models.DateField(default=datetime.date.today, blank=True, help_text='Fim do Evento')
    color = models.CharField(max_length=20)
    def __str__(self):
        return self.name

# Bancas do PFE
class Banca(models.Model):
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, help_text='projeto')
    location = models.CharField(blank=True, max_length=50, help_text='sala em que vai ocorrer banca')
    startDate = models.DateTimeField(default=datetime.datetime.now, blank=True, help_text='Inicio da Banca')
    endDate = models.DateTimeField(default=datetime.datetime.now, blank=True, help_text='Fim da Banca')
    color = models.CharField(max_length=20,blank=True)
    membro1 = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL, related_name='membro1', help_text='membro da banca')
    membro2 = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL, related_name='membro2', help_text='membro da banca')
    membro3 = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL, related_name='membro3', help_text='membro da banca')
    def __str__(self):
        return self.projeto.titulo

# Encontros (para dinâmicas de grupos)
class Encontro(models.Model):
    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.CASCADE, help_text='projeto')
    location = models.CharField(blank=True, max_length=50, help_text='sala em que vai ocorrer a dinâmica')
    startDate = models.DateTimeField(default=datetime.datetime.now, help_text='Inicio da Dinâmica')
    endDate = models.DateTimeField(default=datetime.datetime.now, help_text='Fim da Dinâmica')
    facilitador = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL, related_name='facilitador', help_text='facilitador da dinâmica')
    def __str__(self):
        return str(self.startDate)

# Anotacoes de comunicações com as organizações pareceiras
class Anotacao(models.Model):
    data = models.DateField(default=datetime.date.today, blank=True, help_text='Data da comunicação')
    organizacao = models.ForeignKey(Empresa, null=True, blank=True, on_delete=models.CASCADE, help_text='Organização parceira')
    autor = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL, related_name='professor_orientador', help_text='quem fez a anotação')
    texto = models.TextField(max_length=2000, help_text='Anotação')
    def __str__(self):
        return str(self.data)

class Documento(models.Model):
    organizacao = models.ForeignKey(Empresa, null=True, blank=True, on_delete=models.SET_NULL, help_text='Empresa que propôs projeto') # Algumas empresas podem ter contrato e não ter projeto
    usuario = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL, help_text='Usuário do documento')
    projeto = models.ForeignKey(Projeto, null=True, blank=True, on_delete=models.SET_NULL, help_text='Documento do Projeto')
    documento = models.FileField(upload_to=get_upload_path, help_text='Documento PDF')
    anotacao = models.CharField(null=True, blank=True, max_length=50, help_text='qualquer anotação sobre o documento em questão')
    data = models.DateField(null=True, blank=True, help_text='Data do documento')
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
      (14, 'outros'),
    )
    tipo_de_documento = models.PositiveSmallIntegerField(choices=TIPO_DE_DOCUMENTO, default=0)
    def __str__(self):
        return str(self.TIPO_DE_DOCUMENTO[self.tipo_de_documento][1])

# Lista dos Bancos Existentes no Brasil
class Banco(models.Model):
    nome = models.CharField(max_length=50, help_text='nome do banco')
    codigo = models.PositiveSmallIntegerField(help_text='código do banco')

    @classmethod
    def create(cls, nome, codigo):
        banco = cls(nome=nome,codigo=codigo)
        return banco

    def __str__(self):
        return str(self.nome)


class Reembolso(models.Model):
    usuario = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL, help_text='usuário pedindo reembolso')
    banco = models.ForeignKey(Banco, null=True, on_delete=models.SET_NULL, help_text='banco a se fazer o reembolso')
    agencia = models.CharField(max_length=6, null=True, blank=True, help_text='agência no banco')
    conta = models.CharField(max_length=16, null=True, blank=True, help_text='conta no banco')
    descricao = models.TextField(max_length=2000, help_text='desrição do pedido de reembolso')
    valor = models.DecimalField(max_digits=5, decimal_places=2, help_text='valor a ser reembolsado')
    data = models.DateTimeField(default=datetime.datetime.now, help_text='data e hora da criação do pedido de reembolso')
    nota = models.FileField(upload_to=get_upload_path, null=True, blank=True, help_text='Nota(s) Fiscal(is)')

    @classmethod
    def create(cls, usuario):
        reembolso = cls(usuario=usuario)
        return reembolso

    def __str__(self):
        return str(str(self.usuario)+str(self.data))

# Avisos para a Coordenação do PFE
class Aviso(models.Model):
    titulo = models.CharField(max_length=120, null=True, blank=True, help_text='Título do Aviso')
    delta = models.SmallIntegerField(default=0, help_text='dias passados do início do semestre')
    #mensagem = models.TextField(max_length=2000, help_text='Anotação')
    def __str__(self):
        return str(self.titulo)