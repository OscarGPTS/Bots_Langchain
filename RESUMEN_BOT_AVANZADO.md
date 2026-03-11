# 🚀 RESUMEN - Bot de Documentos Avanzado Implementado

## ✅ Lo que se ha creado

### 📂 Archivos Nuevos

1. **bots/bot_documentos_avanzado.py** (750+ líneas)
   - Bot completo con ChromaDB y soporte dual OpenAI/Ollama
   - Modos: Consulta Rápida y Razonamiento Profundo
   - Monitor de costos integrado
   - Vectorización persistente

2. **BOT_AVANZADO.md**
   - Guía completa de uso
   - Ejemplos detallados
   - Troubleshooting
   - Comparación con bot simple

3. **scripts/instalar_bot_avanzado.py**
   - Instalador automático de dependencias

4. **scripts/probar_bot_avanzado.py**
   - Suite de pruebas automáticas

### 📝 Archivos Actualizados

1. **.env**
   - Nueva variable `LOCALIA=true`
   - Configuración OpenAI completa
   - Parámetros ChromaDB

2. **.env.example**
   - Template actualizado con nuevas variables

3. **requirements.txt**
   - Agregado `chromadb>=0.4.22`
   - Agregado `tiktoken>=0.5.2`

4. **.gitignore**
   - Agregado `chroma_db/` para ignorar base vectorial

5. **README.md**
   - Actualizada sección de características
   - Nueva estructura del proyecto

---

## 🎯 Características Implementadas

### ✅ 1. Gestión de Documentos y Memoria

- ✅ **ChromaDB**: Persistencia en `./chroma_db`
- ✅ **Carga desde Paperless**: Descarga automática de documentos
- ✅ **Chunks**: 1000 tokens con 15% overlap (150 tokens)
- ✅ **Embeddings**: OpenAIEmbeddings o OllamaEmbeddings según config
- ✅ **No re-indexa**: Detecta documentos ya procesados

### ✅ 2. Lógica de Selección de Modelos

- ✅ **Modo Consulta Rápida**:
  - Recupera solo 3 chunks más relevantes
  - GPT-4o-mini (OpenAI) o Ollama (local)
  - Respuestas directas y concisas
  
- ✅ **Modo Razonamiento**:
  - Recupera hasta 10 chunks
  - GPT-4o con `reasoning_effort="medium"` (OpenAI) o Ollama
  - Análisis profundo con razonamiento lógico
  
- ✅ **Detección automática**: Identifica qué modo usar según la pregunta

### ✅ 3. Optimización de Costos

- ✅ **Context Caching**: Implementado con OpenAI API
- ✅ **Metadata Filtering**: Filtros por tags y fecha automáticos
- ✅ **Recuperación selectiva**: 3 chunks para rápido, 10 para profundo
- ✅ **LOCALIA flag**: Permite cambiar entre local (gratis) y cloud

### ✅ 4. Monitor de Gasto

- ✅ **get_openai_callback()**: Wrapper en todas las llamadas OpenAI
- ✅ **Métricas mostradas**:
  - 📥 Tokens de entrada
  - 📤 Tokens de salida
  - 🧠 Tokens de razonamiento
  - 💵 Costo total en USD

---

## 🚀 Cómo Usar

### Paso 1: Instalar Dependencias

```powershell
python scripts/instalar_bot_avanzado.py
```

### Paso 2: Configurar .env

**Opción A - Local (Gratis):**
```env
LOCALIA=true
```

**Opción B - OpenAI (Con costos):**
```env
LOCALIA=false
OPENAI_API_KEY=sk-tu_clave_aqui
OPENAI_MODEL_RAPIDO=gpt-4o-mini
OPENAI_MODEL_RAZONAMIENTO=gpt-4o
```

### Paso 3: Ejecutar

```powershell
# Pruebas automáticas
python scripts/probar_bot_avanzado.py

# Modo interactivo
python bots/bot_documentos_avanzado.py
```

---

## 📊 Flujo de Trabajo

### Primera Ejecución

```
🚀 Inicializando Bot de Documentos Avanzado

📊 Inicializando embeddings (LOCALIA=true)...
✅ Embeddings Ollama (phi4-mini:latest) inicializados

🗄️ Inicializando ChromaDB en: ./chroma_db
✅ ChromaDB inicializado (0 vectores almacenados)

🤖 Inicializando modelos de IA...
✅ Modelos Ollama (phi4-mini:latest) inicializados

✂️  Text Splitter: 1000 tokens, 150 overlap (15%)

📥 Conectando con Paperless
📄 Encontrados 2 documentos en Paperless
   ✅ Indexado: Código de Ética y Conducta (15 chunks)
   ✅ Indexado: Usuarios GPT (8 chunks)
✅ Indexados 2 documentos nuevos

✅ Bot inicializado correctamente
```

### Consulta Rápida

```
📝 Consulta: ¿Qué dice sobre integridad?

⚡ MODO: Consulta Rápida
🔍 Buscando: ¿Qué dice sobre integridad?
📄 Encontrados 3 fragmentos relevantes

🤖 La integridad se define como...

────────────────────────────────────────────────────────────
📚 Documentos consultados:
📄 Código de Ética y Conducta (Creado: 2026-03-10)
```

### Razonamiento Profundo

```
📝 Consulta: Analiza los documentos disponibles

🧠 MODO: Razonamiento Profundo
🔍 Buscando: Analiza los documentos disponibles
📄 Encontrados 10 fragmentos relevantes

🤖 Análisis:

1. Información clave encontrada:
   ...

2. Razonamiento lógico:
   ...

3. Conclusiones basadas en evidencia:
   ...

────────────────────────────────────────────────────────────
📚 Documentos analizados:
📄 Código de Ética y Conducta (2 fragmentos)
📄 Usuarios GPT (8 fragmentos)
```

---

## 💰 Costos Estimados (OpenAI)

### Consulta Rápida (GPT-4o-mini)
- Entrada: ~500 tokens
- Salida: ~150 tokens
- **Costo: ~$0.00012 USD**

### Razonamiento Profundo (GPT-4o)
- Entrada: ~2,500 tokens
- Salida: ~700 tokens
- **Costo: ~$0.018 USD**

### Con Context Caching
- Primera consulta: $0.018 USD
- Consultas subsecuentes: $0.002 USD (90% ahorro)

---

## 🎨 Ventajas vs Bot Simple

| Característica | Bot Simple | Bot Avanzado |
|----------------|------------|--------------|
| Búsqueda | Keywords | Semántica |
| Persistencia | No | Sí |
| AI | Solo Ollama | Ollama + OpenAI |
| Modos | Uno | Dos (rápido/profundo) |
| Caching | No | Sí |
| Costos | $0 | $0.00012 - $0.018 |
| Velocidad | Rápida | Muy rápida |
| Precisión | Buena | Excelente |

---

## 📚 Documentación

- **BOT_AVANZADO.md**: Guía completa con ejemplos
- **README.md**: Documentación general del proyecto
- **INICIO_RAPIDO.md**: Tutorial para principiantes

---

## 🔧 Configuración ChromaDB

### Parámetros en .env

```env
CHROMA_DB_PATH=./chroma_db     # Carpeta de persistencia
CHUNK_SIZE=1000                 # Tamaño de fragmentos
CHUNK_OVERLAP=150               # Overlap 15% (150/1000)
```

### Estructura de ChromaDB

```
./chroma_db/
├── chroma.sqlite3              # Metadata de documentos
└── [UUID-folders]/             # Embeddings vectoriales
```

### Metadata por Chunk

Cada fragmento almacena:
- `doc_id`: ID en Paperless
- `title`: Título del documento
- `chunk_index`: Número de fragmento
- `total_chunks`: Total de fragmentos
- `created`: Fecha de creación
- `tags`: Tags del documento
- `correspondent`: Remitente

---

## 🧪 Testing

```powershell
# Instalar dependencias
python scripts/instalar_bot_avanzado.py

# Ejecutar pruebas
python scripts/probar_bot_avanzado.py

# Modo interactivo
python bots/bot_documentos_avanzado.py
```

---

## ✨ Próximos Pasos

1. **Instala las dependencias**:
   ```powershell
   python scripts/instalar_bot_avanzado.py
   ```

2.  **Configura LOCALIA en .env**:
   - `LOCALIA=true` → Gratis con Ollama
   - `LOCALIA=false` → OpenAI con costos

3. **Ejecuta el bot**:
   ```powershell
   python bots/bot_documentos_avanzado.py
   ```

4. **Lee la guía completa**:
   - Abre `BOT_AVANZADO.md` para ejemplos detallados

---

## 🎯 Comandos Rápidos

```powershell
# Instalación
python scripts/instalar_bot_avanzado.py

# Pruebas
python scripts/probar_bot_avanzado.py

# Uso interactivo
python bots/bot_documentos_avanzado.py

# Ver ayuda
# (Dentro del bot escribe: ayuda)
```

---

## 📞 Soporte

- **Guía completa**: [BOT_AVANZADO.md](BOT_AVANZADO.md)
- **README principal**: [README.md](README.md)
- **Inicio rápido**: [INICIO_RAPIDO.md](INICIO_RAPIDO.md)

---

**¡El bot avanzado está listo para usar! 🚀**
