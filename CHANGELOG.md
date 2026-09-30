# Changelog

Todas las versiones notables de **dharmabot** quedan registradas aquí.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y versionado semántico.

## [0.1.0] — 2026-09-30

Funda del repositorio formal y consolidación del dataset global en producción.

### Añadido

- Repositorio público de **código y documentación** (`core/`, scripts operativos, docs).
- Capa profesional: `README.md`, `pyproject.toml`, `requirements.txt`, `Makefile`, `.gitignore`, `LICENSE` propietaria.
- `core/csv_lock.py` como contrato único de escritura (flock + atómica) para todos los writers.

### Mejorado

- **Dataset global**: 14.491 eventos psytrance 2025-2028 bajo operación continua.
- **Fechas**: 94,5% resueltas (pipeline FB `og:description` + variante móvil); el resto queda como `fecha_pendiente` sin inventar datos.
- **Organizador**: 92% de cobertura (SERP por ciudad + explotación offline de cachés de descripción FB).
- **Email de contacto**: 88% de cobertura (Rama A, venue-first y propagación por host de página).
- **Clasificación no-psy**: 2.345 filas archivadas con motivo; 3 eventos psy reclamados y devueltos al dataset.

### Seguridad / Operación

- Runtime migrado a `~/dharmabot`; jobs de LaunchAgents recargados con las rutas nuevas.
- Proyecto renombrado a **dharmabot** (adiós a `dharmadhatu_agent_qwen`): sin "qwen", sin "agente".
- Repositorios puestos en privado hasta definición de publicación.

## [0.0.1] — 2026-07 (desarrollo inicial)

- Primeros prototipos de scraping de eventos Facebook, Resident Advisor y Goabase.
- Clasificador de subgéneros por palabras clave (progressive, forest, darkpsy, hi-tech, goa, full-on, suomisaundi).
- Introducción de Tor como canal obligatorio de tráfico.