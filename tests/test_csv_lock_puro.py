"""csv_lock: funciones puras + fusion aditiva sobre un CSV temporal (sin red).

escribir_fusionando es el contrato SUMA-nunca-resta del pipeline: rellena
huecos N/A, anade filas nuevas y NUNCA borra ni pisa filas ajenas.
"""

import csv

from core.csv_lock import _clave_fila, _na_valor, escribir_fusionando


def test_na_valor():
    for v in (None, "", "  ", "n/a", "NA ", "None", "null", "-", "?"):
        assert _na_valor(v) is True, v
    for v in ("x", "0", "España"):
        assert _na_valor(v) is False, v


def test_clave_fila_preferencia_link():
    assert _clave_fila({"link": "HTTPS://X.COM/E1", "nombre": "A", "fecha": "2026"}) == (
        "L",
        "https://x.com/e1",
    )
    # link basura -> cae a nombre|fecha
    assert _clave_fila({"link": "n/a", "nombre": " A ", "fecha": " 2026-01-01 "}) == (
        "N",
        "a",
        "2026-01-01",
    )


def _escribir_csv(path, filas):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["nombre", "fecha", "email", "link"])
        w.writeheader()
        w.writerows(filas)


def _leer_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_escribir_fusionando_suma_sin_pisar(tmp_path):
    csv_path = tmp_path / "t.csv"
    _escribir_csv(
        csv_path,
        [
            {"nombre": "Ozora", "fecha": "2026-07-01", "email": "", "link": "https://x.com/1"},
            {
                "nombre": "Ajena",
                "fecha": "2026-08-01",
                "email": "keep@me.com",
                "link": "https://x.com/2",
            },
        ],
    )
    res = escribir_fusionando(
        csv_path,
        [
            {
                "nombre": "Ozora",
                "fecha": "2026-07-01",
                "email": "info@ozora.com",
                "link": "https://x.com/1",
            },
            {
                "nombre": "Nueva",
                "fecha": "2026-09-01",
                "email": "n@n.com",
                "link": "https://x.com/3",
            },
        ],
    )
    filas = _leer_csv(csv_path)
    por_link = {r["link"]: r for r in filas}
    assert res == {"fusionadas": 3, "agregadas": 1}
    assert por_link["https://x.com/1"]["email"] == "info@ozora.com"  # relleno N/A
    assert por_link["https://x.com/2"]["email"] == "keep@me.com"  # fila ajena intacta
    assert por_link["https://x.com/3"]["nombre"] == "Nueva"  # fila anadida


def test_escribir_fusionando_no_pisa_valor_existente(tmp_path):
    csv_path = tmp_path / "t.csv"
    _escribir_csv(
        csv_path,
        [
            {
                "nombre": "Ozora",
                "fecha": "2026-07-01",
                "email": "original@x.com",
                "link": "https://x.com/1",
            }
        ],
    )
    escribir_fusionando(
        csv_path,
        [
            {
                "nombre": "Ozora",
                "fecha": "2026-07-01",
                "email": "inventado@x.com",
                "link": "https://x.com/1",
            }
        ],
    )
    assert _leer_csv(csv_path)[0]["email"] == "original@x.com"
