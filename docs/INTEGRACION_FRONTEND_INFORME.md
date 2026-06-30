# Integración Frontend — Respuesta de Consultas (nuevo `tipo: "informe"`)

Guía para consumir el endpoint de Consultas desde el frontend (Laravel + Livewire),
con foco en la **nueva funcionalidad de informe ejecutivo en Markdown**. El backend ya
entrega el contenido formateado: **el front ya no arma el formato del informe**, solo lo
renderiza.

---

## 1. Qué cambió (resumen)

- Nuevo valor en el campo `tipo`: **`"informe"`** (antes solo `texto | tabla | grafico`).
- Cuando `tipo === "informe"`, el campo **`texto` contiene Markdown** ya redactado
  (informe ejecutivo: título, resumen, hallazgos, tabla embebida, recomendaciones).
- El informe **incluye además los datos crudos** en `tabla` (y `grafico` si aplica), por
  si quieres mostrarlos o auditarlos aparte del Markdown.
- **Doble disparo:**
  - **Explícito:** manda `formato: "informe"` en la petición → respuesta garantizada como informe.
  - **Automático:** si la pregunta pide "informe / reporte / análisis ejecutivo / resumen",
    la IA devuelve `tipo: "informe"` sola, sin que mandes nada especial.
- Retrocompatible: `texto`, `tabla`, `grafico` siguen igual. Si tu front no conoce
  `"informe"`, basta tratarlo como texto.

---

## 2. Contrato de la respuesta

`POST /api/v1/consultas/` (JSON) → `200`:

```jsonc
{
  "origen": "cartera_db",
  "tipo": "informe",                 // texto | tabla | grafico | informe
  "titulo": "Informe ejecutivo de la cartera",
  "texto": "## Informe Ejecutivo...\n\n**Resumen ejecutivo**\n...",  // MARKDOWN si tipo=informe
  "tabla": {                          // datos crudos que sustentan el informe (puede venir null)
    "columnas": ["banda", "ofertas", "bruto", "esperado"],
    "filas": [["75% Probable", 6, 34096673.90, 25572505.43], ["..."]],
    "total_filas": 4,
    "truncado": false                 // true si se alcanzó el tope de filas (max_filas)
  },
  "grafico": null,                    // GraficoPayload o null
  "meta": {
    "origen_tipo": "sql_mysql",
    "consulta_generada": "SELECT ...",// SQL ejecutado (auditoría)
    "candidatos": ["proyectos"],
    "advertencias": ["..."]           // avisos (p. ej. fallback aplicado); mostrar como nota
  },
  "tiempo_respuesta": 2.34
}
```

### Petición

```jsonc
// POST /api/v1/consultas/
{
  "consulta": "genérame un informe ejecutivo de la cartera de oportunidades",
  "origen": "cartera_db",
  "formato": "informe",   // opcional: fuerza el informe. Si se omite, la IA decide.
  "usuario": "Oscar"      // opcional: personaliza el informe ("Oscar, la cartera...")
}
```

### Semántica del campo `texto` según `tipo`

| `tipo`      | `texto`                                  | `tabla`        | `grafico` |
|-------------|------------------------------------------|----------------|-----------|
| `texto`     | resumen corto en **texto plano**         | normalmente null | null    |
| `tabla`     | nota corta ("Aquí tienes: N registros")  | datos          | null      |
| `grafico`   | nota corta                               | datos (respaldo) | spec Chart.js |
| **`informe`** | **Markdown** (informe ejecutivo)        | datos crudos   | opcional  |

> Regla de oro en el front: **renderiza `texto` como Markdown solo cuando `tipo === "informe"`**.
> Para los demás tipos, `texto` es texto plano.

---

## 3. Flujo con Livewire + controlador

Como la data pasa por tu controlador antes de llegar al componente:

```php
// app/Http/Controllers/.../ConsultasController.php  (o un Service)
public function consultar(string $pregunta, ?string $formato = null): array
{
    $resp = Http::timeout(30)
        ->acceptJson()
        ->post(config('services.bots.url').'/api/v1/consultas/', [
            'consulta' => $pregunta,
            'origen'   => 'cartera_db',
            'formato'  => $formato,          // 'informe' para forzarlo, o null
            'usuario'  => auth()->user()?->name,
        ]);

    $resp->throw();                          // 400/503/... -> excepción
    return $resp->json();                    // array con tipo, texto, tabla, grafico, meta
}
```

```php
// En el componente Livewire
public array $resultado = [];

public function preguntar(string $pregunta): void
{
    // Si tienes un botón "Informe ejecutivo", pasa formato='informe'
    $this->resultado = app(ConsultasController::class)->consultar($pregunta);
}

// Helper para la vista
public function getEsInformeProperty(): bool
{
    return ($this->resultado['tipo'] ?? null) === 'informe';
}
```

### Render en Blade (switch por `tipo`)

```blade
@php $r = $resultado; @endphp

@if(($r['tipo'] ?? '') === 'informe')
    {{-- texto es Markdown: convertir a HTML y SANITIZAR --}}
    <div class="prose max-w-none">
        {!! $this->renderMarkdown($r['texto'] ?? '') !!}
    </div>

    {{-- opcional: datos crudos que sustentan el informe --}}
    @if(!empty($r['tabla']['filas']))
        <details class="mt-4">
            <summary>Ver datos</summary>
            <x-tabla :columnas="$r['tabla']['columnas']" :filas="$r['tabla']['filas']" />
        </details>
    @endif

@elseif(($r['tipo'] ?? '') === 'grafico')
    <x-chart :spec="$r['grafico']" />
@elseif(($r['tipo'] ?? '') === 'tabla')
    <x-tabla :columnas="$r['tabla']['columnas']" :filas="$r['tabla']['filas']" />
@else
    <p>{{ $r['texto'] ?? '' }}</p>   {{-- texto plano --}}
@endif

@foreach(($r['meta']['advertencias'] ?? []) as $aviso)
    <p class="text-amber-600 text-sm">⚠️ {{ $aviso }}</p>
@endforeach
```

---

## 4. Renderizar el Markdown (y seguridad)

El Markdown viene del backend pero **al convertirlo a HTML debes sanitizar** (es contenido
generado; nunca lo imprimas sin limpiar para evitar XSS).

```php
use Illuminate\Support\Str;

public function renderMarkdown(string $md): string
{
    // Str::markdown usa league/commonmark. Activa el saneado del propio CommonMark:
    return Str::markdown($md, [
        'html_input'         => 'escape',  // ignora/escapa HTML embebido
        'allow_unsafe_links' => false,
    ]);
}
```

- Si quieres doble capa, pasa el HTML por **HTMLPurifier** antes de `{!! !!}`.
- Usa la clase `prose` (Tailwind Typography) o tus estilos para que el Markdown se vea bien
  (tablas, listas, encabezados, negritas).
- **Nunca** uses `{!! $r['texto'] !!}` directo sin convertir+sanear.

---

## 5. Consideraciones

- **Respuestas largas:** el informe está pensado para texto extenso. `texto` (Markdown)
  **no se trunca**. La `tabla` cruda sí respeta el tope de filas del backend
  (`max_filas`); revisa `tabla.truncado` para avisar "se recortó el listado".
- **`tipo` desconocido:** si llega un `tipo` que el front no maneja, trátalo como texto
  (`{{ $r['texto'] }}`). Así no rompes ante futuros tipos.
- **Datos crudos opcionales:** en `informe`, mostrar la `tabla` es opcional (el Markdown ya
  suele traer una tabla embebida). Úsala para "Ver datos" / exportar / auditar con
  `meta.consulta_generada`.
- **`grafico` en informe:** normalmente `null`; solo viene si la consulta ameritaba gráfico.
- **Voz:** `POST /api/v1/consultas/voz` devuelve la MISMA estructura dentro de `resultado`
  (más `pregunta_transcrita` y `audio_base64`). El manejo de `tipo='informe'` es idéntico;
  ahí `formato` se manda como campo de formulario (`multipart/form-data`).
- **Errores HTTP a contemplar:** `400` (origen/consulta inválida o SQL no permitido),
  `503` (módulo deshabilitado o error de conexión al origen), y en voz `413` (audio grande)
  / `422` (audio ininteligible). Muestra `detail` del JSON de error al usuario.
- **`meta.advertencias`:** array de avisos no fatales (p. ej. "se aplicó un fallback").
  Conviene mostrarlos discretamente; no son errores.
- **Latencia:** el informe hace una llamada extra al LLM (redacción del Markdown), así que
  tarda un poco más que una tabla simple. Considera un loader específico.
- **Botón sugerido en UI:** ofrece "Respuesta normal" vs "Informe ejecutivo" → el segundo
  manda `formato: "informe"`. Aun sin botón, frases como "dame un informe de…" lo activan solas.
```
