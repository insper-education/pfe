from django.contrib import admin

from .models import Aluno, Projeto, Opcao, Empresa, Professor, Funcionario

admin.site.register(Aluno)
admin.site.register(Projeto)
admin.site.register(Opcao)
admin.site.register(Empresa)
admin.site.register(Professor)
admin.site.register(Funcionario)
