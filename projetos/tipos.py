 #!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 6 de Novembro de 2023
"""

TIPO_EVENTO = (
    (0, "Feriado", "#D3D3D3"),
    (1, "Aula cancelada", "#D3D3D3"),

    (9, "Conversas iniciais entre Grupo/Orientador/Organização", "#FFA520"),

    (10, "Início das aulas", "#FF1010"),
    (11, "Evento de abertura", "#FFA500"),  # Obsoleto
    (12, "Aula", "#90EE90"),
    (13, "Evento de encerramento", "#FF4500"),
    (14, "Bancas Intermediárias", "#EE82EE"),
    (15, "Bancas Finais", "#FFFF00"),
    (16, "Apresentação formal final na organização", "#DEB887"),
    (17, "Apresentação opcional intermediária na organização", "#F0E68C"),
    (18, "Probation", "#B0C4DE"),
    (19, "Mentoria Profissional (especialistas do mercado)", "#DB7093"),

    (20, "Relato quinzenal (Individual)", "#7FFFD4"),
    (21, "Entrega de Relatório Preliminar (Grupo)", "#ADD8E6"),  # antigo relat. de planej.
    (22, "Entrega do Relatório Intermediário (Grupo e Individual)", "#008080"),
    (23, "Entrega do Relatório Final (Grupo e Individual)", "#00FFFF"),
    (24, "Entrega do Relatório Revisado (Grupo)", "#00BFFF"),
    (25, "Entrega do Banner (Grupo)", "#D2691E"),
    (26, "Entrega do Vídeo (Grupo)", "#E6E6FA"),

    (30, "Feedback dos estudantes", "#FFA510"),
    (31, "Avaliação de Pares Intermediária", "#FFC0CB"),
    (32, "Avaliação de Pares Final", "#FFC0DB"),

    (40, "Laboratório", "#FFA500"),
    (41, "Semana de provas", "#FF0000"),

    (50, "Apresentação para Certificação Falconi", "#FF8C00"),

    (101, "Apólice Seguro Acidentes Pessoais", "#7FFFD4"),

    (111, "Bate-papo com estudantes que cursarão no próximo semestre", "#E0FFFF"),

    (112, "Estudantes informarem que adiarão projeto", "#32CD32"),  # A principio não usar mais

    (113, "Apresentação das propostas disponíveis para estudantes", "#2E8B57"),

    (120, "Limite para submissão de propostas pelas organizações", "#00FF00"),
    (121, "Comitê planeja busca de propostas para o semestre", "#7FFF00"),

    (123, "Indicação de interesse nas propostas pelos estudante", "#FF69B4 "),
    (124, "Notificação para estudantes dos grupos formados", "#AFEEEE"),
    (125, "Notificação para organizações dos projetos fechados", "#FFE4B5"),
    (126, "Professores tiram dúvidas das proposta para estudantes", "#FFA07A"),
    (127, "Reunião do comitê para montar grupos de projetos", "#B0E0E6"),
    (128, "Reunião de Debriefing do Semestre com os Orientadores", "#FFD700"),

    (129, "Limite para contrato pronto para assinaturas", "#FF7F50"),

    (130, "Validação dos projetos pelo comitê", "#CD853F"),

    (140, "Reunião de orientações aos orientadores", "#FFEFD5"),
    (141, "Orientações para Bancas Intermediárias", "#E5D7BF"),
    (142, "Orientações para Bancas Finais", "#CCBFAA"),

)


TIPO_DE_CERTIFICADO = (
    (0, "Não definido"),
    (1, "Estudante destaque"),
    (2, "Equipe destaque"),
    (11, "Destaque Falconi"),
    (12, "Excelência Falconi"),
    (101, "Orientação de Projeto"),
    (102, "Coorientação de Projeto"),
    (103, "Membro de Banca Intermediária"),
    (104, "Membro de Banca Final"),
    (105, "Membro da Banca Falconi"),
    (106, "Mentoria Profissional"),  # antigo mentor na Falconi
    (107, "Mentoria Técnica"),  # mentor da empresa
    (108, "Membro de Banca de Probation"),
)