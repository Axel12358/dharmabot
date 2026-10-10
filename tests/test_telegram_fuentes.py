"""Logica pura de canales Telegram: limpieza de HTML y filtro de eventos."""

from core.telegram_fuentes import _es_evento, _limpiar


def test_limpiar_html():
    html = "<b>Ozora</b> &amp; friends &quot;x&quot; &#39;y&#39;"
    assert _limpiar(html) == "Ozora & friends \"x\" 'y'"


def test_limpiar_colapsa_espacios():
    assert _limpiar("  a\n\n  b\tc  ") == "a b c"


def test_es_evento_con_keyword_y_anio():
    assert _es_evento("Shankra Festival 2026 — tickets a la venta")
    assert _es_evento("Open air party 2026-03-14 en la playa")


def test_es_evento_rechaza_ruido():
    assert not _es_evento("Festival tickets sold out")  # keyword sin año
    assert not _es_evento("2026 fue un gran año")  # año sin keyword
    assert not _es_evento("happy birthday!")  # nada
