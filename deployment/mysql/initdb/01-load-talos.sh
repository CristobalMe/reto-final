#!/bin/bash
set -euo pipefail

echo "Initializing talos_tecmty database..."

mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" <<'SQL'
CREATE DATABASE IF NOT EXISTS talos_tecmty CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SQL

echo "Importing structure..."
mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" talos_tecmty < "/seed/talos_tecmty _structure.sql"

echo "Importing data (this can take a while)..."
mysql -uroot -p"${MYSQL_ROOT_PASSWORD}" talos_tecmty < "/seed/talos_tecmty_data.sql"

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
