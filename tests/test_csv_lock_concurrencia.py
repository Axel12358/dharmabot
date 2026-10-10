"""Carrera real de locks: dos hilos escribiendo el MISMO CSV bajo flock.

Si alguien quita o rompe el flock de csv_locked_rows, las escrituras se pisan
y se pierden filas — este test lo detecta. El contrato es: la union de todos
los escritores SOBREVIVE siempre.
"""

import csv
import threading

from core.csv_lock import escribir_fusionando

CAMPOS = ["nombre", "fecha", "email", "link"]


def _init(path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        w.writerow(
            {"nombre": "base", "fecha": "2026-01-01", "email": "", "link": "https://x.com/base"}
        )


def _leer(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_dos_hilos_concurrentes_no_pierden_filas(tmp_path):
    csv_path = tmp_path / "carrera.csv"
    _init(csv_path)
    errores = []

    def writer(tag):
        try:
            for i in range(5):
                escribir_fusionando(
                    csv_path,
                    [
                        {
                            "nombre": f"{tag}{i}",
                            "fecha": "2026-07-01",
                            "email": f"{tag}{i}@x.com",
                            "link": f"https://x.com/{tag}{i}",
                        }
                    ],
                    timeout=30,
                )
        except Exception as e:  # noqa: BLE001
            errores.append(f"{tag}: {type(e).__name__}: {e}")

    hilos = [
        threading.Thread(target=writer, args=("A",)),
        threading.Thread(target=writer, args=("B",)),
    ]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(timeout=60)
        assert not h.is_alive(), "writer colgado: lock no se libera"

    assert not errores, f" excepciones en escritores concurrentes: {errores}"
    filas = _leer(csv_path)
    links = [r["link"] for r in filas]
    assert len(links) == len(set(links)), "filas duplicadas"
    esperados = {"https://x.com/base"} | {f"https://x.com/{t}{i}" for t in "AB" for i in range(5)}
    assert set(links) == esperados, f"filas perdidas: {esperados - set(links)}"
    assert filas[0]["nombre"] == "base"  # la base no se toca
