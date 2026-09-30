# Plan Búsqueda Amplia — Matriz Subgéneros × Ciudades × Años

**Objetivo:** pasar de 46 ciudades × 14 subgéneros × 2 años (1,288 combos) a **120 ciudades × 34 sinónimos × 4 años × 8 tipos** (~130k combos teóricos) explorados de forma inteligente sin saturar Tor ni generar ruido.

## 1. Diagnóstico actual (2-sep-2026)

- CSV: 1,701 eventos, 74 países, top: Alemania 357, España 327, Países Bajos 176, Francia 167, UK 152.
- 46 ciudades en `config_loop.json:4-15` (lotes 16/25/34/46). Cubre solo capitales europeas + 10 globales.
- 14 subgéneros canónicos en `event_extractor.py:189` (SUBGENEROS_BASE) pero 34 sinónimos reales en `SINONIMOS:146` (dark, prog, hi-tech, etc. no se usan en dorks).
- SERP: `buscar_serp_fb()` genera `site:facebook.com/events {sub} {tipo} {ciudad} {año}` solo con 4 tipos (festival/gathering/party/open air) y 2 años (2026/27).
- Scrapers directos (edmdance, setline, etc.) solo visitan `/genre/psytrance` — no iteran por subgénero.
- `no_psy`: 483 (28%) y `N/A` 526 (31%) — 59% sin psytrance confirmado → matriz actual no filtra bien antes de SERP.

## 2. Matriz propuesta

| Eje | Actual | Propuesto | Fuente |
|-----|--------|-----------|--------|
| **Ciudades** | 46 | **120** | +74 hubs psy reales (ver §3) |
| **Subgéneros (queries)** | 14 | **34** | Todos los SINONIMOS + 14 base |
| **Años** | 2 (26/27) | **4** (25-28) | Cubre early bird + preventa |
| **Tipos** | 4 | **8** | festival, gathering, open air, party, rave, ceremony, ritual, celebration |
| **Combos teóricos** | 1,288 | ~130k | No se ejecutan todos — sampling inteligente §4 |

## 3. 74 ciudades nuevas (priorizadas por yield histórico)

**Tier A — Alta densidad (top 5 países, 4-6 ciudades c/u):**
Alemania: Stuttgart, Leipzig, Frankfurt, Dortmund, Essen, Düsseldorf
España: Valencia, Sevilla, Málaga, Ibiza, Zaragoza, Bilbao
Países Bajos: Rotterdam, Utrecht, Groningen, Eindhoven
Francia: Toulouse, Lille, Nantes, Strasbourg, Nice
UK: Bristol, Manchester, Liverpool, Birmingham, Glasgow

**Tier B — Hubs psy globales (no capitales):**
India: Arambol/Goa, Anjuna, Vagator, Pune, Bangalore, Delhi
Tailandia: Koh Phangan, Chiang Mai, Phuket, Pai
México: Tulum, Playa del Carmen, Guadalajara, Monterrey
Brasil: Florianópolis, Rio, Belo Horizonte, Curitiba
Japón: Osaka, Kyoto, Fukuoka
Australia: Byron Bay, Melbourne, Sydney, Perth
Israel: Haifa, Eilat
Portugal: Algarve, Coimbra
Italia: Bologna (ya), Verona, Genoa, Turin completas
USA: Los Angeles, San Francisco, New York, Miami, Austin
Bali: Canggu, Ubud; Sudáfrica: Johannesburg, Durban; Marruecos: Marrakech; etc.

Total 120: 46 existentes + 74 nuevas. Archivo: `config/ciudades_120.json`.

## 4. Estrategia de exploración inteligente (no brute force)

Ejecutar 130k queries saturaría Tor y generaría 90% duplicados. Sampling:

1. **Scoring de ciudades:** peso = eventos históricos en ese país / nº ciudades del país en CSV. Alemania 357/6=59.5, España 327/6=54.5 → prioriza DE/ES primero.
2. **Scoring de subgéneros:** peso = frecuencia en CSV psytrance real (psytrance 389, progressive 74, goa 53 → prioriza esos 3 en 60% de queries).
3. **Muestreo adaptativo:** cada run toma `presupuesto = 200 queries` (configurable). 60% top-tier (Tier A × top subgéneros), 30% exploración (Tier B × sinónimos raros como suomisaundi/zenon), 10% aleatorio puro para descubrir hubs nuevos.
4. **Dedup temprano:** antes de SERP, hashear `sub+ciudad+año+tipo` y saltar si ya está en `historial_improvement_loop.json` o `cache_dedup.json`.
5. **Anti-bloqueo:** cada query por `core/serp_tor.py` (DDG+SearxNG vía Tor `socks5h`), 1.2s sleep entre queries, rotación Tor cada 10 queries vía `tor_pool.py`.

## 5. Cambios de código (Fase 6)

1. **`config/ciudades_120.json`** — 120 ciudades con país/continente, tier A/B, peso.
2. **`core/matriz_busqueda.py` (nuevo)** — `generar_combinaciones(presupuesto=200)` → lista de dorks `site:facebook.com/events {sinónimo} {tipo} {ciudad} {año}` + consulta directa para RA/Goabase. Exporta `combinaciones_pendientes.json`.
3. **`core/serp_tor.py:377`** — ampliar `buscar_serp_fb()` para aceptar `sinonimo` y `tipo` dinámicos (ya lo hace, solo ampliar vocabulario).
4. **Scrapers directos** — `edmdancedirectory.py`, `setline.py`, etc.: iterar por `?genre={sub}` para cada sinónimo (no solo psytrance), con fallback si 404.
5. **`core/auto_optimizer.py:127`** — ya penaliza `no_psy` (-1) y premia psytrance (+1); añadir peso `+2` por evento con `organizador` no N/A (perfiles).
6. **Loop:** `matriz_busqueda.py` → `serp_tor.py`/scrapers → `deduplicador.py` → `eventos_encontrados.csv` → `loop_completar.py` (normaliza país).

## 6. Estimación

- 200 queries/run × 5s avg (Tor) = ~16 min/run
- 200 queries × 30% hit rate histórico (FB dorks) ≈ 60 eventos nuevos/run antes de dedup → ~20 nuevos tras dedup (similar a última vuelta +239 en 5 runs)
- Con 120 ciudades, se cubre todo el mapa en ~10 runs (2,000 queries) → plateau esperado a ~2,500 eventos consolidados.

## 7. Próximos pasos

1. Crear `config/ciudades_120.json` y `core/matriz_busqueda.py`
2. Ejecutar `python core/matriz_busqueda.py --presupuesto 50 --dry-run` para validar
3. Integrar `matriz_busqueda.py` en `run_vivo.py` antes del orquestador
4. Lanzar `run_vivo.py` con nueva matriz y medir +Δ eventos/run
