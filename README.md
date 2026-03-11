# 🤖 Proyecto LangChain - Bots Empresariales

Proyecto de bots inteligentes usando LangChain para consultas de Recursos Humanos y documentos en Paperless, con IA local mediante Ollama.

## 📋 Tabla de Contenidos

- [Características](#características)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso de los Bots](#uso-de-los-bots)
- [Scripts de Utilidad](#scripts-de-utilidad)
- [Ejemplos de Consultas](#ejemplos-de-consultas)

---

## ✨ Características

- **🤖 Bot General**: Consulta inteligente de RH y documentos Paperless con IA
- **👥 Bot de RH**: Especializado en consultas de Recursos Humanos
- **📄 Bot de Documentos**: Búsqueda inteligente y análisis de documentos con OCR
- **🧠 IA Local**: Usa Ollama (phi4-mini:latest) - sin costos de API
- **📄 Integración Paperless**: Búsqueda de documentos con OCR
- **🔍 Búsqueda Inteligente**: Respuestas naturales usando LangChain
- **⚙️ Configuración Simple**: Todo en un archivo `.env`

---

## 📁 Estructura del Proyecto

```
langchain/
├── bots/                      # Bots principales
│   ├── bot_general.py        # Bot que consulta RH + Paperless
│   ├── bot_rh.py             # Bot especializado en RH
│   └── bot_documentos.py     # Bot de búsqueda en documentos
├── scripts/                   # Scripts de utilidad
│   ├── crear_db_ejemplo.py   # Crear base de datos de prueba
│   ├── generar_token_paperless.py
│   ├── probar_api_rh.py      # Verificar conexión con API RH
│   └── probar_paperless.py   # Verificar Paperless
├── utils/                     # Herramientas
│   └── verificar_ollama.py   # Ver modelos disponibles
├── data/                      # Datos locales
│   └── empresa.db            # Base de datos SQLite (opcional)
├── .env                       # Configuración (TU ARCHIVO)
├── .env.example              # Plantilla de configuración
├── .gitignore                # Archivos ignorados por Git
├── requirements.txt          # Dependencias Python
└── README.md                 # Esta documentación
```

---

## 🚀 Instalación

### 1. Requisitos Previos

- Python 3.9 o superior
- Servidor Ollama con modelos instalados
- Acceso a API de RH (opcional)
- Instancia de Paperless-ngx (opcional)

### 2. Instalar Dependencias

```powershell
# Crear entorno virtual (recomendado)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Verificar Instalación

```powershell
# Ver modelos de Ollama disponibles
python utils/verificar_ollama.py
```

---

## ⚙️ Configuración

### 1. Crear archivo de configuración

Copia el archivo de ejemplo:

```powershell
Copy-Item .env.example .env
```

### 2. Editar `.env` con tus valores

```env
# ===== API de Recursos Humanos =====
API_RH_URL=https://services.satechenergy.com/api/rh

# ===== Paperless-ngx =====
PAPERLESS_URL=https://tu-servidor-paperless.com
PAPERLESS_TOKEN=tu_token_aqui

# ===== Ollama (Modelo de IA Local) =====
OLLAMA_URL=https://ollama.tech-energy.lat
OLLAMA_MODEL=phi4-mini:latest

# ===== OpenAI (Opcional) =====
OPENAI_API_KEY=

# ===== Base de Datos SQLite (Opcional) =====
DATABASE_PATH=data/empresa.db
```

### 3. Obtener Token de Paperless (opcional)

```powershell
python scripts/generar_token_paperless.py
```

### 4. Verificar Conexiones

```powershell
# Probar API de RH
python scripts/probar_api_rh.py

# Probar Paperless
python scripts/probar_paperless.py
```

---

## 🤖 Uso de los Bots

### Bot General (RH + Paperless + IA)

Consulta empleados y documentos en una sola interfaz:

```powershell
python bots/bot_general.py
```

**Ejemplos de consultas:**

```
🧑 Pregunta: ¿Cuántos empleados tenemos en Manufactura?
🧑 Pregunta: Busca documentos sobre políticas de vacaciones
🧑 Pregunta: ¿Quién es el jefe de Alan Rodríguez?
🧑 Pregunta: Muéstrame contratos de 2025
```

---

### Bot de Recursos Humanos

Especializado en consultas de personal:

```powershell
python bots/bot_rh.py
```

**Ejemplos de consultas:**

```
🧑 Pregunta: Busca a Juan Rodríguez
🧑 Pregunta: ¿Cuántos empleados hay en IT?
🧑 Pregunta: Lista del departamento de Soldadura
🧑 

---

### Bot de Documentos

Búsqueda inteligente en documentos con análisis de contenido:

```powershell
python bots/bot_documentos.py
```

**Ejemplos de consultas:**

```
📝 Consulta: Busca documentos sobre contratos
📝 Consulta: ¿Qué dice la política de vacaciones?
📝 Consulta: Resume el documento sobre seguridad
📝 Consulta: Lista documentos recientes
📝 Consulta: Analiza documento 123
```

**Capacidades:**
- 🔍 Búsqueda por texto completo (OCR)
- 📖 Extracción de información específica
- 📝 Resumen automático de documentos
- 💬 Responde preguntas sobre el contenido
- 🔗 Análisis de documentos por IDPregunta: Estadísticas por área
```

---

## 🛠️ Scripts de Utilidad

### Verificar Modelos de Ollama

```powershell
python utils/verificar_ollama.py
```

Muestra todos los modelos disponibles en tu servidor Ollama.

### Probar API de RH

```powershell
python scripts/probar_api_rh.py
```

Verifica conectividad y muestra estadísticas de empleados.

### Probar Paperless

```powershell
python scripts/probar_paperless.py
```

Verifica conexión con Paperless y muestra documentos recientes.

### Crear Base de Datos de Ejemplo

```powershell
python scripts/crear_db_ejemplo.py
```

Crea una base de datos SQLite con datos de prueba.

---

## 💬 Ejemplos de Consultas

### Consultas de RH

| Pregunta | Tipo de Búsqueda |
|----------|------------------|
| ¿Cuántos empleados tenemos? | Total de empleados |
| Busca a Alan Hernández | Por nombre |
| Lista empleados de Manufactura | Por departamento |
| ¿Quién trabaja en Servicios Técnicos? | Por área |
| Estadísticas por departamento | Resumen |

### Consultas de Documentos (Paperless)

| Pregunta | Tipo de Búsqueda |
|----------|------------------|
| Busca contratos de 2025 | Por texto y fecha |
| Encuentra la política de vacaciones | Por contenido |
| ¿Tienes facturas pendientes? | Por estado |
| Muéstrame reportes mensuales | Por categoría |

### Consultas Mixtas (Bot General)

| Pregunta | Fuentes |
|----------|---------|
| ¿Quién puede revisar este contrato? | RH + Paperless |
| Busca información sobre el proyecto X | Ambas fuentes |
| ¿A quién contacto sobre la póliza de seguros? | RH + Paperless |

---

## 🔧 Personalización

### Cambiar Modelo de IA

Edita `.env`:

```env
# Modelo rápido (2.3 GB)
OLLAMA_MODEL=phi4-mini:latest

# Modelo potente (4.6 GB)
OLLAMA_MODEL=llama3.1:latest
```

### Usar OpenAI en lugar de Ollama

1. Obtén tu API Key en https://platform.openai.com
2. Edita `.env`:

```env
OPENAI_API_KEY=tu_key_aqui
```

3. Modifica el bot para usar `ChatOpenAI` en lugar de `ChatOllama`

---

## 🐛 Solución de Problemas

### Error: "No se pudo cargar empleados"

- Verifica que `API_RH_URL` en `.env` sea correcto
- Ejecuta: `python scripts/probar_api_rh.py`

### Error: "IA no disponible"

- Verifica que el servidor Ollama esté activo
- Confirma que el modelo esté instalado: `python utils/verificar_ollama.py`
- Revisa `OLLAMA_URL` y `OLLAMA_MODEL` en `.env`

### Error: "Paperless no responde"

- Verifica `PAPERLESS_URL` en `.env`
- Regenera el token: `python scripts/generar_token_paperless.py`
- Prueba la conexión: `python scripts/probar_paperless.py`

### Errores de dependencias

```powershell
# Reinstalar todas las dependencias
pip install -r requirements.txt --force-reinstall
```

---

## 📚 Tecnologías Utilizadas

- **[LangChain](https://python.langchain.com/)** - Framework para apps con IA
- **[Ollama](https://ollama.com/)** - Modelos de IA locales
- **[Paperless-ngx](https://docs.paperless-ngx.com/)** - Gestión de documentos
- **[Python 3.13](https://www.python.org/)** - Lenguaje de programación
- **[SQLite](https://www.sqlite.org/)** - Base de datos ligera

---

## 📝 Notas Importantes

1. **Seguridad**: El archivo `.env` está en `.gitignore` - nunca lo subas a Git
2. **Tokens**: Genera tokens nuevos de Paperless regularmente
3. **Modelos**: `phi4-mini` es más rápido, `llama3.1` es más preciso
4. **Performance**: Respuestas con IA tardan 2-5 segundos

---

## 🤝 Contribuciones

Para reportar errores o sugerir mejoras, abre un issue en el repositorio.

---

## 📄 Licencia

Este proyecto es de uso interno empresarial.

---

**¿Necesitas ayuda?** Revisa la sección de [Solución de Problemas](#solución-de-problemas) o ejecuta los scripts de verificación en la carpeta `scripts/`.
