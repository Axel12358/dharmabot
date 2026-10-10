"""Smoke de imports: TODO módulo de core/ debe importar sin error, sin red.

Cubre regresiones como `requests` sin importar (NameError en runtime) que el
lint no siempre captura y que solo explotan al importar el módulo.
"""

import importlib
import pkgutil
import warnings

import core

SALTO_DOCUMENTADO = {
    "agente_coordinador": "requiere el paquete scrapers/ (repo legacy), no incluido aqui",
}


def test_paquete_core_no_vacio():
    nombres = [m.name for m in pkgutil.iter_modules(core.__path__) if not m.name.startswith("_")]
    assert len(nombres) >= 30, f"core/ casi vacio: solo {len(nombres)} modulos"


def test_todos_los_modulos_de_core_importan():
    warnings.filterwarnings("ignore")
    nombres = sorted(
        m.name for m in pkgutil.iter_modules(core.__path__) if not m.name.startswith("_")
    )
    fallas = []
    for n in nombres:
        if n in SALTO_DOCUMENTADO:
            continue
        try:
            importlib.import_module(f"core.{n}")
        except Exception as e:  # noqa: BLE001 — cualquier error de import es fallo
            fallas.append(f"core.{n}: {type(e).__name__}: {e}")
    assert not fallas, "Modulos que NO importan:\n" + "\n".join(fallas)


def test_saltos_documentados_siguen_existiendo():
    """Si un modulo con salto desaparece, limpiar el diccionario de saltos."""
    actuales = {m.name for m in pkgutil.iter_modules(core.__path__)}
    fantasma = SALTO_DOCUMENTADO.keys() - actuales
    assert not fantasma, f"Quitar del diccionario de saltos (ya no existen): {fantasma}"
