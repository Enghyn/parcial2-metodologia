"""Seed idempotente de demostración (C-02 core-models-seed).

El plan de datos es puro y determinista; la aplicación resuelve cada entidad
por su clave natural y crea solo lo que falta. El comando es explícito y no se
engancha al arranque de la aplicación.
"""
from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

import bcrypt
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import registry  # noqa: F401  (registra todas las tablas antes de sembrar)
from app.db.session import get_session_factory
from app.modules.admin.models import Usuario
from app.modules.agenda.models import Profesional, Sillon
from app.modules.clinica.models import Paciente


@dataclass(frozen=True)
class SeedPlan:
    sillones: tuple[dict[str, object], ...]
    usuarios: tuple[dict[str, object], ...]
    profesionales: tuple[dict[str, object], ...]
    pacientes: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class SeedReport:
    sillones: int = 0
    usuarios: int = 0
    profesionales: int = 0
    pacientes: int = 0

    @property
    def total(self) -> int:
        return self.sillones + self.usuarios + self.profesionales + self.pacientes


class SeedRepository(Protocol):
    def find_sillon(self, nombre: str) -> Sillon | None: ...

    def find_usuario(self, email: str) -> Usuario | None: ...

    def find_profesional(self, matricula: str) -> Profesional | None: ...

    def find_paciente(self, dni: str) -> Paciente | None: ...

    def add(self, entidad: object) -> None: ...


class SqlAlchemySeedRepository:
    """Implementación real del repositorio del seed sobre una sesión SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def find_sillon(self, nombre: str) -> Sillon | None:
        return self.session.scalar(select(Sillon).where(Sillon.nombre == nombre))

    def find_usuario(self, email: str) -> Usuario | None:
        return self.session.scalar(
            select(Usuario).where(func.lower(Usuario.email) == email.lower())
        )

    def find_profesional(self, matricula: str) -> Profesional | None:
        return self.session.scalar(select(Profesional).where(Profesional.matricula == matricula))

    def find_paciente(self, dni: str) -> Paciente | None:
        return self.session.scalar(select(Paciente).where(Paciente.dni == dni))

    def add(self, entidad: object) -> None:
        self.session.add(entidad)


def _hash_password(password: str, rounds: int) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=rounds)).decode("utf-8")


def build_seed_plan(default_password: str | None = None, rounds: int = 12) -> SeedPlan:
    """Plan determinista: 3 sillones, 4 usuarios, 2 profesionales y 2 pacientes."""
    credenciales = (
        ("Administrador", "admin@consultorio.com", "admin", "admin123"),
        ("Recepcionista", "recepcion@consultorio.com", "recepcion", "recepcion123"),
        ("Dr. Pérez", "dr.perez@consultorio.com", "odontologo", "odontologo123"),
        ("Dra. Gómez", "dra.gomez@consultorio.com", "odontologo", "odontologo123"),
    )
    usuarios = tuple(
        {
            "nombre": nombre,
            "email": email,
            "password_hash": _hash_password(default_password or password, rounds),
            "rol": rol,
            "activo": True,
        }
        for nombre, email, rol, password in credenciales
    )

    return SeedPlan(
        sillones=(
            {"nombre": "Sillón 1", "descripcion": "Box Principal", "activo": True},
            {"nombre": "Sillón 2", "descripcion": "Box Secundario", "activo": True},
            {"nombre": "Sillón 3", "descripcion": "Box Quirúrgico / Endodoncia", "activo": True},
        ),
        usuarios=usuarios,
        profesionales=(
            {
                "usuario_email": "dr.perez@consultorio.com",
                "nombre": "Dr. Pérez",
                "matricula": "MP-1001",
                "especialidad": "Odontología General",
                "duracion_default_min": 30,
                "activo": True,
            },
            {
                "usuario_email": "dra.gomez@consultorio.com",
                "nombre": "Dra. Gómez",
                "matricula": "MP-1002",
                "especialidad": "Ortodoncia",
                "duracion_default_min": 45,
                "activo": True,
            },
        ),
        pacientes=(
            {
                "nombre": "María López",
                "dni": "30111222",
                "telefono": "1144556677",
                "email": "maria.lopez@example.com",
                "obra_social": "OSDE",
                "nro_afiliado": "12345",
                "activo": True,
            },
            {
                "nombre": "Juan Pérez",
                "dni": "27999888",
                "telefono": "1155667788",
                "email": None,
                "obra_social": None,
                "nro_afiliado": None,
                "activo": True,
            },
        ),
    )


def apply_seed(
    repo: SeedRepository,
    plan: SeedPlan,
    *,
    app_env: str = "local",
    force: bool = False,
) -> SeedReport:
    """Aplica el plan sin duplicar: resuelve por clave natural y crea lo faltante."""
    if app_env == "production" and not force:
        raise RuntimeError(
            "Seed bloqueado con APP_ENV=production; usá --force si la carga es intencional"
        )

    creados = {"sillones": 0, "usuarios": 0, "profesionales": 0, "pacientes": 0}

    for datos in plan.sillones:
        if repo.find_sillon(str(datos["nombre"])) is None:
            repo.add(Sillon(id=uuid4(), **datos))
            creados["sillones"] += 1

    usuarios_por_email: dict[str, Usuario] = {}
    for datos in plan.usuarios:
        email = str(datos["email"])
        usuario = repo.find_usuario(email)
        if usuario is None:
            usuario = Usuario(id=uuid4(), **datos)
            repo.add(usuario)
            creados["usuarios"] += 1
        usuarios_por_email[email.lower()] = usuario

    for datos in plan.profesionales:
        if repo.find_profesional(str(datos["matricula"])) is None:
            info = dict(datos)
            email = str(info.pop("usuario_email"))
            usuario = usuarios_por_email.get(email.lower())
            if usuario is None:
                raise RuntimeError(f"El plan referencia un usuario inexistente: {email}")
            repo.add(Profesional(id=uuid4(), usuario_id=usuario.id, **info))
            creados["profesionales"] += 1

    for datos in plan.pacientes:
        if repo.find_paciente(str(datos["dni"])) is None:
            repo.add(Paciente(id=uuid4(), **datos))
            creados["pacientes"] += 1

    return SeedReport(**creados)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Carga idempotente de datos de demostración")
    parser.add_argument(
        "--force", action="store_true", help="Permite ejecutar con APP_ENV=production"
    )
    args = parser.parse_args(argv)

    settings = get_settings()
    plan = build_seed_plan(default_password=os.environ.get("SEED_DEFAULT_PASSWORD"))
    session = None
    try:
        session = get_session_factory()()
        report = apply_seed(
            SqlAlchemySeedRepository(session),
            plan,
            app_env=settings.app_env,
            force=args.force,
        )
        session.commit()
    except SQLAlchemyError as exc:
        if session is not None:
            session.rollback()
        print(
            "Seed falló: no se pudo conectar o escribir en la base "
            f"({type(exc).__name__}). Verificá DATABASE_URL y ejecutá "
            "'alembic upgrade head'.",
            file=sys.stderr,
        )
        return 1
    except Exception:
        if session is not None:
            session.rollback()
        raise
    finally:
        if session is not None:
            session.close()

    print(
        "Seed OK: "
        f"{report.total} registros creados "
        f"({report.sillones} sillones, {report.usuarios} usuarios, "
        f"{report.profesionales} profesionales, {report.pacientes} pacientes)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
