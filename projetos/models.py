# Desenvolvido para o Projeto Final de Engenharia
# Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
# Data: 15 de Maio de 2019

from django.db import models
from django.urls import reverse  # To generate URLS by reversing URL patterns
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib import admin
#from users.models import Professor, Funcionario

# RENOMEAR PARA ORGANIZACAO
class Empresa(models.Model):
    login = models.CharField(primary_key=True, max_length=20)
    #login = models.CharField(max_length=20)     # em algum momento concertar isso
    nome_empresa = models.CharField(max_length=80)
    sigla = models.CharField(max_length=20)
    endereco = models.TextField(max_length=200, help_text='Endereço da Empresa')
    website = models.URLField(max_length=250)
    # contatoEmpresa = models.CharField(max_length=80)
    class Meta:
        ordering = ['sigla']
        permissions = (("altera_empresa", "Empresa altera valores"), ("altera_professor", "Professor altera valores"), )
    def __str__(self):
        return self.nome_empresa

class Projeto(models.Model):
    titulo = models.CharField(max_length=100, help_text='Titulo do projeto')
    descricao = models.TextField(max_length=2000, help_text='Descricao do projeto')
    expectativas = models.TextField(max_length=2000, help_text='Expectativas em relação ao projeto')
    areas = models.TextField(max_length=1000, help_text='Áreas da engenharia envolvidas no projeto')
    recursos = models.TextField(max_length=1000, help_text='Recursos a serem disponibilizados aos Alunos')
    imagem = models.ImageField(null=True, blank=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    ano = models.PositiveIntegerField(validators=[MinValueValidator(2018),MaxValueValidator(3018)], help_text='Ano que o projeto comeca')
    semestre = models.PositiveIntegerField(validators=[MinValueValidator(1),MaxValueValidator(2)], help_text='Semestre que o projeto comeca')
    disponivel = models.BooleanField(default=False)
    # contato1 = models.CharField(max_length=80)
    # contato2 = models.CharField(max_length=80)
    # contato3 = models.CharField(max_length=80)
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
        return self.titulo

class Configuracao(models.Model):
    ano = models.PositiveIntegerField(validators=[MinValueValidator(2018),MaxValueValidator(3018)], help_text='Ano que o projeto comeca')
    semestre = models.PositiveIntegerField(validators=[MinValueValidator(1),MaxValueValidator(2)], help_text='Semestre que o projeto comeca')

class ConfiguracaoAdmin(admin.ModelAdmin):
  def has_add_permission(self, request):
    # if there's already an entry, do not allow adding
    count = Configuracao.objects.all().count()
    if count == 0:
      return True
    return False