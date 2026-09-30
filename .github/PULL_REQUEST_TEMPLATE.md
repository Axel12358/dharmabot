## Descripción

<!-- Resumen del cambio y motivación. Incluye issue relacionado si existe. -->

## Cambios

- [ ] Funcionalidad implementada
- [ ] Documentación actualizada (si aplica)
- [ ] `requirements.txt`/`pyproject.toml` actualizado (si aplica)

## Verificación

- [ ] No rompe otros módulos de `core/` (imports y flujo intactos).
- [ ] **No añade credenciales**, URLs privadas ni IPs reales al código versionado.
- [ ] Si escribe datos: usa `core/csv_lock.csv_locked_rows()` (lock + atómica).
- [ ] Si es red: sale por Tor (`socks5h://127.0.0.1:9050`).
- [ ] Lint limpio: `make lint` (ruff).

## Pruebas

<!-- Comandos ejecutados y resultados. -->

```bash
# algo como:
python -c "import core.csv_lock"
```

## Notas

<!-- Contexto adicional, capturas, trades-offs. -->