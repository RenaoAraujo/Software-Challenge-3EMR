import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

# Par fixo para testes manuais; criado na subida se ainda não existir (além do seed inicial).
_TEST_USER = "teste"
_TEST_PASSWORD = "123456"

from app.config import settings
from app.models.entities import Robot, RobotStatus, ServiceOrder, ServiceOrderStatus, User
from app.services.auth_service import AuthService


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


def seed_default_user(db: Session) -> None:
    """Cria usuário inicial quando não há contas (credenciais via EMR_AUTH_DEFAULT_* / config)."""
    n = db.scalar(select(func.count()).select_from(User))
    if n and n > 0:
        return
    username = settings.auth_default_username.strip().lower()
    if not username:
        return
    pwd_hash = AuthService.hash_password(settings.auth_default_password)
    db.add(User(username=username, password_hash=pwd_hash, is_admin=False))
    db.commit()


def ensure_common_test_user(db: Session) -> None:
    """Garante o usuário de teste comum (mesmo que o banco já tenha outro login inicial)."""
    uname = _TEST_USER.strip().lower()
    exists = db.scalar(select(User.id).where(User.username == uname))
    if exists is not None:
        return
    db.add(
        User(
            username=uname,
            password_hash=AuthService.hash_password(_TEST_PASSWORD),
            is_admin=False,
        )
    )
    db.commit()


def ensure_admin_user(db: Session) -> None:
    """Garante usuário administrador (aba Logs). Credenciais: EMR_ADMIN_USERNAME / EMR_ADMIN_PASSWORD."""
    uname = (settings.admin_username or "").strip().lower()
    if not uname:
        return
    pwd = settings.admin_password or ""
    if not pwd:
        return
    h = AuthService.hash_password(pwd)
    existing = db.scalar(select(User.id).where(User.username == uname))
    if existing is None:
        db.add(User(username=uname, password_hash=h, is_admin=True))
        db.commit()
        return
    user = db.get(User, existing)
    if user is not None and not user.is_admin:
        user.is_admin = True
        db.add(user)
        db.commit()
