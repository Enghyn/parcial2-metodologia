"""TDD C-03 tarea 2.1 — núcleo de seguridad JWT (sin DB, `app.core.security`).

Cubre los escenarios del spec auth: hash bcrypt, round-trip de token con
claims mínimos, expiración configurable, token vencido, firma ajena y rol
fuera del catálogo (R9: sin email ni nombre en el payload; R2: sin tenant_id).
"""
import jwt as pyjwt
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.security import crear_access_token, decodificar_token, hash_password, verify_password

SECRETO = "secreto-de-test-de-mas-de-32-caracteres-config"


def settings_con(secret: str = SECRETO, expire_min: int = 720) -> Settings:
    return Settings(
        DATABASE_URL="postgresql+psycopg://u:p@localhost:5432/odonto_test",
        JWT_SECRET=secret,
        JWT_EXPIRE_MIN=expire_min,
    )


# --- hash de contraseñas (bcrypt, D3) ---


def test_hash_produce_formato_bcrypt_y_verifica() -> None:
    hash_generado = hash_password("admin123")
    assert hash_generado != "admin123"
    assert hash_generado.startswith("$2")  # formato bcrypt
    assert verify_password("admin123", hash_generado) is True


def test_verify_rechaza_password_distinta() -> None:
    hash_generado = hash_password("admin123")
    assert verify_password("otra-password", hash_generado) is False


def test_verify_con_hash_incorrecto_es_falso() -> None:
    assert verify_password("admin123", "hash-corrumpido") is False


# --- round-trip del access token (D5: claims mínimos sub/rol/iat/exp) ---


def test_roundtrip_token_devuelve_sub_y_rol() -> None:
    token = crear_access_token(
        sub="11111111-1111-1111-1111-111111111111", rol="admin", secret=SECRETO, expire_min=720
    )
    payload = decodificar_token(token, SECRETO)
    assert payload.sub == "11111111-1111-1111-1111-111111111111"
    assert payload.rol == "admin"
    assert payload.exp is not None


def test_payload_no_lleva_email_ni_nombre_ni_tenant() -> None:
    """R9: el token solo lleva sub/rol/iat/exp; R2: nunca tenant_id."""
    token = crear_access_token(
        sub="22222222-2222-2222-2222-222222222222", rol="recepcion", secret=SECRETO, expire_min=60
    )
    claims = pyjwt.decode(token, options={"verify_signature": False})
    assert set(claims) == {"sub", "rol", "iat", "exp"}


def test_token_con_exp_vencido_rechaza() -> None:
    token = crear_access_token(sub="abc", rol="admin", secret=SECRETO, expire_min=-1)
    with pytest.raises(pyjwt.ExpiredSignatureError):
        decodificar_token(token, SECRETO)


def test_token_firmado_con_otra_clave_rechaza() -> None:
    token = crear_access_token(sub="abc", rol="odontologo", secret=SECRETO, expire_min=60)
    with pytest.raises(pyjwt.InvalidSignatureError):
        decodificar_token(token, "otra-clave-de-secreto-totalmente-distinta")


def test_token_con_rol_fuera_del_catalogo_rechaza() -> None:
    """D5: rol fuera de ROLES_USUARIO no puede pasarse aunque la firma sea válida."""
    token = pyjwt.encode(
        {
            "sub": "abc",
            "rol": "superadmin",
            "iat": 1699000000,
            "exp": 1799999999,  # lejano a futuro: el rechazo debe venir del rol, no de exp
        },
        SECRETO,
        algorithm="HS256",
    )
    with pytest.raises(ValidationError):
        decodificar_token(token, SECRETO)


# --- expiración configurable vía settings (D5, spec auth) ---


def test_expiracion_configurable_usando_settings() -> None:
    """Spec: `JWT_EXPIRE_MIN = 720` → exp queda a exactamente 720 min de la emisión."""
    settings = settings_con(expire_min=720)
    token = crear_access_token(
        sub="33333333-3333-3333-3333-333333333333",
        rol="odontologo",
        secret=settings.jwt_secret,
        expire_min=settings.jwt_expire_min,
    )
    claims = pyjwt.decode(
        token, settings.jwt_secret, algorithms=["HS256"], options={"require": ["exp", "iat", "sub", "rol"]}
    )
    assert claims["exp"] - claims["iat"] == 720 * 60


def test_expiracion_distinta_cambia_el_delta_de_exp() -> None:
    token_corto = crear_access_token(sub="abc", rol="admin", secret=SECRETO, expire_min=60)
    token_largo = crear_access_token(sub="abc", rol="admin", secret=SECRETO, expire_min=720)
    c_corto = pyjwt.decode(token_corto, SECRETO, algorithms=["HS256"])
    c_largo = pyjwt.decode(token_largo, SECRETO, algorithms=["HS256"])
    assert c_largo["exp"] - c_largo["iat"] == 720 * 60
    assert c_corto["exp"] - c_corto["iat"] == 60 * 60
