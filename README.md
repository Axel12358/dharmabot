# dharmabot

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Estado](https://img.shields.io/badge/estado-operativo-green)
![Visibilidad](https://img.shields.io/badge/visibilidad-privada-lightgrey)
![Datos](https://img.shields.io/badge/datos-no%20versionados-orange)

Pipeline de OSINT y clasificación de eventos **psytrance / psychedelic trance** a nivel mundial (2025-2028). Descubre, enriquece y mantiene un dataset global estructurado (organizador, email, fecha, lugar, subgénero) a partir de fuentes públicas — todo local, sin APIs de pago y sin exponer IP real.

> Repositorio limpio de **código y documentación**. Los datasets y caches (CSV, JSON de estado) se generan al ejecutar y **no se versionan**; la copia de trabajo operativa es `/Users/angelgarcia/dharmabot`.

## Estado actual (dataset global)

| Métrica | Valor |
|---|---|
| Eventos 2025-2028 | **14.491** |
| Organizador resuelto | ~**92%** |
| Email válido | ~**88%** |
| Fecha específica resuelta | ~**94.5%** (resto `YYYY-01-01` = pendiente por muro de login FB) |

- Eventos fuera de rango **se archivan, nunca se borran** (`eventos_deadstock_2021_2024.csv`, `eventos_historicos_pre2021.csv`).
- No-psy / ruido de palabra clave → `non_psy.csv` con motivo.
- Escritura concurrente protegida por **lock cooperativo** (`core/csv_lock.py`, `fcntl.flock` + escritura atómica).

## Arquitectura

```
LaunchAgents (macOS, persistente)          Procesos manuales (1-off)
  com.dharma.loop  (enriquecimiento)          recuperar_fechas.py   (fechas FB og)
  com.dharma.orquestador                      fecha_alt.py          (pase FB móvil)
        │                                     empujar_org_email.py  (org/email offline)
        ▼                                     email_burst.py        (DDG emails)
┌───────────────────────────────┐
│  loop_completar.py            │
│  • SERP por ciudad (org)      │
│  • Rama A: email por organiz. │
│  • Telegram / fuentes         │
└───────────────┬───────────────┘
                │   csv_lock (flock+atómico)
                ▼
        eventos_encontrados.csv
```

### Capa `core/`
- `csv_lock.py` — lock cooperativo + escritura atómica (`csv_locked_rows`).
- `fb_ids.py` — extracción de ID de eventos Facebook (URLs y slugs).
- `fecha_parse.py` — parser de fechas multi-idioma (EN/ES/PT/DE/FR/IT/PL/NL).
- `serp_tor.py`, `tor_manager.py`, `tor_pool.py`, `tor_utils.py` — SERP y scraping vía Tor.
- `http_client.py`, `google_stealth.py` — clientes HTTP y anti-bloqueo.
- `deduplicador.py`, `geocode.py`, `hibrido.py` (LLM local + regex), `mcp_*`, `orquestador.py`.

### Fuentes
Facebook (og:description con UA `facebookexternalhit`; móvil `m.facebook`), Resident Advisor, Goabase, Telegram (`t.me/s/`), DDG/SearXNG. Prohibidos: APIs de pago (Apify, Meta Content Library) y exposición de IP real.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Tor (macOS)
brew install tor && brew services start tor

# Enriquecimiento continuo
./run_loop_completar.sh          # o: python run_loop.py

# Pases puntuales
python recuperar_fechas.py       # fechas desde FB og:description
python empujar_org_email.py      # org/email offline desde caches
```

## Organización del repo

| Ruta | Contenido |
|---|---|
| `core/` | Paquete principal de la pipeline |
| `*.py` (raíz) | Scripts operativos (fechas, org, email, loop, clasificación) |
| `config*`, `config/`, `searxng_settings.yml` | Configuración declarativa |
| `docs/` | Documentación técnica (Tor, fuentes, subgéneros, scrapers) |
| `opencode/skills/` | Skill reutilizable `fb-organizer-osint` |
| `utils/`, `sources/`, `agents/`, `scripts/` | Soporte (proxies, geo, fuentes, agentes) |

## Operación en macOS (LaunchAgents)

El supervisor de arranque vive en `~/Library/LaunchAgents/com.dharma.*.plist`:

```bash
launchctl list | grep dharma
launchctl start com.dharma.loop
tail -f $HOME/dharmadhatu_agent_qwen/loop_completar.log
```

## Reglas de diseño

1. **Nunca borrar filas**: fuera de rango o ruido → archivar con motivo.
2. **Todo escritor usa `csv_locked_rows()`** — lectura fresca bajo lock, fusión por clave.
3. **Sin IP real**: todo el tráfico HTTP vía `socks5h://127.0.0.1:9050`.
4. **Cero APIs de pago** y cero credenciales en el repo.
5. **Scripts reutilizables no viven en `/tmp`** (se limpia); van al repo.

## Contribuir

Ver [`CONTRIBUTING.md`](CONTRIBUTING.md) y [`ARCHITECTURE.md`](ARCHITECTURE.md).

## Licencia

Uso privado — distribución restringida. Ver [`LICENSE`](LICENSE).