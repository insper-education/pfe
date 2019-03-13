from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return HttpResponse("Pagina inicial para o Projeto Final de Engenharia.")
