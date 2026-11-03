"""Seed idempotente de demostración (C-02)."""
import bcrypt
import pytest
from sqlalchemy.exc import OperationalError

import app.db.seed as seed_module
from app.db.seed import SeedPlan, SeedReport, apply_seed, build_seed_plan
from app.modules.admin.models import Usuario
from app.modules.agenda.models import Profesional, Sillon
from app.modules.clinica.models import Paciente


class FakeRepo:
    """Repositorio en memoria con la misma interfaz que el de SQLAlchemy."""

    def __init__(self) -> None:
        self.sillones: list[Sillon] = []
        self.usuarios: list[Usuario] = []
        self.profesionales: list[Profesional] = []
        self.pacientes: list[Paciente] = []

    def find_sillon(self, nombre: str) -> Sillon | None:
        return next((s for s in self.sillones if s.nombre == nombre), None)

    def find_usuario(self, email: str) -> Usuario | None:
        return next((u for u in self.usuarios if u.email.lower() == email.lower()), None)

    def find_profesional(self, matricula: str) -> Profesional | None:
        return next((p for p in self.profesionales if p.matricula == matricula), None)

    def find_paciente(self, dni: str) -> Paciente | None:
        return next((p for p in self.pacientes if p.dni == dni), None)

    def add(self, entidad: object) -> None:
        if isinstance(entidad, Sillon):
            self.sillones.append(entidad)
        elif isinstance(entidad, Usuario):
            self.usuarios.append(entidad)
        elif isinstance(entidad, Profesional):
            self.profesionales.append(entidad)
        elif isinstance(entidad, Paciente):
            self.pacientes.append(entidad)
        else:  # pragma: no cover - protege contra un plan mal armado
            raise TypeError(f"entidad no soportada: {type(entidad).__name__}")


def test_el_plan_tiene_los_conteos_del_enunciado() -> None:
    plan = build_seed_plan(rounds=4)
    assert len(plan.sillones) == 3
    assert len(plan.usuarios) == 4
    assert len(plan.profesionales) == 2
    assert len(plan.pacientes) == 2


def test_las_credenciales_son_hashes_bcrypt_validos() -> None:
    plan = build_seed_plan(rounds=4)
    admin = next(u for u in plan.usuarios if u["rol"] == "admin")
    assert admin["email"] == "admin@consultorio.com"
    assert bcrypt.checkpw(b"admin123", admin["password_hash"].encode())


def test_override_de_password_para_todas_las_cuentas() -> None:
    plan = build_seed_plan(default_password="unica-demo", rounds=4)
    for usuario in plan.usuarios:
        assert bcrypt.checkpw(b"unica-demo", usuario["password_hash"].encode())


def test_primera_carga_crea_todo() -> None:
    repo = FakeRepo()
    report = apply_seed(repo, build_seed_plan(rounds=4), app_env="test")
    assert report == SeedReport(sillones=3, usuarios=4, profesionales=2, pacientes=2)
    assert len(repo.sillones) == 3
    assert len(repo.usuarios) == 4
    assert len(repo.profesionales) == 2
    assert len(repo.pacientes) == 2


def test_segunda_carga_no_duplica() -> None:
    repo = FakeRepo()
    plan = build_seed_plan(rounds=4)
    apply_seed(repo, plan, app_env="test")
    report = apply_seed(repo, plan, app_env="test")

    assert report == SeedReport(sillones=0, usuarios=0, profesionales=0, pacientes=0)
    assert len(repo.sillones) == 3
    assert len(repo.usuarios) == 4
    assert len(repo.profesionales) == 2
    assert len(repo.pacientes) == 2


def test_base_parcialmente_poblada_solo_crea_lo_faltante() -> None:
    repo = FakeRepo()
    repo.pacientes.append(
        Paciente(nombre="María López", dni="30111222", telefono="1144556677")
    )
    report = apply_seed(repo, build_seed_plan(rounds=4), app_env="test")

    assert report.pacientes == 1
    assert len(repo.pacientes) == 2


def test_profesionales_quedan_vinculados_a_su_usuario() -> None:
    repo = FakeRepo()
    apply_seed(repo, build_seed_plan(rounds=4), app_env="test")

    emails = {u.email for u in repo.usuarios}
    vinculados = {p.usuario_id for p in repo.profesionales}
    assert len(vinculados) == 2
    assert all(p.usuario_id is not None for p in repo.profesionales)
    assert emails == {
        "admin@consultorio.com",
        "recepcion@consultorio.com",
        "dr.perez@consultorio.com",
        "dra.gomez@consultorio.com",
    }


def test_guarda_de_produccion_sin_force() -> None:
    with pytest.raises(RuntimeError, match="production"):
        apply_seed(FakeRepo(), build_seed_plan(rounds=4), app_env="production")


def test_guarda_de_produccion_con_force_permite_cargar() -> None:
    repo = FakeRepo()
    report = apply_seed(repo, build_seed_plan(rounds=4), app_env="production", force=True)
    assert report.usuarios == 4


class _SesionQueFalla:
    """Sesión falsa que falla al primer acceso a la base y registra el cierre."""

    def __init__(self) -> None:
        self.rolled = False
        self.closed = False

    def scalar(self, statement: object) -> object:
        raise OperationalError("SELECT 1", {}, Exception("sin conexión"))

    def add(self, entidad: object) -> None:
        pass

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        self.rolled = True

    def close(self) -> None:
        self.closed = True


def test_main_sin_base_devuelve_1_y_mensaje_claro(monkeypatch, capsys) -> None:
    def fabrica_que_falla():
        raise OperationalError("SELECT 1", {}, Exception("sin conexión"))

    monkeypatch.setattr(seed_module, "get_session_factory", fabrica_que_falla)
    monkeypatch.setattr(seed_module, "build_seed_plan", lambda **_: SeedPlan((), (), (), ()))

    assert seed_module.main([]) == 1
    assert "DATABASE_URL" in capsys.readouterr().err


def test_main_hace_rollback_y_cierra_si_falla_a_mitad(monkeypatch, capsys) -> None:
    sesion = _SesionQueFalla()
    monkeypatch.setattr(seed_module, "get_session_factory", lambda: lambda: sesion)
    monkeypatch.setattr(
        seed_module,
        "build_seed_plan",
        lambda **_: SeedPlan(({"nombre": "Sillón 1"},), (), (), ()),
    )

    assert seed_module.main([]) == 1
    assert sesion.rolled is True
    assert sesion.closed is True
    assert "DATABASE_URL" in capsys.readouterr().err
