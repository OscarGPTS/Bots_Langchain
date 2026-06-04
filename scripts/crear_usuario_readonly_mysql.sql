-- =====================================================================
-- Usuario MySQL/MariaDB de SOLO LECTURA para el módulo de Consultas
-- =====================================================================
-- Crea un usuario con permiso únicamente de SELECT sobre las tablas que el
-- catálogo (config/rules.yaml) expone para `cartera_db`. Es la capa de
-- seguridad a nivel motor (defensa en profundidad junto a la validación de SQL).
--
-- Cómo ejecutarlo (XAMPP / Windows PowerShell):
--   & "C:\xampp\mysql\bin\mysql.exe" -u root < scripts\crear_usuario_readonly_mysql.sql
-- O desde phpMyAdmin -> pestaña SQL -> pegar y ejecutar.
--
-- ⚠️ CAMBIA la contraseña por una propia antes de usar en algo serio.
-- =====================================================================

-- 1) Crear el usuario (para conexión TCP por 127.0.0.1 y por localhost)
CREATE USER IF NOT EXISTS 'cartera_ro'@'127.0.0.1' IDENTIFIED BY 'CAMBIA_ESTA_CONTRASENA';
CREATE USER IF NOT EXISTS 'cartera_ro'@'localhost'  IDENTIFIED BY 'CAMBIA_ESTA_CONTRASENA';

-- 2) Conceder SOLO SELECT y SOLO sobre las tablas mapeadas (mínimo privilegio).
--    Si prefieres permitir toda la base, usa en su lugar:
--      GRANT SELECT ON cartera_clientes.* TO 'cartera_ro'@'127.0.0.1';
GRANT SELECT ON cartera_clientes.clientes          TO 'cartera_ro'@'127.0.0.1';
GRANT SELECT ON cartera_clientes.contactos_cliente TO 'cartera_ro'@'127.0.0.1';
GRANT SELECT ON cartera_clientes.proyectos         TO 'cartera_ro'@'127.0.0.1';
GRANT SELECT ON cartera_clientes.cotizaciones      TO 'cartera_ro'@'127.0.0.1';
GRANT SELECT ON cartera_clientes.users             TO 'cartera_ro'@'127.0.0.1';

GRANT SELECT ON cartera_clientes.clientes          TO 'cartera_ro'@'localhost';
GRANT SELECT ON cartera_clientes.contactos_cliente TO 'cartera_ro'@'localhost';
GRANT SELECT ON cartera_clientes.proyectos         TO 'cartera_ro'@'localhost';
GRANT SELECT ON cartera_clientes.cotizaciones      TO 'cartera_ro'@'localhost';
GRANT SELECT ON cartera_clientes.users             TO 'cartera_ro'@'localhost';

-- 3) Aplicar cambios
FLUSH PRIVILEGES;

-- 4) (Opcional) Verificar los privilegios otorgados
-- SHOW GRANTS FOR 'cartera_ro'@'127.0.0.1';

-- =====================================================================
-- Luego, en .env (NO versionado), apunta el DSN a este usuario con la contraseña real:
--   CARTERA_DB_URL=mysql+pymysql://cartera_ro:TU_PASSWORD@127.0.0.1:3306/cartera_clientes
-- Nota: si la contraseña tiene caracteres especiales (@ : / # etc.), codifícalos en el
-- DSN (URL-encoding). Por ejemplo, '@' se escribe como %40.
-- =====================================================================
