

# def get_next_opcao(numb, opcoes):
#     """Busca proxima opcao do aluno."""
#     numb += 1
#     lopcoes = opcoes.filter(prioridade=numb)
#     num_total_projetos = Projeto.objects.all().count() # Depois filtrar melhor
#     while (not lopcoes) and (numb <= num_total_projetos):
#         numb += 1
#         lopcoes = opcoes.filter(prioridade=numb)
#     if lopcoes: # Se a lista tem algum elemento
#         return numb
#     else:
#         return 0

# def get_opcao(numb, opcoes, min_group, max_group, projetos_ajustados):
#     """Pega a opcao de preferencia do aluno se possivel."""

#     try:
#         configuracao = Configuracao.objects.get()
#     except Configuracao.DoesNotExist:
#         return HttpResponse("Falha na configuracao do sistema.", status=401)

#     try:
#         opcao = opcoes.get(prioridade=numb)
#     except Opcao.DoesNotExist:
#         return HttpResponse("Opção não encontrada.", status=401)

#     while True:
#         opcoesp = Opcao.objects.filter(proposta=opcao.proposta)
#         opcoesp_alunos = opcoesp.filter(aluno__user__tipo_de_usuario=1)
#         opcoesp_validas = opcoesp_alunos.filter(aluno__anoPFE=configuracao.ano).\
#                                          filter(aluno__semestrePFE=configuracao.semestre)

#         if len(opcoesp_validas) >= min_group: #Checa se projeto tem numero minimo de aplicantes
#             pass
#             # checa se alunos no projeto ja tem CR maior dos que ja estao no momento no projeto
#         crh = 0
#         for optv in projetos_ajustados[opcao.proposta]:
#             if optv.aluno.cr > opcao.aluno.cr:
#                 crh += 1 #conta cada aluno com cr maior que o aluno sendo alocado
#         if crh < max_group:
#             break #se tudo certo retorna esse projeto mesmo
#         # Nao achou tentando outra opcao
#         numbx = get_next_opcao(numb, opcoes)
#         if numbx != 0:
#             try:
#                 opcao = opcoes.get(prioridade=numbx)
#             except Opcao.DoesNotExist:
#                 return None
#             break
#         else:  # caso nao encontre mais nenhuma opcao valida
#             return None
#     return opcao

# def limita_grupo(max_group, ano, semestre, projetos_ajustados):
#     """
#         Removendo alunos de grupos superlotados.
#         max_group: quantidade máxima de alunos por grupo    """

#     pref_pri_cr = 0.1  #talvez remover

#     balanceado = True
#     balanceado_max = False
#     count = 200 # Numero máximo de iterações, para não travar
#     while (not balanceado_max) and (count > 0):
#         count -= 1 # para nao correr o risco de um loop infinito
#         balanceado_max = True
#         for projeto, ops in projetos_ajustados.items():
#             if len(ops) > max_group: # Checa se projeto esta superlotado
#                 remove_opcao = None
#                 for option in ops:
#                     if option.prioridade < 5: #Nao move se prioridade < que 5 (REVER)
#                         if remove_opcao is None:
#                             remove_opcao = option
#                         elif (\
#                 option.aluno.cr * (1-((option.prioridade-1)*pref_pri_cr))) \
#                 < (remove_opcao.aluno.cr * (1-((remove_opcao.prioridade-1) * pref_pri_cr))):
#                             remove_opcao = option
#                 if remove_opcao is not None:
#                     opcoes = Opcao.objects.filter(aluno=remove_opcao.aluno).\
#                                             filter(proposta__ano=ano).\
#                                             filter(proposta__semestre=semestre)
#                     next_op = get_next_opcao(remove_opcao.prioridade, opcoes)
#                     if next_op != 0:
#                         #busca nas opcoes do aluno
#                         #op2 = get_opcao(next_op, opcoes, min_group,
#                         op2 = get_opcao(next_op, opcoes, 3,
#                                         max_group, projetos_ajustados)
#                         if op2: #op2 != None
#                             balanceado_max = False
#                             balanceado = False
#                             #menor_grupo = 1
#                             projetos_ajustados[projeto].remove(remove_opcao)
#                             projetos_ajustados[op2.projeto].append(op2)
#                             #print("Movendo(a) "+remove_opcao.aluno.user.first_name.lower()\
#                             #+" (DE): "+projeto.titulo+" (PARA):"+op2.projeto.titulo)
#     return balanceado

# def desmonta_grupo(min_group, ano, semestre, projetos_ajustados):
#     """Realocando alunos de grupos muito pequenos (um aluno por vez)."""

#     #menor_grupo = 1 # usado para elimnar primeiro grupos de 1, depois de 2, etc


#     remove_opcao = None
#     remove_projeto = None
#     menor_opcao = sys.maxsize

#     # identifica projeto potencial para desmontar
#     for projeto, ops in projetos_ajustados.items():
#         menor_opcao_tmp = 0
#         if ops and (len(ops) < min_group):
#             opcoes = Opcao.objects.filter(proposta=projeto.proposta)
#             for opt in opcoes:
#                 if opt.prioridade <= 5:
#                     menor_opcao_tmp += (6-opt.prioridade)**2 # prioridade 1 tem mais chances
#             if menor_opcao_tmp < menor_opcao:
#                 remove_projeto = projeto
#                 menor_opcao = menor_opcao_tmp
#     #print(remove_projeto)

#     if remove_projeto:
#         for remove_opcao in projetos_ajustados[remove_projeto]:
#             opcoes = Opcao.objects.filter(aluno=remove_opcao.aluno).\
#                                     filter(proposta__ano=ano).\
#                                     filter(proposta__semestre=semestre)
#             next_op = get_next_opcao(remove_opcao.prioridade, opcoes)
#             if next_op != 0:
#                 #busca nas opcoes do aluno
#                 #op2 = get_opcao(next_op, opcoes, min_group, max_group, projetos_ajustados)
#                 op2 = get_opcao(next_op, opcoes, min_group, 5, projetos_ajustados)
#                 if op2: #op2 != None:
#                     #balanceado = False
#                     #menor_grupo = 1
#                     projetos_ajustados[remove_projeto].remove(remove_opcao)
#                     projetos_ajustados[op2.projeto].append(op2)
#                     #print("Movendo(b) "+remove_opcao.aluno.user.first_name.lower()+\
#                     # " (DE): "+remove_projeto.titulo+" (PARA):"+op2.projeto.titulo)

# @login_required
# @permission_required('users.altera_professor', raise_exception=True)
# def propor(request):
#     """Monta grupos de PFE."""
    ############################################
    ## COLOCAR ESSE VALOR ACESSIVEL NO SISTEMA #
    ############################################
    #pref_pri_cr = 0.1  # Ficar longe da prioridade tem um custo de 5% na selecao do projeto

    # configuracao = Configuracao.objects.get()
    # projeto_list = []
    # opcoes_list = []
    # projetos = Projeto.objects.filter(disponivel=True).\
    #                            filter(ano=configuracao.ano).\
    #                            filter(semestre=configuracao.semestre)

    # if request.method == 'POST':
    #     min_group = int(request.POST.get('min', 1))
    #     max_group = int(request.POST.get('max', 5))
    #     projetos_ajustados = {}
    #     alunos = Aluno.objects.filter(user__tipo_de_usuario=1).\
    #                            filter(anoPFE=configuracao.ano).\
    #                            filter(semestrePFE=configuracao.semestre)

    #     for aluno in alunos: #Checa se o CR de todos os alunos esta coreto
    #         if aluno.cr < 5.0:
    #             #return HttpResponse("Aluno: "+aluno.user.first_name+" "+aluno.user.last_name+\
    #             #                    " ("+aluno.user.username+') com CR = '+str(aluno.cr))
    #             mensagem = "Detectado aluno: "+aluno.user.first_name+" "+aluno.user.last_name+\
    #                                 " ("+aluno.user.username+') com CR = '+str(aluno.cr)
    #             context = {
    #                 "area_principal": True,
    #                 "mensagem": mensagem,
    #             }
    #             return render(request, 'generic.html', context=context)

    #     #Cria Lista para todos os projetos
    #     for projeto in projetos:
    #         projetos_ajustados[projeto] = []

    #     #Posiciona os alunos nas suas primeiras opcoes (supondo projeto permitir)
    #     for aluno in alunos:
    #         opcoes = Opcao.objects.filter(aluno=aluno).\
    #                                filter(proposta__ano=configuracao.ano).\
    #                                filter(proposta__semestre=configuracao.semestre)
    #         if len(opcoes) >= 5: # checa se aluno preencheu formulario
    #             #busca nas opcoes do aluno
    #             opcoes1 = get_opcao(1, opcoes, min_group, max_group, projetos_ajustados)
    #             projetos_ajustados[opcoes1.projeto].append(opcoes1)

    #     #Posiciona os alunos nas suas melhores opcoes sem estourar o tamanho do grupo
    #     balanceado = False
    #     #count = 200
    #     count = 8
    #     while (not balanceado) and (count > 0):
    #         #balanceado = True
    #         balanceado = False

    #         limita_grupo(max_group, configuracao.ano, configuracao.semestre, projetos_ajustados)
    #         desmonta_grupo(min_group, configuracao.ano, configuracao.semestre, projetos_ajustados)

    #         # Próxima estapa seria puxar de volta os alunos que ficaram muito para frente nas opç

    #         count -= 1

    #     #Cria lista para enviar para o template html
    #     for projeto, ops in projetos_ajustados.items():
    #         if ops: #len(ops) > 0
    #             projeto_list.append(projeto)
    #             opcoes_list.append(ops)
    # else:
    #     for projeto in projetos:
    #         opcoes = Opcao.objects.filter(proposta=projeto.proposta)
    #         opcoes_alunos = opcoes.filter(aluno__user__tipo_de_usuario=1)
    #         opcoes_validas = opcoes_alunos.filter(aluno__anoPFE=configuracao.ano).\
    #                                        filter(aluno__semestrePFE=configuracao.semestre)
    #         opcoes1 = opcoes_validas.filter(prioridade=1)
    #         if opcoes1: #len(opcoes1) > 0
    #             projeto_list.append(projeto)
    #             opcoes_list.append(opcoes1)

    # mylist = zip(projeto_list, opcoes_list)
    # context = {
    #     'mylist': mylist,
    #     'length': len(projeto_list),
    # }
    # return render(request, 'projetos/propor.html', context)

    # DESLIGANDO
    # return HttpResponseNotFound('<h1>Sistema de propor projetos está obsoleto.</h1>')


