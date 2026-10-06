"""Tests puros (sin red) para core.fecha_parse."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.fecha_parse import parse_fecha


def test_iso_directo():
    assert parse_fecha("2026-03-14") == "2026-03-14"


def test_iso_fecha_invalida_ignorada():
    assert parse_fecha("xx 2026-13-40 yy") is None


def test_guion_formato_mes_texto_es():
    assert parse_fecha("14 de marzo de 2026") == "2026-03-14"


def test_orden_invertido_mes_dia():
    assert parse_fecha("March 14, 2026") == "2026-03-14"


def test_dia_mes_texto_con_sufijo_en():
    assert parse_fecha("14th March 2026") == "2026-03-14"


def test_guion_fallback_anio():
    assert parse_fecha("15 de junio", fallback_year="2026") == "2026-06-15"


def test_guion_fallback_fuera_de_rango():
    assert parse_fecha("15 de junio", fallback_year="1999") is None


def test_fecha_vacia():
    assert parse_fecha(None) is None
    assert parse_fecha("") is None


def test_guion_doodle_extra():
    assert parse_fecha("Sep 2026") is None


def test_guion_sin_anio_sin_fallback():
    assert parse_fecha("22 de julio") is None