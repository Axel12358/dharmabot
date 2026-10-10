"""Funciones puras de completar_na: normalizacion de paises y deteccion de N/A."""

from core.completar_na import NORMALIZACION_PAISES, _na, _norm


def test_na_variantes_comunes():
    for v in (None, "", "   ", "n/a", " N/A ", "na", "None", "null", "-", "?"):
        assert _na(v) is True, f"_na({v!r}) deberia ser True"


def test_na_valores_reales_no_son_na():
    for v in ("psytrance", "0", "España", "info@x.com"):
        assert _na(v) is False, f"_na({v!r}) deberia ser False"


def test_norm_elimina_ruido():
    # comportamiento documentado: BORRA acentos/ñ (no translitera) y colapsa espacios
    assert _norm("  EspaÑa!! ") == "espaa"
    assert _norm("país bajos") == "pas bajos"
    assert _norm(None) == ""


def test_normalizacion_paises_mapeos_clave():
    assert NORMALIZACION_PAISES["spain"] == "España"
    assert NORMALIZACION_PAISES["españa"] == "España"
    assert NORMALIZACION_PAISES["holanda"] == "Países Bajos"
    assert NORMALIZACION_PAISES["dutch"] == "Países Bajos"
    assert NORMALIZACION_PAISES["germany"] == "Alemania"
    assert NORMALIZACION_PAISES["brazil"] == "Brasil"


def test_normalizacion_paises_invariantes():
    assert len(NORMALIZACION_PAISES) >= 40, "el diccionario se vacio o redujo demasiado"
    for k, v in NORMALIZACION_PAISES.items():
        assert k == k.strip().lower() and k, f"clave mal formada: {k!r}"
        assert v.strip() and v == v.strip(), f"valor mal formado: {v!r}"
    # sin cadenas de doble mapeo: normalizar un valor canonico lo deja igual
    # (el consumidor busca con .lower(), ver loop_completar._norm_pais)
    for v in set(NORMALIZACION_PAISES.values()):
        assert NORMALIZACION_PAISES.get(v.lower(), v) == v, f"cadena de mapeo en {v!r}"
