 #!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 6 de Novembro de 2023
"""

TIPO_EVENTO = (
    (0, 'Feriado', 'lightgrey'),
    (1, 'Aula cancelada', 'lightgrey'),

    (9, 'Alinhamentos iniciais entre Estudantes/Orientadores/Organizações', 'orange'),
    (10, 'Início das aulas', 'red'),
    (11, 'Evento de abertura do PFE', 'orange'),  # Obsoleto
    (12, 'Aula PFE', 'lightgreen'),
    (13, 'Evento de encerramento do PFE', 'brown'),
    (14, 'Bancas Intermediárias', 'violet'),
    (15, 'Bancas Finais', 'yellow'),
    (16, 'Apresentação formal final na organização', 'burlywood'),
    (17, 'Apresentação opcional intermediária na organização', 'Khaki'),
    (18, 'Probation', 'LightSteelBlue'),

    (20, 'Relato quinzenal (Individual)', 'aquamarine'),
    (21, 'Entrega de Relatório Preliminar (Grupo)', 'lightblue'),  # antigo relat. de planej.
    (22, 'Entrega do Relatório Intermediário (Grupo e Individual)', 'teal'),
    (23, 'Entrega do Relatório Final (Grupo e Individual)', 'aqua'),
    (24, 'Entrega do Relatório Revisado (Grupo)', 'deepskyblue'),
    (25, 'Entrega do Banner (Grupo)', 'chocolate'),
    (26, 'Entrega do Vídeo (Grupo)', 'lavender'),

    (30, 'Feedback dos estudantes sobre PFE', 'orange'),
    (31, 'Avaliação de Pares Intermediária', 'pink'),
    (32, 'Avaliação de Pares Final', 'pink'),

    (40, 'Laboratório', 'orange'),
    (41, 'Semana de provas', 'red'),

    (50, 'Apresentação para Certificação Falconi', 'darkorange'),

    (101, 'Apólice Seguro Acidentes Pessoais', 'aquamarine'),

    (111, 'Bate-papo com estudante que farão PFE no próximo semestre', 'lightcyan'),
    (112, 'Estudantes demonstrarem interesse em adiar PFE para 9º semestre', 'limegreen'),
    (113, 'Apresentação das propostas de projetos disponíveis para estudantes', 'darkslategray'),

    (120, 'Limite para submissão de propostas de projetos pelas organizações', 'lime'),
    (121, 'Pré seleção de propostas de projetos', 'chartreuse'),

    (123, 'Indicação de interesse nos projetos do próximo semestre pelos estudante', 'hotpink '),
    (124, 'Notificação para estudantes dos grupos formados', 'paleturquoise'),
    (125, 'Notificação para organizações dos projetos fechados', 'moccasin'),
    (126, 'Professores tiram dúvidas sobre projetos para estudantes', 'lightsalmon'),
    (127, 'Reunião do comitê para montar grupos para o próximo semestre', 'powderblue'),

    (129, 'Limite para contrato pronto para assinatura pelos estudantes', 'coral'),

    (130, 'Validação dos projetos pelo comitê', 'peru'),

    (140, 'Reunião de orientações aos orientadores', 'maroon'),
)


TIPO_DE_DOCUMENTO = ( # não mudar a ordem dos números
    (0, "Contrato com Organização Parceira"),
    (1, "Contrato entre Organização e Estudante"),
    (2, "Contrado de Confidencialidade"),
    (3, "Relatório Final Revisado"),
    (4, "Autorização de Publicação Empresa"),
    (5, "Autorização de Publicação Estudante"),
    (6, "Regulamento PFE"),
    (7, "Plano de Aprendizado"),
    (8, "Manual do Estudante"),
    (9, "Manual do Orientador"),
    (10, "Manual da Organização Parceira"),
    (11, "Manual do Carreiras"),
    (12, "Manual de Relatórios"),
    (13, "Manual de Planejamentos"),
    (14, "FREE"),
    (15, "Seguros"),
    (16, "FREE"),
    (17, "Template de Relatórios"),
    (18, "Vídeo do Projeto"),
    (19, "FREE"),
    (20, "Banner"),
    (21, "Ata do Comitê do PFE"),
    (22, "Manual de Apresentação"),
    (23, "Manual de Bancas"),
    (24, "Manual de Avaliações"),
    (25, "Relatório Publicado"),
    (26, "Notificação de Relatório"),
    (27, "Apresentação da Banca Final"),
    (28, "Plano de Orientação"),
    (32, "Termo de Parceria - PDF"),
    (33, "Termo de Parceria - DOC"),
    (40, "Relatório Preliminar"),
    (41, "Relatório Intermediário de Grupo"),
    (42, "Relatório Intermediário Individual"),
    (43, "Relatório Final de Grupo"),
    (44, "Relatório Final Individual"),
    (128, "Matéria na Mídia"),
    (255, "Outros"),
)