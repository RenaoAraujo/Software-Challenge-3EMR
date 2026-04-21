"""Motivos pré-definidos para cancelamento de OS (código estável + texto para exibição/relatório).

Códigos atuais usam prefixo CC- (cancelamento) para leitura em relatórios e auditoria.
Códigos antigos continuam reconhecidos só para exibição de registos já gravados.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

OUTROS_CODE: Final = "OUTROS"


@dataclass(frozen=True)
class CancellationReason:
    code: str
    label: str


# Ordem = ordem sugerida no modal (Outros por último).
CANCELLATION_REASONS: tuple[CancellationReason, ...] = (
    CancellationReason("CC-ESTOQUE", "Falta de estoque no depósito"),
    CancellationReason("CC-MED-AUSENTE", "Medicamento ausente na caixa"),
    CancellationReason("CC-PEDIDO-CLIENTE", "Cancelamento solicitado pelo cliente"),
    CancellationReason("CC-ERRO-OPER", "Erro operacional ou equívoco na separação"),
    CancellationReason("CC-EQUIPAMENTO", "Problema no equipamento ou no separador"),
    CancellationReason("CC-PRIOR-OS", "Prioridade para outra ordem de serviço"),
    CancellationReason(OUTROS_CODE, "Outros (especificar)"),
)

# Registos antigos (antes do prefixo CC-) — só para label em relatórios/histórico.
_LEGACY_CODE_LABELS: dict[str, str] = {
    "FALTA_ESTOQUE": "Falta de estoque no depósito",
    "MEDICAMENTO_AUSENTE": "Medicamento ausente na caixa",
    "PEDIDO_CLIENTE": "Cancelamento solicitado pelo cliente",
    "ERRO_OPERACIONAL": "Erro operacional / equívoco na seleção",
    "PROBLEMA_EQUIPAMENTO": "Problema no equipamento / separador",
    "PRIORIDADE_OUTRA_OS": "Prioridade para outra ordem de serviço",
}


def allowed_cancel_codes() -> frozenset[str]:
    return frozenset(r.code for r in CANCELLATION_REASONS)


def label_for_cancel_code(code: str) -> str | None:
    c = (code or "").strip()
    if not c:
        return None
    for r in CANCELLATION_REASONS:
        if r.code == c:
            return r.label
    return _LEGACY_CODE_LABELS.get(c)


def public_reason_list() -> list[dict[str, str]]:
    """Para API GET: lista de {code, label}."""
    return [{"code": r.code, "label": r.label} for r in CANCELLATION_REASONS]
