# Desenvolvido para o Projeto Final de Engenharia
# Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
# Data: 15 de Maio de 2019

from django.db import models
from django.urls import reverse  # To generate URLS by reversing URL patterns
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib import admin
#from datetime import datetime
import datetime 
import os

from django.conf import settings

import users.models

def get_upload_path(instance, filename):
    file_path = os.path.abspath(os.path.join(settings.ARQUIVOS, instance.sigla) )
    return "{0}/{1}".format(file_path, filename)

# RENOMEAR PARA ORGANIZACAO
class Empresa(models.Model):
    login = models.CharField(primary_key=True, max_length=20)
    #login = models.CharField(max_length=20)     # em algum momento concertar isso
    nome_empresa = models.CharField(max_length=80)
    sigla = models.CharField(max_length=20)
    endereco = models.TextField(max_length=200, help_text='Endereço da Empresa')
    website = models.URLField(max_length=250, null=True, blank=True)
    contrato = models.FileField(null=True, blank=True, upload_to=get_upload_path, help_text='Documento PDF contendo o contrato com a Empresa')

    class Meta:
        ordering = ['sigla']
        permissions = (("altera_empresa", "Empresa altera valores"), ("altera_professor", "Professor altera valores"), )
    def __str__(self):
        return self.nome_empresa
    def documento(self):
        return os.path.split(self.contrato.name)[1]

class Projeto(models.Model):
    titulo = models.CharField(max_length=127, help_text='Titulo do projeto')
    descricao = models.TextField(max_length=2000, help_text='Descricao do projeto')
    expectativas = models.TextField(max_length=2000, help_text='Expectativas em relação ao projeto')
    areas = models.TextField(max_length=1000, help_text='Áreas da engenharia envolvidas no projeto')
    recursos = models.TextField(max_length=1000, help_text='Recursos a serem disponibilizados aos Alunos')
    imagem = models.ImageField(null=True, blank=True, help_text='Imagem que representa projeto (se houver)')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, help_text='Empresa que propôs projeto')
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

# Anotacoes de comunicações com as organizações pareceiras
class Anotacao(models.Model):
    data = models.DateField(default=datetime.date.today, blank=True, help_text='Data da comunicação')
    organizacao = models.ForeignKey(Empresa, null=True, blank=True, on_delete=models.CASCADE, help_text='Organização parceira')
    autor = models.ForeignKey('users.PFEUser', null=True, blank=True, on_delete=models.SET_NULL, related_name='professor_orientador', help_text='quem fez a anotação')
    texto = models.TextField(max_length=2000, help_text='Anotação')
    def __str__(self):
        return str(self.data)