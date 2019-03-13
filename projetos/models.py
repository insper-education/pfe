from django.db import models

class Projeto(models.Model):
    titulo = models.CharField(max_length=100)
    abreviacao = models.CharField(max_length=10)
    descricao = models.CharField(max_length=200)
    empresa = models.CharField(max_length=50)
    def __str__(self):
        return self.abreviacao

class Aluno(models.Model):
    TIPOS_CURSO = (
        ('C', 'Computacao'),
        ('M', 'Mecanica'),
        ('X', 'Mecatronica'),
    )
    nome_completo = models.CharField(max_length=80)
    curso = models.CharField(max_length=1, choices=TIPOS_CURSO)
    opcoes = models.ManyToManyField(Projeto, through='Opcao')
    def __str__(self):
        return self.nome_completo

class Opcao(models.Model):
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE)
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)
    razao = models.CharField(max_length=200)