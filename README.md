# Agente Médico - AWS Bedrock Agent Core

Agente médico inteligente desplegado en AWS Bedrock Agent Core, con capacidades de consulta a Knowledge Base, acceso a expedientes de pacientes y análisis de imágenes médicas.

## 🏗️ Arquitectura

- **Framework**: Strands AI Agents
- **Modelo**: Claude 3.5 Sonnet (Cross-region Inference Profile)
- **Plataforma**: AWS Bedrock Agent Core (ARM64 Container)
- **Knowledge Base**: AWS Bedrock Knowledge Base (ID: CJUFII3SIM)
- **Región**: us-east-2

## 📋 Requisitos Previos

- Python 3.12
- AWS CLI configurado con credenciales
- Cuenta AWS con acceso a:
  - AWS Bedrock
  - AWS Bedrock Agent Core
  - Amazon ECR
  - AWS CodeBuild
  - CloudWatch Logs

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/nelsonApraez/agente-medico-backend.git
cd agente-medico-backend
```

### 2. Crear entorno virtual

```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

La variable `KB_INFERENCE_PROFILE_ARN` se configura automáticamente en el deployment a través de `.bedrock_agentcore.yaml`.

Para ejecución local:
```powershell
$env:KB_INFERENCE_PROFILE_ARN = "arn:aws:bedrock:us-east-2:413370510567:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0"
```

## 🏃 Ejecución

### Modo Local (Desarrollo)

```bash
python agente_medico.py
```

Esto iniciará un REPL interactivo donde puedes hacer preguntas al agente.

### Despliegue en AWS Bedrock Agent Core

```bash
# Desplegar por primera vez
.\venv\Scripts\agentcore.exe launch

# Actualizar deployment existente
.\venv\Scripts\agentcore.exe launch --auto-update-on-conflict

# Verificar estado
.\venv\Scripts\agentcore.exe status

# Invocar el agente
.\venv\Scripts\agentcore.exe invoke '{"prompt":"Hola, ¿cómo estás?"}'
```

## 🛠️ Herramientas del Agente

### 1. `consult_knowledge_base(query: str)`
Consulta la Knowledge Base médica de AWS Bedrock.

**Ejemplo:**
```json
{"prompt": "¿Cuáles son los síntomas de la diabetes?"}
```

### 2. `get_patient_record(patient_id: str)`
Obtiene el expediente de un paciente por ID.

**Ejemplo:**
```json
{"prompt": "Muéstrame el expediente del paciente 456"}
```

### 3. `analyze_medical_image(s3_url: str, patient_context: str)`
Analiza imágenes médicas desde S3.

**Ejemplo:**
```json
{"prompt": "Analiza la imagen de rayos-x en s3://bucket/rayos-x.jpg"}
```

## 📁 Estructura del Proyecto

```
agente-medico-backend/
├── agente_medico.py              # Código principal del agente
├── requirements.txt              # Dependencias Python
├── Dockerfile                    # Dockerfile para Agent Core
├── .bedrock_agentcore.yaml       # Configuración de deployment (ignorado en git)
├── .dockerignore                 # Archivos ignorados en build
└── README.md                     # Esta documentación
```

## 🔧 Cambios Clave para AWS Agent Core

### 1. Lazy Initialization
```python
_agente_medico = None

def _get_or_create_agent():
    global _agente_medico
    if _agente_medico is not None:
        return _agente_medico
    # Inicializar solo cuando se necesita
    return _agente_medico
```

### 2. Parámetro Correcto en Agent
```python
# ✅ Correcto
Agent(system_prompt='...')

# ❌ Incorrecto (causa TypeError)
Agent(instructions='...')
```

### 3. Servidor HTTP en Docker
```python
if __name__ == '__main__':
    if os.environ.get('DOCKER_CONTAINER'):
        print("Starting Bedrock AgentCore server...")
        app.run()  # ⭐ Crítico para Agent Core
    else:
        main()  # Modo local
```

### 4. Manejo de Input del Entrypoint
```python
@app.entrypoint
def medical_agent_entrypoint(query: str) -> str:
    # Manejar tanto strings como dicts
    if isinstance(query, dict):
        query = query.get('prompt', query.get('query', str(query)))
    # ... procesar query
```

### 5. Modelo Cross-Region
```python
# ✅ Usar inference profile cross-region
BedrockModel(model_id='us.anthropic.claude-3-5-sonnet-20241022-v2:0')

# ❌ Modelo base puede no estar disponible
BedrockModel(model_id='anthropic.claude-3-sonnet-20240229-v1:0')
```

## 📊 Monitoreo y Logs

### Ver logs en CloudWatch
```bash
aws logs tail /aws/bedrock-agentcore/runtimes/MedicalAgent-6Kd6khBvsu-DEFAULT \
  --log-stream-name-prefix "2025/11/06/[runtime-logs]" \
  --follow
```

### Dashboard de Observabilidad
```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-2#gen-ai-observability/agent-core
```

## 🐛 Solución de Problemas

### Error: "RuntimeClientError when starting the runtime"
**Causa**: El contenedor no inicia el servidor HTTP.  
**Solución**: Verificar que `app.run()` esté en el bloque `if os.environ.get('DOCKER_CONTAINER')`.

### Error: "ValidationException: invalid model identifier"
**Causa**: Modelo no accesible en la región.  
**Solución**: Usar un inference profile cross-region (`us.anthropic.claude-3-5-sonnet-20241022-v2:0`).

### Error: "Dockerfile: no such file or directory"
**Causa**: CodeBuild busca Dockerfile en la raíz.  
**Solución**: Asegurar que `Dockerfile` esté en la raíz del proyecto.

### Error: "KB_INFERENCE_PROFILE_ARN no configurada"
**Causa**: Variable de entorno faltante para Knowledge Base.  
**Solución**: Agregar en `.bedrock_agentcore.yaml`:
```yaml
environment:
  KB_INFERENCE_PROFILE_ARN: "arn:aws:bedrock:..."
```

## 📝 Configuración de Deployment

El archivo `.bedrock_agentcore.yaml` (no versionado) debe contener:

```yaml
agents:
  MedicalAgent:
    name: MedicalAgent
    entrypoint: agente_medico:medical_agent_entrypoint
    region: us-east-2
    platform: linux/arm64
    aws:
      region: us-east-2
      account: 'YOUR_ACCOUNT_ID'
      execution_role_auto_create: true
      ecr_auto_create: true
    environment:
      KB_INFERENCE_PROFILE_ARN: "arn:aws:bedrock:us-east-2:YOUR_ACCOUNT:inference-profile/..."
default_agent: MedicalAgent
```

## 🔐 Seguridad

- Las credenciales AWS se gestionan vía AWS IAM roles
- No se incluyen secrets en el código
- Variables sensibles se pasan como environment variables
- El contenedor usa usuario no-root (`bedrock_agentcore`)

## 📄 Licencia

MIT

## 👥 Autor

Nelson Apraez

## 🔗 Links Útiles

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Strands AI Framework](https://github.com/strands-ai/strands)
- [Bedrock Agent Core SDK](https://pypi.org/project/bedrock-agentcore/)
