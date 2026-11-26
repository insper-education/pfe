from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections

from administracao.models import TextgraderAccessLog


class Command(BaseCommand):
    help = "Cria o schema e a tabela de logs do Textgrader caso ainda não existam."

    def add_arguments(self, parser):
        parser.add_argument("--database", default=DEFAULT_DB_ALIAS)

    def handle(self, *args, **options):
        connection = connections[options["database"]]
        if connection.vendor != "postgresql":
            raise CommandError("A tabela do Textgrader requer PostgreSQL.")

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT c.relkind FROM pg_class c "
                "JOIN pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname = %s AND c.relname = %s",
                ["textgrader", "access_log"],
            )
            relation = cursor.fetchone()

        if relation:
            if relation[0] not in ("r", "p"):
                raise CommandError("textgrader.access_log existe, mas não é uma tabela.")
            self.stdout.write("A tabela textgrader.access_log já existe; nada foi alterado.")
            return

        with connection.schema_editor() as editor:
            editor.execute("CREATE SCHEMA IF NOT EXISTS textgrader")
            editor.create_model(TextgraderAccessLog)

        self.stdout.write(self.style.SUCCESS("Tabela textgrader.access_log criada."))
