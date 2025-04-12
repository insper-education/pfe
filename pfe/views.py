#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Junho de 2023
"""

import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.middleware.csrf import get_token
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

from administracao.models import Carta

# Get an instance of a logger
logger = logging.getLogger("django")

def index(request):
    """Página principal do sistema."""
    if request.user.is_authenticated:
        return render(request, "index.html")
    else:
        info = get_object_or_404(Carta, template="Informação")
        return render(request, "info.html", {"info": info})

def info(request):
    """Página com informações."""
    info = get_object_or_404(Carta, template="Informação")
    return render(request, "info.html", {"info": info})

def manutencao(request):
    """Página de Manutenção do sistema."""
    return render(request, "manutencao.html")

def custom_400(request, exception):
    mensagem = "<h1>Bad Request (400)</h1>"
    if (exception):
        mensagem += str(exception) + "<br>"
    mensagem += "Em caso de dúvida " + settings.CONTATO
    #t = loader.get_template("400.html")
    #t.render(Context({"exception_value": value,})
    return HttpResponse(mensagem)


from organizacoes.models import *
from projetos.models import Organizacao

@login_required
@permission_required("users.view_administrador", raise_exception=True)
def migracao(request):
    """temporário."""
    message = "Nada Feito"

    message = ""
    
    Segmento.objects.get_or_create(nome="Agronegócio", nome_en="Agribusiness", icone="🌾", cor="1f77b4")
    Segmento.objects.get_or_create(nome="Alimentos", nome_en="Food", icone="🍔", cor="ff7f0e")
    Segmento.objects.get_or_create(nome="Arte e Cultura", nome_en="Art and Culture", icone="🎨", cor="2ca02c")
    Segmento.objects.get_or_create(nome="Consultoria e Serviços", nome_en="Consulting and Services", icone="🧑‍💼", cor="d62728")
    Segmento.objects.get_or_create(nome="Energia", nome_en="Energy", icone="⚡", cor="9467bd")
    Segmento.objects.get_or_create(nome="Ensino e Educação", nome_en="Education", icone="🧠", cor="8c564b")
    Segmento.objects.get_or_create(nome="Esporte e Lazer", nome_en="Sports and Leisure", icone="⚽", cor="e377c2")
    Segmento.objects.get_or_create(nome="Finanças e Investimentos", nome_en="Finance and Investments", icone="🏦", cor="bcbd22")
    Segmento.objects.get_or_create(nome="Indústria e Manufatura", nome_en="Industry and Manufacturing", icone="🏭", cor="17becf")
    Segmento.objects.get_or_create(nome="Jogos Digitais", nome_en="Digital Games", icone="🎮", cor="aec7e8")
    Segmento.objects.get_or_create(nome="Saúde e Biotecnologia", nome_en="Health and Biotechnology", icone="🧬", cor="ffbb78")
    Segmento.objects.get_or_create(nome="Segurança e Defesa", nome_en="Security and Defense", icone="🛡️", cor="98df8a")
    Segmento.objects.get_or_create(nome="Setores Públicos e Sociais", nome_en="Public Sectors", icone="🏛️", cor="ff9896")
    Segmento.objects.get_or_create(nome="Sustentabilidade", nome_en="Sustainability", icone="🌱", cor="c5b0d5")
    Segmento.objects.get_or_create(nome="Tecnologia da Informação", nome_en="Information Technology", icone="💻", cor="c49c94")
    Segmento.objects.get_or_create(nome="Transporte e Logística", nome_en="Transport and Logistics", icone="🚚", cor="f7b6d2")
    Segmento.objects.get_or_create(nome="Varejo e Consumo", nome_en="Retail and Consumption", icone="🛒", cor="d787c1")
    
    message += "<br>Segmentos criados com sucesso:<br>"

    empresas = {
        "Agronegócio": [
            "Embrapa",
            "Sipcam Nichino Brasil",
            "Syngenta Seeds",
            "J. Assy",
            "Spacetime Ventures",
        ],
        "Alimentos": [
            "Ambev",
            "Coca-Cola FEMSA",
            "Danone",
            "Puratos",
            "Cargill",
        ],
        "Arte e Cultura": [
            "Daccord Music",
            "MASP",
            "SBT",
        ],
        "Jogos Digitais": [
            "Arvore Experiências Imersivas",
            "Tapps Games",
            "Wildlife Studios",
            "Fanatee",
        ],
        "Consultoria e Serviços": [
            "Backstage Estratégias Digitais",
            "Cambridge Family Enterprise Group",
            "Exed Consulting",
            "Falconi e Associados Consultoria Empresarial",
            "Fintalk",
            "Inmetrics",
            "Insper Alumni",
            "NTT Data Brasil",
            "Pinheiro Guimarães",
            "Projectiva",
            "SAP",
            "Serasa experian",
            "Tivit",
            "Traive",
            "Velt Partners",
            "Sistemas Urbanos",
            "Tata  Consultancy Services",
        ],
        "Energia": [
            "Raízen",
            "Daimon",
        ],
        "Ensino e Educação": [
            "Insper",
            "PrairieLearn",
            "Technische Hochschule Ingolstadt",
            "Universidade Federal de Pernambuco",
            "University of Illinois",
            "University of Texas Rio Grande Valley",
            "Université Côte d'Azur – Mediterranean Institute of Risk, Environment and Sustainable Development"
        ],
        "Esporte e Lazer": [
            "Confederação Brasileira de Futsal",
            "Paraty Brazil by UTMB",
        ],
        "Finanças e Investimentos": [
            "AUGME CAPITAL",
            "Bexs Banco",
            "Blackbelt Finance",
            "Bradesco",
            "BTG Pactual",
            "BW Gestão de Investimentos",
            "C6",
            "DAO Capital",
            "Gauss Capital",
            "Jera Capital",
            "Kapitalo Investimentos",
            "Legacy Capital",
            "Nubank",
            "QI Tech",
            "Rendimento Pay",
            "SRM Asset",
            "Dotz",
            "Lote45",
            "Creditas",
            "Mitsui & Co Coffee Trading Brazil",
        ],
        "Indústria e Manufatura": [
            "ABB",
            "AcelorMittal",
            "Basf",
            "Braskem",
            "CCN Automação",
            "Companhia Siderúrgica Nacional",
            "Embraer",
            "ENTEC Ravago",
            "General Electric",
            "General Motors do Brasil",
            "Gerdau Graphene",
            "Intelbras",
            "JHP Automação",
            "Klabin",
            "Mahle",
            "Maxion Structural Components",
            "Mercedes-Benz do Brasil",
            "OMRON",
            "Pollux Automation",
            "Rockwell Automation",
            "ROMI",
            "Sabó",
            "Santista Têxtil",
            "SCANIA",
            "Schneider Electric",
            "Schulz S.A",
            "Selco Tecnologia e Indústria",
            "Siemens",
            "Voith Paper",
            "VOSS Automotive",
            "Votorantim",
            "WEG",
            "Whirlpool",
            "Suzano",
            "Bioedtech",
            "BPN Transmissões",
            "SCANIA",
            "Incentiv",
            "Confederação Nacional da Indústria",
            "Sindipeças",
            "Klabin",
            "Solar Bot",
            "Suzano",
            "SPI",
            "Indago Devices Inc",
            "Fiberbus",
            "D2Eng",
        ],
        "Saúde e Biotecnologia": [
            "A. C. Camargo Cancer Center",
            "AACD",
            "Braincare Desenvolvimento e Inovação Tecnológica",
            "Bright Photomedicine",
            "EMS",
            "Hospital Albert Einstein",
            "Hospital Alemão Oswaldo Cruz",
            "Hospital Beneficência Portuguesa",
            "Hospital Sírio-Libanês",
            "Johnson & Johnson",
            "Kenvue (J&J)",
            "Magnamed Tecnologia Médica",
            "Mediterrâneo Saúde",
            "Mevo Saúde",
            "Mirca Serviços de Fisioterapia",
            "Albernaz",
            "Fundação Oswaldo Cruz - Instituto carlos chagas",
            "Bayer",
        ],
        "Segurança e Defesa": [
            "Akaer",
            "Salvaguarda"
        ],
        "Setores Públicos e Sociais": [
            "CTI Renato Archer",
            "Correios",
            "Eixo Estratégia Política",
            "Instituto Nacional de Pesquisas Espaciais",
            "IPT",
            "Ministério Público Federal",
            "Polícia Militar do Estado de São Paulo",
            "Sabesp",
            "Salvaguarda",
            "Incentiv",
            "join.valle",
        ],
        "Sustentabilidade": [
            "Inovação Social",
            "Lab. Arq. Futuro de Cidades",
        ],
        "Tecnologia da Informação": [
            "Amazon",
            "Aveva",
            "Binario Cloud",
            "BirminD Otimização",
            "COMPSIS",
            "Connect Data",
            "CWS Platform",
            "Dell Technologies",
            "deX Labs",
            "Google",
            "Grupo BYX",
            "Hewlett-Packard",
            "IBM Brasil",
            "iCelera",
            "ifood",
            "Intel",
            "Loft",
            "Looqbox",
            "Mastertech",
            "Mellanox",
            "Microsoft",
            "NEC",
            "Neorisk",
            "Neoway Business Solutions",
            "Nvidia",
            "Omega7 Systems",
            "Opus Software",
            "Oracle",
            "PCA Engenharia de Software",
            "Peerdustry",
            "Pinpag",
            "Plugify",
            "PREDIPARK",
            "Quinto Andar",
            "SMART Modular Technologies",
            "STMicroelectronics",
            "Unico",
            "Boldr",
            "Airis",
            "Mínimo P&D",
        ],
        "Transporte e Logística": [
            "Alupar",
            "Azul",
            "Latam",
            "Mercosul-Line",
            "Mottu",
            "tembici",
            "Ultracargo",
            "Cicloway",
        ],
        "Varejo e Consumo": [
            "B2W",
            "Via Varejo"
        ]
    }

    for segmento, empresas in empresas.items():
        s = Segmento.objects.get(nome=segmento)
        for empresa in empresas:
            e = Organizacao.objects.filter(nome=empresa).last()
            if not e:
                message += f"<br>{empresa} não encontrada"
                continue
            e.segmento = s
            e.save()
            message += f"<br>{empresa} - {s.nome}"
    message += "<br>Empresas migradas com sucesso:<br>"

    return HttpResponse(message)
