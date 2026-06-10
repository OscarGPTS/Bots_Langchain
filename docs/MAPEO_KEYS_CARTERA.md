# 🗺️ Mapeo de keys — Origen `cartera_db` (Cartera de Clientes)

Referencia para integrar/consumir el servicio de consultas sobre la base
**cartera_clientes** (solo lectura). Resume **cómo identificar el origen** y **qué
palabras (keys) enrutan cada tabla**, además de las columnas disponibles.

> El bot reconoce la tabla por las *keys* presentes en la consulta. Para forzar una tabla
> concreta, usa el campo `objetivo` (p.ej. `"objetivo": "proyectos"`).
> No contiene credenciales: la conexión se configura en el `.env` del servidor.

---

## 🏷️ Identificar el origen (`origen`)

Cualquiera de estos valores resuelve al origen (no distingue mayúsculas, ni `http(s)://`,
ni `/` final). En la respuesta, `origen` siempre vuelve como la clave canónica `cartera_db`.

| Tipo | Valores aceptados |
|------|-------------------|
| Clave canónica | `cartera_db` |
| Alias / nombre | `cartera`, `cartera_clientes`, `Cartera de Clientes` |
| URLs | `https://cartera-clientes.tech-energy.lat`, `http://localhost:8001` |

---

## 🔑 Keys → Tabla

| Tabla | Keys que la activan |
|-------|---------------------|
| `clientes` | cliente, clientes, cuenta, cuentas, razon, razon social, empresa, empresas |
| `contactos_cliente` | contacto, contactos, contacto cliente, persona de contacto |
| `proyectos` | proyecto, proyectos, oportunidad(es), cp, dn, adjudicacion(es), oferta(s), pipeline, cartera |
| `cotizaciones` | cotizacion, cotizaciones, oferta_economica, precio, precios |
| `users` | usuario(s), user(s), vendedor(es), socio(s), responsable(s) |
| `proyecto_ponderacion_historial` | historial, historial de ponderacion, avance, evolucion, ponderacion mensual, snapshot |
| `ponderaciones` | ponderacion, ponderaciones, banda, bandas, probabilidad(es) |
| `sublineas` | sublinea, sublineas, linea de negocio, lineas |
| `lugares` | lugar, lugares, ubicacion(es), sede(s) |
| `proyecto_miembros` | miembro(s), miembros del proyecto, equipo, gerente(s) |
| `tech_references` | tech reference(s), referencia(s) tecnica(s), techref |
| `core_businesses` | core business(es), giro(s) |
| `personnel_acronyms` | acronimo(s), account manager(s), personnel |
| `countries` | pais(es), estado(s), zona(s), country, countries |
| `varios` | varios, vario |
| `sizes` | size(s), medida(s), tamaño |

> **Contexto de negocio** (fórmulas de ponderado/bandas, "adjudicado", catálogos con
> `status=1`, etc.) y **ejemplos** que reproducen las vistas del dashboard están cargados
> en el origen. Detalle/fuente: [context/cartera_db/CONTEXTO_GRAFICAS_DASHBOARD.md](../context/cartera_db/CONTEXTO_GRAFICAS_DASHBOARD.md).

---

## 📋 Tablas y columnas

### `clientes`  *(≈399 registros)*
Clientes de la cartera.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | bigint | ID del cliente |
| razon_social | varchar | Razón social / nombre |
| alias | varchar | Alias corto |
| rfc | varchar | RFC |
| sector | varchar | Sector (industria) |
| segmento | varchar | Segmento comercial |
| activo | tinyint | 1 = activo, 0 = inactivo |
| created_at | timestamp | Fecha de alta |

### `contactos_cliente`
Contactos asociados a cada cliente. **Relación:** `contactos_cliente.cliente_id = clientes.id`.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | bigint | |
| cliente_id | bigint | FK → clientes.id |
| nombre | varchar | Nombre del contacto |
| puesto | varchar | |
| email | varchar | |
| telefono | varchar | |
| principal | tinyint | 1 = contacto principal |

### `proyectos`  *(≈30 registros)*
Proyectos y oportunidades comerciales. **Relación:** `proyectos.cliente_id = clientes.id`.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | bigint | |
| cp_numero | varchar | Número CP |
| dn_numero | varchar | Número DN |
| anio | year | Año |
| cliente_id | bigint | FK → clientes.id |
| usuario_final | varchar | Usuario final |
| sector | varchar | |
| estado | enum | en_revision, cotizando, cotizado, enviado, presentado, adjudicado_pendiente, adjudicado_firmado, en_ejecucion, en_cierre, cerrado, cancelado, perdido, archivado |
| tipo | enum | oportunidad, proyecto |
| ponderacion | tinyint | Ponderación (probabilidad %) |
| monto_usd | decimal | Monto en USD |
| cartera_esperada | decimal | Cartera esperada en USD |
| fecha_envio | date | Fecha de envío de la oferta |
| fecha_inicio_planeada | date | |
| fecha_fin_planeada | date | |
| created_at | timestamp | Fecha de creación |

### `cotizaciones`
Cotizaciones por proyecto. **Relación:** `cotizaciones.proyecto_id = proyectos.id`.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | bigint | |
| proyecto_id | bigint | FK → proyectos.id |
| version | int | |
| precio_venta_final | decimal | Precio de venta final |
| moneda | varchar | |
| status | enum | borrador, revision, interno_aprobado, presentado, aprobado, rechazado |
| fecha_emision | date | |

### `users`
Usuarios internos del sistema.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | bigint | |
| name | varchar | Nombre del usuario |
| email | varchar | |
| departamento | varchar | |
| puesto | varchar | |
| es_socio | tinyint | 1 = socio |
| status | enum | active, invited, suspended |
| created_at | timestamp | |

---

## 🔗 Relaciones (JOIN habilitados)

| Desde | Hacia | Condición |
|-------|-------|-----------|
| contactos_cliente | clientes | `contactos_cliente.cliente_id = clientes.id` |
| proyectos | clientes | `proyectos.cliente_id = clientes.id` |
| cotizaciones | proyectos | `cotizaciones.proyecto_id = proyectos.id` |

---

## 💬 Ejemplos de consulta

| Consulta | Tabla(s) | Resultado típico |
|----------|----------|------------------|
| "¿cuántos clientes hay por sector?" | clientes | gráfico (bar) |
| "lista de clientes activos del sector energía" | clientes | tabla |
| "top 5 proyectos por monto en usd" | proyectos | tabla |
| "monto total por cliente, top 5" *(objetivo: proyectos)* | proyectos + clientes (JOIN) | tabla |
| "proyectos por estado en una gráfica" | proyectos | gráfico |

> Contrato de entrada/salida de la API y más ejemplos: [API_CONSULTAS.md](API_CONSULTAS.md).
> Definición fuente del catálogo: `config/rules.yaml` (origen `cartera_db`).
