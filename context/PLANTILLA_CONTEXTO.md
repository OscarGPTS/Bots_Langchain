# Contexto de visualizaciones — {Nombre del Sistema} (para RAG)

<!-- ============================================================
PLANTILLA — Copiar a context/<clave_origen>/CONTEXTO_<SISTEMA>.md
(la clave_origen DEBE coincidir con la clave del origen en
config/rules.yaml; la carpeta es lo que filtra el retrieval).
Reemplazar los {placeholders}, borrar los comentarios <!- -> y
ejecutar `python scripts/indexar_contexto.py`.
Reglas de oro (detalle en context/README.md):
  - 1 bloque = 1 idea autocontenida, < ~950 caracteres, separado
    por línea en blanco (chunking 1000/150, separador \n\n).
  - Todo bloque inicia con su [id] y repite página/tabla base.
  - 2-4 «Responde preguntas como» por vista, en lenguaje del usuario.
  - El SQL solo usa tablas de la allowlist de rules.yaml.
============================================================ -->

Catálogo de las visualizaciones (tablas, KPIs y gráficas) del sistema {Nombre}
({stack, p.ej. Laravel 12 + Livewire 3}), sobre la base {motor} `{nombre_bd}`.
Su propósito es darle contexto al servicio de Consultas a Datos (RAG): qué tabla(s)
consultar, con qué filtros y columnas, para reproducir fielmente cada vista.

**Formato optimizado para ingestión:** cada visualización se describe en bloques
autocontenidos de ~900 caracteres separados por línea en blanco (alineado al chunking
del RAG: `RecursiveCharacterTextSplitter`, chunk_size=1000, overlap=150, separador
principal `\n\n`). Cada bloque inicia con su `[id]` y página, de modo que cualquier
chunk recuperado funciona sin depender del resto del documento.

**Allowlist:** `config/rules.yaml` del servicio de consultas expone las {N} tablas
del origen `{clave_origen}` (`{tabla1}, {tabla2}, …`). Todas las entradas de este
documento marcan `en_allowlist: sí`.

---

## Glosario y reglas de negocio

<!-- Bloques [glosario_*]: fórmulas, sinónimos del usuario, catálogos de estados,
relaciones FK. Son los chunks más recuperados: invertir aquí. -->

[glosario_metricas] Métricas de {dominio} (aplican en todo el sistema).
**{Métrica A}** = `{fórmula SQL}`. **{Métrica B}** = `{fórmula SQL}`.
Sinónimos: {término del usuario} = {término técnico}; {…} = {…}.

[glosario_estados] Catálogo de `{tabla.columna_estado}` ({N} valores) con su
etiqueta UI: `{valor}` ({Etiqueta}), `{valor}` ({Etiqueta}), …
**"{Agregado de negocio}"** = estado IN (`{v1}`, `{v2}`). **{Otro agregado}**
excluye estado IN (`{v1}`, `{v2}`).

[glosario_relaciones] Relaciones (FK) del modelo de datos `{nombre_bd}`:
`{tabla_a.fk} → {tabla_b.id}` · `{…}` · `{…}`.
{Convenciones transversales: nombre visible, borrado lógico, filtros default.}

---

## Página `{/ruta}` — {Título de la página}

[{pagina_id}] La página `{/ruta}` (ruta `{nombre.ruta}`, componente/controlador
`{Clase}`) {qué muestra y para quién}. {Particularidades globales de la página:
filtros default, qué NO filtra, de dónde sale el eje temporal, etc.}

### [{vista_id}] {Tipo} «{Título visible}» — página {/ruta}

[{vista_id}] pagina: {/ruta} · tipo_grafica: {tabla|kpi|grafico:line|grafico:bar|grafico:pie} ·
tabla_base: {tabla} · relacionadas: {tablas JOIN} · en_allowlist: sí.
Contexto: {qué muestra, fórmulas y filtros implícitos; señalar trampas tipo
"NO filtra por año" o "el monto sale de X, no de Y"}.
Responde preguntas como: «{pregunta natural 1}», «{pregunta natural 2}»,
«{pregunta natural 3}».
Columnas: {col1}, {col2}, {…}.
Fuente: `{Clase::metodo()}`.

SQL equivalente [{vista_id}] (página {/ruta}):
```sql
SELECT {…}
FROM {tabla_base} {alias}
{JOINs}
WHERE {filtros}
{GROUP BY / ORDER BY};
```

<!-- Repetir el par descriptivo+SQL por cada vista. Mantener el MISMO [id]
en ambos bloques: es lo que los une cuando el retrieval trae solo uno. -->

---

## Apéndice — datasets calculados pero NO renderizados

[apendice_no_renderizado] {Componentes que calculan datos sin pintarlos (canvas
comentados, variables sin usar). Listarlos evita que el RAG los trate como
vistas vigentes.} NO deben tratarse como vistas vigentes; se listan por si se
reactivan: {dataset1} ({qué representaría}), {dataset2} ({…}).

---

## Nota de ingestión (para el mantenedor, no para el RAG)

**Fuente de verdad:** este archivo se edita en `{repo_fuente}/docs/` y se
sincroniza como copia de ingestión a `context/{clave_origen}/` del proyecto
langchain (registrarlo en `FUENTES` de `scripts/sincronizar_contexto.py`).
Indexación: `python scripts/indexar_contexto.py` (o `sincronizar_contexto.py`,
que copia y reindexa). Si se agrega una vista nueva: copiar el patrón (bloque
descriptivo + bloque SQL, ambos prefijados con el `[id]`), incluir 2-4 «Responde
preguntas como» en lenguaje de negocio, mantener cada bloque por debajo de ~950
caracteres y reindexar. Las consultas few-shot estructuradas viven en
`config/rules.yaml` (allowlist + ejemplos por tabla); este MD es el contexto
semántico complementario.
