# Reporte Técnico — Dharmadhatu Bot v5
## Análisis de arquitectura y estado para revisión como asesor externo

**Fecha:** 2 de septiembre de 2026
**Objetivo del documento:** Exponer cómo funciona el bot y sus módulos de forma precisa, honesta y verificable, para que un asesor externo (Claude) pueda dar una opinión técnica fundamentada.

---

## 1. Resumen Ejecutivo

| Métrica | Valor |
|---|---|
| **Eventos totales en CSV** | **1,462** |
| Fuentes de datos | 15 |
| Países representados | 74 |
| Con email válido | 1,285 (87.9%) |
| Rango temporal | 2012 – 2027 |
| Scrapers configurados | 21 (19 activos en config) |
| Scrapers reales en ejecución (Fase 5) | 26 |
| Ejecuciones orquestador registradas | 21 |
| Reclasificación LLM | qwen2.5-coder:7b local |
| Tiempo clasificación LLM (490 eventos) | ~19.5 min |
| Optimizador de config | 2 iteraciones, convergió en score 280.5 |

**Propuesta de valor:** Bot 100% local y gratuito que consolida un directorio de eventos psytrance desde múltiples fuentes públicas, con deduplicación global, clasificación por subgénero y anonimato vía Tor — sin ninguna API de pago ni login.

**Objetivo real del proyecto (revisado):** el dato de mayor valor NO son los emails, sino los **PERFILES de organizador / host**. En Facebook, dentro de la descripción del evento existe un apartado de "host/organizador" que es lo que interesa capturar. En Instagram lo que interesa son los **perfiles** (no los posts). El directorio busca construir una base de **contactos organizadores** (perfiles + su actividad), no solo una lista de eventos con email.

---

## 2. Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│                        ENTRADAS                              │
│   main.py ──► core/orquetrador.py  (producción, CON ERRATA)  │
│   run_vivo.py ──► core/orquestador.py (correcto, plugin)    │
└───────────────┬─────────────────────────────────────────────┘
                ▼
    ┌───────────────────────┐    ┌───────────────────────┐
    │  ORQUESTADOR          │    │  AGENTE COORDINADOR   │
    │  ThreadPoolExecutor   │    │  subagentes paralelos  │
    │  timeouts por scraper │    │  TaskQueue persistente │
    └───────────┬───────────┘    └───────────┬───────────┘
                │                            │
                ▼                            ▼
    ┌───────────────────────────────────────────────────────┐
    │            DEDUPLICADOR GLOBAL                        │
    │   hash SHA-256 (nombre|fecha|lugar|fuente)            │
    │   cache_dedup.json  +  auto-limpieza >5000            │
    └───────────────────────┬───────────────────────────────┘
                            ▼
    ┌───────────────────────────────────────────────────────┐
    │  POST-PROCESADO (aditivo)                              │
    │  loop_completar: llena subgénero/tipo_lugar/pais/      │
    │  continente N/A                                        │
    │  verificar_general: reclasifica "general"→psytrance    │
    │  llm_local: reclasifica no_psy por Qwen local          │
    └───────────────────────┬────────────────────────────────┘
                            ▼
               eventos_encontrados.csv  (1,462 filas)
```

### Principios de diseño (reglas del proyecto)
- **No tocar** `goabase.py`, `songkick.py`, `main.py` (excepto añadir al final).
- **Siempre sumar, nunca restar** (escritura aditiva, no destructiva).
- **Todo local, gratuito, sin login** (sin APIs de pago, sin credenciales).
- **Reversible**: cada scraper se puede activar/desactivar sin afectar al resto.
- **Documentar** todo en `docs/*.md`.

---

## 3. Módulos Core (`core/`)

### 3.1 `orquestador.py` vs `orquetrador.py` — ⚠️ DIVERGENCIA CRÍTICA

Hay **dos versiones del orquestador en producción**, con ortografía distinta en el nombre del archivo:

| Aspecto | `orquetrador.py` (errata) | `orquestador.py` (correcto) |
|---|---|---|
| **Quién lo importa** | `main.py:191` (producción) | `run_vivo.py` (solo pruebas) |
| plugin_loader | **NO** lo usa | Sí (auto-descubre scrapers) |
| Métricas file | `metricas_orquetador.json` | `metricas_orquestador.json` |
| Timeout Goabase | 30s | 120s |
| Timeout Songkick | 60s | 120s |
| Telegram | solo print estado | ejecuta scraper real |
| Agente Coordinador | delegado a main.py | ejecuta inline |

**Impacto:** `main.py` (el entry point oficial) usa la versión ANTIGUA sin plugin_loader y con timeouts más agresivos. El trabajo Fase 5 (plugin_loader con auto-descubrimiento de 26 scrapers) solo se activa al usar `run_vivo.py`. **Hay que consolidar en un solo archivo.**

### 3.2 `deduplicador.py` — Deduplicación global
- Hash **SHA-256** de `nombre | fecha | lugar | fuente` normalizados.
- Incluye `fuente` en el hash → el mismo evento en RA y Facebook se conserva en ambas (solo evita re-sumar el mismo evento de la misma fuente).
- `filtrar_nuevos()` no toca caché; `registrar_vistos()/guardar()` persisten de forma atómica (`.tmp` + `os.replace`).
- NO carga `cache_dedup.json` al arrancar — usa el CSV como fuente de verdad.
- Auto-poda a 5,000 entradas conservando las más recientes.

### 3.3 `plugin_loader.py` — Auto-descubrimiento de scrapers (Fase 5)
- Doble fase: (1) escanea `scrapers/*.py` buscando `def scrape_*`, (2) `MODULOS_ESPECIALES` para firmas no estándar.
- Lee metadata de `scrapers/<nombre>.json` y `config_modulos.json` para prioridad de activo.
- `inyectar_deduplicador()` inyecta el dedup global en runtime vía lista mutable compartida.
- Solo lo usa `orquestador.py` (correcto), no el errata.

### 3.4 `serp_tor.py` — Motor SERP centralizado
- Motores: DDG, Bing, Startpage, Google, SearxNG.
- **Realidad vía Tor**: solo **DDG y SearxNG** funcionan (`ORDEN_MOTORES = ["ddg", "searxng"]`). Google/Bing/Startpage bloquean exits de Tor.
- `buscar_serp()` y `buscar_serp_fb()` (genera dork `site:facebook.com/events ...`).
- Usa sesión compartida vía Tor (socks5h, sin DNS leak).

### 3.5 `tor_pool.py` / `tor_manager.py` / `tor_utils.py` — Gestión Tor
- **3 capas solapadas**: `tor_utils` (base) → `tor_pool` (multi-circuito) → `tor_manager` (centralizado), importándose mutuamente con fallbacks.
- Pool de **3 circuitos Tor**: `(9050,9051)`, `(9052,9053)`, `(9054,9055)` (socks, control).
- Rotación de identidad: 3 estrategias en cascada (tor_pool → Stem NEWNYM → reinicio subprocess).
- **Todos usan `socks5h://`** → DNS resuelto dentro del túnel, sin exponer IP real.
- **Verificable hoy**: solo 9050 activo (9052/9054 caídos); el fallback a índice 0 lo cubre.

### 3.6 `http_client.py` — Cliente HTTP con anonimato
- Usa **curl_cffi** con TLS impersonation (chrome110/safari) para simular fingerprint real.
- Prioridad de proxy: proxy residencial de terceros (si existe) → Tor. **Nunca IP del usuario**.
- `get_html()` crea sesión nueva por llamada.

### 3.7 `google_stealth.py` — Playwright + Tor + stealth (873 líneas)
- Anti-detección en 6 capas: stealth dual, init script, perfil persistente, comportamiento humano (mouse + typing), rotación de cookies, rotación Tor.
- Detecta bloqueos (429/403/recaptcha/sorry) y aplica backoff con retry.
- `google_search_prioritario()`: DDG → Bing → Startpage → Mojeek → SearxNG → requests Google.

### 3.8 `mcp_organizador.py` — Motor central de dorks
- Ejecuta búsquedas **secuencialmente** (anti-saturación Tor), 3 fuentes: dorks_unificado, facebook_dorks, instagram_dorks.
- Consolida en `mcp_eventos.json`, expone JSON-RPC sobre stdio.

### 3.9 `agente_coordinador.py` — Sistema multiagente ligero
- Ejecuta subagentes (goabase, RA, facebook_mcp, telegram, reddit, etc.) en paralelo con `ThreadPoolExecutor(max_workers=5)`.
- Timeouts por agente (RA 300s, telegram 120s, reddit 3s...).
- Usa `TaskQueue` persistente.

### 3.10 `auto_optimizer.py` — Optimizador de config (Fase 5)
- **Analítico, NO ejecuta scrapers**: analiza qué aporta al CSV + combinaciones con scoring.
- Score: +0.5/evento histórico, +10/diversidad de tipo, -5/scraper pesado, +15 estáticos+SERP, +3/plugin nuevo.
- Guarda `mejor_config.json`, historial en `optimizer_history.json`.
- Resultado: convergió en 2 iteraciones (config actual es la mejor con score 280.5).

### 3.11 `loop_completar.py` / `verificar_general.py` — Post-procesado
- `loop_completar`: rellena `subgénero/tipo_lugar/pais/continente` N/A hasta que no queden huecos (5 iteraciones máx, propagación intra-CSV + geocode).
- `verificar_general`: reclasifica `general→psytrance` (dork búsqueda Tor → fuente especializada → extractor).

---

## 4. Scrapers (`scrapers/`)

### 4.1 Fuentes especializadas psytrance (núcleo)

| Scraper | Fuente | Método | Tor | Eventos | Función (archivo:línea) |
|---|---|---|---|---|---|
| `goabase.py` | goabase.net | requests JSON-LD API | No | ~100–345 | `scrape_goabase(limit=100)` `:6` |
| `songkick.py` | songkick | requests+BS4 | No | ~1 | `scrape_songkick(limit=100)` `:4` |
| `resident_advisor.py` | ra.co GraphQL | POST GraphQL | No | ~500 | `scrape_ra(ciudades,...)` `:271` |
| `reddit_psy.py` | Reddit RSS | requests Atom/XML | No | ~10–50 | `scrape_reddit_psy()` `:131` |
| `psytrance_pl.py` | portal polaco | requests+BS4 | No | ~6–30 | `scrape_psytrance_pl()` `:97` |
| `isratrance.py` | portal israelí | requests | No | 0 (caído) | `scrape_isratrance()` `:33` |
| `ektoplazm.py` | netlabel | requests+BS4 | No | ~3–20 | `scrape_ektoplazm()` `:45` |
| `psynews.py` | foro legacy | requests+BS4 | No | ~10–30 | `scrape_psynews(limit)` `:6` |
| `meetup_psy.py` | meetup JSON-LD | requests | No | ~0–60 | `scrape_meetup_psy()` `:86` |
| `eventbrite_psy.py` | eventbrite | Playwright async | No | ~40–80 | `scrape_eventbrite_psy()` `:136` |

### 4.2 Facebook (via Tor obligatorio)

| Scraper | Método | Tor | Eventos | Función |
|---|---|---|---|---|
| `facebook_dorks.py` | Google dorks → FB | **Sí** | ~10–154 | `scrape_facebook_dorks()` `:769` |
| `fb_playwright_tor.py` | Playwright directo FB | **Sí** siempre | ~10–20 | `scrape_fb_playwright_tor()` `:293` |
| `facebook_mcp.py` | curl_cffi + multi-estrategia | **Sí** | ~40–80 | `scrape_facebook_events()` `:2594` |

**Realidad técnica**: FB no expone emails en páginas públicas; los emails vienen del organizador extraído o caches internos. El scraping directo de páginas FB individuales choca con login-wall — `fb_playwright_tor` está **desactivado** en config.

> **⚠️ Corrección de objetivo (importante):** para Facebook el objetivo real NO son los emails (que FB no expone en público), sino capturar los **PERFILES de host/organizador** que aparecen en el apartado "host/organizador" dentro de la descripción de cada evento. Esos perfiles son el dato de contacto valioso. Por tanto, la extracción debe priorizar: (1) el perfil del organizador del evento, (2) el enlace al perfil, (3) su actividad/agenda — por encima del email que casi nunca está disponible públicamente.

### 4.3 Nuevos scrapers (Fase 5, directos por Cloudflare)

| Scraper | Fuente | Método | Tor | Eventos | Función |
|---|---|---|---|---|---|
| `edmdancedirectory.py` | EDM Dance Directory | requests+JSON-LD | No | ~49 | `scrape_edmdancedirectory()` `:62` |
| `psytrancefestivals_tv.py` | agenda 2026-27 | requests+BS4 regex | No | ~40–71 | `scrape_psytrancefestivals_tv()` `:85` |
| `psymedia.py` | calendario Sudáfrica | requests+BS4 | No | ~21 | `scrape_psymedia()` `:45` |
| `setline.py` | festivales 2026-27 | requests+BS4 | No | ~27 | `scrape_setline()` `:37` |
| `psychill_space.py` | calendario psychill | requests+BS4 | No | ~2 | `scrape_psychill_space()` `:37` |

> Nota: estos sitios bloquean Tor exits (Cloudflare), por eso van directos. Es una **excepción controlada** a la regla "todo por Tor".

### 4.4 `llm_local.py` — Motor LLM local (clasificación)

| Función | Línea | Descripción |
|---|---|---|
| `extract_events_llm(text, url)` | :113 | Extrae eventos de texto |
| `dedup_semantic_llm(events)` | :139 | Dedup semántico por pares |
| `classify_spam_llm(text)` | :161 | EVENTO vs RUIDO |
| `normalize_location_llm(loc)` | :175 | Normaliza ubicaciones |
| **`reclasificar_no_psy(events, batch)`** | :231 | no_psy → subgénero real (batch 3) |
| `rellenar_email_n_a()` | :310 | Busca emails en N/A |
| `rellenar_organizador_n_a()` | :351 | Busca organizador en N/A |
| `procesar_csv_llm(csv)` | :388 | Pipeline completo |

Cliente: `httpx` → `http://localhost:11434`, modelo `qwen2.5-coder:7b`, temp 0.05–0.1.

### 4.5 `event_extractor.py` — Motor central de clasificación
- `EventExtractor.clasificar_subgenero()` en **3 estrategias en cascada**: substring → sinónimos con word-boundary (34 sinónimos) → puntuación ponderada (título 3, org 2, lugar 1, desc 1, email 1, link 1, umbral 2).
- `_extract_date()` soporta 18 formatos de fecha; `_extract_venue_type()` 17 tipos de lugar; `KNOWN_CITIES` 80+ ciudades, `COUNTRIES_ES` 50+ países.
- Lo usan ~12 scrapers → es el clasificador transversal.

---

## 5. Estado del Dataset (`eventos_encontrados.csv` — 1,462 filas)

### 5.1 Distribución por fuente

| Fuente | Eventos | % |
|---|---:|---:|
| Resident Advisor | 785 | 53.7% |
| Goabase | 345 | 23.6% |
| Facebook (dorks) | 154 | 10.5% |
| Facebook | 40 | 2.7% |
| Telegram | 34 | 2.3% |
| Setline | 27 | 1.8% |
| Facebook (público SERP) | 22 | 1.5% |
| Psymedia | 21 | 1.4% |
| Reddit | 11 | 0.8% |
| Instagram (prueba) | 10 | 0.7% |
| Psytrance.pl | 6 | 0.4% |
| Ektoplazm | 3 | 0.2% |
| Psychill Space | 2 | 0.1% |
| Songkick | 1 | 0.07% |
| Meetup | 1 | 0.07% |

### 5.2 Distribución por subgénero — ⚠️ PUNTO DEBIL

| Subgénero | Eventos | % |
|---|---:|---:|
| **no_psy** | **483** | **33.0%** |
| psytrance | 379 | 25.9% |
| **N/A** | **300** | **20.5%** |
| progressive | 74 | 5.1% |
| goa | 52 | 3.6% |
| psybient | 39 | 2.7% |
| darkpsy | 37 | 2.5% |
| forest | 27 | 1.8% |
| psychill | 17 | 1.2% |
| hitech | 16 | 1.1% |
| suomisaundi | 16 | 1.1% |
| psychedelic | 9 | 0.6% |
| fullon | 8 | 0.5% |
| twilight | 5 | 0.3% |

> **Hallazgo crítico**: solo **46.5%** tiene confirmación positiva de psytrance. 483 (33%) son `no_psy` y 300 (20.5%) son `N/A`. El LLM local solo reclasificó 7 de 490 `no_psy` en 19.5 min.

### 5.3 Emails y países
- **Emails**: 1,285 (87.9%) con email; 177 (12.1%) N/A. Cobertura alta.
- **Países**: 74 distintos. Top: España/Germany ~280 c/u, Países Bajos 153, Francia 134, N/A 125, UK 104, Suiza 79, Cambodia 55, Austria 43, Israel 22.
- **⚠️ Inconsistencia de normalización**: "España" y "Spain" por separado, "Alemania" y "Germany", "Paises Bajos" y "Netherlands". Problema de limpieza de datos.

### 5.4 Rango temporal
- **2012 – 2027** (históricos + futuros predichos ~15 años).

---

## 6. Problemas Conocidos y Errores Recurrentes

### 6.1 Errores reportados en `metricas_orquestador.json` (últimos runs)
| Scraper | Error |
|---|---|
| `instagram_dorks` | `AttributeError` (falta `scrape_instagram_dorks`) |
| `dorks_resultados` | `AttributeError` (`'list' object has no attribute 'lower'`) |
| `mcp_organizador` | timeout recurrente |
| `enriquecer_fb_og` | `ModuleNotFoundError` (falta `ollama`) |
| `facebook_groups_sync` | `TypeError` (argumento faltante) |

### 6.2 Problemas conocidos (de AGENTS.md)
- Reddit: 429 rate-limit tras ~2 peticiones.
- Meetup: 0 eventos psytrance reales (falsos positivos ya filtrados).
- IsraTrance: sitio caído.
- Tor: en algunos runs `ERR_SOCKS_CONNECTION_FAILED`, cae a directo.
- FB sin cookies: grupos privados no rinden; la estrategia productiva es SERP público.
- Tras muchos runs la SERP satura (dedup apenas añade +1-4/run).

---

## 7. Evaluación del Pipeline LLM — ⚠️ PUNTO DEBIL

- Modelo: `qwen2.5-coder:7b` (4.5GB local, 100% CPU).
- Velocidad: ~2.4s/evento, 490 eventos en 19.5 min.
- **Resultado: solo 7 reclasificados de 490 `no_psy`** (1.4% de tasa de conversión).
- El checkpoint guarda 220 procesados; hay discrepancia entre log (490) y checkpoint (220).

**Interpretación**: El LLM casi no encuentra psytrance en los `no_psy` — probablemente porque esos eventos RA realmente NO son psytrance (fuente general filtrada), o el prompt/umbral es demasiado estricto. Es un uso legítimo pero de bajo rendimiento con qwen2.5-coder:7b.

---

## 8. Loop de Mejora / Optimización

- `config_loop.json` → `loop_mejora.py` (Fase 3, para RA + FB params): combina lote ciudades × keywords × visitas × horizonte, score = eventos*2 + email*3 − tiempo*0.1.
- `core/auto_optimizer.py` (Fase 5): analítico, converge en config actual (score 280.5, solo 2 iteraciones).
- `loop_optimizer.py` (Instagram): prueba arquitecturas (requests/playwright), mejor arquitectura `playwright_only`, score final 0 (0 eventos — Instagram no rinde sin login).

> **Nota de objetivo revisado (Instagram):** lo que interesa son los **PERFILES de organizadores** (cuentas de eventos/colectivos psytrance) y TAMBIÉN sus **posts** (para extraer fechas/lugares/descrp de próximos eventos). La métrica de "eventos por run" es engañosa para Instagram — la correcta sería "**perfiles nuevos descubiertos + posts de eventos extraídos**". Hay 15 perfiles semilla conocidos en `instagram_dorks.py:349-381` (psychonaut_nl, goapsy, dreamstate, etc.) usados como puntos de partida. La evaluación debería reorientarse de "0 eventos" → "perfiles de organizadores enriquecidos".

---

## 8b. Estado del Pipeline LLM — ⚠️ NO DISPONIBLE ACTUALMENTE

- **Ollama ya NO está instalado** (verificado 2-sep-2026: el puerto 11434 no responde y el binario `ollama` no está en PATH).
- Por tanto, el pipeline de clasificación por LLM local (`scrapers/llm_local.py` con `qwen2.5-coder:7b`) **queda inoperativo hasta reinstalar Ollama + el modelo**.
- Cuando estuvo activo: ~2.4s/evento, 490 eventos en 19.5 min, solo 7 reclasificados de 490 `no_psy` (1.4% de conversión).
- Módulos que dependen de Ollama y hoy fallan por import: `llm_local.py`, `enriquecer_fb_og` (importaba `ollama`).
- **Pregunta al asesor**: ¿cómo solucionar la pérdida de Ollama? ¿Reinstalar el modelo local (¿cuál recomienda para clasificación? ¿un modelo más ligero?), ¿reemplazar el LLM por otra vía 100% local sin Ollama, o abandonar el LLM y usar solo el clasificador regex de `event_extractor.py`?

---

## 9. Hallazgos para el asesor — LO MÁS IMPORTANTE

### 🔴 Críticos
1. **Divergencia de orquestadores**: `main.py` usa `core/orquetrador.py` (con errata, sin plugin_loader, timeouts agresivos). El trabajo Fase 5 (`orquestador.py` correcto) no está activo en producción. **URL de riesgo**: main.py:191.
2. **Calidad de clasificación baja**: solo 46.5% con psytrance positivo; 33% no_psy + 20.5% N/A. El "CSV limpio de 1,462 eventos" contiene muchos no-psytrance.
3. **Dos archivos de métricas** divergentes (`metricas_orquetador.json` vs `metricas_orquestador.json`).
4. **Ollama no instalado** → **RESUELTO con LLM híbrido**: se creó `core/llm_hibrido.py` con fusión 2+3.
   - **Tier 0:** Ollama local si vuelve (qwen2.5-coder:7b).
   - **Tier 1 (assistant):** 6 modelos `opencode/*` gratuitos sin API key (`muse-spark`, `big-pickle`, `ling-3.0`, `mimo`, `nemotron`) — rotación automática.
   - **Tier 2 (cloud):** 4 modelos `freellmpool/*` gratuitos (Groq/Mistral vía pool) como fallback si Tier 1 se satura.
   - **Tier 3:** Regex `event_extractor.py` — siempre funciona.
   Si un proveedor da 429/timeout se marca bloqueado 5min y se prueba el siguiente. Así el bot **nunca se bloquea** aunque el uso sea muy frecuente. `scrapers/llm_local.py:reclasificar_no_psy()` ya usa el híbrido automáticamente cuando Ollama no responde.

### 🟠 Importantes
4. **3 capas de gestión Tor solapadas** (tor_utils/tor_pool/tor_manager) con imports mutuos — frágil, difícil de mantener.
5. **Instagram / Facebook — reorientar a perfiles de organizadores**: el dato valioso son los **perfiles** (cuentas/hosts), no los emails ni los posts sueltos. En FB el host/organizador está dentro de la descripción del evento; en IG lo que interesa son las cuentas de colectivos/eventos y sus posts con fechas/lugares. Instagram "no rinde" si se mide por eventos, pero sí si se mide por **perfiles descubiertos** (15 semillas en `instagram_dorks.py:349-381`).
6. **Scrapers con errores persistentes** (instagram_dorks, dorks_resultados, mcp_organizador, enriquecer_fb_og) — degradan el run.
7. **Normalización de países inconsistente** (ES/EN duplicados) — afecta la calidad del directorio.

### 🟢 Positivos / Fortalezas
8. **Aditividad estricta** bien implementada (nunca pierde datos, reversible).
9. **Deduplicación global sólida** (SHA-256 multicampo + fuente, atomic persist).
10. **Anonimato cuidado** (socks5h, sin DNS leak, TLS impersonation).
11. **Núcleo estable**: Goabase (345) + RA (785) son fuentes confiables y escalables.
12. **Cobertura de emails alta** (87.9%).

---

## 10. Archivos Clave Referenciados

```
core/orquetrador.py      # ⚠️ orquestador errata (PRODUCCIÓN vía main.py)
core/orquestador.py      # orquestador correcto (plugin_loader, run_vivo)
core/deduplicador.py     # hash SHA-256 global
core/plugin_loader.py    # auto-descubre scrapers (Fase 5)
core/serp_tor.py         # SERP DDG+SearxNG vía Tor
core/tor_pool.py         # 3 circuitos Tor (9050/9052/9054)
core/tor_manager.py      # gestión centralizada Tor
core/tor_utils.py        # capa base Tor
core/http_client.py      # curl_cffi TLS impersonation
core/google_stealth.py   # Playwright+Tor+stealth (873 líneas)
core/mcp_organizador.py  # motor dorks JSON-RPC
core/agente_coordinador.py# subagentes paralelos
core/auto_optimizer.py   # optimizador analítico de config
core/loop_completar.py   # rellena N/A
core/verificar_general.py# general→psytrance
scrapers/goabase.py      # NO TOCAR (345 eventos)
scrapers/songkick.py     # NO TOCAR
scrapers/event_extractor.py # clasificador transversal
scrapers/llm_local.py    # Qwen local (reclasifica no_psy)
scrapers/facebook_dorks.py # FB via dorks Tor (154 eventos)
scrapers/fb_playwright_tor.py # FB directo (desactivado)
scrapers/{edmdancedirectory,psytrancefestivals_tv,psymedia,setline,psychill_space}.py # Fase 5 (directos)
config_modulos.json      # 21 scrapers, 19 activos
eventos_encontrados.csv  # 1,462 eventos
```
