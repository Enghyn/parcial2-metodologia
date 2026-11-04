"""TDD C-03 tarea 3.1 — servicio de autenticación con repositorio fake (D8).

`autenticar_usuario` depende de un Protocol mínimo `find_by_email(email) ->
Usuario | None`: con un fake en memoria se cubren usuario activo, dado de
baja (`activo=False`, R13/lógica), password mal, email no registrado y
normalización de email (trim + minúsculas) ANTES de la búsqueda.
"""
from uuid import uuid4

import bcrypt

from app.modules.admin.models import Usuario
from app.modules.auth import service


class FakeBuscadorUsuarios:
    """Repositorio en memoria con la interfaz mínima del Protocol UsuarioFinder."""

    def __init__(self, usuarios: list[Usuario]) -> None:
        self.usuarios = usuarios
        self.emails_buscados: list[str] = []

    def find_by_email(self, email: str) -> Usuario | None:
        self.emails_buscados.append(email)
        return next((u for u in self.usuarios if u.email == email), None)


def usuario_en_memoria(
    email: str = "admin@consultorio.com",
    password: str = "admin123",
    rol: str = "admin",
    activo: bool = True,
) -> Usuario:
    return Usuario(
        id=uuid4(),
        nombre="Administrador",
        email=email,
        password_hash=bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=4)).decode("utf-8"),
        rol=rol,
        activo=activo,
    )


def test_credenciales_correctas_devuelven_usuario() -> None:
    usuario = usuario_en_memoria()
    buscador = FakeBuscadorUsuarios([usuario])

    resuelto = service.autenticar_usuario(buscador, "admin@consultorio.com", "admin123")

    assert resuelto is usuario


def test_password_mal_devuelve_none() -> None:
    buscador = FakeBuscadorUsuarios([usuario_en_memoria()])

    assert service.autenticar_usuario(buscador, "admin@consultorio.com", "password-incorrecto") is None


def test_email_no_registrado_devuelve_none() -> None:
    buscador = FakeBuscadorUsuarios([usuario_en_memoria()])

    assert service.autenticar_usuario(buscador, "nadie@consultorio.com", "admin123") is None


def test_usuario_dado_de_baja_devuelve_none() -> None:
    """R13/baja lógica: `activo=False` no loguea aunque la contraseña sea correcta."""
    buscador = FakeBuscadorUsuarios([usuario_en_memoria(activo=False)])

    assert service.autenticar_usuario(buscador, "admin@consultorio.com", "admin123") is None


def test_email_se_normaliza_antes_de_buscar() -> None:
    """Spec: `Admin@Consultorio.com ` = forma canónica (normaliza trim + lower)."""
    usuario = usuario_en_memoria()
    buscador = FakeBuscadorUsuarios([usuario])

    resuelto = service.autenticar_usuario(buscador, "  Admin@Consultorio.com ", "admin123")

    assert resuelto is usuario
    assert buscador.emails_buscados == ["admin@consultorio.com"], "debe buscar con el email normalizado"


def test_normalizacion_no_salta_verificacion_de_password() -> None:
    buscador = FakeBuscadorUsuarios([usuario_en_memoria()])

    assert service.autenticar_usuario(buscador, "  ADMIN@Consultorio.com ", "password-incorrecto") is None
