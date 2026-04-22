# AERSA

## Diseño de un copiloto analítico para la interpretación del Cierre de Semana en TALOS

Ideas:
Mejorar UX/UI
Deteccion de errores con series de tiempo (Rechazado por estacionalidad en restaurantes)
Reglas empiricas para deteccion de fraudes
LLM con query tools (copilot)
Reporte semanal con gráficas y alertas con botón de enterado/validar info

## Carga local de `talos_tecmty` con Docker

Se agregó una configuración de `docker-compose` para crear la base `talos_tecmty`, importar estructura y datos desde `data/talos_tecmty/`, y ejecutar una validación inicial.
El puerto publicado por defecto es `3307` (para evitar choques con instalaciones locales en `3306`).

1. Levanta MySQL:

```bash
docker compose up -d mysql
```

2. Revisa el avance de importación (la primera carga puede tardar por el dump de ~2GB):

```bash
docker compose logs -f mysql
```

3. Valida conteos manualmente:

```bash
docker compose exec -T mysql mysql -uroot -proot -D talos_tecmty -e "SHOW TABLES; SELECT COUNT(*) AS unidadmedida FROM unidadmedida; SELECT COUNT(*) AS categoria FROM categoria; SELECT COUNT(*) AS almacen FROM almacen; SELECT COUNT(*) AS productotalos FROM productotalos; SELECT COUNT(*) AS producto FROM producto; SELECT COUNT(*) AS inventariomes FROM inventariomes; SELECT COUNT(*) AS inventariomesdetalle FROM inventariomesdetalle;"
```

Conexión desde host (equivalente a tus comandos originales):

```bash
mysql -h 127.0.0.1 -P 3307 -u root -p talos_tecmty
```

Notas:
- La importación automática corre solo en el primer arranque (cuando el volumen de MySQL está vacío).
- Para volver a importar desde cero:

```bash
docker compose down -v
docker compose up -d mysql
```

## Desarrollo en tiempo real con Docker

Para que frontend y backend reflejen cambios al instante, usa el override `docker-compose.dev.yml`:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

- Frontend: corre en modo `next dev` con recarga en caliente.
- Backend: usa bind mount de `./app/backend` (el `--reload` ya está en su `CMD`).

Para detener:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml down
```
