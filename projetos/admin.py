from django.contrib import admin

from .models import Projeto, Opcao, Empresa, Funcionario


class OpcaoInline(admin.TabularInline):
    model = Opcao
    extra = 5
    max_num = 5

# @admin.register(Aluno)
# class AlunoAdmin(admin.ModelAdmin):
#     list_display = ('nome_completo', 'curso', 'email', 'opcao1', 'opcao2', 'opcao3', 'opcao4', 'opcao5')
#     list_filter = ('nome_completo', 'curso')
#     fields = ['login', 'nome_completo', 'nascimento', 'curso', ('email', 'email_pessoal')]
#     inlines = [OpcaoInline]

@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = ('abreviacao', 'titulo')
    fieldsets = (
        (None, {
            'fields': ('titulo', 'abreviacao', 'descricao', 'imagem', 'ano', 'semestre', 'disponivel')
        }),
        ('Origem', {
            'fields': ('empresa',)
        }),
    )

admin.site.register(Opcao)

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('sigla', 'nome_empresa')
