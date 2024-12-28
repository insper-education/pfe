 #!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 6 de Novembro de 2023
"""


# REMOVER TUDO AQUI


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



TIPO_EVENTO_EN = (
    (0, "Holiday", "#D3D3D3"),
    (1, "Class canceled", "#D3D3D3"),

    (9, "Initial discussions between Group/Advisor/Organization", "#FFA520"),

    (10, "Start of classes", "#FF1010"),
    (11, "Opening event", "#FFA500"),  # Obsolete
    (12, "Class", "#90EE90"),
    (13, "Closing event", "#FF4500"),
    (14, "Intermediate Presentations", "#EE82EE"),
    (15, "Final Presentations", "#FFFF00"),
    (16, "Final formal presentation at the organization", "#DEB887"),
    (17, "Optional intermediate presentation at the organization", "#F0E68C"),
    (18, "Probation", "#B0C4DE"),
    (19, "Professional Mentoring (market specialists)", "#DB7093"),

    (20, "Biweekly report (Individual)", "#7FFFD4"),
    (21, "Preliminary Report Submission (Group)", "#ADD8E6"),  # formerly planning report
    (22, "Intermediate Report Submission (Group and Individual)", "#008080"),
    (23, "Final Report Submission (Group and Individual)", "#00FFFF"),
    (24, "Revised Report Submission (Group)", "#00BFFF"),
    (25, "Banner Submission (Group)", "#D2691E"),
    (26, "Video Submission (Group)", "#E6E6FA"),

    (30, "Student Feedback", "#FFA510"),
    (31, "Intermediate Peer Evaluation", "#FFC0CB"),
    (32, "Final Peer Evaluation", "#FFC0DB"),

    (40, "Laboratory", "#FFA500"),
    (41, "Exam week", "#FF0000"),

    (50, "Presentation for Falconi Certification", "#FF8C00"),

    (101, "Personal Accident Insurance Policy", "#7FFFD4"),

    (111, "Chat with students enrolling next semester", "#E0FFFF"),

    (112, "Students notifying project postponement", "#32CD32"),  # No longer in use

    (113, "Presentation of available proposals for students", "#2E8B57"),

    (120, "Deadline for proposal submission by organizations", "#00FF00"),
    (121, "Committee plans proposal search for the semester", "#7FFF00"),

    (123, "Students express interest in proposals", "#FF69B4 "),
    (124, "Notification to students of formed groups", "#AFEEEE"),
    (125, "Notification to organizations of closed projects", "#FFE4B5"),
    (126, "Professors clarify doubts about proposals for students", "#FFA07A"),
    (127, "Committee meeting to form project groups", "#B0E0E6"),
    (128, "Semester Debriefing Meeting with Advisors", "#FFD700"),

    (129, "Deadline for contract ready for signatures", "#FF7F50"),

    (130, "Project validation by the committee", "#CD853F"),

    (140, "Guidance meeting for advisors", "#FFEFD5"),
    (141, "Guidelines for Intermediate Presentations", "#E5D7BF"),
    (142, "Guidelines for Final Presentations", "#CCBFAA"),
)