import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import Robot, RobotStatus, ServiceOrder, ServiceOrderStatus


def seed_if_empty(db: Session) -> None:
    count = db.scalar(select(func.count()).select_from(Robot))
    if count and count > 0:
        return

    now = datetime.now(UTC)

    orders = [
        ServiceOrder(
            os_code="OS-2026-0142",
            description="Separação — Cardiologia (lote 88-B)",
            client_name="Hospital São Lucas — Cardiologia",
            expected_units=850,
            status=ServiceOrderStatus.IN_PROGRESS.value,
            medicines_json=json.dumps(
                [
                    "Losartana 50 mg — 120 comp.",
                    "Atorvastatina 20 mg — 90 comp.",
                    "AAS 100 mg — 60 comp.",
                    "Clopidogrel 75 mg — 30 comp.",
                    "Carvedilol 12,5 mg — 60 comp.",
                ],
                ensure_ascii=False,
            ),
        ),
        ServiceOrder(
            os_code="OS-2026-0143",
            description="Separação — Oncologia pediátrica",
            client_name="Instituto da Criança",
            expected_units=420,
            status=ServiceOrderStatus.PENDING.value,
            medicines_json=json.dumps(
                [
                    "Ondansetrona 4 mg/ml — 6 ampolas",
                    "Dexametasona 4 mg — 20 comp.",
                ],
                ensure_ascii=False,
            ),
        ),
        ServiceOrder(
            os_code="OS-2026-0144",
            description="Reposição UTI — antibióticos",
            client_name="Rede Mista de Saúde — UTI Central",
            expected_units=1200,
            status=ServiceOrderStatus.PENDING.value,
            medicines_json=json.dumps(
                [
                    "Piperacilina + Tazobactam 4,5 g — 40 frascos",
                    "Meropeném 1 g — 24 frascos",
                    "Vancomicina 500 mg — 36 frascos",
                ],
                ensure_ascii=False,
            ),
        ),
    ]
    db.add_all(orders)
    db.flush()

    robots = [
        Robot(
            code="RB-ALFA",
            name="Separador Alfa",
            location="Centro de dispensação — Sala 1",
            model="MedPick X1",
            specifications=(
                "Braço6 eixos, câmera de visão 12 MP, leitor de código de barras 2D, "
                "gavetas refrigeradas 2–8 °C, throughput nominal480 un/h, certificação GMP."
            ),
            max_units_per_hour=480,
            status=RobotStatus.RUNNING.value,
            current_order_id=orders[0].id,
            job_started_at=now - timedelta(minutes=37, seconds=12),
            units_separated=312,
        ),
        Robot(
            code="RB-BETA",
            name="Separador Beta",
            location="Centro de dispensação — Sala 2",
            model="PharmaSort Pro",
            specifications=(
                "Dupla estação, pesagem dinâmica ±2 mg, interface OPC-UA, "
                "capacidade 600 un/h em modo padrão."
            ),
            max_units_per_hour=600,
            status=RobotStatus.IDLE.value,
            current_order_id=None,
            job_started_at=None,
            units_separated=0,
        ),
        Robot(
            code="RB-GAMA",
            name="Separador Gama",
            location="Almoxarifado — doca B",
            model="MedPick X1",
            specifications="Mesma linha Alfa; reserva para pico de demanda.",
            max_units_per_hour=480,
            status=RobotStatus.MAINTENANCE.value,
            current_order_id=None,
            job_started_at=None,
            units_separated=0,
        ),
    ]
    db.add_all(robots)
    db.commit()
