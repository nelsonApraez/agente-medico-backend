import boto3
import json 
import os

from strands import Agent, tool
from strands.models import BedrockModel
from bedrock_agentcore import BedrockAgentCoreApp

_agente_medico = None

@tool
def consult_knowledge_base(query: str) -> str:
    KNOWLEDGE_BASE_ID = 'CJUFII3SIM' 
    inference_profile_arn = os.environ.get('KB_INFERENCE_PROFILE_ARN')
    if not inference_profile_arn:
        return 'Error: KB_INFERENCE_PROFILE_ARN no configurada'
    region = os.environ.get('AWS_REGION', 'us-east-2')
    client_kb = boto3.client('bedrock-agent-runtime', region_name=region)
    print(f'Consultando KB: {query}')
    try:
        response = client_kb.retrieve_and_generate(
            input={'text': query},
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': KNOWLEDGE_BASE_ID,
                    'modelArn': inference_profile_arn
                }
            }
        )
        return response['output']['text']
    except Exception as e:
        return f'Error al consultar KB: {str(e)}'

@tool
def get_patient_record(patient_id: str) -> str:
    if patient_id == '456':
        return 'Paciente 456: Juan Perez, 55 anos, Hipertension'
    return 'Paciente no encontrado'

@tool
def analyze_medical_image(s3_url: str, patient_context: str) -> str:
    if 'rayos-x' in s3_url.lower():
        return f'Imagen {s3_url}: opacidades pulmonares'
    return f'Imagen {s3_url}: sin hallazgos'

def _get_or_create_agent():
    global _agente_medico
    if _agente_medico is not None:
        return _agente_medico
    model_client = BedrockModel(model_id='us.anthropic.claude-3-5-sonnet-20241022-v2:0')
    _agente_medico = Agent(
        name='Agente Medico',
        model=model_client,
        description='Asistente medico',
        system_prompt='Eres un asistente medico. Usa las herramientas disponibles.',
        tools=[consult_knowledge_base, get_patient_record, analyze_medical_image] 
    )
    return _agente_medico

app = BedrockAgentCoreApp()

@app.entrypoint
def medical_agent_entrypoint(query: str) -> str:
    try:
        print(f"Received query: {query}, type: {type(query)}")
        # Si query es un dict, extraer el 'prompt'
        if isinstance(query, dict):
            query = query.get('prompt', query.get('query', str(query)))
        agente = _get_or_create_agent()
        response = agente(query)
        return response
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f'Error: {str(e)}'

def main():
    print('AGENTE MEDICO')
    while True:
        pregunta = input('Tu pregunta: ').strip()
        if pregunta.lower() in ['salir', 'exit']:
            break
        if pregunta:
            print(medical_agent_entrypoint(pregunta))

# Solo ejecutar main() si se ejecuta directamente (NO en Docker/Agent Core)
if __name__ == '__main__':
    if os.environ.get('DOCKER_CONTAINER'):
        # En Docker, ejecutar el servidor de bedrock-agentcore
        print("Starting Bedrock AgentCore server...")
        app.run()
    else:
        # Localmente, ejecutar el loop interactivo
        main()
