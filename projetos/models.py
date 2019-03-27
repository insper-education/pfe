from django.db import models
from django.urls import reverse  # To generate URLS by reversing URL patterns
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import Aluno, Professor, Funcionario
#from django.contrib.auth.models import User

# prevent unauthorized users from accessing the pages! We leave that as an exercise for you (hint: you could use the PermissionRequiredMixin and either create a new permission or reuse our can_mark_returned permission).

class Empresa(models.Model):
    login = models.CharField(primary_key=True, max_length=20)
    nome_empresa = models.CharField(max_length=80)
    sigla = models.CharField(max_length=20)
    class Meta:
        ordering = ['sigla']
        permissions = (("altera_empresa", "Empresa altera valores"), ("altera_professor", "Professor altera valores"), )
    def __str__(self):
        return self.nome_empresa

class Projeto(models.Model):
    #id = models.UUIDField(primary_key=True, default=uuid.uuid4, help_text='Unique ID para projeto')
    titulo = models.CharField(max_length=100, help_text='Titulo do projeto')
    abreviacao = models.CharField(max_length=10, help_text='Abreviacao usada para o projeto')
    descricao = models.TextField(max_length=1000, help_text='Descricao do projeto')
    imagem = models.ImageField(null=True, blank=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    ano = models.PositiveIntegerField(validators=[MinValueValidator(2018),MaxValueValidator(3018)], help_text='Ano que o projeto comeca')
    semestre = models.PositiveIntegerField(validators=[MinValueValidator(1),MaxValueValidator(2)], help_text='Semestre que o projeto comeca')
    disponivel = models.BooleanField(default=False)

    class Meta:
        ordering = ['abreviacao']
        permissions = (("altera_empresa", "Empresa altera valores"), ("altera_professor", "Professor altera valores"), )

    # Methods
    @property
    def procura_de_alunos(self):
        return 4

    def get_absolute_url(self):
        """Returns the url to access a particular instance of MyModelName."""
        return reverse('projeto-detail', args=[str(self.id)])

    def __str__(self):
        return self.abreviacao

class Opcao(models.Model):
    #id = models.UUIDField(primary_key=True, default=uuid.uuid4, help_text='Unique ID para opcao de projeto')
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE)
    #aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)
    razao = models.CharField(max_length=200)
    prioridade = models.PositiveSmallIntegerField(default=0)
    class Meta:
        ordering = ['prioridade']
        permissions = (("altera_professor", "Professor altera valores"), )
    def __str__(self):
        #return self.projeto.abreviacao+" >>> "+self.aluno.nome_completo
        return "OPCAO"

