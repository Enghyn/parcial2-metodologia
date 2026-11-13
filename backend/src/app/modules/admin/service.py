"""Servicio admin (C-19)."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.modules.admin.models import Usuario
from app.modules.admin.schemas import ProfesionalCreate, SillonCreate, UsuarioCreate
from app.modules.agenda.models import Profesional, Sillon


class AdminService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- Usuarios ---
    def crear_usuario(self, datos: UsuarioCreate) -> Usuario:
        u = Usuario(
            nombre=datos.nombre,
            email=datos.email,
            password_hash=hash_password(datos.password),
            rol=datos.rol,
            activo=datos.activo,
        )
        self.db.add(u)
        self.db.commit()
        self.db.refresh(u)
        return u

    def listar_usuarios(self) -> list[Usuario]:
        return self.db.query(Usuario).all()

    def desactivar_usuario(self, usuario_id: UUID) -> Usuario:
        u = self.db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if u is None:
            raise ValueError("not_found")
        if u.rol == "admin" and u.activo:
            activos = self.db.query(Usuario).filter(Usuario.rol == "admin", Usuario.activo.is_(True)).count()
            if activos <= 1:
                raise ValueError("ultimo_admin")
        u.activo = False
        self.db.commit()
        self.db.refresh(u)
        return u

    # --- Sillones ---
    def crear_sillon(self, datos: SillonCreate) -> Sillon:
        s = Sillon(nombre=datos.nombre, descripcion=datos.descripcion, activo=datos.activo)
        self.db.add(s)
        self.db.commit()
        self.db.refresh(s)
        return s

    def listar_sillones(self) -> list[Sillon]:
        return self.db.query(Sillon).all()

    def baja_sillon(self, sillon_id: UUID) -> Sillon:
        s = self.db.query(Sillon).filter(Sillon.id == sillon_id).first()
        if s is None:
            raise ValueError("not_found")
        s.activo = False
        from datetime import datetime, timezone

        s.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(s)
        return s

    # --- Profesionales ---
    def crear_profesional(self, datos: ProfesionalCreate) -> Profesional:
        p = Profesional(
            nombre=datos.nombre,
            matricula=datos.matricula,
            especialidad=datos.especialidad,
            duracion_default_min=datos.duracion_default_min,
            usuario_id=datos.usuario_id,
            activo=datos.activo,
        )
        self.db.add(p)
        self.db.commit()
        self.db.refresh(p)
        return p

    def listar_profesionales(self) -> list[Profesional]:
        return self.db.query(Profesional).all()

    def baja_profesional(self, profesional_id: UUID) -> Profesional:
        p = self.db.query(Profesional).filter(Profesional.id == profesional_id).first()
        if p is None:
            raise ValueError("not_found")
        p.activo = False
        from datetime import datetime, timezone

        p.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(p)
        return p