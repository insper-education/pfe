from copy import deepcopy

from django.test import SimpleTestCase

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
