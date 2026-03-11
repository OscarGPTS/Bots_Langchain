# 🚀 Bot de Documentos Avanzado - Guía Completa

## 📋 Descripción

Bot inteligente con vectorización ChromaDB que ofrece:
- 🗄️ **ChromaDB**: Base de datos vectorial persistente
- ☁️ **Dual AI**: OpenAI (cloud) o Ollama (local)
- ⚡ **Modo Rápido**: Consultas directas (GPT-4o-mini / Ollama)
- 🧠 **Modo Profundo**: Análisis complejos con reasoning (GPT-4o / Ollama)
- 💰 **Monitor de costos**: Tracking de tokens y gastos USD
- 🔍 **Context Caching**: Reutilización de contexto en OpenAI

---

## 🎯 Configuración

### 1. Instalar dependencias adicionales

```powershell
pip install chromadb tiktoken
```

### 2. Configurar .env

#### Opción A: Modo Local (SIN COSTOS)

```env
# Usar Ollama local
LOCALIA=true

# ChromaDB
CHROMA_DB_PATH=./chroma_db
CHUNK_SIZE=1000
CHUNK_OVERLAP=150
```

#### Opción B: Modo Cloud (OpenAI)

```env
# Usar OpenAI
LOCALIA=false
OPENAI_API_KEY=sk-tu_clave_aqui
OPENAI_MODEL_RAPIDO=gpt-4o-mini
OPENAI_MODEL_RAZONAMIENTO=gpt-4o

# ChromaDB
CHROMA_DB_PATH=./chroma_db
CHUNK_SIZE=1000
CHUNK_OVERLAP=150
```

**Obtén tu API key**: https://platform.openai.com/api-keys

---

## 🚀 Inicio Rápido

### Ejecutar el Bot

```powershell
# Modo interactivo
python bots/bot_documentos_avanzado.py

# O ejecutar pruebas
python scripts/probar_bot_avanzado.py
```

### Primer Uso

Al iniciar, el bot automáticamente:
1. ✅ Conecta con Paperless
2. 📥 Descarga todos los documentos
3. ✂️ Los divide en chunks de 1000 tokens (15% overlap)
4. 🗄️ Los vectoriza y guarda en `./chroma_db`
5. 💾 Persiste la base de datos (no re-indexa en futuros usos)

---

## 🎯 Modos de Uso

El bot detecta automáticamente qué modo usar según tu pregunta.

### ⚡ Modo Consulta Rápida

**Cuándo se activa:** Preguntas directas y específicas

**Comportamiento:**
- Recupera solo los 3 chunks más relevantes
- Usa modelo rápido (GPT-4o-mini o Ollama)
- Respuesta concisa y directa
- Bajo consumo de tokens

**Ejemplos:**
```
📝 ¿Cuál es el monto de la factura X?
📝 ¿Qué dice el contrato sobre confidencialidad?
📝 ¿Cuántos días de vacaciones tengo?
📝 Encuentra el punto 4.19 del código de ética
📝 ¿Quién firmó el contrato X?
```

**Salida ejemplo:**
```
⚡ MODO: Consulta Rápida
🔍 Buscando: ¿Qué dice sobre integridad?
📄 Encontrados 3 fragmentos relevantes

🤖 La integridad se define como actuar conforme a las normas 
éticas sin mentir ni engañar, respetando la confidencialidad...

────────────────────────────────────────────────────────────
📚 Documentos consultados:
📄 Código de Ética y Conducta (Creado: 2026-03-10)

────────────────────────────────────────────────────────────
💰 Estadísticas de uso:
   📥 Tokens entrada: 450
   📤 Tokens salida: 120
   💵 Costo estimado: $0.000234 USD
```

---

### 🧠 Modo Razonamiento Profundo

**Cuándo se activa:** Análisis complejos, comparaciones, tendencias

**Palabras clave que lo activan:**
- analiza, compara, resume
- tendencia, patrón, relación
- evolución, historia, explicación detallada
- razonamiento, conclusión, evalúa
- por qué, cómo se relaciona

**Comportamiento:**
- Recupera hasta 10 chunks relevantes
- Usa modelo avanzado (GPT-4o con reasoning o Ollama)
- Análisis detallado con razonamiento lógico
- Mayor consumo de tokens pero mejor calidad

**Ejemplos:**
```
📝 Analiza la tendencia de gastos de los últimos 6 meses
📝 Compara los contratos A y B
📝 Resume los puntos clave del proyecto X
📝 ¿Por qué se rechazó la propuesta anterior?
📝 Evalúa el cumplimiento de las políticas en 2025
```

**Salida ejemplo:**
```
🧠 MODO: Razonamiento Profundo
🔍 Buscando: Analiza los documentos disponibles
📄 Encontrados 10 fragmentos relevantes

🤖 Análisis:

1. Información clave encontrada:
   - Código de Ética con 6 secciones principales
   - Lista de 86 usuarios activos en el sistema
   - Políticas de confidencialidad y conducta

2. Razonamiento lógico:
   Los documentos muestran una empresa estructurada...

3. Conclusiones basadas en evidencia:
   - Alta prioridad en ética empresarial
   - Sistema bien documentado
   
4. Recomendaciones:
   - Mantener actualización periódica...

────────────────────────────────────────────────────────────
📚 Documentos analizados:
📄 Código de Ética y Conducta (2 fragmentos)
📄 Usuarios GPT (8 fragmentos)

────────────────────────────────────────────────────────────
💰 Estadísticas de uso (con razonamiento):
   📥 Tokens entrada: 2,450
   📤 Tokens salida: 680
   🧠 Tokens razonamiento: incluidos en entrada
   💵 Costo estimado: $0.008234 USD
```

---

## 🔍 Filtros Automáticos

El bot detecta automáticamente filtros en tus preguntas:

### Filtro por Año
```
📝 Muestra documentos de 2026
📝 Contratos del año 2025
```
→ Busca solo en documentos creados en ese año

### Filtro por Tipo
```
📝 Busca facturas
📝 Encuentra contratos
📝 Políticas de la empresa
```
→ Busca documentos con esos tags/palabras en el título

### Combinación de Filtros
```
📝 Facturas de 2025
📝 Contratos del proyecto X en 2026
```

---

## 🗄️ ChromaDB - Gestión de Vectores

### Primera ejecución
```
📥 Conectando con Paperless
📄 Encontrados 10 documentos
   ✅ Indexado: Código de Ética (15 chunks)
   ✅ Indexado: Usuarios GPT (8 chunks)
   ...
✅ Indexados 10 documentos nuevos
```

### Siguientes ejecuciones
```
📥 Conectando con Paperless
📄 Encontrados 10 documentos
✅ Todos los documentos ya están indexados
```

### Estructura de ChromaDB
```
./chroma_db/
├── chroma.sqlite3          # Metadata
└── [UUID folders]/         # Vectores embeddings
```

### Metadata almacenada por chunk
- `doc_id`: ID del documento en Paperless
- `title`: Título del documento
- `chunk_index`: Número de fragmento
- `total_chunks`: Total de fragmentos del documento
- `created`: Fecha de creación
- `tags`: Tags del documento
- `correspondent`: Remitente/corresponsal

---

## 💰 Optimización de Costos (OpenAI)

### Context Caching

Si haces varias preguntas sobre los mismos documentos, OpenAI reutiliza el contexto:

```
Primera pregunta: $0.008234 USD
Segunda pregunta sobre mismo tema: $0.001234 USD (85% ahorro!)
```

### Estrategias de Ahorro

1. **Usa modo rápido para preguntas simples**: 3 chunks vs 10 chunks
2. **Agrupa preguntas relacionadas**: aprovecha context caching
3. **Filtra por fecha/tipo**: reduce documentos a buscar
4. **LOCALIA=true**: usa Ollama local (sin costos)

### Costos Estimados (OpenAI)

**Consulta Rápida (GPT-4o-mini):**
- ~500 tokens entrada → ~$0.000075 USD
- ~150 tokens salida → ~$0.000045 USD
- **Total: ~$0.00012 USD por consulta**

**Razonamiento Profundo (GPT-4o):**
- ~2,500 tokens entrada → ~$0.0075 USD
- ~700 tokens salida → ~$0.0105 USD
- **Total: ~$0.018 USD por análisis**

---

## 🧪 Pruebas y Desarrollo

### Pruebas Automáticas

```powershell
python scripts/probar_bot_avanzado.py
```

Ejecuta:
- ✅ Inicialización de ChromaDB
- ✅ Consulta rápida
- ✅ Razonamiento profundo
- ✅ Detección automática de modo

### Comandos Interactivos

Una vez dentro del bot:

```
📝 help          → Mostrar ayuda
📝 ayuda         → Mostrar ayuda
📝 salir         → Cerrar bot
📝 exit          → Cerrar bot
```

---

## 🔧 Troubleshooting

### Error: "OPENAI_API_KEY not found"

**Solución:**
```env
# En .env
OPENAI_API_KEY=sk-tu_clave_real
```

### Error: "chromadb not installed"

**Solución:**
```powershell
pip install chromadb tiktoken
```

### ChromaDB está desactualizado

```powershell
# Eliminar y recrear
Remove-Item -Recurse -Force ./chroma_db
python bots/bot_documentos_avanzado.py
```

### Bot no encuentra documentos nuevos

El bot verifica automáticamente. Si agregaste documentos a Paperless:
```powershell
# Eliminar ChromaDB y re-indexar
Remove-Item -Recurse -Force ./chroma_db
python bots/bot_documentos_avanzado.py
```

---

## 📊 Comparación: Bot Simple vs Avanzado

| Característica | Bot Simple | Bot Avanzado |
|----------------|------------|--------------|
| Búsqueda | Keyword en Paperless | Semántica con vectores |
| Persistencia | No | Sí (ChromaDB) |
| AI | Solo Ollama | Ollama + OpenAI |
| Modos | Único | Rápido + Profundo |
| Context Caching | No | Sí (OpenAI) |
| Costos | Gratis | $0.00012 - $0.018 por consulta |
| Velocidad | Rápida | Muy rápida (cache) |
| Precisión | Buena | Excelente |
| Análisis | Básico | Avanzado con reasoning |

---

## 💡 Casos de Uso Recomendados

### Bot Simple (bot_documentos.py)
- ✅ Búsquedas rápidas ocasionales
- ✅ Preguntas directas simples
- ✅ No quieres instalar ChromaDB
- ✅ Solo usas Ollama local

### Bot Avanzado (bot_documentos_avanzado.py)
- ✅ Consultas frecuentes al mismo conjunto de documentos
- ✅ Análisis complejos y comparaciones
- ✅ Gran volumen de documentos (100+)
- ✅ Necesitas búsqueda semántica precisa
- ✅ Tienes presupuesto para OpenAI (opcional)

---

## 📚 Recursos Adicionales

- [Documentación LangChain](https://python.langchain.com/)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [OpenAI Pricing](https://openai.com/api/pricing/)
- [Ollama Models](https://ollama.ai/library)

---

## 🤝 Soporte

Para problemas o preguntas:
1. Revisa esta guía
2. Verifica el README.md principal
3. Consulta los scripts de prueba en `scripts/`
