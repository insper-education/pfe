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
    
    Segmento.objects.get_or_create(nome="Outros", nome_en="Others", icone="❓")
    Segmento.objects.get_or_create(nome="Saúde e Biotecnologia", nome_en="Health and Biotechnology", icone="🧬")
    Segmento.objects.get_or_create(nome="Indústria e Manufatura", nome_en="Industry and Manufacturing", icone="🏭")
    Segmento.objects.get_or_create(nome="Tecnologia da Informação", nome_en="Information Technology", icone="💻")
    Segmento.objects.get_or_create(nome="Ensino e Educação", nome_en="Education", icone="🧠")
    Segmento.objects.get_or_create(nome="Finanças e Investimentos", nome_en="Finance and Investments", icone="🏦")
    Segmento.objects.get_or_create(nome="Varejo e Consumo", nome_en="Retail and Consumption", icone="🛒")
    Segmento.objects.get_or_create(nome="Consultoria e Serviços", nome_en="Consulting and Services", icone="🧑‍💼")
    Segmento.objects.get_or_create(nome="Transporte e Logística", nome_en="Transport and Logistics", icone="🚚")
    Segmento.objects.get_or_create(nome="Sustentabilidade", nome_en="Sustainability", icone="🌱")
    Segmento.objects.get_or_create(nome="Setores Públicos", nome_en="Public Sectors", icone="🏛️")
    Segmento.objects.get_or_create(nome="Agronegócio e Alimentos", nome_en="Agribusiness and Food", icone="🌾")
    Segmento.objects.get_or_create(nome="Arte e Cultura", nome_en="Art and Culture", icone="🎨")
    Segmento.objects.get_or_create(nome="Segurança e Defesa", nome_en="Security and Defense", icone="🛡️")
    Segmento.objects.get_or_create(nome="Esporte e Lazer", nome_en="Sports and Leisure", icone="⚽")
    
    message += "<br>Segmentos criados com sucesso:<br>"

    empresas = {
        "Agronegócio e Alimentos": [
            "Ambev",
            "Bayer",
            "Cargill",
            "Coca-Cola FEMSA",
            "Danone",
            "Embrapa",
            "Mitsui & Co Coffee Trading Brazil",
            "Puratos",
            "Raízen",
            "Sipcam Nichino Brasil",
            "Syngenta Seeds"
        ],
        "Arte e Cultura": [
            "Arvore Experiências Imersivas",
            "Daccord Music",
            "Lote45",
            "MASP",
            "SBT",
            "Wildlife Studios"
        ],
        "Consultoria e Serviços": [
            "AUGME CAPITAL",
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
            "Velt Partners"
        ],
        "Ensino e Educação": [
            "Bioedtech",
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
            "Tapps Games"
        ],
        "Finanças e Investimentos": [
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
            "SRM Asset"
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
            "Sindipeças",
            "Voith Paper",
            "VOSS Automotive",
            "Votorantim",
            "WEG",
            "Whirlpool"
        ],
        "Outros": [
            "Albernaz",
            "Boldr",
            "Confederação Nacional da Indústria",
            "Correios",
            "Dotz",
            "Eixo Estratégia Política",
            "Fundação Oswaldo Cruz - Instituto carlos chagas",
            "Inovação Social",
            "Instituto Nacional de Pesquisas Espaciais",
            "IPT",
            "J. Assy",
            "Ministério Público Federal",
            "Polícia Militar do Estado de São Paulo",
            "Sabesp",
            "Salvaguarda",
            "Sistemas Urbanos",
            "Suzano"
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
            "Indago Devices Inc",
            "Johnson & Johnson",
            "Kenvue (J&J)",
            "Magnamed Tecnologia Médica",
            "Mediterrâneo Saúde",
            "Mevo Saúde",
            "Mirca Serviços de Fisioterapia"
        ],
        "Segurança e Defesa": [
            "Akaer",
            "Airis",
            "Akaer",
            "Salvaguarda"
        ],
        "Setores Públicos": [
            "CTI Renato Archer"
        ],
        "Sustentabilidade": [
            "Cicloway",
            "Klabin",
            "Mínimo P&D",
            "Solar Bot",
            "Suzano",
            "Université Côte d'Azur – Mediterranean Institute of Risk, Environment and Sustainable Development"
        ],
        "Tecnologia da Informação": [
            "Amazon",
            "Aveva",
            "Binario Cloud",
            "BirminD Otimização",
            "COMPSIS",
            "Connect Data",
            "CWS Platform",
            "D2Eng",
            "Dell Technologies",
            "deX Labs",
            "Fanatee",
            "Fiberbus",
            "Google",
            "Grupo BYX",
            "Hewlett-Packard",
            "IBM Brasil",
            "iCelera",
            "ifood",
            "Intel",
            "join.valle",
            "Lab. Arq. Futuro de Cidades",
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
            "Spacetime Ventures",
            "SPI",
            "STMicroelectronics",
            "Tata  Consultancy Services",
            "Unico"
        ],
        "Transporte e Logística": [
            "Alupar",
            "Azul",
            "BPN Transmissões",
            "Latam",
            "Mercosul-Line",
            "Mottu",
            "SCANIA",
            "tembici",
            "Ultracargo"
        ],
        "Varejo e Consumo": [
            "B2W",
            "Creditas",
            "Daimon",
            "Incentiv",
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
