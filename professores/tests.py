from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from threading import Event, local
from types import SimpleNamespace
from unittest.mock import Mock, PropertyMock, patch

from django.db import close_old_connections
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase, TransactionTestCase
from django.urls import reverse

from academica.models import Composicao, Exame, Peso
from administracao.models import TipoEvento
from projetos.models import Avaliacao2, Avaliacao_Velha, Banca, Configuracao, ObjetivosDeAprendizagem, Projeto
from users.models import Alocacao, Aluno, PFEUser, Professor
from .support import bloqueia_avaliacao, move_avaliacoes
from .views import avaliar_entregas, banca_avaliar

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


class BloqueiaAvaliacaoTests(SimpleTestCase):
    def test_sem_documento_antes_e_depois_do_prazo(self):
        documentos = Mock()
        documentos.first.return_value = None
        casos = [
            (date(2026, 11, 25), (False, False)),
            (date(2026, 11, 24), (True, True)),
        ]
        with patch("professores.support.datetime.datetime") as relogio:
            relogio.now.return_value = datetime(2026, 11, 25, 12)
            for prazo, esperado in casos:
                with self.subTest(prazo=prazo):
                    self.assertEqual(
                        bloqueia_avaliacao(documentos, SimpleNamespace(endDate=prazo)),
                        esperado,
                    )

    def test_documentos_entregues_mantem_regras_de_atraso(self):
        documentos = Mock()
        evento = SimpleNamespace(endDate=date(2026, 11, 24))
        casos = [
            (datetime(2026, 11, 24, 23), False, (False, False)),
            (datetime(2026, 11, 25, 8), False, (True, False)),
            (datetime(2026, 11, 25, 8), True, (False, False)),
        ]
        with patch("professores.support.datetime.datetime") as relogio:
            relogio.now.return_value = datetime(2026, 11, 25, 12)
            for data, tolerado, esperado in casos:
                with self.subTest(data=data, tolerado=tolerado):
                    documentos.first.return_value = SimpleNamespace(
                        data=data, atraso_tolerado=tolerado,
                    )
                    self.assertEqual(bloqueia_avaliacao(documentos, evento), esperado)


class ReenvioBancaMixin:
    def setUp(self):
        Configuracao.objects.create(ano=2026, semestre=2)
        self.avaliador = PFEUser.objects.create_user(username="avaliador")
        orientador = Professor.objects.create(user=self.avaliador)
        self.projeto = Projeto.objects.create(orientador=orientador)
        aluno = Aluno.objects.create(user=PFEUser.objects.create_user(username="aluno"))
        self.alocacao = Alocacao.objects.create(projeto=self.projeto, aluno=aluno)
        tipo = TipoEvento.objects.create(nome="Banca final", sigla="BF")
        self.banca = Banca.objects.create(
            projeto=self.projeto, tipo_evento=tipo, slug="banca",
            startDate=datetime.now() - timedelta(days=1), endDate=datetime.now(),
        )
        exame = Exame.objects.create(titulo="Banca Final", sigla="BF", grupo=True)
        self.exame_individual = Exame.objects.create(
            titulo="Banca Final Individual", sigla="BFI",
        )
        composicao = Composicao.objects.create(exame=exame, data_inicial=date(2020, 1, 1))
        individual = Composicao.objects.create(exame=self.exame_individual, data_inicial=date(2020, 1, 1))
        self.objetivo = ObjetivosDeAprendizagem.objects.create(titulo="Objetivo", ordem=1)
        Peso.objects.create(composicao=composicao, objetivo=self.objetivo, peso=14)
        Peso.objects.create(composicao=individual, objetivo=self.objetivo, peso=14)

    def requisicao(self, conceito):
        request = RequestFactory().post("/", {
            "avaliador": self.avaliador.pk,
            "objetivo.{}".format(self.objetivo.pk): "{}.B".format(self.objetivo.pk),
            "bindividual.{}.objetivo.{}".format(self.alocacao.pk, self.objetivo.pk): "{}.{}".format(self.objetivo.pk, conceito),
        })
        request.user = self.avaliador
        return request

    def enviar(self, conceito):
        request = self.requisicao(conceito)
        with patch("professores.views.render_message", return_value=""), \
             patch("professores.views.mensagem_orientador", return_value=""), \
             patch("professores.views.email"), \
             patch("professores.views.Projeto.get_titulo_org", return_value="Projeto"), \
             patch("professores.views.render", return_value=HttpResponse("ok")):
            return banca_avaliar(request, self.banca.slug)


class ReenvioBancaTests(ReenvioBancaMixin, TestCase):
    def test_reenvio_pela_url_e_abertura_da_tela_de_notas(self):
        self.projeto.ano = 2026
        self.projeto.semestre = 2
        self.projeto.save()
        self.avaliador.tipo_de_usuario = 4
        self.avaliador.is_superuser = True
        self.avaliador.save()
        self.client.force_login(self.avaliador)
        dados = {
            "avaliador": self.avaliador.pk,
            "objetivo.{}".format(self.objetivo.pk): "{}.B".format(self.objetivo.pk),
            "bindividual.{}.objetivo.{}".format(self.alocacao.pk, self.objetivo.pk): "{}.B".format(self.objetivo.pk),
        }
        with patch("professores.views.render_message", return_value=""), \
             patch("professores.views.mensagem_orientador", return_value=""), \
             patch("professores.views.email"), \
             patch("projetos.models.Projeto.get_titulo_org", return_value="Projeto"), \
             patch("projetos.models.Projeto.get_titulo", return_value="Projeto"), \
             patch("projetos.models.Projeto.organizacao", new_callable=PropertyMock, return_value=None):
            url = reverse("banca_avaliar", kwargs={"slug": self.banca.slug})
            self.assertEqual(self.client.post(url, dados).status_code, 200)
            self.assertEqual(self.client.post(url, dados).status_code, 200)
            resposta = self.client.get(reverse("edita_notas", kwargs={"primarykey": self.alocacao.pk}))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Avaliacao2.objects.filter(exame=self.exame_individual, alocacao=self.alocacao).count(), 1)
        self.assertEqual(Avaliacao_Velha.objects.filter(exame=self.exame_individual, alocacao=self.alocacao).count(), 1)

    def test_reenvio_arquiva_nota_individual_anterior(self):
        self.enviar("B")
        nota_original = Avaliacao2.objects.get(exame=self.exame_individual).nota
        self.enviar("C")

        atual = Avaliacao2.objects.get(exame=self.exame_individual, alocacao=self.alocacao)
        anterior = Avaliacao_Velha.objects.get(exame=self.exame_individual, alocacao=self.alocacao)
        self.assertEqual(anterior.nota, nota_original)
        self.assertNotEqual(atual.nota, nota_original)

    def test_arquiva_apenas_nota_individual_do_avaliador_e_objetivo(self):
        outro_avaliador = PFEUser.objects.create_user(username="outro")
        outra = Avaliacao2.objects.create(
            projeto=self.projeto, exame=self.exame_individual, alocacao=self.alocacao,
            avaliador=outro_avaliador, objetivo=self.objetivo, nota=9,
        )
        outro_objetivo = ObjetivosDeAprendizagem.objects.create(titulo="Outro objetivo", ordem=2)
        outra_nota = Avaliacao2.objects.create(
            projeto=self.projeto, exame=self.exame_individual, alocacao=self.alocacao,
            avaliador=self.avaliador, objetivo=outro_objetivo, nota=8,
        )
        self.enviar("B")
        self.enviar("B")
        self.assertTrue(Avaliacao2.objects.filter(pk=outra.pk, nota=9).exists())
        self.assertTrue(Avaliacao2.objects.filter(pk=outra_nota.pk, nota=8).exists())
        self.assertEqual(Avaliacao2.objects.filter(exame=self.exame_individual).count(), 3)

    def test_reenvio_arquiva_todas_as_notas_anteriores_do_mesmo_objetivo(self):
        self.enviar("B")
        Avaliacao2.objects.create(
            projeto=self.projeto, exame=self.exame_individual, alocacao=self.alocacao,
            avaliador=self.avaliador, objetivo=self.objetivo, nota=5,
        )
        self.enviar("C")
        self.assertEqual(Avaliacao2.objects.filter(exame=self.exame_individual).count(), 1)
        self.assertEqual(Avaliacao_Velha.objects.filter(exame=self.exame_individual).count(), 2)


class ReenvioBancaConcorrenteTests(ReenvioBancaMixin, TransactionTestCase):
    def test_envios_simultaneos_sao_serializados(self):
        primeiro_no_arquivamento = Event()
        liberar_primeiro = Event()
        segundo_iniciado = Event()
        segundo_no_arquivamento = Event()
        thread_state = local()

        def arquivar(*args, **kwargs):
            if thread_state.primeiro and not primeiro_no_arquivamento.is_set():
                primeiro_no_arquivamento.set()
                if not liberar_primeiro.wait(10):
                    raise TimeoutError("Primeiro envio não foi liberado")
            elif not thread_state.primeiro:
                segundo_no_arquivamento.set()
            return move_avaliacoes(*args, **kwargs)

        def enviar(primeiro):
            thread_state.primeiro = primeiro
            if not primeiro:
                segundo_iniciado.set()
            try:
                return banca_avaliar(self.requisicao("B"), self.banca.slug)
            finally:
                close_old_connections()

        with patch("professores.views.move_avaliacoes", side_effect=arquivar), \
             patch("professores.views.render_message", return_value=""), \
             patch("professores.views.mensagem_orientador", return_value=""), \
             patch("professores.views.email"), \
             patch("professores.views.Projeto.get_titulo_org", return_value="Projeto"), \
             patch("professores.views.render", return_value=HttpResponse("ok")), \
             ThreadPoolExecutor(max_workers=2) as executor:
            primeiro = executor.submit(enviar, True)
            try:
                self.assertTrue(primeiro_no_arquivamento.wait(10))
                segundo = executor.submit(enviar, False)
                self.assertTrue(segundo_iniciado.wait(10))
                self.assertFalse(segundo_no_arquivamento.wait(1))
            finally:
                liberar_primeiro.set()
            self.assertEqual(primeiro.result(timeout=10).status_code, 200)
            self.assertEqual(segundo.result(timeout=10).status_code, 200)

        self.assertEqual(Avaliacao2.objects.filter(exame=self.exame_individual).count(), 1)
        self.assertEqual(Avaliacao_Velha.objects.filter(exame=self.exame_individual).count(), 1)
