"""Higiene del repo: anti-regresión de los bugs reales encontrados en Oct 2026.

1. Caracteres de control (volcados de terminal U+001B/[8D[K) en .py.
2. pyproject.toml debe seguir siendo TOML valido con metadatos saneados.
3. uv.lock debe existir (el CI de setup-uv lo exige).
4. Sin claves de diccionario duplicadas en literales de core/ (F601).
5. Regresion del typo de cooldown en tor_pool (bloqueado_desdes).
"""

import ast
from pathlib import Path

import tomllib

REPO = Path(__file__).resolve().parent.parent
CARACTERES_PROHIBIDOS = (
    set(range(0, 8)) | {11, 12} | set(range(14, 32))
)  # salvo \t(9) \n(10) \r(13)


def _archivos_py():
    for p in REPO.rglob("*.py"):
        partes = set(p.parts)
        if partes & {".venv", "venv", ".git", "__pycache__"}:
            continue
        yield p


def test_py_sin_caracteres_de_control():
    """Ningun .py debe contener ESC ni otros controles (dumps de terminal)."""
    culpables = []
    for p in _archivos_py():
        data = p.read_bytes()
        malos = sorted({b for b in data if b in CARACTERES_PROHIBIDOS})
        if malos:
            culpables.append(f"{p.relative_to(REPO)}: bytes {malos}")
    assert not culpables, "Archivos con caracteres de control:\n" + "\n".join(culpables)


def test_pyproject_toml_valido():
    pyproject = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    proj = pyproject["project"]
    assert proj["name"] == "dharmabot"
    assert isinstance(proj["dependencies"], list) and len(proj["dependencies"]) >= 8
    assert all(isinstance(d, str) and ">=" in d for d in proj["dependencies"])
    assert "dev" in proj["optional-dependencies"]


def test_uv_lock_existe_y_no_vacio():
    lock = REPO / "uv.lock"
    assert lock.exists(), "uv.lock falta: setup-uv(enable-cache) y uv sync lo necesitan"
    assert lock.stat().st_size > 100


def _claves_duplicadas_en(path: Path):
    """Literales de dict con clave constante repetida (mismo estilo F601 de ruff)."""
    arbol = ast.parse(path.read_text(encoding="utf-8"))
    out = []
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Dict):
            continue
        vistas = {}
        for k in nodo.keys:
            if isinstance(k, ast.Constant) and isinstance(k.value, (str, int)):
                if k.value in vistas:
                    out.append(f"{path.name}:{k.lineno}: clave {k.value!r} repetida")
                vistas[k.value] = k.lineno
    return out


def test_core_sin_claves_de_dict_duplicadas():
    fallas = []
    for p in sorted((REPO / "core").glob("*.py")):
        fallas.extend(_claves_duplicadas_en(p))
    assert not fallas, "Claves duplicadas en literales dict de core/:\n" + "\n".join(fallas)


def test_regresion_cooldown_tor_pool():
    """El typo 'bloqueado_desdes' en la comparacion anulaba el cooldown (Oct 2026)."""
    src = (REPO / "core" / "tor_pool.py").read_text(encoding="utf-8")
    assert "- bloqueado_desdes <" not in src, "typo 'bloqueado_desdes' volvio a la comparacion"
    assert "- bloqueado_desde <" in src, "falta la comparacion correcta del cooldown"
