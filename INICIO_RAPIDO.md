# 🚀 Inicio Rápido - Bot de Documentos

## Test Rápido (1 minuto)

### 1. Verifica que Paperless esté funcionando

```powershell
python scripts/probar_paperless.py
```

**Resultado esperado:**
```
✅ Paperless conectado correctamente
📄 Documentos encontrados: X
```

---

### 2. Ejecuta el Bot de Documentos

```powershell
python bots/bot_documentos.py
```

---

### 3. Prueba estas consultas de ejemplo

#### 🔍 Listar documentos disponibles
```
📝 Consulta: lista documentos recientes
```

#### 📄 Buscar documentos específicos
```
📝 Consulta: busca contratos
📝 Consulta: busca política de vacaciones
📝 Consulta: busca documentos sobre seguridad
```

#### 🧠 Análisis con IA
```
📝 Consulta: ¿Qué dice el contrato sobre confidencialidad?
📝 Consulta: Resume el documento de políticas
📝 Consulta: Extrae las cláusulas de pago
```

#### 🎯 Analizar documento específico (si conoces el ID)
```
📝 Consulta: analiza documento 123
📝 Consulta: analiza documento 456 sobre el tema de sanciones
```

---

## 📖 Cómo funciona

1. **Búsqueda por keywords**: El bot busca documentos en Paperless que contengan las palabras clave
2. **Obtención de contenido**: Descarga el texto completo extraído por OCR
3. **Análisis con IA**: Ollama analiza el contenido y responde tu pregunta específica
4. **Respuesta contextualizada**: Te muestra extractos relevantes con el ID del documento

---

## 🎯 Flujo de trabajo recomendado

### Primer uso (descubrimiento):
```
📝 Consulta: lista documentos recientes
```
→ Conoce qué documentos tienes disponibles

### Búsqueda general:
```
📝 Consulta: busca [tema o keyword]
```
→ Encuentra todos los documentos relacionados

### Análisis específico:
```
📝 Consulta: analiza documento [ID] sobre [pregunta específica]
```
→ Extrae información precisa de un documento conocido

### Extracción directa:
```
📝 Consulta: ¿Qué dice [documento] sobre [tema]?
```
→ El bot busca, lee y analiza automáticamente

---

## ⚡ Ejemplos reales de uso

### Caso 1: Buscar cláusulas en contratos
```
📝 Consulta: busca en los contratos la cláusula de confidencialidad
```

**El bot hará:**
1. Buscar documentos con "contratos" y "confidencialidad"
2. Leer el contenido OCR de cada documento encontrado
3. Analizar dónde se menciona "confidencialidad"
4. Extraer y mostrarte los párrafos relevantes

---

### Caso 2: Resumir una política específica
```
📝 Consulta: resume la política de vacaciones
```

**El bot hará:**
1. Buscar "política" y "vacaciones"
2. Leer el documento completo
3. Generar un resumen con IA
4. Mostrarte los puntos clave

---

### Caso 3: Verificar información específica
```
📝 Consulta: ¿Cuántos días de vacaciones tengo según el contrato?
```

**El bot hará:**
1. Buscar documentos relacionados con "vacaciones" y "contrato"
2. Leer el contenido
3. Extraer la información numérica sobre días de vacaciones
4. Responder directamente con el dato

---

## 🔧 Solución de problemas

### "No se encontraron documentos"
- ✅ Verifica que hayas subido documentos a Paperless
- ✅ Asegúrate de que tengan contenido OCR procesado
- ✅ Prueba con términos de búsqueda más generales

### "Error al conectar con Paperless"
```powershell
# Verifica tu configuración
python scripts/probar_paperless.py
```
- ✅ Revisa que PAPERLESS_URL esté correcto en `.env`
- ✅ Verifica que PAPERLESS_TOKEN sea válido

### "Error al conectar con Ollama"
```powershell
# Verifica los modelos disponibles
python utils/verificar_ollama.py
```
- ✅ Asegúrate de que OLLAMA_URL esté correcto
- ✅ Verifica que el modelo phi4-mini:latest esté descargado

---

## 💡 Tips de uso

1. **Sé específico**: En lugar de "busca contratos", di "busca contratos laborales 2024"
2. **Usa comandos especiales**:
   - `lista documentos recientes` → Ve qué hay disponible
   - `analiza documento [ID]` → Analiza un documento conocido
3. **Pregunta como lo harías a un humano**: "¿Qué dice el contrato sobre..." funciona mejor que "extrae datos de..."
4. **Combina búsqueda + pregunta**: "Busca la política de vacaciones y dime cuántos días corresponden"

---

## 📚 Siguientes pasos

Una vez familiarizado con el bot básico, prueba:

### Bot General (RH + Documentos)
```powershell
python bots/bot_general.py
```
- Combina consultas de empleados Y documentos
- Búsqueda inteligente con fallback de IA

### Bot RH Especializado
```powershell
python bots/bot_rh.py
```
- Consultas estadísticas complejas
- Datos de empleados, departamentos, áreas

---

## 📞 ¿Necesitas ayuda?

Revisa el [README.md](README.md) completo para:
- Configuración avanzada
- Estructura del proyecto
- Scripts de utilidades
- Información de mantenimiento
