#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 8 de Janeiro de 2025
"""

import datetime
import logging

from django.core.exceptions import ValidationError
from .models import Alocacao

from academica.models import Exame
from projetos.models import Avaliacao2
from projetos.models import Banca
from projetos.models import Evento


# Get an instance of a logger
logger = logging.getLogger("django")

