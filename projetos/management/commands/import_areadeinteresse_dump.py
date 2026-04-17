import csv
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from projetos.models import Area
from projetos.models import AreaDeInteresse
from projetos.models import Proposta


class Command(BaseCommand):
    help = (
        "Extrai e opcionalmente importa registros de AreaDeInteresse com proposta"
        " a partir de um dump JSON legado."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "dump_path",
            help="Caminho para o dump JSON legado.",
        )
        parser.add_argument(
            "--output",
            help="Arquivo CSV para salvar os dados extraidos.",
        )
        parser.add_argument(
            "--import",
            dest="do_import",
            action="store_true",
            help="Importa os registros encontrados para a base atual.",
        )
        parser.add_argument(
            "--match-by-title",
            action="store_true",
            help=(
                "Em vez de usar os PKs antigos, tenta localizar Proposta e Area na base atual"
                " pelos titulos do dump."
            ),
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Limita a quantidade de registros processados.",
        )

    def handle(self, *args, **options):
        dump_path = Path(options["dump_path"])
        if not dump_path.exists():
            raise CommandError(f"Arquivo nao encontrado: {dump_path}")

        rows = self._load_rows(dump_path)
        if options.get("limit"):
            rows = rows[: options["limit"]]

        self.stdout.write(self.style.SUCCESS(f"Registros com proposta encontrados: {len(rows)}"))

        output_path = options.get("output")
        if output_path:
            self._write_csv(Path(output_path), rows)
            self.stdout.write(self.style.SUCCESS(f"CSV gerado em: {output_path}"))

        if not options["do_import"]:
            self._print_preview(rows)
            self.stdout.write(self.style.WARNING("Dry-run apenas. Nada foi importado."))
            return

        imported, skipped = self._import_rows(rows, match_by_title=options["match_by_title"])
        self.stdout.write(self.style.SUCCESS(f"Importados: {imported}"))
        self.stdout.write(self.style.WARNING(f"Ignorados: {skipped}"))

    def _load_rows(self, dump_path):
        with dump_path.open("r", encoding="utf-8") as file_obj:
            data = json.load(file_obj)

        propostas = {}
        areas = {}
        for item in data:
            model = item.get("model")
            if model == "projetos.proposta":
                propostas[item["pk"]] = item.get("fields", {})
            elif model == "projetos.area":
                areas[item["pk"]] = item.get("fields", {})

        rows = []
        for item in data:
            if item.get("model") != "projetos.areadeinteresse":
                continue

            fields = item.get("fields", {})
            proposta_pk = fields.get("proposta")
            if not proposta_pk:
                continue

            area_pk = fields.get("area")
            proposta_fields = propostas.get(proposta_pk, {})
            area_fields = areas.get(area_pk, {}) if area_pk else {}
            rows.append(
                {
                    "legacy_pk": item.get("pk"),
                    "proposta_pk": proposta_pk,
                    "proposta_titulo": proposta_fields.get("titulo"),
                    "area_pk": area_pk,
                    "area_titulo": area_fields.get("titulo"),
                    "outras": fields.get("outras"),
                    "nivel_interesse": fields.get("nivel_interesse"),
                }
            )
        return rows

    def _write_csv(self, output_path, rows):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "legacy_pk",
            "proposta_pk",
            "proposta_titulo",
            "area_pk",
            "area_titulo",
            "outras",
            "nivel_interesse",
        ]
        with output_path.open("w", encoding="utf-8", newline="") as file_obj:
            writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def _print_preview(self, rows):
        preview = rows[:10]
        for row in preview:
            self.stdout.write(str(row))

    @transaction.atomic
    def _import_rows(self, rows, match_by_title=False):
        imported = 0
        skipped = 0

        for row in rows:
            proposta = self._resolve_proposta(row, match_by_title=match_by_title)
            area = self._resolve_area(row, match_by_title=match_by_title)

            if not proposta:
                self.stdout.write(
                    self.style.WARNING(
                        f"Ignorado legacy_pk={row['legacy_pk']}: proposta nao localizada"
                    )
                )
                skipped += 1
                continue

            if row["area_pk"] and not area:
                self.stdout.write(
                    self.style.WARNING(
                        f"Ignorado legacy_pk={row['legacy_pk']}: area nao localizada"
                    )
                )
                skipped += 1
                continue

            _, created = AreaDeInteresse.objects.get_or_create(
                usuario=None,
                proposta=proposta,
                area=area,
                outras=row["outras"],
                defaults={"nivel_interesse": row["nivel_interesse"]},
            )
            if created:
                imported += 1
            else:
                skipped += 1

        return imported, skipped

    def _resolve_proposta(self, row, match_by_title=False):
        if not match_by_title:
            return Proposta.objects.filter(pk=row["proposta_pk"]).first()

        titulo = row.get("proposta_titulo")
        if not titulo:
            return None
        return Proposta.objects.filter(titulo=titulo).first()

    def _resolve_area(self, row, match_by_title=False):
        if not row.get("area_pk"):
            return None

        if not match_by_title:
            return Area.objects.filter(pk=row["area_pk"]).first()

        titulo = row.get("area_titulo")
        if not titulo:
            return None
        return Area.objects.filter(titulo=titulo).first()