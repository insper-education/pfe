from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase

from academica.models import Exame
from .views import avaliar_entregas

from .rubricas_evidencias import (
    RubricConfigError,
    calculate_maximum_grade,
    calculate_path,
    load_rubric_config,
    validate_rubric_config,
)


class RubricaEvidenciasEngineTests(SimpleTestCase):
    """Testes do fluxo condicional de limites para execução técnica."""

    def setUp(self):
        self.config = load_rubric_config("execucao-tecnica")

    def test_carrega_fluxo_booleano_condicional(self):
        rubric = self.config["rubric"]
        self.assertEqual(rubric["presentation"], "conditional_boolean")
        self.assertEqual(
            [node["id"] for node in rubric["nodes"]][-1],
            "revisao",
        )

    def test_resposta_nao_encerra_o_fluxo(self):
        path = calculate_path(self.config, {"exec_testes": ["nao"]})
        self.assertEqual(path, ["exec_testes", "org_metodologia"])

    def test_limites_progressivos(self):
        cases = [
            ({"exec_testes": ["nao"]}, "I"),
            ({"exec_testes": ["sim"], "exec_prototipo": ["nao"]}, "D"),
        ]
        for answers, maximum_grade in cases:
            with self.subTest(answers=answers):
                self.assertEqual(calculate_maximum_grade(self.config, answers), maximum_grade)

    def test_detecta_limite_invalido(self):
        config = deepcopy(self.config)
        config["rubric"]["nodes"][0]["options"][0]["maximum_grade"] = "Z"
        with self.assertRaises(RubricConfigError):
            validate_rubric_config(config)


class AvaliarEntregasTests(SimpleTestCase):
    def test_tipos_entregas_sao_unicos_e_ordenados_por_titulo(self):
        exame_z = Exame(pk=1, titulo="Zebra")
        exame_a = Exame(pk=2, titulo="alfa")
        exame_sem_titulo = Exame(pk=3, titulo=None)
        composicoes = [
            SimpleNamespace(exame=exame_z),
            SimpleNamespace(exame=exame_a),
            SimpleNamespace(exame=exame_z),
            SimpleNamespace(exame=None),
            SimpleNamespace(exame=exame_sem_titulo),
        ]
        request = RequestFactory().get("/")
        request.user = SimpleNamespace(
            is_authenticated=True, eh_admin=True, has_perms=lambda permissions: True,
        )
        configuracao = SimpleNamespace(ano=2026, semestre=1)

        with patch("professores.views.get_object_or_404", return_value=configuracao), \
             patch("professores.views.get_edicoes", return_value=(["2026.1"],)), \
             patch("professores.views.Composicao.objects.filter") as filtrar, \
             patch("professores.views.render") as render:
            filtrar.return_value.select_related.return_value = composicoes
            avaliar_entregas(request, prof_id="todos")

        filtrar.assert_called_once_with(entregavel=True)
        self.assertEqual(
            render.call_args.kwargs["context"]["tipos_entregas"],
            [exame_sem_titulo, exame_a, exame_z],
        )
