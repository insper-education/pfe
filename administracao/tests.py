from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from administracao.models import TextgraderAccessLog


class PrepararTextgraderTests(SimpleTestCase):
    def setUp(self):
        self.connection = MagicMock()
        self.connection.vendor = "postgresql"
        self.cursor = self.connection.cursor.return_value.__enter__.return_value
        self.editor = self.connection.schema_editor.return_value.__enter__.return_value
        patcher = patch(
            "administracao.management.commands.preparar_textgrader.connections",
            {"default": self.connection},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_creates_missing_table(self):
        self.cursor.fetchone.return_value = None

        call_command("preparar_textgrader", stdout=StringIO())

        self.editor.execute.assert_called_once_with("CREATE SCHEMA IF NOT EXISTS textgrader")
        self.editor.create_model.assert_called_once_with(TextgraderAccessLog)

    def test_preserves_existing_table(self):
        self.cursor.fetchone.return_value = ("r",)

        call_command("preparar_textgrader", stdout=StringIO())

        self.connection.schema_editor.assert_not_called()

    def test_rejects_non_table_relation(self):
        self.cursor.fetchone.return_value = ("v",)

        with self.assertRaises(CommandError):
            call_command("preparar_textgrader", stdout=StringIO())
        self.connection.schema_editor.assert_not_called()

    def test_requires_postgresql(self):
        self.connection.vendor = "sqlite"

        with self.assertRaises(CommandError):
            call_command("preparar_textgrader", stdout=StringIO())
        self.connection.cursor.assert_not_called()
