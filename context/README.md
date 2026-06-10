# `context/` — Contexto semántico por origen (para el módulo de Consultas)

Cada subcarpeta corresponde a un **origen** del catálogo `config/rules.yaml`
(la clave canónica del origen, p. ej. `cartera_db`). Los `.md` que contenga se
indexan en una colección propia de ChromaDB y el orquestador de consultas
inyecta los chunks relevantes al prompt NL→SQL como sección «Vistas del sistema».

```
context/
└── cartera_db/                        # = clave del origen en rules.yaml
    └── CONTEXTO_GRAFICAS_DASHBOARD.md # catálogo de vistas del sistema Laravel
```

## Flujo

1. **Fuente de verdad:** el documento se edita en el repo del proyecto que
   documenta (p. ej. `GPT_Catera_Clientes2/docs/`) y se sincroniza aquí como
   copia de ingestión.
2. **Indexar:** `python scripts/indexar_contexto.py` (idempotente: reemplaza
   los chunks del archivo en la colección).
3. **Consumo:** `app/services/consultas/contexto_rag.py` recupera top-k chunks
   filtrados por origen y los inyecta en `generador.generar_sql()`. Si ChromaDB
   no está disponible o la colección está vacía, las consultas degradan a solo
   `rules.yaml` sin fallar.

## Convención de formato (optimizada para chunking)

El splitter es `RecursiveCharacterTextSplitter` con `chunk_size=1000`,
`chunk_overlap=150` y separador principal `\n\n`. Por eso:

- **Un bloque = una idea autocontenida**, separado por línea en blanco y de
  **menos de ~950 caracteres**, para que nunca se parta a la mitad.
- Cada bloque inicia con su **`[id]`** (slug único) y repite página y tabla
  base: cualquier chunk recuperado funciona sin el resto del documento.
- Por cada visualización van **dos bloques** con el mismo `[id]`:
  1. *Descriptivo*: `pagina · tipo_grafica · tabla_base · relacionadas ·
     en_allowlist`, contexto de negocio, columnas y **2–4 «Responde preguntas
     como»** en lenguaje del usuario (anclas semánticas del retrieval).
  2. *SQL equivalente*: un solo fence ```sql con la consulta que reproduce la
     vista, usando únicamente tablas de la allowlist.
- Glosario y reglas de negocio transversales van en bloques `[glosario_*]` al
  inicio del documento.
- Nada de tablas Markdown largas ni JSON consolidado: se trocean mal y duplican
  contenido.

## Checklist al agregar/editar una vista

- [ ] Bloque descriptivo + bloque SQL, ambos prefijados con el `[id]`.
- [ ] Bloques < ~950 caracteres y separados por línea en blanco.
- [ ] El SQL solo referencia tablas en la allowlist de `rules.yaml`.
- [ ] Si la vista introduce una fórmula/regla nueva, espejearla también en el
      `contexto` o `ejemplos` del origen en `rules.yaml` (few-shot estructurado).
- [ ] Re-ejecutar `python scripts/indexar_contexto.py`.
