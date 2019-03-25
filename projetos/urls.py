from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'), #pagina inicial
    path('login/', views.login, name='login'), #pagina que trata informações para logar

    #path('alunos/', views.alunos, name='alunos'), #pagina que lista alunos
    path('alunos/', views.AlunoListView.as_view(), name='alunos'), #pagina que lista alunos

    #path('aluno/<str:aluno_id>/', views.aluno, name='aluno'), # edita informacoes do aluno

    path('aluno/<str:pk>/', views.AlunoDetailView.as_view(), name='aluno-detail'),

    path('myprojs/', views.ProjetosByUserListView.as_view(), name='my-proj'),

    #re_path(r'^book/(?P<pk>\d+)$', views.BookDetailView.as_view(), name='book-detail'),
    #path('aluno/<str:aluno_id>/', views.aluno, name='aluno'), # edita informacoes do aluno

    path('aluno/<str:pk>/nascimento/', views.nascimento, name='nascimento-aluno'),

    path('empresa/<str:empresa_id>/', views.empresa, name='empresa'), # edita informacoes da empresa
    path('professor/<str:professor_id>/', views.professor, name='professor'), # edita informacoes do professor

    path('projeto/', views.projeto, name='projeto'), # edita informacoes do projeto

    path('projeto/<int:pk>', views.ProjetoDetailView.as_view(), name='projeto-detail'),
    path('projeto/<int:pk>/', views.ProjetoDetailView.as_view(), name='projeto-detail/'),

    path('projeto/create/', views.ProjetoCreate.as_view(), name='projeto_create'),
    path('projeto/<int:pk>/update/', views.ProjetoUpdate.as_view(), name='projeto_update'),
    path('projeto/<int:pk>/delete/', views.ProjetoDelete.as_view(), name='projeto_delete'),



    # abaixo ainda muito lixo
    path('<int:aluno_id>/', views.detalhes_aluno, name='detalhes_aluno'), # /projetos/? - ? id do aluno
    path('<int:aluno_id>/projetos/', views.projetos_aluno, name='projetos_aluno'), # ex: /projetos/?/projetos - lista os projetos do aluno ?
    path('detalhes/', views.detalhes, name='detalhes'), # ex: /detalhes - lista todos os detalhes

]
