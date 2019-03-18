from django.db import models

class Empresa(models.Model):
    login = models.CharField(max_length=20)
    nome_empresa = models.CharField(max_length=80)
    sigla = models.CharField(max_length=20)
    def __str__(self):
        return self.nome_empresa

class Projeto(models.Model):
    titulo = models.CharField(max_length=100)
    abreviacao = models.CharField(max_length=10)
    descricao = models.CharField(max_length=200)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    def __str__(self):
        return self.abreviacao

class Aluno(models.Model):
    TIPOS_CURSO = (
        ('C', 'Computacao'),
        ('M', 'Mecanica'),
        ('X', 'Mecatronica'),
    )
    login = models.CharField(max_length=20)
    nome_completo = models.CharField(max_length=80)
    curso = models.CharField(max_length=1, choices=TIPOS_CURSO)
    opcoes = models.ManyToManyField(Projeto, through='Opcao')
    def __str__(self):
        return self.nome_completo

class Opcao(models.Model):
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE)
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)
    razao = models.CharField(max_length=200)
    prioridade = models.PositiveSmallIntegerField(default=0)
    def __str__(self):
        return self.projeto.abreviacao+" >>> "+self.aluno.nome_completo

class Professor(models.Model):
    login = models.CharField(max_length=20)
    nome = models.CharField(max_length=80)
    def __str__(self):
        return self.nome

class Funcionario(models.Model):  # da empresa (não do Insper)
    login = models.CharField(max_length=20)
    nome = models.CharField(max_length=80)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    def __str__(self):
        return self.nome
