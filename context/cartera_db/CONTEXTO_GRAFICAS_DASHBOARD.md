# Contexto de visualizaciones — Cartera de Clientes (para RAG)

Catálogo de las visualizaciones (tablas, KPIs y gráficas) del sistema GPT Services
"Cartera de Clientes" (Laravel 12 + Livewire 3), sobre la base MySQL `cartera_clientes`.
Su propósito es darle contexto al servicio de Consultas a Datos (RAG): qué tabla(s)
consultar, con qué filtros y columnas, para reproducir fielmente cada vista.

**Formato optimizado para ingestión:** cada visualización se describe en bloques
autocontenidos de ~900 caracteres separados por línea en blanco (alineado al chunking
del RAG: `RecursiveCharacterTextSplitter`, chunk_size=1000, overlap=150, separador
principal `\n\n`). Cada bloque inicia con su `[id]` y página, de modo que cualquier
chunk recuperado funciona sin depender del resto del documento.

**Allowlist:** `config/rules.yaml` del servicio de consultas ya expone las 16 tablas
del origen `cartera_db` (`clientes, contactos_cliente, proyectos, cotizaciones, users,
proyecto_ponderacion_historial, ponderaciones, sublineas, lugares, proyecto_miembros,
tech_references, core_businesses, personnel_acronyms, countries, varios, sizes`).
Todas las entradas de este documento marcan `en_allowlist: sí`.

---

## Glosario y reglas de negocio

[glosario_metricas] Métricas de la cartera comercial (aplican en todo el sistema).
**Monto BRUTO** = `SUM(proyectos.monto_usd)`. **Monto ESPERADO / ponderado** =
`SUM(monto_usd * ponderacion / 100)`. **Eficiencia %** = esperado / bruto × 100.
**Cartera esperada** (campo por proyecto) = `monto_usd × ponderacion / 100`
(atributo calculado en vivo en el modelo Proyecto, redondeado a 2 decimales).
`proyectos.ponderacion` = % de probabilidad actual (0–100). `proyectos.tipo` ∈
{`oportunidad`, `proyecto`}: una "oferta" u "oportunidad" es `tipo='oportunidad'`.
Sinónimos: pipeline = cartera = ofertas activas; ponderado = esperado = cartera esperada.

[glosario_bandas] Bandas de probabilidad (dashboard `/`): clasifican el % de
ponderación de cada oferta. p100: =100 → «100% Contratada». p75: 75–99 → «75%
Probable». p25: 25–74 → «25% Posible». p10: 10–24 → «10% Remoto». p0: =0 → «0%
Perdida». En la página `/oportunidades` y en el detalle de cliente se usan etiquetas
por valor exacto de `ponderacion`: 10 → Remoto, 25 → Posible, 50 → Probable,
75 → Casi Probable, 100 → Contratado (otros valores se muestran como «N%»).

[glosario_estados] Catálogo de `proyectos.estado` (12 valores) con su etiqueta UI:
`en_revision` (En revisión), `cotizando`, `cotizado`, `presentado`,
`adjudicado_pendiente` (Adjudicado pend.), `adjudicado_firmado` (Adjudicado),
`en_ejecucion` (En ejecución), `en_cierre`, `cerrado`, `cancelado`, `perdido`,
`archivado`. **"Adjudicado"** agregado = estado IN (`adjudicado_pendiente`,
`adjudicado_firmado`, `en_ejecucion`). **Pipeline activo** excluye estado IN
(`cancelado`, `perdido`, `archivado`). **"Enviadas"** = estado NOT IN
(`en_revision`, `cotizando`).

[glosario_relaciones] Relaciones (FK) del modelo de datos `cartera_clientes`:
`proyectos.cliente_id → clientes.id` · `proyectos.sublinea_id → sublineas.id` ·
`proyectos.lugar_id → lugares.id` · `proyectos.elaboro_id → users.id` (quien elaboró)
· `cotizaciones.proyecto_id → proyectos.id` (versiones; monto vigente =
`MAX(precio_venta_final)` por proyecto) · `proyecto_miembros(proyecto_id, user_id,
rol)`: el responsable/gerente es `rol='gerente_proyectos'` → `users.name` ·
`proyecto_ponderacion_historial(proyecto_id, ponderacion_id, anio, mes)` →
`ponderaciones.id` (snapshot mensual del % de cada oferta) ·
`contactos_cliente.cliente_id → clientes.id` · `tech_references.cliente_id →
clientes.id` · `personnel_acronyms.user_id → users.id`. Nombre visible de un cliente
= `COALESCE(clientes.alias, clientes.razon_social)`. Los catálogos usan borrado
lógico: filtrar siempre `status = 1`.

---

## Página `/` — Dashboard ejecutivo

[dashboard_pagina] La página `/` (ruta `dashboard`, alias `/ejecutivo`) es el tablero
ejecutivo de la cartera de oportunidades. Componente
`App\Livewire\Ejecutivo\DashboardIndex`; todas sus visualizaciones derivan de la
computed property `getStatusOfertasDataProperty()`. **Importante:** aunque el título
muestra el año en curso, la consulta NO filtra por año — toma TODAS las oportunidades
(`proyectos.tipo='oportunidad'`). El eje temporal sale de los snapshots mensuales en
`proyecto_ponderacion_historial`. Incluye además el buscador inteligente de IA
(componente `<x-buscador-inteligente />`), que es el punto de entrada a este servicio
de consultas.

### [dash_detalle_ofertas] Tabla «Detalle de Ofertas {año}» — página /

[dash_detalle_ofertas] pagina: / · tipo_grafica: tabla · tabla_base: proyectos ·
relacionadas: clientes, proyecto_miembros, users · en_allowlist: sí.
Contexto: lista todas las oportunidades (`tipo='oportunidad'`, sin filtro de año) con
nombre visible (alias del cliente + tech_reference o CP), monto en millones USD y el
% de probabilidad ACTUAL con su banda (el "actual" es la última ponderación no nula
del historial; si no hay historial usa `proyectos.ponderacion`). Cada fila se expande
al historial mensual (ver [dash_historial_mes]).
Responde preguntas como: «¿qué ofertas tenemos y en qué probabilidad van?», «lista de
oportunidades con su monto y % actual», «¿quién es el responsable de cada oferta?».
Columnas: nombre (cliente + ref), cp_numero, monto_usd, ponderación actual + banda,
responsable (gerente de proyectos o quien elaboró).
Fuente: `DashboardIndex::getStatusOfertasDataProperty()`.

SQL equivalente [dash_detalle_ofertas] (página /):
```sql
SELECT p.id, p.cp_numero, p.tech_reference, p.monto_usd, p.estado,
       p.ponderacion AS ponderacion_actual,
       CONCAT(COALESCE(c.alias, c.razon_social), ' ',
              COALESCE(p.tech_reference, p.cp_numero, '—')) AS nombre,
       COALESCE(gp.name, el.name, 'Sin asignar') AS responsable
FROM proyectos p
LEFT JOIN clientes c           ON c.id = p.cliente_id
LEFT JOIN proyecto_miembros pm ON pm.proyecto_id = p.id AND pm.rol = 'gerente_proyectos'
LEFT JOIN users gp             ON gp.id = pm.user_id
LEFT JOIN users el             ON el.id = p.elaboro_id
WHERE p.tipo = 'oportunidad'
ORDER BY p.id;
```

### [dash_historial_mes] Tabla anidada «Detalle por mes» — página /

[dash_historial_mes] pagina: / · tipo_grafica: tabla · tabla_base:
proyecto_ponderacion_historial · relacionadas: ponderaciones · en_allowlist: sí.
Contexto: fila expandida de la tabla de ofertas del dashboard. Matriz mes × % de
ponderación de una oferta, coloreada por banda. Los meses del eje son la unión de
todos los snapshots existentes (clave `anio*100+mes`, etiquetas tipo «Ene 26»); si
una oferta no tiene snapshot en un mes la celda queda vacía. Si ninguna oferta tiene
historial, se muestra una sola columna «Actual» con `proyectos.ponderacion`.
Responde preguntas como: «¿cómo ha evolucionado la probabilidad de la oferta X?»,
«historial mensual de ponderación de un proyecto», «¿en qué mes subió a 75%?».
Fuente: `DashboardIndex::getStatusOfertasDataProperty()`.

SQL equivalente [dash_historial_mes] (página /):
```sql
SELECT h.proyecto_id, h.anio, h.mes, pond.porcentaje AS ponderacion_mes
FROM proyecto_ponderacion_historial h
JOIN ponderaciones pond ON pond.id = h.ponderacion_id
WHERE h.proyecto_id = :proyecto_id
ORDER BY h.anio, h.mes;
```

### [dash_evolucion_cartera] Gráfica «Evolución de la cartera esperada» — página /

[dash_evolucion_cartera] pagina: / · tipo_grafica: grafico:line · tabla_base:
proyectos · relacionadas: proyecto_ponderacion_historial, ponderaciones ·
en_allowlist: sí.
Contexto: gráfica de líneas (Chart.js) con 6 series por mes: el monto bruto agrupado
en las 5 bandas de probabilidad (100% Contratada, 75% Probable, 25% Posible, 10%
Remoto, 0% Perdida) más la línea overlay «Cartera esperada (ponderada)» =
Σ `monto_usd × porcentaje_del_mes / 100`. Eje Y en millones de USD. Solo suma meses
con probabilidad > 0. Sin filtro de año: cubre todos los meses con snapshot.
Responde preguntas como: «¿cómo evoluciona la cartera esperada mes a mes?»,
«evolución del pipeline por banda de probabilidad», «¿cuánto monto contratado había
en marzo?».
Fuente: `DashboardIndex::getStatusOfertasDataProperty()` → `carteraEvolucion`.

SQL equivalente [dash_evolucion_cartera] (página /):
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

### [dash_nivel_probabilidad] Card «Por nivel de probabilidad» — página /

[dash_nivel_probabilidad] pagina: / · tipo_grafica: tabla (lista con barras) ·
tabla_base: proyectos · en_allowlist: sí.
Contexto: distribución de la cartera en las 5 bandas usando la ÚLTIMA ponderación
conocida de cada oferta (≈ `proyectos.ponderacion`). Por banda muestra: monto
ponderado, nº de ofertas, monto bruto y eficiencia (ponderado/bruto×100). El ancho de
cada barra = bruto de la banda / bruto total. Incluye un insight textual: banda con
mayor concentración de monto y banda con más ofertas.
Responde preguntas como: «¿cómo se distribuye la cartera por probabilidad?»,
«¿cuántas ofertas hay en 75% probable y cuánto valen?», «¿dónde se concentra el
monto del pipeline?».
Fuente: `DashboardIndex::getStatusOfertasDataProperty()` → `levelResumen`.

SQL equivalente [dash_nivel_probabilidad] (página /):
```sql
SELECT CASE WHEN p.ponderacion = 100 THEN '100% Contratada'
            WHEN p.ponderacion BETWEEN 75 AND 99 THEN '75% Probable'
            WHEN p.ponderacion BETWEEN 25 AND 74 THEN '25% Posible'
            WHEN p.ponderacion BETWEEN 10 AND 24 THEN '10% Remoto'
            ELSE '0% Perdida' END AS banda,
       COUNT(*) AS ofertas, SUM(p.monto_usd) AS bruto,
       SUM(p.monto_usd * p.ponderacion / 100) AS ponderado,
       ROUND(SUM(p.monto_usd * p.ponderacion / 100)
             / NULLIF(SUM(p.monto_usd),0) * 100, 1) AS eficiencia_pct
FROM proyectos p
WHERE p.tipo = 'oportunidad' AND p.monto_usd > 0
GROUP BY banda;
```

### [dash_kpis_cartera] KPIs «Bruto / Esperado / Eficiencia» — página /

[dash_kpis_cartera] pagina: / · tipo_grafica: kpi · tabla_base: proyectos ·
en_allowlist: sí.
Contexto: totales de la cartera de oportunidades mostrados al pie de la card «Por
nivel de probabilidad»: monto BRUTO (suma de montos), ESPERADO (suma ponderada por
probabilidad) y EFICIENCIA ponderada (esperado/bruto×100), más el conteo de ofertas
con monto. Sin filtro de año.
Responde preguntas como: «¿cuánto vale la cartera?», «¿cuál es el monto esperado del
pipeline?», «¿qué eficiencia ponderada tenemos?», «monto total de oportunidades».
Fuente: `DashboardIndex::getStatusOfertasDataProperty()` → `carteraKpis`.

SQL equivalente [dash_kpis_cartera] (página /):
```sql
SELECT SUM(p.monto_usd) AS bruto,
       SUM(p.monto_usd * p.ponderacion / 100) AS esperado,
       ROUND(SUM(p.monto_usd * p.ponderacion / 100)
             / NULLIF(SUM(p.monto_usd),0) * 100, 1) AS eficiencia_pct,
       COUNT(*) AS ofertas
FROM proyectos p
WHERE p.tipo = 'oportunidad' AND p.monto_usd > 0;
```

---

## Página `/oportunidades` — Listado de oportunidades

[oportunidades_pagina] La página `/oportunidades` (ruta `oportunidades.index`,
componente `App\Livewire\Proyectos\OportunidadesIndex`) lista el pipeline comercial
del año. **No filtra por `tipo`**: muestra tanto oportunidades como proyectos que
cumplan los filtros. Filtros disponibles: `search` (busca en `cp_numero`,
`dn_numero`, `clientes.razon_social`, `usuario_final`, case-insensitive), `anio`
(default año en curso; valor `todos` quita el filtro; tabs de año-2 a año+1),
`sublineasSeleccionadas[]` (IN sobre `sublinea_id`), `estadosSeleccionados[]` (IN
sobre `estado`), `soloMios` (proyectos donde el usuario autenticado es
`gerente_proyectos` en `proyecto_miembros`). Orden: ofertas con `fecha_envio`
primero, descendente; nulos al final. Paginación 25/50/100 por página.

### [oportunidades_tabla] Tabla «Listado de oportunidades» — página /oportunidades

[oportunidades_tabla] pagina: /oportunidades · tipo_grafica: tabla · tabla_base:
proyectos · relacionadas: clientes, lugares, sublineas, proyecto_miembros, users,
cotizaciones · en_allowlist: sí.
Contexto: tabla paginada con 16 columnas en este orden: CP (`cp_numero`) · Cliente
(`clientes.razon_social`) · Lugar (`lugares.nombre`) · Alcance (`alcance`) · Oferta
(= `tech_reference`, la referencia técnica) · Fecha Envío (`fecha_envio`, con
fallback a la `fecha_emision` de la cotización más reciente) · Fecha Modif.
(`fecha_modificacion_oferta`) · Ofertas Emitidas (= `monto_usd` en USD) · Hitos de
Pago (`hitos_pago`) · Responsable (`elaboro` o, si no, el gerente de proyectos) ·
Status (`estado`) · Arch. Oferta (`archivo_oferta`) · Resultado
(`concepto_adjudicacion`) · % Adj. (= `ponderacion`, con etiqueta 10 Remoto / 25
Posible / 50 Probable / 75 Casi Probable / 100 Contratado) · Cartera Esp.
(`monto_usd × ponderacion / 100`) · Acciones. La fila expandida agrega Contacto,
Datos de Contacto y «% Real» (= `porcentaje_adjudicacion`).
Responde preguntas como: «listado de oportunidades de este año», «¿qué ofertas se
enviaron y cuándo?», «oportunidades de la sublínea X en estado cotizado», «mis
oportunidades como responsable».
Fuente: `OportunidadesIndex::getOportunidadesProperty()`.

SQL equivalente [oportunidades_tabla] (página /oportunidades):
```sql
SELECT p.id, p.cp_numero, c.razon_social AS cliente, l.nombre AS lugar, p.alcance,
       p.tech_reference AS oferta,
       COALESCE(p.fecha_envio, (SELECT MAX(co.fecha_emision) FROM cotizaciones co
                                WHERE co.proyecto_id = p.id)) AS fecha_envio,
       p.fecha_modificacion_oferta, p.monto_usd AS ofertas_emitidas, p.hitos_pago,
       COALESCE(el.name, gp.name) AS responsable, p.estado, p.archivo_oferta,
       p.concepto_adjudicacion AS resultado, p.ponderacion AS pct_adj,
       p.porcentaje_adjudicacion AS pct_real,
       ROUND(p.monto_usd * p.ponderacion / 100, 2) AS cartera_esperada
FROM proyectos p
LEFT JOIN clientes c           ON c.id = p.cliente_id
LEFT JOIN lugares l            ON l.id = p.lugar_id
LEFT JOIN users el             ON el.id = p.elaboro_id
LEFT JOIN proyecto_miembros pm ON pm.proyecto_id = p.id AND pm.rol = 'gerente_proyectos'
LEFT JOIN users gp             ON gp.id = pm.user_id
WHERE p.anio = :anio          -- omitir si anio = 'todos'; NO filtra por tipo
ORDER BY (p.fecha_envio IS NULL), p.fecha_envio DESC;
```

### [oportunidades_kpis] KPIs «Total Ofertas / Ponderado / Adjudicado / Enviadas» — página /oportunidades

[oportunidades_kpis] pagina: /oportunidades · tipo_grafica: kpi · tabla_base:
proyectos · en_allowlist: sí.
Contexto: 4 tarjetas resumen del año. Solo aplican el filtro de año (ignoran search,
sublíneas, estados y soloMios) y excluyen siempre `cancelado, perdido, archivado`:
**Total Ofertas** (conteo + monto del pipeline), **Monto Ponderado** (Σ monto ×
ponderación/100) con **Ponderación Media** (promedio redondeado), **Adjudicado**
(monto + conteo con estado adjudicado_pendiente / adjudicado_firmado / en_ejecucion)
y **Enviadas** (conteo con estado fuera de en_revision/cotizando).
Responde preguntas como: «¿cuánto llevamos adjudicado este año?», «¿cuántas ofertas
hemos enviado?», «monto ponderado del pipeline 2026», «ponderación media de la
cartera».
Fuente: `OportunidadesIndex::getKpisProperty()`.

SQL equivalente [oportunidades_kpis] (página /oportunidades):
```sql
SELECT COUNT(*) AS pipeline_count,
       SUM(monto_usd) AS pipeline_monto,
       COALESCE(SUM(monto_usd * ponderacion / 100), 0) AS monto_ponderado,
       ROUND(AVG(ponderacion)) AS ponderacion_media,
       SUM(CASE WHEN estado IN ('adjudicado_pendiente','adjudicado_firmado','en_ejecucion')
                THEN monto_usd ELSE 0 END) AS adjudicado_monto,
       SUM(CASE WHEN estado IN ('adjudicado_pendiente','adjudicado_firmado','en_ejecucion')
                THEN 1 ELSE 0 END) AS adjudicado_count,
       SUM(CASE WHEN estado NOT IN ('en_revision','cotizando') THEN 1 ELSE 0 END) AS enviadas_count
FROM proyectos
WHERE estado NOT IN ('cancelado','perdido','archivado')
  AND anio = :anio;            -- omitir si anio = 'todos'
```

---

## Página `/clientes` — Cartera de clientes

### [clientes_tabla] Tabla «Listado de clientes» — página /clientes

[clientes_tabla] pagina: /clientes · tipo_grafica: tabla · tabla_base: clientes ·
relacionadas: contactos_cliente · en_allowlist: sí.
Contexto: tabla paginada (25/pág, componente `App\Livewire\Comercial\ClientesIndex`)
de la cartera de clientes. Columnas: Alias · Razón Social · RFC · Sector · Segmento
· Contactos (conteo de `contactos_cliente`) · Estado (activo/inactivo) · acción «Ver
detalle» que lleva a `/clientes/{id}`. Filtros: `buscar` (razon_social, alias, rfc,
case-insensitive), `sector` (valores distintos en BD; típicos: Gobierno, Energía,
Industrial, Privado) e `incluirInactivos` (por defecto solo `activo=1`). Orden por
razón social. Segmentos: A — Estratégico, B — Crecimiento, C — Operativo.
Responde preguntas como: «listado de clientes activos», «clientes del sector
gobierno», «¿cuántos contactos tiene cada cliente?», «buscar cliente por RFC».
Fuente: `ClientesIndex::getClientesProperty()`.

SQL equivalente [clientes_tabla] (página /clientes):
```sql
SELECT c.id, c.alias, c.razon_social, c.rfc, c.sector, c.segmento, c.activo,
       (SELECT COUNT(*) FROM contactos_cliente cc WHERE cc.cliente_id = c.id) AS contactos
FROM clientes c
WHERE c.activo = 1            -- omitir si incluirInactivos
  -- AND (LOWER(c.razon_social) LIKE :q OR LOWER(c.alias) LIKE :q OR LOWER(c.rfc) LIKE :q)
  -- AND c.sector = :sector
ORDER BY c.razon_social;
```

---

## Página `/clientes/{id}` — Detalle de cliente

[cliente_detalle_pagina] La página `/clientes/{id}` (p. ej. `/clientes/48`, ruta
`clientes.show`, componente `App\Livewire\Comercial\ClienteDetalle`) es la ficha 360°
de un cliente. Tiene 5 tabs: **Resumen** (default, con 4 KPIs + proyectos recientes +
condiciones comerciales), **Oportunidades** (tabla de 18 columnas con las ofertas
activas del cliente), **Proyectos** (histórico completo), **Facturación** y
**Documentos** (estos dos últimos en desarrollo, sin datos). Todas las métricas se
calculan sobre los proyectos del cliente (`proyectos.cliente_id = :cliente_id`).

### [cliente_ficha] Header — ficha del cliente — página /clientes/{id}

[cliente_ficha] pagina: /clientes/{id} · tipo_grafica: kpi/ficha · tabla_base:
clientes · relacionadas: contactos_cliente, proyectos · en_allowlist: sí.
Contexto: encabezado con identidad del cliente: razón social, alias (avatar con sus
3 primeras letras), badges de estado (activo/inactivo) y segmento (A/B/C), RFC,
sector, «cliente desde» (`created_at`), nº total de proyectos y última actividad
(`updated_at`). El segmento determina el «score de crédito»: A = bajo riesgo,
B = riesgo medio, C = riesgo alto.
Responde preguntas como: «datos generales del cliente X», «¿qué segmento y sector
tiene el cliente?», «¿desde cuándo es cliente?», «¿el cliente está activo?».
Fuente: `ClienteDetalle` (mount + render).

SQL equivalente [cliente_ficha] (página /clientes/{id}):
```sql
SELECT c.id, c.alias, c.razon_social, c.rfc, c.sector, c.segmento, c.activo,
       c.created_at,
       (SELECT COUNT(*) FROM contactos_cliente cc WHERE cc.cliente_id = c.id) AS contactos,
       (SELECT COUNT(*) FROM proyectos p WHERE p.cliente_id = c.id) AS proyectos_totales
FROM clientes c
WHERE c.id = :cliente_id;
```

### [cliente_kpis] KPIs del tab Resumen — página /clientes/{id}

[cliente_kpis] pagina: /clientes/{id} · tipo_grafica: kpi · tabla_base: proyectos ·
relacionadas: cotizaciones · en_allowlist: sí.
Contexto: 4 tarjetas del cliente. **Facturado total** = Σ por proyecto del
`MAX(cotizaciones.precio_venta_final)` con estado IN (cerrado, en_cierre,
adjudicado_firmado, en_ejecucion). **Pipeline activo** = misma suma con estado IN
(cotizando, cotizado, presentado). **Oportunidades activas** = conteo de proyectos
con estado NOT IN (cancelado, perdido, archivado, en_ejecucion, en_cierre, cerrado).
**Proyectos totales** = conteo de todos los proyectos del cliente. OJO: los montos
salen de la cotización máxima por proyecto, NO de `monto_usd`.
Responde preguntas como: «¿cuánto le hemos facturado al cliente X?», «¿qué pipeline
activo tiene el cliente?», «¿cuántas oportunidades abiertas tiene este cliente?».
Fuente: `ClienteDetalle::render()`.

SQL equivalente [cliente_kpis] (página /clientes/{id}):
```sql
SELECT
  SUM(CASE WHEN p.estado IN ('cerrado','en_cierre','adjudicado_firmado','en_ejecucion')
           THEN cot.max_precio ELSE 0 END) AS facturado_total,
  SUM(CASE WHEN p.estado IN ('cotizando','cotizado','presentado')
           THEN cot.max_precio ELSE 0 END) AS pipeline_activo,
  SUM(CASE WHEN p.estado NOT IN ('cancelado','perdido','archivado',
                                 'en_ejecucion','en_cierre','cerrado')
           THEN 1 ELSE 0 END) AS oportunidades_activas,
  COUNT(*) AS proyectos_totales
FROM proyectos p
LEFT JOIN (SELECT proyecto_id, MAX(precio_venta_final) AS max_precio
           FROM cotizaciones GROUP BY proyecto_id) cot ON cot.proyecto_id = p.id
WHERE p.cliente_id = :cliente_id;
```

### [cliente_proyectos_recientes] Tabla «Proyectos» del tab Resumen — página /clientes/{id}

[cliente_proyectos_recientes] pagina: /clientes/{id} · tipo_grafica: tabla ·
tabla_base: proyectos · relacionadas: sublineas, cotizaciones · en_allowlist: sí.
Contexto: en el tab Resumen se listan los 8 proyectos más recientes del cliente
(orden `updated_at` DESC). Columnas: Proyecto (CP o DN) · Tipo/Sublínea
(`sublineas.nombre`) · Monto (= `MAX(cotizaciones.precio_venta_final)` del proyecto)
· Estado · Cierre (`fecha_fin_planeada`). El tab «Proyectos» muestra esta misma
estructura SIN límite (todos los proyectos) agregando la columna Año (`anio`).
Responde preguntas como: «¿qué proyectos tiene el cliente X?», «últimos proyectos
del cliente y su estado», «¿cuándo cierra cada proyecto del cliente?».
Fuente: `ClienteDetalle::render()` (`$proyectos->take(8)`).

SQL equivalente [cliente_proyectos_recientes] (página /clientes/{id}):
```sql
SELECT p.cp_numero, p.dn_numero, p.tech_reference, s.nombre AS sublinea,
       (SELECT MAX(co.precio_venta_final) FROM cotizaciones co
        WHERE co.proyecto_id = p.id) AS monto,
       p.estado, p.fecha_fin_planeada, p.anio
FROM proyectos p
LEFT JOIN sublineas s ON s.id = p.sublinea_id
WHERE p.cliente_id = :cliente_id
ORDER BY p.updated_at DESC
LIMIT 8;                       -- sin LIMIT en el tab "Proyectos"
```

### [cliente_oportunidades_tab] Tabla del tab Oportunidades — página /clientes/{id}

[cliente_oportunidades_tab] pagina: /clientes/{id} · tipo_grafica: tabla ·
tabla_base: proyectos · relacionadas: lugares, users, proyecto_miembros,
cotizaciones · en_allowlist: sí.
Contexto: ofertas ACTIVAS del cliente (estado NOT IN cancelado, perdido, archivado,
en_ejecucion, en_cierre, cerrado), en una tabla de 18 columnas — las mismas de
`/oportunidades` más Contacto (`contacto`), Datos Contacto (`datos_contacto`) y
% Real (`porcentaje_adjudicacion`) visibles directamente. Filas expandibles con el
detalle completo. Mismas etiquetas de ponderación (10 Remoto … 100 Contratado) y
misma cartera esperada (`monto_usd × ponderacion / 100`).
Responde preguntas como: «¿qué oportunidades activas tiene el cliente X?», «ofertas
en curso del cliente con su monto y probabilidad», «¿quién es el contacto de cada
oferta del cliente?».
Fuente: `ClienteDetalle::render()` (`$oportunidades`).

SQL equivalente [cliente_oportunidades_tab] (página /clientes/{id}):
```sql
SELECT p.cp_numero, p.contacto, p.datos_contacto, l.nombre AS lugar, p.alcance,
       p.tech_reference,
       COALESCE(p.fecha_envio, (SELECT MAX(co.fecha_emision) FROM cotizaciones co
                                WHERE co.proyecto_id = p.id)) AS fecha_envio,
       p.fecha_modificacion_oferta, p.monto_usd, p.hitos_pago, p.estado,
       p.ponderacion, p.porcentaje_adjudicacion,
       ROUND(p.monto_usd * p.ponderacion / 100, 2) AS cartera_esperada,
       COALESCE(el.name, gp.name) AS responsable
FROM proyectos p
LEFT JOIN lugares l            ON l.id = p.lugar_id
LEFT JOIN users el             ON el.id = p.elaboro_id
LEFT JOIN proyecto_miembros pm ON pm.proyecto_id = p.id AND pm.rol = 'gerente_proyectos'
LEFT JOIN users gp             ON gp.id = pm.user_id
WHERE p.cliente_id = :cliente_id
  AND p.estado NOT IN ('cancelado','perdido','archivado',
                       'en_ejecucion','en_cierre','cerrado');
```

### [cliente_contactos] Contactos del cliente — página /clientes/{id}

[cliente_contactos] pagina: /clientes/{id} · tipo_grafica: tabla · tabla_base:
contactos_cliente · en_allowlist: sí.
Contexto: directorio de contactos del cliente (nombre, puesto, email, teléfono y
bandera `principal`; solo puede haber un contacto principal por cliente). Se
gestionan desde el modal «Agregar contacto» de la ficha.
Responde preguntas como: «¿quién es el contacto principal del cliente X?»,
«teléfono y correo de los contactos del cliente», «¿cuántos contactos tiene?».
SQL equivalente: `SELECT nombre, puesto, email, telefono, principal FROM
contactos_cliente WHERE cliente_id = :cliente_id ORDER BY principal DESC, nombre;`

---

## Página `/catalogos-admin` — Administración de catálogos

[catalogos_pagina] La página `/catalogos-admin` (ruta `catalogos.crud.index`,
controlador `App\Http\Controllers\Catalogos\CatalogosCrudController@index`) administra
7 catálogos seleccionables con `?tab={slug}`: `ponderaciones`, `tech_references`,
`core_businesses`, `personnel_acronyms`, `countries`, `varios`, `sizes`. Patrón
común: tabla paginada (25, 50 o 100 por página según el tab), SIN buscador, filtrada
por `status = 1` (borrado lógico: eliminar = poner `status = 0`) y ordenada por `id`.
Cada tab muestra un badge con su total: `COUNT(*) WHERE status = 1`.

### [cat_ponderaciones] Catálogo «Ponderaciones» — /catalogos-admin?tab=ponderaciones

[cat_ponderaciones] tipo_grafica: tabla · tabla_base: ponderaciones · en_allowlist:
sí · paginación: 25/pág.
Contexto: catálogo de bandas de probabilidad que alimenta la ponderación de las
ofertas y el historial mensual. Columnas: Orden (`orden`) · Concepto (`concepto`) ·
% (`porcentaje`) · Color (`color`).
Responde preguntas como: «¿qué niveles de ponderación existen?», «catálogo de
probabilidades y sus colores».
SQL: `SELECT id, orden, concepto, porcentaje, color FROM ponderaciones
WHERE status = 1 ORDER BY id;`

### [cat_tech_references] Catálogo «Tech References» — /catalogos-admin?tab=tech_references

[cat_tech_references] tipo_grafica: tabla · tabla_base: tech_references ·
relacionadas: clientes · en_allowlist: sí · paginación: 50/pág.
Contexto: catálogo de referencias técnicas (proyectos históricos del cliente).
Columnas visibles: Tech Ref (`tech_reference`) · CP (`cp_numero`) · Cliente
(`clientes.alias`) · Proyecto (`nombre_proyecto_cliente`) · Core Bus.
(`core_business`) · USD (`amount_usd`) · Acct Mgr (`account_manager`). La tabla
tiene más columnas en BD (fecha_referencia, revision, contacto, estado_cliente,
pais, zona, pipe_in, branch_in, descripcion_larga, amount_mxn, quotation_personnel).
Responde preguntas como: «referencias técnicas del cliente X», «¿qué tech references
hay por core business?», «monto USD de las referencias técnicas».

SQL equivalente [cat_tech_references]:
```sql
SELECT t.id, t.tech_reference, t.cp_numero, c.alias AS cliente,
       t.nombre_proyecto_cliente, t.core_business, t.amount_usd, t.account_manager
FROM tech_references t
LEFT JOIN clientes c ON c.id = t.cliente_id
WHERE t.status = 1
ORDER BY t.id;
```

### [cat_core_businesses] Catálogo «Core Business» — /catalogos-admin?tab=core_businesses

[cat_core_businesses] tipo_grafica: tabla · tabla_base: core_businesses ·
en_allowlist: sí · paginación: 50/pág.
Contexto: catálogo de líneas de negocio core. Columnas: Core Business
(`core_business`) · Acrónimo (`acronym`) · Descripción (`description`).
Responde preguntas como: «¿qué core business manejamos?», «acrónimos de líneas de
negocio».
SQL: `SELECT id, core_business, acronym, description FROM core_businesses
WHERE status = 1 ORDER BY id;`

### [cat_personnel_acronyms] Catálogo «Personnel Acronyms» — /catalogos-admin?tab=personnel_acronyms

[cat_personnel_acronyms] tipo_grafica: tabla · tabla_base: personnel_acronyms ·
relacionadas: users · en_allowlist: sí · paginación: 50/pág.
Contexto: acrónimos de personal / account managers, opcionalmente ligados a un
usuario del sistema. Columnas: Acrónimo (`acronym`) · Account Manager
(`account_manager`) · Usuario (`users.name`).
Responde preguntas como: «¿qué acrónimo corresponde a cada account manager?»,
«lista de account managers».
SQL: `SELECT pa.id, pa.acronym, pa.account_manager, u.name AS usuario
FROM personnel_acronyms pa LEFT JOIN users u ON u.id = pa.user_id
WHERE pa.status = 1 ORDER BY pa.id;`

### [cat_countries] Catálogo «Countries / States» — /catalogos-admin?tab=countries

[cat_countries] tipo_grafica: tabla · tabla_base: countries · en_allowlist: sí ·
paginación: 100/pág.
Contexto: catálogo geográfico de estados/zonas/países. Columnas: Estado (`state`) ·
Zona (`zone`) · País (`country`).
Responde preguntas como: «¿qué estados y zonas están dados de alta?», «catálogo de
países».
SQL: `SELECT id, state, zone, country FROM countries WHERE status = 1 ORDER BY id;`

### [cat_varios] Catálogo «Varios» — /catalogos-admin?tab=varios

[cat_varios] tipo_grafica: tabla · tabla_base: varios · en_allowlist: sí ·
paginación: 100/pág.
Contexto: catálogo libre de conceptos varios. Columna única: Nombre (`nombre`).
SQL: `SELECT id, nombre FROM varios WHERE status = 1 ORDER BY id;`

### [cat_sizes] Catálogo «Sizes» — /catalogos-admin?tab=sizes

[cat_sizes] tipo_grafica: tabla · tabla_base: sizes · en_allowlist: sí ·
paginación: 100/pág.
Contexto: catálogo de medidas. Columnas: Size Principal en pulgadas
(`size_principal`) · Size Secundario (`size_secundario`).
SQL: `SELECT id, size_principal, size_secundario FROM sizes
WHERE status = 1 ORDER BY id;`

---

## Apéndice — datasets calculados pero NO renderizados (Dashboard)

[apendice_no_renderizado] `DashboardIndex` calcula y serializa a JS datos que hoy NO
se pintan (sus `<canvas>` están comentados o las variables no se usan en el blade).
NO deben tratarse como vistas vigentes; se listan por si se reactivan:
`chartData.byMonth` (monto por mes apilado por banda, fuente
`cotizaciones.precio_venta_final`), `chartData.bySublinea` (top 10 sublíneas),
`chartData.byCliente` (top 8 clientes), `carteraData` (bruto/esperado acumulado por
umbral ≥0/≥10/≥25/≥75/=100), `byResponsable` (bruto/ponderado/conteo por
responsable), `mesesSinContratacion.burn_serie` (burn-down del backlog) y la función
`initProjChart(idx)` (mini-línea de probabilidad + ponderado por oferta, canvas
comentado). También `montoByMonth`, `ponderadoByMonth` y `contratadoByMonth`
(series mensuales) se calculan sin pintarse.

---

## Nota de ingestión (para el mantenedor, no para el RAG)

**Fuente de verdad:** este archivo se edita AQUÍ (repo Laravel, documenta sus vistas)
y se sincroniza como copia de ingestión a `context/cartera_db/` del proyecto
langchain, donde se indexa en ChromaDB vía `scripts/indexar_contexto.py` (colección
propia del módulo de consultas; el orquestador inyecta los top-k chunks relevantes
al prompt NL→SQL). Cada bloque entre líneas en blanco cabe en un chunk
(chunk_size=1000, overlap=150) y repite su `[id]`, página y tabla base, por lo que
con top-k=3 cualquier chunk recuperado es autosuficiente. Si se agrega una vista
nueva: copiar el patrón (bloque descriptivo + bloque SQL, ambos prefijados con el
`[id]`), incluir 2-4 «Responde preguntas como» en lenguaje de negocio, mantener cada
bloque por debajo de ~950 caracteres y re-ejecutar `python scripts/indexar_contexto.py`.
Las consultas few-shot estructuradas viven en `config/rules.yaml` (allowlist +
ejemplos por tabla); este MD es el contexto semántico complementario.
