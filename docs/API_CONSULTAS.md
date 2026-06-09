# 🗂️ API de Consultas a Datos — Guía del servicio

> Servicio que responde, en **lenguaje natural** (texto o voz), consultas de **solo
> lectura** sobre distintos orígenes de datos (bases **MySQL/MariaDB** y **APIs REST**),
> y devuelve un **objeto estructurado** (`texto` / `tabla` / `grafico`) listo para pintar
> en el frontend.

Esta guía es **autocontenida**: con ella un equipo puede consumir el servicio y/o
configurar nuevos orígenes sin leer el resto del proyecto.

---

## 📑 Índice

1. [¿Qué hace y cómo funciona?](#-qué-hace-y-cómo-funciona)
2. [Endpoints](#-endpoints)
3. [Esquema de la respuesta](#-esquema-de-la-respuesta)
4. [Campos de la petición](#-campos-de-la-petición)
5. [Ejemplos de uso](#-ejemplos-de-uso)
6. [Pintar tabla y gráfico (frontend)](#-pintar-tabla-y-gráfico-frontend)
7. [Consulta por voz](#-consulta-por-voz)
8. [Configurar orígenes (rules.yaml)](#-configurar-orígenes-rulesyaml)
9. [Seguridad (solo lectura)](#-seguridad-solo-lectura)
10. [Códigos de error](#-códigos-de-error)
11. [Puesta en marcha (.env)](#-puesta-en-marcha-env)
12. [FAQ / problemas comunes](#-faq--problemas-comunes)

---

## 📥 Importar la API (OpenAPI / Postman)

Para empezar a probar sin copiar curls a mano:

- **OpenAPI / Swagger:** [`openapi_consultas.json`](openapi_consultas.json) — impórtalo en
  Swagger Editor, Insomnia, o cualquier cliente compatible con OpenAPI 3.
- **Postman:** [`postman_consultas.json`](postman_consultas.json) — *Import* en Postman;
  trae los 3 endpoints con ejemplos. Ajusta la variable `baseUrl` (por defecto
  `http://localhost:8000`).
- **Swagger UI en vivo:** `http://localhost:8000/docs` (grupo **Consultas**).

> Ambos archivos se regeneran con: `python scripts/exportar_openapi_consultas.py`.

---

## 🧠 ¿Qué hace y cómo funciona?

El cliente envía **qué quiere** (`consulta`) y **dónde buscarlo** (`origen`). El servicio:

1. **Acota el contexto** — usa un catálogo de reglas (`config/rules.yaml`) para detectar,
   por palabras clave (`keys`), qué tablas/recursos son relevantes. Así envía al modelo
   solo lo necesario (menos tokens, menos errores). Se puede **fijar la entidad** con el
   campo `objetivo`.
2. **Genera la consulta** — un LLM traduce la pregunta a un `SELECT` de MySQL (o elige un
   endpoint REST `GET` con sus parámetros).
3. **Valida y ejecuta (solo lectura)** — el SQL pasa por un validador (solo `SELECT`,
   allowlist de tablas, `LIMIT` forzado) y se ejecuta con un usuario MySQL de solo
   lectura; el REST solo admite `GET` contra el host configurado.
4. **Estructura la salida** — decide si conviene `texto`, `tabla` o `grafico` y arma el
   objeto de respuesta (incluida la agregación de datos para gráficos).

```
consulta + origen ──► [matcher/objetivo] ──► [LLM: NL→SQL/REST] ──► [validación+ejecución RO] ──► objeto {texto|tabla|grafico}
```

**Base URL:** `https://bots.tech-energy.lat` (prod) · `http://localhost:8000` (local).
**Prefijo:** `/api/v1/consultas`.

### Mensajes conversacionales (saludos / ayuda)

Antes de intentar consultar datos, el bot reconoce mensajes que **no** son una consulta
(saludos, agradecimientos, despedidas y peticiones de ayuda) y responde de forma amigable,
**sin generar SQL ni tocar la base de datos**. Así un `"hola"` o `"¿qué puedes hacer?"` no
produce errores. La respuesta llega como `tipo: "texto"` (con `meta.consulta_generada: null`).

| Entrada | Respuesta |
|---------|-----------|
| `"hola"` | Saludo + qué puede consultar el origen |
| `"¿qué puedes hacer?"`, `"ayuda"`, `"no sé qué preguntar"` | Lista de entidades del origen + ejemplos |
| `"gracias"`, `"adiós"` | Respuesta cordial |

> Es determinista (sin coste de LLM) y respeta `usuario` para personalizar. Para mensajes
> que sí son consultas reales, el flujo continúa normal.

---

## 🔌 Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/v1/consultas/` | Consulta por texto → objeto estructurado |
| `POST` | `/api/v1/consultas/voz` | Consulta por voz (audio) → objeto + resumen hablado |
| `GET`  | `/api/v1/consultas/health` | Estado del módulo y orígenes disponibles |

### `GET /api/v1/consultas/health`

```json
{
  "consultas_enabled": true,
  "rules_cargado": true,
  "rules_path": "config/rules.yaml",
  "total_origenes": 2,
  "origenes": [
    { "clave": "cartera_db", "tipo": "sql_mysql", "descripcion": "...", "tablas_o_recursos": ["clientes", "proyectos", "cotizaciones", "users"] },
    { "clave": "rh_api", "tipo": "rest_api", "descripcion": "...", "tablas_o_recursos": ["empleados"] }
  ],
  "error_rules": null
}
```
Úsalo para descubrir **qué orígenes y entidades** hay disponibles antes de consultar.

---

## 📦 Esquema de la respuesta

`POST /api/v1/consultas/` devuelve un objeto `ConsultaResponse`:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `origen` | string | Origen consultado |
| `tipo` | `"texto"` \| `"tabla"` \| `"grafico"` | Cómo representar la respuesta |
| `titulo` | string \| null | Título legible |
| `texto` | string \| null | Resumen/respuesta en lenguaje natural (corto, apto para voz) |
| `tabla` | objeto \| null | Datos tabulares (ver abajo) |
| `grafico` | objeto \| null | Especificación de gráfico (ver abajo) |
| `meta` | objeto | Trazabilidad (SQL/endpoint ejecutado, candidatos, advertencias) |
| `tiempo_respuesta` | number | Segundos |

**`tabla`:**
```json
{ "columnas": ["sector", "cantidad"], "filas": [["Oil & Gas", 20]], "total_filas": 6, "truncado": false }
```

**`grafico`** (formato compatible con Chart.js):
```json
{ "tipo_grafico": "bar", "etiquetas": ["Oil & Gas", "Gasoductos"], "series": [{ "label": "cantidad", "data": [20, 16] }] }
```

**`meta`:**
```json
{ "origen_tipo": "sql_mysql", "consulta_generada": "SELECT ...", "candidatos": ["clientes"], "advertencias": [] }
```

> **Regla de oro para el frontend:** mira `tipo` y pinta `texto`, `tabla` o `grafico`.
> Cuando `tipo="grafico"` también viene `tabla` con los datos crudos (por si quieres
> mostrar ambos).

---

## 📝 Campos de la petición

`POST /api/v1/consultas/` (JSON):

| Campo | Req. | Tipo | Descripción |
|-------|------|------|-------------|
| `consulta` | ✅ | string (3–1000) | Lo que pide el usuario en lenguaje natural |
| `origen` | ✅ | string | Identificador del origen: su **clave** (`cartera_db`) o cualquier **alias** (nombre del sistema, tag o URL). Ver "Identificar el origen" abajo. |
| `formato` | — | `texto`\|`tabla`\|`grafico` | Fuerza el tipo de salida (si se omite, lo decide la IA) |
| `objetivo` | — | string | **Tabla/recurso específico**: omite el matcher y trabaja solo sobre esa entidad (más preciso) |
| `usuario` | — | string | Nombre de quien consulta; personaliza `texto`/audio |

---

## 💡 Ejemplos de uso

### Listado → `tabla`
```bash
curl -X POST "http://localhost:8000/api/v1/consultas/" \
  -H "Content-Type: application/json" \
  -d '{"consulta":"top 5 proyectos por monto en usd","origen":"cartera_db","usuario":"Óscar"}'
```
```json
{
  "origen": "cartera_db", "tipo": "tabla",
  "titulo": "Top 5 proyectos por monto en USD",
  "texto": "Óscar, aquí tienes el resultado: 5 registro(s).",
  "tabla": { "columnas": ["id","cp_numero","monto_usd","estado"], "filas": [[18,null,23983952.93,"presentado"]], "total_filas": 5, "truncado": false },
  "grafico": null,
  "meta": { "origen_tipo": "sql_mysql", "consulta_generada": "SELECT id, cp_numero, monto_usd, estado FROM proyectos ORDER BY monto_usd DESC LIMIT 5", "candidatos": ["proyectos"], "advertencias": [] },
  "tiempo_respuesta": 2.1
}
```

### Agregación → `grafico`
```bash
curl -X POST "http://localhost:8000/api/v1/consultas/" -H "Content-Type: application/json" \
  -d '{"consulta":"cuántos clientes hay por sector","origen":"cartera_db"}'
```
```json
{
  "tipo": "grafico", "titulo": "Clientes por sector",
  "grafico": { "tipo_grafico": "bar", "etiquetas": ["Oil & Gas","Gasoductos"], "series": [{ "label": "cantidad", "data": [20,16] }] },
  "tabla": { "columnas": ["sector","cantidad"], "total_filas": 6, "truncado": false },
  "meta": { "consulta_generada": "SELECT sector, COUNT(*) AS cantidad FROM clientes GROUP BY sector ORDER BY cantidad DESC LIMIT 500" }
}
```

### Consulta dirigida (`objetivo`) + relación FK (JOIN)
```bash
curl -X POST "http://localhost:8000/api/v1/consultas/" -H "Content-Type: application/json" \
  -d '{"consulta":"monto total por cliente, top 5","origen":"cartera_db","objetivo":"proyectos"}'
```
Al fijar `objetivo:"proyectos"` y tener declarada la relación `proyectos→clientes` en las
reglas, el modelo genera el JOIN correcto:
```sql
SELECT c.razon_social, SUM(p.monto_usd) AS total_monto
FROM proyectos AS p JOIN clientes AS c ON p.cliente_id = c.id
GROUP BY c.id, c.razon_social ORDER BY total_monto DESC LIMIT 5
```

### PowerShell
```powershell
$body = @{ consulta = "cuántos clientes hay por sector"; origen = "cartera_db" } | ConvertTo-Json
Invoke-RestMethod "http://localhost:8000/api/v1/consultas/" -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 8
```

---

## 🖥️ Pintar tabla y gráfico (frontend)

```javascript
async function consultar(consulta, origen, opts = {}) {
  const r = await fetch("/api/v1/consultas/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ consulta, origen, ...opts })   // opts: { formato, objetivo, usuario }
  }).then(x => x.json());

  switch (r.tipo) {
    case "grafico":
      new Chart(document.getElementById("canvas"), {
        type: r.grafico.tipo_grafico,                 // "bar" | "line" | "pie"
        data: { labels: r.grafico.etiquetas, datasets: r.grafico.series }  // series = [{label, data}]
      });
      break;
    case "tabla":
      pintarTabla(r.tabla.columnas, r.tabla.filas);   // tu render de tabla
      break;
    default:                                          // "texto"
      mostrarTexto(r.texto);
  }
}
```

---

## 🎙️ Consulta por voz

`POST /api/v1/consultas/voz` — **multipart/form-data**. Transcribe el audio (STT), lo
procesa igual que una consulta de texto y devuelve el objeto estructurado + un **resumen
hablado** opcional. Requiere `VOICE_ENABLED=true`.

**Campos (form-data):** `file` (audio webm/wav/mp3/ogg/m4a, requerido), `origen`
(requerido), `formato`, `objetivo`, `usuario`, `responder_voz` (bool, default `true`).

```bash
curl -X POST "http://localhost:8000/api/v1/consultas/voz" \
  -F "file=@pregunta.webm" -F "origen=cartera_db" -F "usuario=Óscar"
```

**Respuesta (`ConsultaVozResponse`):**
```json
{
  "pregunta_transcrita": "cuántos clientes hay por sector",
  "resultado": { "...": "objeto ConsultaResponse completo (tipo/tabla/grafico/meta)" },
  "audio_base64": "UklGRiQAAABXQVZF...(WAV del resumen hablado)..."
}
```

> El audio **no dicta las filas** (sería enorme): lee una frase corta y personalizada
> (`resultado.texto`), p.ej. *"Óscar, aquí tienes el resultado: 6 registros."* La tabla
> o el gráfico completos se pintan desde `resultado`.

---

## 🏷️ Identificar el origen (clave o alias)

El campo `origen` acepta tanto la **clave canónica** como cualquier **alias** declarado en
`rules.yaml`. Los alias permiten que el cliente envíe el nombre del sistema, un tag o una
**URL**, sin tener que conocer la clave interna. La comparación es tolerante: ignora
mayúsculas, el esquema `http(s)://` y el `/` final.

```yaml
origenes:
  cartera_db:                       # clave canónica (uso interno, logs, respuesta)
    alias:
      - cartera
      - "Cartera de Clientes"
      - https://cartera-clientes.tech-energy.lat
      - http://localhost:8001
```

Con eso, todas estas peticiones resuelven al mismo origen (`origen` en la respuesta será
siempre la clave canónica `cartera_db`):
```json
{ "consulta": "...", "origen": "cartera" }
{ "consulta": "...", "origen": "https://cartera-clientes.tech-energy.lat/" }
{ "consulta": "...", "origen": "CARTERA_DB" }
```

> Los alias deben ser **únicos entre orígenes** (si dos orígenes comparten un alias, la
> resolución es ambigua). `GET /health` lista los alias de cada origen para que el cliente
> sepa qué puede enviar.

---

## ⚙️ Configurar orígenes (`rules.yaml`)

El catálogo `config/rules.yaml` es la **única fuente de verdad** de qué puede consultar el
bot (allowlist). **No contiene secretos**: las credenciales/URLs se referencian por
**nombre de variable de entorno**.

### Origen SQL (MySQL/MariaDB)

**Conexión — dos formas (elige una por origen):**

```yaml
# A) Estilo Laravel (recomendado): componentes por prefijo. No requiere URL-encodear
#    la contraseña. Lee {PREFIJO}_HOST, _PORT, _DATABASE, _USERNAME, _PASSWORD del .env.
origenes:
  cartera_db:
    tipo: sql_mysql
    conexion_prefijo: DB            # → DB_HOST, DB_PORT, DB_DATABASE, DB_USERNAME, DB_PASSWORD
```
```env
# .env (estilo Laravel)
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=cartera_clientes
DB_USERNAME=cartera_ro
DB_PASSWORD=tu_password            # se URL-encodea solo; '@', ':' etc. sin problema
```
```yaml
# B) DSN completo en una variable (alternativa).
origenes:
  cartera_db:
    tipo: sql_mysql
    descripcion: "Cartera de clientes (solo lectura)."
    dsn_env: CARTERA_DB_URL          # nombre de la var de entorno con el DSN read-only
    max_filas: 500                   # tope de filas (no supera CONSULTAS_MAX_FILAS)
    timeout: 8                       # segundos máx. de ejecución
    tablas:
      - nombre: proyectos
        keys: [proyecto, proyectos, oportunidad, oferta]   # alias que dispara esta tabla
        descripcion: "Proyectos y oportunidades comerciales."
        relaciones:                                        # FKs disponibles para JOIN
          - { tabla: clientes, on: "proyectos.cliente_id = clientes.id", descripcion: "Cliente del proyecto" }
        columnas:
          - { nombre: id, tipo: bigint }
          - { nombre: monto_usd, tipo: decimal, descripcion: "Monto en USD" }
          - { nombre: estado, tipo: enum, descripcion: "en_revision|cotizando|...|cerrado" }
          - { nombre: fecha_envio, tipo: date }
```

### Origen REST

```yaml
  rh_api:
    tipo: rest_api
    base_url_env: API_RH_URL          # host validado (anti-SSRF); solo GET
    timeout: 15
    recursos:
      - nombre: empleados
        keys: [empleado, empleados, rh, colaborador]
        endpoint: "/users"            # GET {base_url}/users
        lista_en: "data"              # dónde está la lista dentro del JSON ({success,total,data:[...]})
        params_permitidos: []         # allowlist de query params (vacío = ninguno)
        descripcion: "Empleados con departamento, área y puesto."
```

### Dar contexto de negocio (escalable)

Para que el bot "sepa por dónde ir" (fórmulas, convenciones, JOINs típicos) sin tocar
código, usa dos campos en `rules.yaml`:

- **`contexto`** (en el origen y/o en cada tabla): reglas de negocio en lenguaje natural.
  Ej.: *"Monto esperado = SUM(monto_usd \* ponderacion / 100)"*, *"catálogos: filtra status = 1"*.
- **`ejemplos`** (por tabla): pares `pregunta → sql` que el modelo replica adaptándolos.
  Ideales para reproducir vistas/dashboards existentes.

```yaml
tablas:
  - nombre: proyectos
    contexto: "Oportunidades = tipo='oportunidad'. Esperado = SUM(monto_usd*ponderacion/100)."
    ejemplos:
      - pregunta: "KPIs de la cartera: bruto, esperado y eficiencia"
        sql: >
          SELECT SUM(monto_usd) AS bruto,
                 SUM(monto_usd*ponderacion/100) AS esperado,
                 ROUND(SUM(monto_usd*ponderacion/100)/NULLIF(SUM(monto_usd),0)*100,1) AS eficiencia_pct
          FROM proyectos WHERE tipo='oportunidad' AND monto_usd > 0
```

> El contexto del origen se inyecta siempre; el contexto y los ejemplos de una tabla solo
> cuando esa tabla es candidata (mantiene el prompt enfocado y los tokens bajos). Las
> relaciones se resuelven de forma **transitiva** (hasta 2 saltos), así un ejemplo que
> cruza `proyectos → historial → ponderaciones` funciona sin declarar cada salto a mano.
>
> Ejemplo real completo: origen `cartera_db` en [config/rules.yaml](../config/rules.yaml),
> derivado de [CONTEXTO_GRAFICAS_DASHBOARD.md](CONTEXTO_GRAFICAS_DASHBOARD.md).

### Cómo agregar un nuevo origen (paso a paso)

1. **Crea un usuario MySQL de solo lectura** (ver más abajo) y añade su DSN en `.env`
   (p.ej. `VENTAS_DB_URL=mysql+pymysql://ro_user:pass@host:3306/ventas`).
2. **Declara el origen** en `rules.yaml` (`tipo`, `dsn_env`/`base_url_env`).
3. **Mapea las tablas/recursos** que quieras exponer, con sus `keys`, `columnas` y, si
   aplica, `relaciones` (FKs).
4. Reinicia la API y verifica en `GET /api/v1/consultas/health` que el origen aparece.

> **Menos es más:** expón solo las tablas/columnas necesarias. Reduce tokens, mejora la
> precisión y limita la superficie de datos accesible.

### Referencia de campos del catálogo

| Campo | Ámbito | Descripción |
|-------|--------|-------------|
| `tipo` | origen | `sql_mysql` \| `rest_api` |
| `alias` | origen | Identificadores alternativos aceptados como `origen` (nombres, tags, URLs). Únicos entre orígenes |
| `dsn_env` | SQL | Nombre de la var de entorno con el DSN completo (usuario read-only) |
| `conexion_prefijo` | SQL | Alternativa estilo Laravel: prefijo de variables `{P}_HOST/_PORT/_DATABASE/_USERNAME/_PASSWORD` |
| `base_url_env` | REST | Nombre de la var de entorno con la base URL |
| `max_filas`, `timeout` | origen | Topes locales (acotados por los globales del `.env`) |
| `tablas[]` / `recursos[]` | origen | Entidades expuestas |
| `keys[]` | entidad | Alias que el matcher busca en la consulta |
| `columnas[]` | tabla | `{nombre, tipo, descripcion}` (guía al modelo) |
| `relaciones[]` | tabla | `{tabla, on, descripcion}` — habilita JOIN y amplía la allowlist (transitivo hasta 2 saltos) |
| `contexto` | origen y tabla | Reglas de negocio/glosario que se inyectan al prompt (fórmulas, convenciones, filtros por defecto) |
| `ejemplos[]` | tabla | Few-shot `{pregunta, sql}`: enseñan a reproducir vistas/fórmulas del sistema. Se inyectan cuando la tabla es candidata |
| `endpoint`, `lista_en`, `params_permitidos` | recurso REST | Ruta GET, ubicación de la lista en el JSON, params permitidos |

---

## 🔒 Seguridad (solo lectura)

Defensa en capas. El bot **nunca** escribe:

1. **Usuario de BD read-only** — el DSN usa un usuario con `GRANT SELECT`. Es la defensa
   más fuerte (el motor rechaza cualquier escritura). Ver `scripts/crear_usuario_readonly_mysql.sql`.
2. **Validación del SQL generado** — solo `SELECT`/`WITH`; se rechaza `INSERT/UPDATE/DELETE/
   DDL`, multi-statement, `INTO OUTFILE`, `LOAD_FILE`, `SLEEP`, esquemas de sistema; las
   tablas deben estar en el catálogo; se fuerza/recorta `LIMIT`.
3. **Sesión** — `SET SESSION TRANSACTION READ ONLY` + timeout de ejecución.
4. **REST** — solo `GET`, host validado contra `base_url` (anti-SSRF), params filtrados.
5. **Catálogo (allowlist)** — solo las tablas/columnas/recursos declarados son accesibles.

> En `meta.consulta_generada` queda registrado el SQL/endpoint ejecutado para auditoría.

---

## 🚦 Códigos de error

| Código | Significado |
|--------|-------------|
| `200` | OK |
| `400` | Origen/objetivo inexistente, consulta inválida o SQL no permitido |
| `413` | (voz) Audio demasiado grande |
| `422` | (voz) Audio vacío o ininteligible |
| `503` | Módulo deshabilitado (`CONSULTAS_ENABLED`/`VOICE_ENABLED=false`), dependencias de voz faltantes o error de conexión con el origen |

Los errores devuelven `{ "detail": "mensaje" }`. Los detalles internos no se exponen.

---

## 🚀 Puesta en marcha (`.env`)

```env
CONSULTAS_ENABLED=true
RULES_PATH=config/rules.yaml
CONSULTAS_MAX_FILAS=500          # tope global de filas
CONSULTAS_SQL_TIMEOUT=8          # seg. máx. por consulta SQL
CONSULTAS_REST_TIMEOUT=10        # seg. timeout REST

# Proveedor del LLM (recomendado uno bueno con JSON estructurado)
LLM_PROVIDER=opencode            # ollama | openai | opencode

# DSN(s) de orígenes SQL — SIEMPRE usuario de SOLO LECTURA
CARTERA_DB_URL=mysql+pymysql://cartera_ro:PASSWORD@127.0.0.1:3306/cartera_clientes

# (voz, opcional) reutiliza la config del módulo /api/v1/voz
VOICE_ENABLED=true
```

Crear el usuario read-only (MySQL/MariaDB):
```sql
CREATE USER 'cartera_ro'@'127.0.0.1' IDENTIFIED BY 'PASSWORD';
GRANT SELECT ON cartera_clientes.* TO 'cartera_ro'@'127.0.0.1';
FLUSH PRIVILEGES;
```
> Si la contraseña tiene `@`, codifícalo como `%40` en el DSN. Ver
> `scripts/crear_usuario_readonly_mysql.sql` para la versión por tablas (mínimo privilegio).

Arrancar y probar:
```bash
python scripts/iniciar_api.py        # http://localhost:8000/docs (grupo "Consultas")
```

---

## ❓ FAQ / problemas comunes

- **`503 ... deshabilitado`** → falta `CONSULTAS_ENABLED=true` (o `VOICE_ENABLED=true` para voz).
- **`health` con `rules_cargado:false`** → revisa `RULES_PATH` y que `rules.yaml` exista/sea válido (`error_rules` da la causa).
- **`El origen 'X' requiere la variable de entorno '...'`** → falta el DSN en `.env`.
- **`Unknown system variable 'MAX_EXECUTION_TIME'`** → es MariaDB; ya se maneja con `max_statement_time` automáticamente.
- **El modelo "no devolvió un JSON válido"** → usa un LLM más capaz (`LLM_PROVIDER=opencode`/`openai`); modelos muy pequeños fallan al estructurar.
- **La consulta elige mal la tabla** → usa `objetivo` para fijarla, o mejora las `keys` en `rules.yaml`.
- **Quiero cruzar dos tablas (FK)** → declara `relaciones` en la tabla; el JOIN se habilita y la allowlist se amplía sola.
- **El gráfico sale como tabla** → fuerza `"formato": "grafico"` o reformula ("gráfica de…", "cuántos por…").

---

📚 Documentos relacionados: [ARQUITECTURA.md](ARQUITECTURA.md) (diseño interno e
integración de voz) · [API_DOCUMENTATION.md](API_DOCUMENTATION.md) (API completa de todos
los bots).
