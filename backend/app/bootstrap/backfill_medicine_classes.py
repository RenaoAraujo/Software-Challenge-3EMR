"""Reclassifica itens legados de OS para o formato rico do catálogo real de produtos.

Antes de termos a planilha de produtos, OS aleatórias eram criadas com strings genéricas
como "Medicamento (teste) 1" ou "losartana #1".  Esta migração roda no startup de forma
idempotente e substitui cada item nesse formato antigo por um produto real sorteado do
catálogo (Planilha_Produtos_Atualizada).

Itens que já são dicts (formato novo) são preservados intactos.
"""

from __future__ import annotations

import json
import random
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import ServiceOrder
from app.services.product_catalog import catalog_size, random_products

# Padrão legacy: "Medicamento (teste) N" ou "princípio ativo #N"
_LEGACY_STRING_PATTERN = re.compile(
    r"^(?:Medicamento\s*\(teste\)\s*\d+|\S.*\s#\d+)$",
    re.IGNORECASE,
)


def _is_legacy_string(item: object) -> bool:
    return isinstance(item, str) and bool(_LEGACY_STRING_PATTERN.match(item.strip()))


def _needs_backfill(items: list) -> bool:
    return any(_is_legacy_string(x) for x in items)


def backfill_medicine_classes(db: Session) -> int:
    """Substitui itens legados por produtos reais do catálogo.

    Retorna a quantidade de OS atualizadas.
    """
    if catalog_size() == 0:
        return 0

    updated = 0
    stmt = select(ServiceOrder)
    orders = list(db.scalars(stmt).all())

    for o in orders:
        try:
            items = json.loads(o.medicines_json or "[]")
        except Exception:
            continue
        if not isinstance(items, list) or not _needs_backfill(items):
            continue

        rng = random.Random(f"emr-catalog::{o.os_code or o.id}")
        n_legacy = sum(1 for x in items if _is_legacy_string(x))
        real_products = random_products(n_legacy, rng=rng)

        new_items: list = []
        prod_idx = 0
        for x in items:
            if _is_legacy_string(x):
                new_items.append(real_products[prod_idx] if prod_idx < len(real_products) else x)
                prod_idx += 1
            else:
                new_items.append(x)

        o.medicines_json = json.dumps(new_items, ensure_ascii=False)
        db.add(o)
        updated += 1

    if updated:
        db.commit()
    return updated
