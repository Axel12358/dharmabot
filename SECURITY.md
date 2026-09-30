# Politica de Seguridad

**dharmabot** opera como plataforma privada de inteligencia de eventos. La seguridad del código, de los datos y del anonimato de la infraestructura es una prioridad de diseño.

## Principios

- **Cero credenciales en el repositorio**: no se versionan tokens, contraseñas ni claves de ningún tipo.
- **Cero IP real**: todo el tráfico HTTP de red viaja por Tor (`socks5h://127.0.0.1:9050`).
- **Cero APIs de pago**: no se utilizan servicios de extracción de pago.
- **Datos privados**: los datasets, cachés y estado de ejecución reside solo en la máquina operativa (`~/dharmabot`) y por defecto el repositorio es privado.

## Reportar una vulnerabilidad

Este repositorio es **privado y de uso interno**. Si detectas una vulnerabilidad en el código o en la configuración:

1. **No** la expongas en issues, PRs ni en foros públicos.
2. Reporta por canal privado (contacto directo del titular del repositorio).
3. Incluye: archivo/línea afectada, descripción del impacto y pasos de reproducción (si aplica).

## Alcance de soporte

| Componente | Soporte |
|---|---|
| `core/` (pipeline) | Activo |
| Scripts operativos raíz | Activo |
| Datos/caches/módulos generados | Fuera de alcance (runtime local) |

## Buenas prácticas al implementar

- Todos los escritores de datos deben pasar por `core/csv_lock.py` (`csv_locked_rows`).
- No introducir credenciales, URLs privadas ni identificadores de terceros en código versionado.
- No deshabilitar la salida por Tor en nuevos módulos HTTP.