# 📊 Contexto de gráficas, tablas y vistas — para RAG

> Catálogo de las visualizaciones (tablas, gráficas y KPIs) del sistema, pensado para
> **entrenar / alimentar un sistema RAG externo** (API de Consultas a Datos). El objetivo es
> darle al RAG el **contexto de dónde partir**: qué tabla(s) consultar, con qué filtros y qué
> columnas, de modo que sus respuestas reproduzcan **lo más fielmente posible** las vistas
> existentes (p. ej. el dashboard).
>
> Las vistas Livewire no ejecutan SQL plano: arman los datos en PHP dentro de *computed
> properties*. Aquí se documenta el **SQL equivalente** sobre la base `cartera_clientes`
> (MySQL/MariaDB) que produce el mismo conjunto de datos.

---

## 🧷 Esquema de cada entrada

Cada visualización se describe con estos campos (los mismos del bloque JSON al final):

| Campo | Descripción |
|-------|-------------|
| `id` | Identificador único de la visualización |
| `pagina` | Ruta URL donde aparece (p. ej. `/oportunidades`) |
| `ruta_nombre` | Nombre de la ruta Laravel (p. ej. `oportunidades.index`) |
| `titulo_grafica` | Título visible |
| `contexto` | Qué muestra y de dónde sale (en lenguaje natural) |
| `tabla_base` | Tabla principal → mapea al campo `objetivo` de la API de Consultas |
| `tablas_relacionadas` | Tablas que se cruzan (JOIN) |
| `columnas` | Columnas/medidas visibles en la vista |
| `filtros` | Filtros disponibles (ganchos de lenguaje natural para el RAG) |
| `fuente_php` | Método Livewire/Controller que genera los datos |
| `consulta_bd` | SQL equivalente |
| `tipo_grafica` | `tabla` · `kpi` · `grafico:line` · `grafico:bar` · `grafico:pie` … |

> ✅ **Estado en la API (origen `cartera_db`):** estas tablas YA están en la allowlist de
> `config/rules.yaml`: `clientes, contactos_cliente, proyectos, cotizaciones, users,
> proyecto_ponderacion_historial, ponderaciones, sublineas, lugares, proyecto_miembros,
> tech_references, core_businesses, personnel_acronyms, countries, varios, sizes`.
> Además, el origen lleva un `contexto` de negocio (fórmulas de ponderado/bandas, etc.) y
> las tablas clave traen `ejemplos` (few-shot) tomados de estas vistas, para que el RAG
> reproduzca el dashboard. Este documento es la **fuente** de esa configuración.

---

## 🗂️ Modelo de datos

| Tabla | Columnas clave | Notas |
|-------|----------------|-------|
| `proyectos` | `id, tipo, anio, cp_numero, dn_numero, tech_reference, usuario_final, monto_usd, estado, ponderacion, porcentaje_adjudicacion, cartera_esperada, plazo_estimado, fecha_envio, fecha_modificacion_oferta, cliente_id, sublinea_id, lugar_id, elaboro_id` | `tipo` ∈ {`oportunidad`,`proyecto`}. `ponderacion` = % de probabilidad actual (0–100). |
| `clientes` | `id, razon_social, alias, rfc, sector, segmento, activo` | Nombre visible = `COALESCE(alias, razon_social)`. |
| `contactos_cliente` | `id, cliente_id, …` | Contactos por cliente. |
| `sublineas` | `id, codigo, nombre` | Línea de negocio. |
| `lugares` | `id, nombre` | Ubicación del proyecto. |
| `proyecto_ponderacion_historial` | `proyecto_id, anio, mes, ponderacion_id` | Snapshot mensual del % de cada oportunidad. |
| `ponderaciones` | `id, orden, concepto, porcentaje, color, status` | Catálogo de bandas (0,10,25,75,100). |
| `proyecto_miembros` | `proyecto_id, user_id, rol` | Roles: `gerente_proyectos`, `director_dn`, … |
| `users` | `id, name, email` | Responsables/usuarios. |
| `cotizaciones` | `proyecto_id, version, precio_venta_final, fecha_emision` | Monto cotizado. |
| `tech_references` | `id, tech_reference, cp_numero, cliente_id, nombre_proyecto_cliente, core_business, amount_usd, amount_mxn, account_manager, …, status` | Catálogo de referencias técnicas. |
| `core_businesses` | `id, core_business, acronym, description, status` | Catálogo. |
| `personnel_acronyms` | `id, acronym, account_manager, user_id, status` | Catálogo. |
| `countries` | `id, state, zone, country, status` | Catálogo estados/zonas/país. |
| `varios` | `id, nombre, status` | Catálogo libre. |
| `sizes` | `id, size_principal, size_secundario, status` | Catálogo de medidas. |

**Bandas de probabilidad** (clasificación del % de ponderación):

| Banda | Rango % | Etiqueta |
|-------|---------|----------|
| p100 | = 100 | 100% Contratada |
| p75  | 75–99 | 75% Probable |
| p25  | 25–74 | 25% Posible |
| p10  | 10–24 | 10% Remoto |
| p0   | = 0   | 0% Perdida |

**Catálogo de estados** de `proyectos.estado`: `en_revision, cotizando, cotizado,
presentado, adjudicado_pendiente, adjudicado_firmado, en_ejecucion, en_cierre, cerrado,
cancelado, perdido, archivado`.

---

## Página `/` — Dashboard ejecutivo

- **Ruta:** `/` (`dashboard`) · alias `/ejecutivo` (`ejecutivo.dashboard`)
- **Componente:** `App\Livewire\Ejecutivo\DashboardIndex`
- **Vista:** `resources/views/livewire/ejecutivo/dashboard-index.blade.php`
- Todas las visualizaciones visibles derivan de `getStatusOfertasDataProperty()`.

### 1. Tabla — «Detalle de Ofertas {año}»
- **Contexto:** Lista todas las oportunidades (`proyectos.tipo='oportunidad'`) con nombre
  (cliente + ref. técnica/CP), monto USD y % de ponderación actual con su banda. Cada fila se
  expande al historial mensual (ver #2). Pie de tabla: total de cartera activa.
- **tabla_base:** `proyectos` · **relacionadas:** `clientes, proyecto_miembros, users`
- **consulta_bd:**
  ```sql
  SELECT p.id, p.cp_numero, p.tech_reference, p.monto_usd, p.estado,
         p.ponderacion AS ponderacion_actual, p.plazo_estimado,
         c.alias AS cliente_alias, c.razon_social AS cliente_razon_social,
         gp.name AS gerente_proyectos, el.name AS elaboro
  FROM proyectos p
  LEFT JOIN clientes c           ON c.id = p.cliente_id
  LEFT JOIN proyecto_miembros pm ON pm.proyecto_id = p.id AND pm.rol = 'gerente_proyectos'
  LEFT JOIN users gp             ON gp.id = pm.user_id
  LEFT JOIN users el             ON el.id = p.elaboro_id
  WHERE p.tipo = 'oportunidad'
  ORDER BY p.cp_numero;
  ```
- **tipo_grafica:** `tabla`

### 2. Tabla anidada — «Detalle por mes» (historial de ponderación)
- **Contexto:** Fila expandida: matriz mes × % de ponderación de la oferta, coloreada por banda.
- **tabla_base:** `proyecto_ponderacion_historial` · **relacionadas:** `ponderaciones`
- **consulta_bd:**
  ```sql
  SELECT h.proyecto_id, h.anio, h.mes, pond.porcentaje AS ponderacion_mes
  FROM proyecto_ponderacion_historial h
  JOIN ponderaciones pond ON pond.id = h.ponderacion_id
  WHERE h.proyecto_id = :proyecto_id
  ORDER BY h.anio, h.mes;
  ```
- **tipo_grafica:** `tabla`

### 3. Gráfica — «Evolución de la cartera esperada»
- **Contexto:** Línea por mes del monto bruto agrupado por banda (100/75/25/10/0%) + línea de
  cartera esperada (ponderada = Σ `monto_usd × porcentaje/100`). Eje Y en millones USD.
- **tabla_base:** `proyectos` · **relacionadas:** `proyecto_ponderacion_historial, ponderaciones`
- **consulta_bd:**
  ```sql
  SELECT h.anio, h.mes,
         CASE WHEN pond.porcentaje = 100 THEN '100% Contratada'
              WHEN pond.porcentaje BETWEEN 75 AND 99 THEN '75% Probable'
              WHEN pond.porcentaje BETWEEN 25 AND 74 THEN '25% Posible'
              WHEN pond.porcentaje BETWEEN 10 AND 24 THEN '10% Remoto'
              ELSE '0% Perdida' END AS banda,
         SUM(p.monto_usd) AS bruto,
         SUM(p.monto_usd * pond.porcentaje / 100) AS ponderado
  FROM proyectos p
  JOIN proyecto_ponderacion_historial h ON h.proyecto_id = p.id
  JOIN ponderaciones pond               ON pond.id = h.ponderacion_id
  WHERE p.tipo = 'oportunidad' AND pond.porcentaje > 0
  GROUP BY h.anio, h.mes, banda
  ORDER BY h.anio, h.mes;
  ```
- **tipo_grafica:** `grafico:line`

### 4. Desglose — «Por nivel de probabilidad»
- **Contexto:** Distribución de la cartera por banda (último % conocido de cada oferta): bruto,
  ponderado, conteo y eficiencia. Render como lista con barras.
- **tabla_base:** `proyectos`
- **consulta_bd:**
  ```sql
  SELECT CASE WHEN p.ponderacion = 100 THEN '100% Contratada'
              WHEN p.ponderacion BETWEEN 75 AND 99 THEN '75% Probable'
              WHEN p.ponderacion BETWEEN 25 AND 74 THEN '25% Posible'
              WHEN p.ponderacion BETWEEN 10 AND 24 THEN '10% Remoto'
              ELSE '0% Perdida' END AS banda,
         COUNT(*) AS ofertas, SUM(p.monto_usd) AS bruto,
         SUM(p.monto_usd * p.ponderacion / 100) AS ponderado,
         ROUND(SUM(p.monto_usd * p.ponderacion / 100) / NULLIF(SUM(p.monto_usd),0) * 100, 1) AS eficiencia_pct
  FROM proyectos p
  WHERE p.tipo = 'oportunidad' AND p.monto_usd > 0
  GROUP BY banda;
  ```
- **tipo_grafica:** `tabla`

### 5. KPIs — «Bruto / Esperado / Eficiencia»
- **Contexto:** Totales de la cartera de oportunidades: bruto, esperado (ponderado) y eficiencia.
- **tabla_base:** `proyectos`
- **consulta_bd:**
  ```sql
  SELECT SUM(p.monto_usd) AS bruto,
         SUM(p.monto_usd * p.ponderacion / 100) AS esperado,
         ROUND(SUM(p.monto_usd * p.ponderacion / 100) / NULLIF(SUM(p.monto_usd),0) * 100, 1) AS eficiencia_pct,
         COUNT(*) AS ofertas
  FROM proyectos p
  WHERE p.tipo = 'oportunidad' AND p.monto_usd > 0;
  ```
- **tipo_grafica:** `kpi`

---

## Página `/oportunidades` — Listado de oportunidades

- **Ruta:** `/oportunidades` (`oportunidades.index`)
- **Componente:** `App\Livewire\Proyectos\OportunidadesIndex`
- **Vista:** `resources/views/livewire/proyectos/oportunidades-index.blade.php`
- **Filtros:** `search` (CP, DN, razón social del cliente, usuario final), `anio` (default año
  actual; `todos` = sin filtro), `sublineasSeleccionadas[]`, `estadosSeleccionados[]`,
  `soloMios` (donde el usuario es `gerente_proyectos`). Orden: ofertas con `fecha_envio` primero (DESC), nulos al final.

### 6. Tabla — «Listado de oportunidades»
- **Contexto:** Tabla paginada (25/pág) de proyectos del año con sus columnas comerciales. NO
  fija `tipo`; muestra los proyectos que cumplan los filtros (por defecto, del año vigente).
- **tabla_base:** `proyectos` · **relacionadas:** `clientes, sublineas, lugares, proyecto_miembros, users, cotizaciones`
- **columnas:** CP · Cliente · Lugar · Alcance · Oferta (monto USD) · Fecha Envío · Fecha Modif. ·
  Ofertas Emitidas · Hitos de Pago · Responsable · Status (estado) · Arch. Oferta · Resultado ·
  % Adj. (`porcentaje_adjudicacion`) · Cartera Esp. (`cartera_esperada`)
- **consulta_bd:**
  ```sql
  SELECT p.id, p.cp_numero, p.dn_numero, p.usuario_final,
         p.monto_usd, p.estado, p.ponderacion,
         p.fecha_envio, p.fecha_modificacion_oferta,
         p.porcentaje_adjudicacion, p.cartera_esperada, p.anio,
         c.razon_social AS cliente, c.alias AS cliente_alias,
         s.codigo AS sublinea, l.nombre AS lugar,
         gp.name AS responsable
  FROM proyectos p
  LEFT JOIN clientes c           ON c.id = p.cliente_id
  LEFT JOIN sublineas s          ON s.id = p.sublinea_id
  LEFT JOIN lugares l            ON l.id = p.lugar_id
  LEFT JOIN proyecto_miembros pm ON pm.proyecto_id = p.id AND pm.rol = 'gerente_proyectos'
  LEFT JOIN users gp             ON gp.id = pm.user_id
  WHERE p.anio = :anio                                  -- omitir si anio = 'todos'
    -- AND (LOWER(p.cp_numero) LIKE :q OR LOWER(p.dn_numero) LIKE :q
    --      OR LOWER(c.razon_social) LIKE :q OR LOWER(p.usuario_final) LIKE :q)
    -- AND p.sublinea_id IN (:sublineas)
    -- AND p.estado IN (:estados)
  ORDER BY (p.fecha_envio IS NULL), p.fecha_envio DESC;
  ```
- **tipo_grafica:** `tabla`

### 7. KPIs — «Pipeline / Ponderado / Adjudicado»
- **Contexto:** Tarjetas resumen del año (excluye `cancelado, perdido, archivado`): conteo y
  monto del pipeline, monto ponderado, ponderación media, monto/conteo adjudicado y nº de
  ofertas ya enviadas.
- **tabla_base:** `proyectos`
- **fuente_php:** `OportunidadesIndex::getKpisProperty()`
- **consulta_bd:**
  ```sql
  SELECT COUNT(*) AS pipeline_count,
         SUM(monto_usd) AS pipeline_monto,
         COALESCE(SUM(monto_usd * ponderacion / 100), 0) AS monto_ponderado,
         ROUND(AVG(ponderacion)) AS ponderacion_media,
         SUM(CASE WHEN estado IN ('adjudicado_pendiente','adjudicado_firmado','en_ejecucion') THEN monto_usd ELSE 0 END) AS adjudicado_monto,
         SUM(CASE WHEN estado IN ('adjudicado_pendiente','adjudicado_firmado','en_ejecucion') THEN 1 ELSE 0 END) AS adjudicado_count,
         SUM(CASE WHEN estado NOT IN ('en_revision','cotizando') THEN 1 ELSE 0 END) AS enviadas_count
  FROM proyectos
  WHERE estado NOT IN ('cancelado','perdido','archivado')
    AND anio = :anio;                                   -- omitir si anio = 'todos'
  ```
- **tipo_grafica:** `kpi`

---

## Página `/clientes` — Cartera de clientes

- **Ruta:** `/clientes` (`clientes.index`)
- **Componente:** `App\Livewire\Comercial\ClientesIndex`
- **Vista:** `resources/views/livewire/comercial/clientes-index.blade.php`
- **Filtros:** `buscar` (razón social, alias, RFC), `sector`, `incluirInactivos` (default solo
  `activo=1`). Orden por razón social.

### 8. Tabla — «Listado de clientes»
- **Contexto:** Tabla paginada (25/pág) de clientes con su nº de contactos y estado activo/inactivo.
- **tabla_base:** `clientes` · **relacionadas:** `contactos_cliente`
- **columnas:** Alias · Razón Social · RFC · Sector · Segmento · Contactos (conteo) · Estado (`activo`)
- **consulta_bd:**
  ```sql
  SELECT c.id, c.alias, c.razon_social, c.rfc, c.sector, c.segmento, c.activo,
         (SELECT COUNT(*) FROM contactos_cliente cc WHERE cc.cliente_id = c.id) AS contactos
  FROM clientes c
  WHERE c.activo = 1                                    -- omitir si incluirInactivos
    -- AND (LOWER(c.razon_social) LIKE :q OR LOWER(c.alias) LIKE :q OR LOWER(c.rfc) LIKE :q)
    -- AND c.sector = :sector
  ORDER BY c.razon_social;
  ```
- **tipo_grafica:** `tabla`

---

## Página `/catalogos-admin` — Administración de catálogos

- **Ruta:** `/catalogos-admin` (`catalogos.crud.index`); `?tab={slug}` selecciona el catálogo.
- **Controlador:** `App\Http\Controllers\Catalogos\CatalogosCrudController@index`
- **Vista:** `resources/views/catalogos/crud.blade.php`
- **Patrón común:** cada catálogo es una **tabla paginada** filtrada por `status = true`
  (borrado lógico) y ordenada por `id`. El `total` por tab es `COUNT(*) WHERE status = 1`.

### 9. Tabla — «Ponderaciones»
- **tabla_base:** `ponderaciones` · **columnas:** Orden · Concepto · % (`porcentaje`) · Color
- **consulta_bd:** `SELECT id, orden, concepto, porcentaje, color FROM ponderaciones WHERE status = 1 ORDER BY id;`
- **tipo_grafica:** `tabla`

### 10. Tabla — «Tech References»
- **tabla_base:** `tech_references` · **relacionadas:** `clientes`
- **columnas:** Tech Ref · CP (`cp_numero`) · Cliente (`cliente.alias`) · Proyecto (`nombre_proyecto_cliente`) · Core Bus. · USD (`amount_usd`) · Acct Mgr (`account_manager`)
- **consulta_bd:**
  ```sql
  SELECT t.id, t.tech_reference, t.cp_numero, c.alias AS cliente,
         t.nombre_proyecto_cliente, t.core_business, t.amount_usd, t.account_manager
  FROM tech_references t
  LEFT JOIN clientes c ON c.id = t.cliente_id
  WHERE t.status = 1
  ORDER BY t.id;
  ```
- **tipo_grafica:** `tabla`

### 11. Tabla — «Core Business»
- **tabla_base:** `core_businesses` · **columnas:** Core Business · Acrónimo (`acronym`) · Descripción (`description`)
- **consulta_bd:** `SELECT id, core_business, acronym, description FROM core_businesses WHERE status = 1 ORDER BY id;`
- **tipo_grafica:** `tabla`

### 12. Tabla — «Personnel Acronyms»
- **tabla_base:** `personnel_acronyms` · **relacionadas:** `users`
- **columnas:** Acrónimo (`acronym`) · Account Manager (`account_manager`) · Usuario (`user.name`)
- **consulta_bd:**
  ```sql
  SELECT pa.id, pa.acronym, pa.account_manager, u.name AS usuario
  FROM personnel_acronyms pa
  LEFT JOIN users u ON u.id = pa.user_id
  WHERE pa.status = 1
  ORDER BY pa.id;
  ```
- **tipo_grafica:** `tabla`

### 13. Tabla — «Countries / States»
- **tabla_base:** `countries` · **columnas:** Estado (`state`) · Zona (`zone`) · País (`country`)
- **consulta_bd:** `SELECT id, state, zone, country FROM countries WHERE status = 1 ORDER BY id;`
- **tipo_grafica:** `tabla`

### 14. Tabla — «Varios»
- **tabla_base:** `varios` · **columnas:** Nombre (`nombre`)
- **consulta_bd:** `SELECT id, nombre FROM varios WHERE status = 1 ORDER BY id;`
- **tipo_grafica:** `tabla`

### 15. Tabla — «Sizes»
- **tabla_base:** `sizes` · **columnas:** Size Principal (`size_principal`) · Size Secundario (`size_secundario`)
- **consulta_bd:** `SELECT id, size_principal, size_secundario FROM sizes WHERE status = 1 ORDER BY id;`
- **tipo_grafica:** `tabla`

---

## 🧩 JSON consolidado (para ingestión RAG)

```json
[
  {
    "id": "dashboard_tabla_detalle_ofertas",
    "pagina": "/",
    "ruta_nombre": "dashboard",
    "titulo_grafica": "Detalle de Ofertas {año}",
    "contexto": "Lista todas las oportunidades (proyectos tipo=oportunidad) con nombre (cliente + referencia técnica/CP), monto USD y % de ponderación actual con su banda. Cada fila se expande al historial de avance por mes. El pie muestra el total de cartera activa.",
    "tabla_base": "proyectos",
    "tablas_relacionadas": ["clientes", "proyecto_miembros", "users"],
    "columnas": ["nombre_proyecto", "cp_numero", "monto_usd", "ponderacion", "estado"],
    "filtros": [],
    "fuente_php": "App\\Livewire\\Ejecutivo\\DashboardIndex::getStatusOfertasDataProperty()",
    "consulta_bd": "SELECT p.id, p.cp_numero, p.tech_reference, p.monto_usd, p.estado, p.ponderacion AS ponderacion_actual, p.plazo_estimado, c.alias AS cliente_alias, c.razon_social AS cliente_razon_social, gp.name AS gerente_proyectos, el.name AS elaboro FROM proyectos p LEFT JOIN clientes c ON c.id = p.cliente_id LEFT JOIN proyecto_miembros pm ON pm.proyecto_id = p.id AND pm.rol = 'gerente_proyectos' LEFT JOIN users gp ON gp.id = pm.user_id LEFT JOIN users el ON el.id = p.elaboro_id WHERE p.tipo = 'oportunidad' ORDER BY p.cp_numero;",
    "tipo_grafica": "tabla"
  },
  {
    "id": "dashboard_tabla_detalle_por_mes",
    "pagina": "/",
    "ruta_nombre": "dashboard",
    "titulo_grafica": "Detalle por mes (historial de ponderación)",
    "contexto": "Fila expandida de la tabla de ofertas. Matriz mes x % de ponderación por oportunidad, coloreada por banda. Los meses salen de los snapshots en proyecto_ponderacion_historial.",
    "tabla_base": "proyecto_ponderacion_historial",
    "tablas_relacionadas": ["ponderaciones"],
    "columnas": ["anio", "mes", "porcentaje"],
    "filtros": ["proyecto_id"],
    "fuente_php": "App\\Livewire\\Ejecutivo\\DashboardIndex::getStatusOfertasDataProperty()",
    "consulta_bd": "SELECT h.proyecto_id, h.anio, h.mes, pond.porcentaje AS ponderacion_mes FROM proyecto_ponderacion_historial h JOIN ponderaciones pond ON pond.id = h.ponderacion_id WHERE h.proyecto_id = :proyecto_id ORDER BY h.anio, h.mes;",
    "tipo_grafica": "tabla"
  },
  {
    "id": "dashboard_grafica_evolucion_cartera",
    "pagina": "/",
    "ruta_nombre": "dashboard",
    "titulo_grafica": "Evolución de la cartera esperada",
    "contexto": "Línea temporal por mes del monto bruto de oportunidades agrupado por banda de probabilidad (100/75/25/10/0%), más la línea de cartera esperada (ponderada = suma de monto_usd * porcentaje/100). Eje Y en millones USD.",
    "tabla_base": "proyectos",
    "tablas_relacionadas": ["proyecto_ponderacion_historial", "ponderaciones"],
    "columnas": ["anio", "mes", "banda", "bruto", "ponderado"],
    "filtros": [],
    "fuente_php": "App\\Livewire\\Ejecutivo\\DashboardIndex::getStatusOfertasDataProperty()",
    "consulta_bd": "SELECT h.anio, h.mes, CASE WHEN pond.porcentaje = 100 THEN '100% Contratada' WHEN pond.porcentaje BETWEEN 75 AND 99 THEN '75% Probable' WHEN pond.porcentaje BETWEEN 25 AND 74 THEN '25% Posible' WHEN pond.porcentaje BETWEEN 10 AND 24 THEN '10% Remoto' ELSE '0% Perdida' END AS banda, SUM(p.monto_usd) AS bruto, SUM(p.monto_usd * pond.porcentaje / 100) AS ponderado FROM proyectos p JOIN proyecto_ponderacion_historial h ON h.proyecto_id = p.id JOIN ponderaciones pond ON pond.id = h.ponderacion_id WHERE p.tipo = 'oportunidad' AND pond.porcentaje > 0 GROUP BY h.anio, h.mes, banda ORDER BY h.anio, h.mes;",
    "tipo_grafica": "grafico:line"
  },
  {
    "id": "dashboard_desglose_por_nivel_probabilidad",
    "pagina": "/",
    "ruta_nombre": "dashboard",
    "titulo_grafica": "Por nivel de probabilidad",
    "contexto": "Distribución de la cartera por banda de probabilidad usando la última ponderación conocida de cada oferta: monto ponderado, ofertas, bruto y eficiencia. Render como lista con barras.",
    "tabla_base": "proyectos",
    "tablas_relacionadas": [],
    "columnas": ["banda", "ofertas", "bruto", "ponderado", "eficiencia_pct"],
    "filtros": [],
    "fuente_php": "App\\Livewire\\Ejecutivo\\DashboardIndex::getStatusOfertasDataProperty()",
    "consulta_bd": "SELECT CASE WHEN p.ponderacion = 100 THEN '100% Contratada' WHEN p.ponderacion BETWEEN 75 AND 99 THEN '75% Probable' WHEN p.ponderacion BETWEEN 25 AND 74 THEN '25% Posible' WHEN p.ponderacion BETWEEN 10 AND 24 THEN '10% Remoto' ELSE '0% Perdida' END AS banda, COUNT(*) AS ofertas, SUM(p.monto_usd) AS bruto, SUM(p.monto_usd * p.ponderacion / 100) AS ponderado, ROUND(SUM(p.monto_usd * p.ponderacion / 100) / NULLIF(SUM(p.monto_usd),0) * 100, 1) AS eficiencia_pct FROM proyectos p WHERE p.tipo = 'oportunidad' AND p.monto_usd > 0 GROUP BY banda;",
    "tipo_grafica": "tabla"
  },
  {
    "id": "dashboard_kpis_cartera",
    "pagina": "/",
    "ruta_nombre": "dashboard",
    "titulo_grafica": "Bruto total / Esperado / Eficiencia ponderada",
    "contexto": "KPIs totales de la cartera de oportunidades: bruto (suma de montos), esperado (suma ponderada por probabilidad) y eficiencia (esperado/bruto).",
    "tabla_base": "proyectos",
    "tablas_relacionadas": [],
    "columnas": ["bruto", "esperado", "eficiencia_pct", "ofertas"],
    "filtros": [],
    "fuente_php": "App\\Livewire\\Ejecutivo\\DashboardIndex::getStatusOfertasDataProperty()",
    "consulta_bd": "SELECT SUM(p.monto_usd) AS bruto, SUM(p.monto_usd * p.ponderacion / 100) AS esperado, ROUND(SUM(p.monto_usd * p.ponderacion / 100) / NULLIF(SUM(p.monto_usd),0) * 100, 1) AS eficiencia_pct, COUNT(*) AS ofertas FROM proyectos p WHERE p.tipo = 'oportunidad' AND p.monto_usd > 0;",
    "tipo_grafica": "kpi"
  },
  {
    "id": "oportunidades_tabla_listado",
    "pagina": "/oportunidades",
    "ruta_nombre": "oportunidades.index",
    "titulo_grafica": "Listado de oportunidades",
    "contexto": "Tabla paginada (25/pág) de proyectos del año con columnas comerciales. No fija tipo; muestra los proyectos que cumplan los filtros (por defecto, del año vigente).",
    "tabla_base": "proyectos",
    "tablas_relacionadas": ["clientes", "sublineas", "lugares", "proyecto_miembros", "users", "cotizaciones"],
    "columnas": ["cp_numero", "cliente", "lugar", "alcance", "monto_usd", "fecha_envio", "fecha_modificacion_oferta", "responsable", "estado", "porcentaje_adjudicacion", "cartera_esperada"],
    "filtros": ["search (cp_numero, dn_numero, cliente.razon_social, usuario_final)", "anio", "sublinea_id[]", "estado[]", "soloMios"],
    "fuente_php": "App\\Livewire\\Proyectos\\OportunidadesIndex::getOportunidadesProperty()",
    "consulta_bd": "SELECT p.id, p.cp_numero, p.dn_numero, p.usuario_final, p.monto_usd, p.estado, p.ponderacion, p.fecha_envio, p.fecha_modificacion_oferta, p.porcentaje_adjudicacion, p.cartera_esperada, p.anio, c.razon_social AS cliente, c.alias AS cliente_alias, s.codigo AS sublinea, l.nombre AS lugar, gp.name AS responsable FROM proyectos p LEFT JOIN clientes c ON c.id = p.cliente_id LEFT JOIN sublineas s ON s.id = p.sublinea_id LEFT JOIN lugares l ON l.id = p.lugar_id LEFT JOIN proyecto_miembros pm ON pm.proyecto_id = p.id AND pm.rol = 'gerente_proyectos' LEFT JOIN users gp ON gp.id = pm.user_id WHERE p.anio = :anio ORDER BY (p.fecha_envio IS NULL), p.fecha_envio DESC;",
    "tipo_grafica": "tabla"
  },
  {
    "id": "oportunidades_kpis",
    "pagina": "/oportunidades",
    "ruta_nombre": "oportunidades.index",
    "titulo_grafica": "Pipeline / Ponderado / Adjudicado",
    "contexto": "KPIs del año (excluye cancelado, perdido, archivado): conteo y monto del pipeline, monto ponderado, ponderación media, monto/conteo adjudicado y nº de ofertas enviadas.",
    "tabla_base": "proyectos",
    "tablas_relacionadas": [],
    "columnas": ["pipeline_count", "pipeline_monto", "monto_ponderado", "ponderacion_media", "adjudicado_monto", "adjudicado_count", "enviadas_count"],
    "filtros": ["anio"],
    "fuente_php": "App\\Livewire\\Proyectos\\OportunidadesIndex::getKpisProperty()",
    "consulta_bd": "SELECT COUNT(*) AS pipeline_count, SUM(monto_usd) AS pipeline_monto, COALESCE(SUM(monto_usd * ponderacion / 100), 0) AS monto_ponderado, ROUND(AVG(ponderacion)) AS ponderacion_media, SUM(CASE WHEN estado IN ('adjudicado_pendiente','adjudicado_firmado','en_ejecucion') THEN monto_usd ELSE 0 END) AS adjudicado_monto, SUM(CASE WHEN estado IN ('adjudicado_pendiente','adjudicado_firmado','en_ejecucion') THEN 1 ELSE 0 END) AS adjudicado_count, SUM(CASE WHEN estado NOT IN ('en_revision','cotizando') THEN 1 ELSE 0 END) AS enviadas_count FROM proyectos WHERE estado NOT IN ('cancelado','perdido','archivado') AND anio = :anio;",
    "tipo_grafica": "kpi"
  },
  {
    "id": "clientes_tabla_listado",
    "pagina": "/clientes",
    "ruta_nombre": "clientes.index",
    "titulo_grafica": "Listado de clientes",
    "contexto": "Tabla paginada (25/pág) de clientes con su número de contactos y estado activo/inactivo.",
    "tabla_base": "clientes",
    "tablas_relacionadas": ["contactos_cliente"],
    "columnas": ["alias", "razon_social", "rfc", "sector", "segmento", "contactos", "activo"],
    "filtros": ["buscar (razon_social, alias, rfc)", "sector", "incluirInactivos"],
    "fuente_php": "App\\Livewire\\Comercial\\ClientesIndex::getClientesProperty()",
    "consulta_bd": "SELECT c.id, c.alias, c.razon_social, c.rfc, c.sector, c.segmento, c.activo, (SELECT COUNT(*) FROM contactos_cliente cc WHERE cc.cliente_id = c.id) AS contactos FROM clientes c WHERE c.activo = 1 ORDER BY c.razon_social;",
    "tipo_grafica": "tabla"
  },
  {
    "id": "catalogos_ponderaciones",
    "pagina": "/catalogos-admin?tab=ponderaciones",
    "ruta_nombre": "catalogos.crud.index",
    "titulo_grafica": "Ponderaciones",
    "contexto": "Catálogo de bandas de probabilidad. Tabla filtrada por status=true.",
    "tabla_base": "ponderaciones",
    "tablas_relacionadas": [],
    "columnas": ["orden", "concepto", "porcentaje", "color"],
    "filtros": ["status = true"],
    "fuente_php": "App\\Http\\Controllers\\Catalogos\\CatalogosCrudController@index",
    "consulta_bd": "SELECT id, orden, concepto, porcentaje, color FROM ponderaciones WHERE status = 1 ORDER BY id;",
    "tipo_grafica": "tabla"
  },
  {
    "id": "catalogos_tech_references",
    "pagina": "/catalogos-admin?tab=tech_references",
    "ruta_nombre": "catalogos.crud.index",
    "titulo_grafica": "Tech References",
    "contexto": "Catálogo de referencias técnicas (proyectos del cliente). Tabla filtrada por status=true.",
    "tabla_base": "tech_references",
    "tablas_relacionadas": ["clientes"],
    "columnas": ["tech_reference", "cp_numero", "cliente.alias", "nombre_proyecto_cliente", "core_business", "amount_usd", "account_manager"],
    "filtros": ["status = true"],
    "fuente_php": "App\\Http\\Controllers\\Catalogos\\CatalogosCrudController@index",
    "consulta_bd": "SELECT t.id, t.tech_reference, t.cp_numero, c.alias AS cliente, t.nombre_proyecto_cliente, t.core_business, t.amount_usd, t.account_manager FROM tech_references t LEFT JOIN clientes c ON c.id = t.cliente_id WHERE t.status = 1 ORDER BY t.id;",
    "tipo_grafica": "tabla"
  },
  {
    "id": "catalogos_core_businesses",
    "pagina": "/catalogos-admin?tab=core_businesses",
    "ruta_nombre": "catalogos.crud.index",
    "titulo_grafica": "Core Business",
    "contexto": "Catálogo de core business. Tabla filtrada por status=true.",
    "tabla_base": "core_businesses",
    "tablas_relacionadas": [],
    "columnas": ["core_business", "acronym", "description"],
    "filtros": ["status = true"],
    "fuente_php": "App\\Http\\Controllers\\Catalogos\\CatalogosCrudController@index",
    "consulta_bd": "SELECT id, core_business, acronym, description FROM core_businesses WHERE status = 1 ORDER BY id;",
    "tipo_grafica": "tabla"
  },
  {
    "id": "catalogos_personnel_acronyms",
    "pagina": "/catalogos-admin?tab=personnel_acronyms",
    "ruta_nombre": "catalogos.crud.index",
    "titulo_grafica": "Personnel Acronyms",
    "contexto": "Catálogo de acrónimos de personal / account managers. Tabla filtrada por status=true.",
    "tabla_base": "personnel_acronyms",
    "tablas_relacionadas": ["users"],
    "columnas": ["acronym", "account_manager", "user.name"],
    "filtros": ["status = true"],
    "fuente_php": "App\\Http\\Controllers\\Catalogos\\CatalogosCrudController@index",
    "consulta_bd": "SELECT pa.id, pa.acronym, pa.account_manager, u.name AS usuario FROM personnel_acronyms pa LEFT JOIN users u ON u.id = pa.user_id WHERE pa.status = 1 ORDER BY pa.id;",
    "tipo_grafica": "tabla"
  },
  {
    "id": "catalogos_countries",
    "pagina": "/catalogos-admin?tab=countries",
    "ruta_nombre": "catalogos.crud.index",
    "titulo_grafica": "Countries / States",
    "contexto": "Catálogo de estados/zonas/países. Tabla filtrada por status=true.",
    "tabla_base": "countries",
    "tablas_relacionadas": [],
    "columnas": ["state", "zone", "country"],
    "filtros": ["status = true"],
    "fuente_php": "App\\Http\\Controllers\\Catalogos\\CatalogosCrudController@index",
    "consulta_bd": "SELECT id, state, zone, country FROM countries WHERE status = 1 ORDER BY id;",
    "tipo_grafica": "tabla"
  },
  {
    "id": "catalogos_varios",
    "pagina": "/catalogos-admin?tab=varios",
    "ruta_nombre": "catalogos.crud.index",
    "titulo_grafica": "Varios",
    "contexto": "Catálogo libre. Tabla filtrada por status=true.",
    "tabla_base": "varios",
    "tablas_relacionadas": [],
    "columnas": ["nombre"],
    "filtros": ["status = true"],
    "fuente_php": "App\\Http\\Controllers\\Catalogos\\CatalogosCrudController@index",
    "consulta_bd": "SELECT id, nombre FROM varios WHERE status = 1 ORDER BY id;",
    "tipo_grafica": "tabla"
  },
  {
    "id": "catalogos_sizes",
    "pagina": "/catalogos-admin?tab=sizes",
    "ruta_nombre": "catalogos.crud.index",
    "titulo_grafica": "Sizes",
    "contexto": "Catálogo de medidas. Tabla filtrada por status=true.",
    "tabla_base": "sizes",
    "tablas_relacionadas": [],
    "columnas": ["size_principal", "size_secundario"],
    "filtros": ["status = true"],
    "fuente_php": "App\\Http\\Controllers\\Catalogos\\CatalogosCrudController@index",
    "consulta_bd": "SELECT id, size_principal, size_secundario FROM sizes WHERE status = 1 ORDER BY id;",
    "tipo_grafica": "tabla"
  }
]
```

---

## 📎 Apéndice — datasets calculados pero NO renderizados (Dashboard)

`DashboardIndex` calcula y serializa a JS datos que **hoy no se pintan** (sus `<canvas>` están
comentados). Se documentan por si se reactivan:

| Dataset (PHP) | Qué representaría | tipo_grafica | Fuente de monto |
|---------------|-------------------|--------------|-----------------|
| `chartData.byMonth` | Monto por mes apilado por banda | `grafico:bar` (apilado) | `cotizaciones.precio_venta_final` |
| `chartData.bySublinea` | Monto por sublínea (top 10) | `grafico:bar` (horizontal) | `cotizaciones.precio_venta_final` |
| `chartData.byCliente` | Monto por cliente (top 8) | `grafico:bar` (horizontal) | `cotizaciones.precio_venta_final` |
| `mesesSinContratacion.burn_serie` | Burn-down del backlog contratado | `grafico:line` | `proyectos.monto_usd` |
| `byResponsable` | Bruto/ponderado/conteo por responsable | `grafico:bar` | `getStatusOfertasDataProperty()` |
| `initProjChart(idx)` | Mini-línea prob% + ponderado por oferta | `grafico:line` | historial de ponderación |
