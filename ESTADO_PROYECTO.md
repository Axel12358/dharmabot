# Dharmadhatu — Estado del Proyecto (compacto)

## Contexto global
Bot que scrapea eventos psytrance (RA, Goabase, Songkick, Facebook, Instagram) y los consolida en `eventos_encontrados.csv`. Los eventos se enriquecen con email/organizador vía triangulación. Regla de oro del proyecto: **sumar, nunca restar** eventos del CSV. Todo CSV-escritor DEBE usar `from core.csv_lock import csv_locked_rows` (read fresco bajo fcntl.flock).

## Procesos corriendo AHORA (verificar con `ps aux | grep -iE "python|loop|main"`)
- `loop_completar.py` (PID 1818) — loop de enriquecimiento. Es el proceso "bueno" que debe seguir corriendo.
- `main.py` (PID 16351) — bot principal. **CAUSA DEL TRUNCADO DEL CSV.** Se está decidiendo: pararlo y/o arreglarlo.
- `run_orquestador.py` (PID 15657) → importa `orquestar_scrapers` desde `core/orquestador.py` (nota: hay DOS archivos: `core/orquetrador.py` con typo "t", ya deshabilitado en `__main__`; el REAL es `core/orquestador.py` sin t, que usa csv_locked_rows, es correcto).
- `core/mcp_clasificar.py` (PID 1113) — MCP de clasificación.
- launchd: `~/Library/LaunchAgents/com.dharma.orquestador.plist` (RunAtLoad=true, KeepAlive=true, ThrottleInterval=300, corre `run_orquestador.sh`).

## Estado del CSV (CRÍTICO)
- Estado correcto: ~5,039 filas. **AHORA truncado a ~1,282** porque `main.py` lo sobrescribe.
- En `loop_completar.py`, `es_email_valido()` NO detecta "N/A" como inválido → el loop solo cuenta eventos con email vacío real (~141), no los N/A (~3,950). ESTO ES INTENCIONAL/OK: el loop enriquece los que de verdad faltan (RA principalmente).
- Restauración: `python3 loop_reclasificar_spam.py` (lee de `.bak_filtro_falsos`, criterio link+fecha+lugar+keyword psy en nombre/lugar/org = EVENTO; 412 ruido real descartado).
- Backups: `eventos_encontrados.csv.bak_filtro_falsos` (~5,272 filas), `.bak_antes_restaura`, `.bak_jeandupont`, `.bak_ra_integrate`.

## BUG DE main.py (por qué trunca el CSV)
`main.py` en su ciclo scrapea eventos nuevos, y luego:
- L169: `save_csv(eventos, "eventos_encontrados.csv")` (de `utils/helpers.py`) — re-lee SIN lock y re-escribe TODO el CSV → carrera con loop_completar.
- L191: `orquestar_scrapers(dry_run=False)` → escribe al CSV.
- L218: `completar_eventos_fb()`, L233: `completar_fb_externo()`, L250: `enriquecer_fb_og()` (solo si `enriquecer_fb_og` activo), L309: `ejecutar_agentes()`, L324: `supervisar_y_mejorar(CSV, aplicar_cambios=True)`.
Todos esos módulos escriben al CSV concurrentemente mientras el loop corre → truncado.

## PLAN ACORDADO (próximos pasos)
1. Parar `main.py` (kill PID si corre) → restaurar CSV (`python3 loop_reclasificar_spam.py`) → confirmar ~5,039 filas.
2. Arreglar `main.py` para que NO destruya el CSV: su `save_csv` debe leer bajo `csv_locked_rows` (como core/agente_coordinador.py L288-306) o desactivar la escritura de main.py y dejar solo al loop como enriquecedor.
3. Confirmar estabilidad: `wc -l eventos_encontrados.csv` durante 30-60 min debe quedarse en ~5,039.
4. Pendiente Qwen cleanup (del otro workstream): borrar `estrategia_qwen` de `scrapers/strategies.py` (~L117-168) y refs a `llm_local` en `scrapers/agents/__init__.py`. Verificar con `grep -rn "ollama|qwen|MODELO"`.

## Comandos útiles
- Estado loop: `grep -E "Iteración|Sin email" loop_completar_run.log | tail -3`
- Filas CSV: `python3 -c "import csv;print(sum(1 for _ in csv.DictReader(open('eventos_encontrados.csv'))))"`
- Sin email real: contar el CSV con email vacío (no N/A).
- Monitoreo 30min: loop con `sleep 1800` reportando iteración + filas (timeout >7200000).
- Restaurar: `python3 loop_reclasificar_spam.py`
- Loop: BATCH=40 por checkpoint, bloques rotativos por fuente (`bloque = iter % 3`: 0=RA, 1=FB matriz, 2=resto), Tor 1.2s, venue-first cada 5.

## Archivos clave
- `loop_completar.py` — enriquecedor, ya con fix indentación L865, BATCH 40, bloques por fuente.
- `core/csv_lock.py` — `csv_locked_rows` (flock). TODO escritor debe usarlo.
- `core/agente_coordinador.py` — ejemplo CORRECTO de escritura aditiva bajo lock (L288-306).
- `core/orquetrador.py` (typo) — `__main__` deshabilitado + prints DEBUG "DEBUG orquestador: conservo N filas".
- `core/orquestador.py` (real) — usa csv_locked_rows, correcto.
- `run_orquestador.py` — `from core.orquestador import orquestar_scrapers`.
- `loop_reclasificar_spam.py` — restauración.
- `config_modulos.json` — activa/desactiva módulos de main.py.