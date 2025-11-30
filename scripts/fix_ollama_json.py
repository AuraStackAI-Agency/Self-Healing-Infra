#!/usr/bin/env python3
"""Fix Ollama JSON by adding a prepare node before the HTTP request"""
import requests
import json

N8N_API_URL = "https://n8n.aurastackai.com/api/v1"
N8N_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkN2Q3ZTM2Mi1kMjJhLTQ4OWYtYTdkMi1lNjNjNGNmNjU3OTAiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzYyNjk5MTUwfQ.Gi6k_zcap4NUNKQTrEf8BM1DAwbv-iV5eVYV2VoS44U"
WORKFLOW_ID = "YPOEAMIDhDEdRLyX"

headers = {
    "X-N8N-API-KEY": N8N_API_KEY,
    "Content-Type": "application/json"
}

# Get workflow
response = requests.get(f"{N8N_API_URL}/workflows/{WORKFLOW_ID}", headers=headers)
w = response.json()

print(f"Workflow: {w['name']}")

# Add a new node to prepare Ollama payload
prepare_ollama_node = {
    "parameters": {
        "jsCode": '''const incident = $input.first().json;

// Escape logs for JSON - remove problematic characters
const cleanLogs = (incident.error_logs || '')
  .substring(0, 3000)
  .replace(/\\\\/g, '\\\\\\\\')
  .replace(/"/g, '\\\\"')
  .replace(/\\n/g, '\\\\n')
  .replace(/\\r/g, '\\\\r')
  .replace(/\\t/g, '\\\\t');

// Build the prompt
const prompt = `Tu es un analyste systeme Niveau 1. Analyse ces logs et retourne UNIQUEMENT un JSON valide.

Service: ${incident.service_name}
Status: ${incident.status}

Logs:
${cleanLogs}

Reponds UNIQUEMENT avec ce format JSON:
{"cause": "description courte", "confidence": 0.85, "action_command": "commande ou ESCALATE", "action_type": "restart|reload|clean|ESCALATE", "is_safe": true, "explanation": "explication"}`;

// Build complete Ollama payload
const ollamaPayload = {
  model: "qwen2.5-coder:3b-instruct",
  prompt: prompt,
  stream: false,
  options: { temperature: 0.1, num_predict: 500 }
};

return [{ json: { ...incident, _ollama_payload: ollamaPayload } }];'''
    },
    "id": "prepare-ollama",
    "name": "Preparer Ollama Payload",
    "type": "n8n-nodes-base.code",
    "typeVersion": 2,
    "position": [1000, 0]
}

# Add the new node
w['nodes'].append(prepare_ollama_node)
print("[OK] Added 'Preparer Ollama Payload' node")

# Update Ollama node to use the prepared payload
for node in w['nodes']:
    if node['name'] == 'Ollama - Qwen N1':
        node['parameters']['jsonBody'] = "={{ JSON.stringify($json._ollama_payload) }}"
        node['position'] = [1200, 0]  # Move it to the right
        print("[OK] Updated Ollama node to use prepared payload")

# Update connections
conns = w['connections']

# Agreger Logs now connects to Preparer Ollama Payload
conns['Agreger Logs'] = {"main": [[{"node": "Preparer Ollama Payload", "type": "main", "index": 0}]]}

# Preparer Ollama Payload connects to Ollama
conns['Preparer Ollama Payload'] = {"main": [[{"node": "Ollama - Qwen N1", "type": "main", "index": 0}]]}

print("[OK] Updated connections")

# Update workflow
clean_data = {
    "name": w["name"],
    "nodes": w["nodes"],
    "connections": conns,
    "settings": {"executionOrder": "v1"}
}

response = requests.put(
    f"{N8N_API_URL}/workflows/{WORKFLOW_ID}",
    headers=headers,
    json=clean_data
)

if response.status_code == 200:
    print("[OK] Workflow updated successfully")
else:
    print(f"[ERROR] {response.status_code}: {response.text}")
