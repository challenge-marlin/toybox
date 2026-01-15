"""
Load Card master data from a PostgreSQL dump that contains a COPY section for public.cards.

Why:
- In some production setups the cards table is partially seeded (or empty), causing:
  - Card names to fall back to IDs (code)
  - Random draw to become deterministic (e.g. only one SSR card exists in DB)

This command extracts card rows from a dump like:
  COPY public.cards (id, code, name, rarity, image_url, ...) FROM stdin;
  ...
  \.

and upserts into gamification.models.Card by code.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import re

from django.core.management.base import BaseCommand

from gamification.models import Card


@dataclass
class _DumpCardRow:
    code: str
    name: str
    rarity: str
    image_url: Optional[str]
    description: Optional[str]


def _decode_dump_bytes(raw: bytes) -> str:
    """
    Dump files in this repo/server have sometimes been created with a legacy encoding.
    Try UTF-8 first, then CP932 (Windows Japanese).
    """
    for enc in ("utf-8", "cp932", "utf-8-sig"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    # Last resort
    return raw.decode("utf-8", errors="replace")


def _parse_cards_from_dump(text: str) -> list[_DumpCardRow]:
    in_cards_copy = False
    rows: list[_DumpCardRow] = []
    # Accept variations:
    # - COPY public.cards (...)
    # - COPY cards (...)
    # - COPY public."cards" (...)
    # - leading spaces
    copy_cards_re = re.compile(r'^COPY\s+(?:[A-Za-z_][\w]*\.)?"?cards"?\s*\(', re.IGNORECASE)

    for line in text.splitlines():
        if not in_cards_copy:
            l = line.lstrip()
            if copy_cards_re.match(l) and "FROM stdin" in l:
                in_cards_copy = True
            continue

        if line.strip() == r"\.":
            break

        # Tab-separated COPY rows:
        # id, code, name, rarity, image_url, description, old_id, created_at, updated_at, image
        parts = line.split("\t")
        if len(parts) < 5:
            continue

        code = (parts[1] or "").strip()
        name = (parts[2] or "").strip()
        rarity = (parts[3] or "").strip()
        image_url = (parts[4] or "").strip()
        description = parts[5].strip() if len(parts) > 5 else None

        if not code:
            continue

        if image_url == r"\N":
            image_url = ""
        if description == r"\N":
            description = None

        rows.append(
            _DumpCardRow(
                code=code,
                name=name or code,
                rarity=rarity or "common",
                image_url=image_url or None,
                description=description,
            )
        )

    return rows


class Command(BaseCommand):
    help = "Load Card master data from a backup SQL dump (COPY public.cards ... FROM stdin)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--sql-file",
            type=str,
            default="backup_current_20251217_152233.sql",
            help="Path to backup SQL dump (relative to backend/).",
        )

    def handle(self, *args, **options):
        sql_file = Path(options["sql_file"])
        if not sql_file.is_absolute():
            # backend/ is the working dir in most deployments
            sql_file = Path.cwd() / sql_file

        if not sql_file.exists():
            self.stdout.write(self.style.ERROR(f"SQL dump not found: {sql_file}"))
            return

        raw = sql_file.read_bytes()
        text = _decode_dump_bytes(raw)
        rows = _parse_cards_from_dump(text)
        if not rows:
            self.stdout.write(self.style.ERROR("No cards found in dump (COPY public.cards ...)."))
            return

        created = 0
        updated = 0

        allowed_rarity = {c.value for c in Card.Rarity}

        for r in rows:
            rarity = r.rarity
            # Some dumps may contain Next.js style (N/R/SR/SSR). Normalize if needed.
            if rarity in {"N", "R", "SR", "SSR"}:
                rarity_map = {
                    "N": "common",
                    "R": "rare",
                    "SR": "seasonal",
                    "SSR": "special",
                }
                rarity = rarity_map.get(rarity, "common")
            if rarity not in allowed_rarity:
                rarity = "common"

            card, was_created = Card.objects.update_or_create(
                code=r.code,
                defaults={
                    "name": r.name,
                    "rarity": rarity,
                    "image_url": r.image_url or f"/uploads/cards/{r.code}.png",
                    "description": r.description,
                },
            )
            created += 1 if was_created else 0
            updated += 0 if was_created else 1

        self.stdout.write(self.style.SUCCESS(f"Done. created={created}, updated={updated}, total={Card.objects.count()}"))


