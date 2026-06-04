# 🗂️ Plan: Módulo de Consultas a Datos (NL → SQL / API REST)

> Consultar datos de **distintos orígenes** (APIs REST y bases MySQL) a partir de lo
> que el usuario diga (texto o voz), usando un **archivo de reglas** que define qué
> tablas/recursos hay disponibles y por qué "keys" se reconocen. La IA **solo lee**
> (nunca escribe) y devuelve un **objeto estructurado** (texto / tabla / —fase 2—
> gráfico).

---

## 🎯 Objetivo

Añadir un módulo nuevo (`/api/v1/consultas`) que:

1. Reciba `consulta` (texto; la voz ya se transcribe con el módulo existente) y `origen`.
2. Use un **catálogo de reglas** (`config/rules.yaml`) para, a partir de las "keys"
   de la consulta, **acotar** las tablas/recursos candidatos → **menos tokens** y la IA
   sabe de dónde sacar la información.
3. Genere una **consulta de solo lectura**:
   - **SQL (MySQL/MariaDB)**: la IA genera un `SELECT`, se **valida** y se ejecuta con
     un usuario **read-only**.
   - **API REST**: la IA (o el mapeo de reglas) elige el endpoint `GET` y arma los params.
4. Devuelva un **objeto estructurado** con `tipo` (`texto` | `tabla` | `grafico`),
   columnas, filas, resumen y metadatos.

### Alcance por fases

| Fase | Contenido | Estado |
|------|-----------|--------|
| **Fase 1** | Orígenes REST + MySQL read-only, catálogo de reglas, NL→SQL/intent, salida `texto`/`tabla`, seguridad en capas. | ✅ Implementada |
| **Fase 2** | `tipo: grafico` → el objeto incluye `grafico` (`tipo_grafico`, `etiquetas`, `series`) listo para Chart.js. Agregación `conteo`/`suma` en el servidor para REST; `GROUP BY`/`SUM` en la BD para SQL. | ✅ Implementada |

---

## 🧩 Decisiones (confirmadas con el usuario)

- **Orígenes**: principalmente **API REST** (menor riesgo); **MySQL** local y externas como segundo origen.
- **Solo-lectura en capas**: **usuario MySQL read-only** + **validación del SQL generado** + estándares de seguridad.
- **Salida**: **objeto estructurado** (el frontend pinta tabla/gráfico).

---

## 🏗️ Arquitectura

```
                ┌──────────────────────────────────────────────┐
   texto/voz →  │  POST /api/v1/consultas  (consulta, origen)  │
                └───────────────────────┬──────────────────────┘
                                        ▼
                              ┌───────────────────┐
                              │   Orquestador     │
                              └─────────┬─────────┘
            ┌───────────────────────────┼───────────────────────────┐
            ▼                           ▼                           ▼
   ┌─────────────────┐        ┌──────────────────┐        ┌──────────────────┐
   │  Catálogo +     │        │   Generador LLM  │        │   Formateador    │
   │  Matcher (keys) │  ───▶  │ NL→SQL / NL→intent│ ───▶  │  objeto estruct. │
   └─────────────────┘        └────────┬─────────┘        └──────────────────┘
        (rules.yaml)                   ▼
                          ┌─────────────────────────────┐
                          │  origen = sql_mysql          │
                          │   seguridad_sql (read-only)  │
                          │   ejecutor_sql (user RO)     │
                          │  origen = rest_api           │
                          │   ejecutor_rest (GET + SSRF) │
                          └─────────────────────────────┘
```

### Archivos nuevos

```
config/
  rules.example.yaml                 # Catálogo de orígenes (copiar a rules.yaml)
app/
  schemas/consultas.py               # Pydantic: request + respuesta estructurada
  clients/mysql.py                   # Factory de engines MySQL read-only (cache por origen)
  services/consultas/
    __init__.py
    catalogo.py                      # Carga rules.yaml + matcher por keys/aliases
    llm.py                           # Factory de LLM de chat (reusa LLM_PROVIDER)
    seguridad_sql.py                 # Validación read-only (sqlglot) + LIMIT forzado
    ejecutor_sql.py                  # Ejecuta SELECT con timeout y tope de filas
    ejecutor_rest.py                 # Cliente REST GET con allowlist de host (anti-SSRF)
    generador.py                     # NL→SQL (MySQL) / NL→intent (REST) vía LLM
    formateador.py                   # Construye el objeto estructurado de salida
    orquestador.py                   # Une todo el flujo
  api/v1/endpoints/consultas.py      # Router /api/v1/consultas
tests/unit/test_seguridad_sql.py     # Tests offline de la validación read-only
```

### Archivos modificados

- `requirements.txt` → `pymysql`, `sqlglot`, `pyyaml` (SQLAlchemy y pandas ya están).
- `app/core/config.py` → settings del módulo (flag, ruta de reglas, topes, timeouts).
- `app/api/v1/router.py` → incluir `consultas_router`.
- `.env.example` → variables nuevas (documentadas).

---

## 📐 Catálogo de reglas (`config/rules.yaml`)

El catálogo es la **única fuente de verdad** de qué puede consultar el bot. Los secretos
**no** van en el YAML: se referencian por **nombre de variable de entorno**.

```yaml
origenes:
  rh_api:
    tipo: rest_api
    descripcion: "API de Recursos Humanos (empleados, departamentos)"
    base_url_env: API_RH_URL          # se lee de .env; valida host (anti-SSRF)
    timeout: 10
    recursos:
      - nombre: empleados
        keys: [empleado, empleados, usuario, usuarios, user, personal, colaborador]
        endpoint: "/users"            # solo GET
        descripcion: "Lista de empleados con departamento, área, puesto"
        params_permitidos: [departamento, area, activo, q]

  ventas_db:
    tipo: sql_mysql
    descripcion: "Base de datos de ventas (solo lectura)"
    dsn_env: VENTAS_DB_URL            # mysql+pymysql://ro_user:***@host/db
    max_filas: 500
    timeout: 8
    tablas:
      - nombre: usuarios
        keys: [usuario, usuarios, user, users, cliente, clientes]
        descripcion: "Usuarios registrados"
        columnas:
          - {nombre: id, tipo: int, descripcion: "ID"}
          - {nombre: nombre, tipo: varchar, descripcion: "Nombre completo"}
          - {nombre: email, tipo: varchar}
          - {nombre: fecha_ingreso, tipo: date, descripcion: "Alta del usuario"}
```

**Matcher (reducción de tokens):** se normaliza la consulta (minúsculas, sin acentos) y
se buscan las `keys`. Solo el esquema de las tablas/recursos que coinciden se envía al LLM.
Si nada coincide, se manda una lista compacta (solo nombres + descripción) para que el LLM
elija, o se pide aclaración.

---

## 🔒 Seguridad en capas (estándares)

1. **Usuario MySQL read-only** (a nivel motor):
   ```sql
   CREATE USER 'ro_bot'@'%' IDENTIFIED BY '***';
   GRANT SELECT ON ventas.* TO 'ro_bot'@'%';
   ```
   El DSN del `.env` usa estas credenciales. Es la defensa más fuerte.

2. **Validación del SQL generado** (`seguridad_sql.py`, con `sqlglot`):
   - Solo se permite **una** sentencia y debe ser `SELECT` (o `WITH … SELECT`).
   - Se rechaza cualquier DDL/DML (`INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/GRANT/…`),
     transacciones, multi-statement y comentarios.
   - Se bloquean primitivas peligrosas de MySQL: `INTO OUTFILE/DUMPFILE`, `LOAD_FILE`,
     `SLEEP`, `BENCHMARK`, `information_schema` (salvo que se permita explícitamente).
   - **Allowlist**: las tablas/columnas referidas deben existir en las reglas del origen.
   - **LIMIT forzado**: si falta, se inyecta; si excede `max_filas`, se recorta.

3. **Ejecución acotada** (`ejecutor_sql.py`):
   - `SET SESSION MAX_EXECUTION_TIME` (timeout en el servidor) + timeout de conexión.
   - Tope de filas materializadas (`max_filas`).
   - Engine por origen con `pool_pre_ping`; credenciales nunca en logs.

4. **REST anti-SSRF** (`ejecutor_rest.py`):
   - Solo método **GET**; la URL final debe pertenecer al `base_url` configurado.
   - `params` filtrados por `params_permitidos`; timeout y tope de tamaño de respuesta.

5. **Generales**:
   - Flag `CONSULTAS_ENABLED` (apagado por defecto).
   - Límites de longitud de entrada; **auditoría** (log de origen + consulta generada).
   - Errores genéricos al cliente (el handler global ya oculta detalles internos).

---

## 🔁 Flujo detallado

1. **Entrada** → `{consulta, origen, formato?}`. Se valida que `origen` exista y esté habilitado.
2. **Matcher** → tablas/recursos candidatos a partir de las keys.
3. **Generación (LLM)** → devuelve JSON:
   - SQL: `{ "sql": "...", "titulo": "...", "tipo": "tabla|texto" }`.
   - REST: `{ "recurso": "...", "params": {...}, "titulo": "...", "tipo": "..." }`.
4. **Validación + ejecución** según el origen (read-only).
5. **Formateo** → `ConsultaResponse` estructurada (columnas/filas/resumen/meta).
6. **Salida** → JSON al frontend (que pinta tabla; en fase 2, gráfico).

### Ejemplo de respuesta

```json
{
  "origen": "ventas_db",
  "tipo": "tabla",
  "titulo": "Usuarios registrados desde 2026-01-01",
  "texto": "Se encontraron 42 usuarios registrados a partir del 1 de enero de 2026.",
  "tabla": {
    "columnas": ["id", "nombre", "email", "fecha_ingreso"],
    "filas": [[1, "Ana López", "ana@x.com", "2026-02-03"]],
    "total_filas": 42,
    "truncado": false
  },
  "grafico": null,
  "meta": {
    "origen_tipo": "sql_mysql",
    "consulta_generada": "SELECT id, nombre, email, fecha_ingreso FROM usuarios WHERE fecha_ingreso >= '2026-01-01' LIMIT 500",
    "advertencias": []
  },
  "tiempo_respuesta": 1.8
}
```

---

## ⚙️ Variables de entorno nuevas

```env
# ===== Módulo de Consultas a Datos =====
CONSULTAS_ENABLED=false
RULES_PATH=config/rules.yaml
CONSULTAS_MAX_FILAS=500          # tope global de filas devueltas
CONSULTAS_SQL_TIMEOUT=8          # segundos máx. de ejecución por consulta SQL
CONSULTAS_REST_TIMEOUT=10        # segundos de timeout para orígenes REST

# DSN de cada origen SQL (usuario READ-ONLY). El nombre lo define dsn_env en rules.yaml
VENTAS_DB_URL=mysql+pymysql://ro_bot:password@localhost:3306/ventas
```

---

## ✅ Pasos de implementación

1. Dependencias + settings + `.env.example`.
2. `config/rules.example.yaml`.
3. `schemas/consultas.py`.
4. `services/consultas/catalogo.py` (carga + matcher).
5. `services/consultas/seguridad_sql.py` (+ test unitario offline).
6. `clients/mysql.py` + `ejecutor_sql.py` + `ejecutor_rest.py`.
7. `services/consultas/llm.py` + `generador.py` + `formateador.py`.
8. `services/consultas/orquestador.py` + `endpoints/consultas.py` + registrar router.
9. Verificar imports y tests.

---

## 🧪 Pruebas

- **Unitario (offline)**: `seguridad_sql` acepta `SELECT`/`WITH` y rechaza DML/DDL,
  multi-statement, `INTO OUTFILE`, `SLEEP`, tablas fuera de la allowlist; inyecta/recorta `LIMIT`.
- **Integración (manual)**: `/api/v1/consultas/health`, una consulta REST contra la API RH
  y una consulta SQL contra una MySQL de prueba con usuario read-only.

---

## 🚫 Fuera de alcance (fase 1)

- Generación de gráficos (solo se deja el campo `grafico` y el `tipo`).
- Escritura en cualquier origen (el sistema es estrictamente de solo lectura).
- `JOIN`/consultas multi-tabla complejas no acotadas por reglas (se permiten solo tablas del catálogo).
