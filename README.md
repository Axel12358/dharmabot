# dharmabot

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Estado](https://img.shields.io/badge/estado-operativo-green)
![Mantenido](https://img.shields.io/badge/mantenimiento-activo-brightgreen)
![Visibilidad](https://img.shields.io/badge/visibilidad-privada-lightgrey)
![Datos](https://img.shields.io/badge/datos-no%20versionados-orange)
![Cobertura org](https://img.shields.io/badge/organizadores-92%25-brightgreen)
![Cobertura email](https://img.shields.io/badge/email-88%25-brightgreen)
![Cobertura fecha](https://img.shields.io/badge/fechas-94%25-brightgreen)
![Licencia](https://img.shields.io/badge/licencia-propietaria-inactive)

**Plataforma de inteligencia y descubrimiento de eventos psytrance a escala global (2025-2028).** dharmabot opera en producción un canal 24/7 de monitoreo de fuentes públicas, extracción, clasificación y enriquecimiento de eventos de música psicodélica en todo el mundo — un dataset profesional estructurado (organizador, email, fecha, lugar, subgénero) construido y mantenido de forma continua, 100% local y sin APIs de pago.

> Repositorio limpio de **código y documentación** (los datos y caches se generan al ejecutar y no se versionan). La instalación operativa vive en `~/dharmabot`.

## Capacidades

- **Descubrimiento continuo** de eventos psytrance desde Facebook, Resident Advisor, Goabase y Telegram.
- **Enriquecimiento automatizado**: organizador, email de contacto y fecha específica por evento.
- **Clasificación por subgénero** (progressive, forest, darkpsy, hi-tech, goa, full-on, suomisaundi…) con LLM local + regex.
- **Coordinación multi-proceso segura**: escritura atómica con lock cooperativo `fcntl` (`core/csv_lock.py`).
- **Anonimato real**: todo el tráfico vía Tor (`socks5h`); cero IP real, cero APIs de pago.
- **Política de datos cero-pérdida**: nada se borra; fuera de rango y ruido se archivan con motivo.

## Estado operativo (dataset global)

| Métrica | Valor |
|---|---|
| Eventos 2025-2028 en producción | **14.491** |
| Organizador resuelto | **92%** |
| Email de contacto válido | **88%** |
| Fecha específica resuelta | **94.5%** |

- Fechas pendientes (`YYYY-01-01`) → eventos Facebook tras muro de login; se mantienen como `fecha_pendiente`, sin inventar datos.
- Fuera de rango → archivos `eventos_deadstock_2021_2024.csv` / `eventos_historicos_pre2021.csv`.
- No-psy / ruido de palabra clave → `non_psy.csv` con motivo.

## Arquitectura

```
LaunchAgents (macOS, persistente)     Procesos puntuales (1-off)
  com.dharma.loop  (enriquecimiento)     recuperar_fechas.py   (fechas vía FB og)
  com.dharma.enricher                   fecha_alt.py          (pase FB móvil)
        │                               empujar_org_email.py  (org/email offline)
        ▼                               email_burst.py        (DDG emails)
┌───────────────────────────────┐
│  loop_completar.py            │
│  • SERP por ciudad (org)      │
│  • Rama A: email por organ.   │
│  • Telegram / fuentes         │
└───────────────┬───────────────┘
                │  csv_lock (flock + atómico)
                ▼
        eventos_encontrados.csv
```

### Capa `core/`

- `csv_lock.py` — cooperación de escritores (lectura fresca bajo lock + fusión por clave).
- `fb_ids.py` — resolución de IDs de eventos Facebook (URLs y slugs).
- `fecha_parse.py` — parser de fechas multi-idioma (EN/ES/PT/DE/FR/IT/PL/NL).
- `serp_tor.py`, `tor_manager.py`, `tor_pool.py`, `tor_utils.py` — SERP y scraping vía Tor.
- `http_client.py`, `google_stealth.py` — clientes HTTP con anti-bloqueo.
- `deduplicador.py`, `geocode.py`, `hibrido.py` (LLM local + regex), `mcp_*`, `orquestador.py`.

### Fuentes

Facebook (og:description con UA específica; variante móvil `m.facebook`), Resident Advisor, Goabase, Telegram (`t.me/s/`), DDG/SearXNG. **Excluidas**: APIs de pago (Apify, Meta Content Library) y cualquier exposición de IP real.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Tor (macOS)
brew install tor && brew services start tor

# Enriquecimiento continuo (producción)
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
launchctl list | grep dharma          # ver jobs activos
launchctl start com.dharma.loop
tail -f $HOME/dharmabot/loop_completar.log
```

## Reglas de diseño

1. **Nunca borrar filas** — fuera de rango o ruido se archivan con motivo.
2. **Todo escritor usa `csv_locked_rows()`** — lectura fresca bajo lock, fusión por clave.
3. **Sin IP real** — todo el tráfico HTTP vía `socks5h://127.0.0.1:9050`.
4. **Cero APIs de pago** y cero credenciales en el repositorio.
5. **Scripts reutilizables** viven en el repo (no en `/tmp`, que se limpia).

## Roadmap

- [ ] Empujar cobertura de organizador/email >95% en el dataset global.
- [ ] Resolver el 5.47 % restante de fechas pendientes (estrategias de autenticación/verificación alternativas).
- [ ] Clasificación `no_psy` asistida por modelo y revalidación de 2.3 k filas archivadas.
- [ ] Exportadores (iCal/JSON API) y panel de métricas del dataset.

## Contribuir

Ver [`CONTRIBUTING.md`](CONTRIBUTING.md), [`ARCHITECTURE.md`](ARCHITECTURE.md),
[`CHANGELOG.md`](CHANGELOG.md) y [`SECURITY.md`](SECURITY.md).
Usa las plantillas de [issues](.github/ISSUE_TEMPLATE) y [PR](.github/PULL_REQUEST_TEMPLATE.md).

## Licencia

Uso privado — distribución restringida. Ver [`LICENSE`](LICENSE).