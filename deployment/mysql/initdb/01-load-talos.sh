#!/bin/bash
set -euo pipefail

# Set USE_SUBSET=1 to load only sucursal 13 data (fast, for Railway/staging).
# Leave unset or USE_SUBSET=0 for the full dataset.
USE_SUBSET="${USE_SUBSET:-0}"

echo "Initializing talos_tecmty database..."

mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" <<'SQL'
CREATE DATABASE IF NOT EXISTS talos_tecmty CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SQL

if [ "${USE_SUBSET}" = "1" ]; then
  echo "Importing subset (sucursal 13 only — structure + data in one file)..."
  mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" talos_tecmty < "/seed/subset_sucursal13.sql"
else
  echo "Importing full structure..."
  mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" talos_tecmty < "/seed/talos_tecmty _structure.sql"
  echo "Importing full data (this can take a while)..."
  mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" talos_tecmty < "/seed/talos_tecmty_data.sql"
fi

echo "Running validation queries..."
mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" talos_tecmty <<'SQL'
SHOW TABLES;
SELECT COUNT(*) AS unidadmedida FROM unidadmedida;
SELECT COUNT(*) AS categoria FROM categoria;
SELECT COUNT(*) AS almacen FROM almacen;
SELECT COUNT(*) AS productotalos FROM productotalos;
SELECT COUNT(*) AS producto FROM producto;
SELECT COUNT(*) AS inventariomes FROM inventariomes;
SELECT COUNT(*) AS inventariomesdetalle FROM inventariomesdetalle;
SQL

echo "talos_tecmty import completed."
