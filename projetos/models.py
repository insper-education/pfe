from django.db import models
from django.urls import reverse  # To generate URLS by reversing URL patterns
import uuid # Required for unique book instances

class Empresa(models.Model):
    login = models.CharField(primary_key=True, max_length=20)
    nome_empresa = models.CharField(max_length=80)
    sigla = models.CharField(max_length=20)
    class Meta:
        ordering = ['sigla']
    def __str__(self):
        return self.nome_empresa

class Projeto(models.Model):
    #id = models.UUIDField(primary_key=True, default=uuid.uuid4, help_text='Unique ID para projeto')
    titulo = models.CharField(max_length=100, help_text='Titulo do projeto')
    abreviacao = models.CharField(max_length=10, help_text='Abreviacao usada para o projeto')
    descricao = models.TextField(max_length=1000, help_text='Descricao do projeto')
    imagem = models.ImageField(null=True, blank=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    class Meta:
        ordering = ['abreviacao']
    # Methods
    def get_absolute_url(self):
        """Returns the url to access a particular instance of MyModelName."""
        return reverse('model-detail-view', args=[str(self.id)])
    def __str__(self):
        return self.abreviacao

class Aluno(models.Model):
    TIPOS_CURSO = (
        ('C', 'Computacao'),
        ('M', 'Mecanica'),
        ('X', 'Mecatronica'),
    )
    login = models.CharField(primary_key=True, max_length=20)
    nome_completo = models.CharField(max_length=80,help_text='Nome completo do aluno')
    curso = models.CharField(max_length=1, choices=TIPOS_CURSO, help_text='Curso Matriculado',)
    opcoes = models.ManyToManyField(Projeto, through='Opcao', help_text='Opcoes de projeto escolhidos')
    email = models.EmailField(null=True, blank=True)
    email_pessoal = models.EmailField(null=True, blank=True)
    class Meta:
        ordering = ['nome_completo']  
    def __str__(self):
        return self.nome_completo
    def opcao(self,i):
        try:
            valor = self.opcoes.all()[i]
        except IndexError:
            valor = 'vazio'
        return valor
    def opcao1(self):
        return self.opcao(0)
    def opcao2(self):
        return self.opcao(1)
    def opcao3(self):
        return self.opcao(2)
    def opcao4(self):
        return self.opcao(3)
    def opcao5(self):
        return self.opcao(4)
    opcao1.short_description = 'Opcao 1'
    opcao2.short_description = 'Opcao 2'
    opcao3.short_description = 'Opcao 3'
    opcao4.short_description = 'Opcao 4'
    opcao5.short_description = 'Opcao 5'

class Opcao(models.Model):
    #id = models.UUIDField(primary_key=True, default=uuid.uuid4, help_text='Unique ID para opcao de projeto')
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE)
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)
    razao = models.CharField(max_length=200)
    prioridade = models.PositiveSmallIntegerField(default=0)
    def __str__(self):
        return self.projeto.abreviacao+" >>> "+self.aluno.nome_completo

class Professor(models.Model):
    login = models.CharField(primary_key=True, max_length=20)
    nome = models.CharField(max_length=80)
    email = models.EmailField(null=True, blank=True)
    class Meta:
        ordering = ['nome']  
    def __str__(self):
        return self.nome

class Funcionario(models.Model):  # da empresa (não do Insper)
    login = models.CharField(primary_key=True, max_length=20)
    nome = models.CharField(max_length=80)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    email = models.EmailField(null=True, blank=True)
    #gestor_responsavel = models.EmailField()
    #mentor_tecnico = models.EmailField()
    #recursos_humanos = models.EmailField()
    class Meta:
        ordering = ['nome']  
    def __str__(self):
        return self.nome
