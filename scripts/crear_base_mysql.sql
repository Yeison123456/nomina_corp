-- ==========================================================================
-- Libra — Sistema de Nómina
-- Crea la base de datos y el usuario de la aplicación en MySQL 8.
--
-- Ejecutar como root:
--   mysql -u root -p < scripts/crear_base_mysql.sql
--
-- Cambie la contraseña 'libra2026' y use la misma en el archivo .env
-- ==========================================================================

CREATE DATABASE IF NOT EXISTS libra_nomina
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'libra'@'localhost' IDENTIFIED BY 'libra2026';
CREATE USER IF NOT EXISTS 'libra'@'127.0.0.1' IDENTIFIED BY 'libra2026';

-- Permisos sobre la base de la aplicación
GRANT ALL PRIVILEGES ON libra_nomina.* TO 'libra'@'localhost';
GRANT ALL PRIVILEGES ON libra_nomina.* TO 'libra'@'127.0.0.1';

-- Permisos sobre la base temporal que crean las pruebas automatizadas
GRANT ALL PRIVILEGES ON test_libra_nomina.* TO 'libra'@'localhost';
GRANT ALL PRIVILEGES ON test_libra_nomina.* TO 'libra'@'127.0.0.1';

FLUSH PRIVILEGES;
