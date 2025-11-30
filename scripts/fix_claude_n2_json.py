#!/usr/bin/env python3
"""Fix Claude N2 - Add payload preparation node like we did for Ollama"""
import requests
import json

N8N_API_URL = "https://n8n.aurastackai.com/api/v1"
N8N_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkN2Q3ZTM2Mi1kMjJhLTQ4OWYtYTdkMi1lNjNjNGNmNjU3OTAiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzYyNjk5MTUwfQ.Gi6k_zcap4NUNKQTrEf8BM1DAwbv-iV5eVYV2VoS44U"
WORKFLOW_ID = "m239OOMCarIbNa7C"

headers = {
    "X-N8N-API-KEY": N8N_API_KEY,
    "Content-Type": "application/json"
}

# Get workflow
response = requests.get(f"{N8N_API_URL}/workflows/{WORKFLOW_ID}", headers=headers)
w = response.json()

print(f"Workflow: {w['name']}")

# Find positions
ssh_collect_pos = None
claude_n2_pos = None
for node in w['nodes']:
    if node['name'] == 'SSH - Collecter Logs':
        ssh_collect_pos = node['position']
    if node['name'] == 'Claude N2':
        claude_n2_pos = node['position']

# Add Preparer Claude Payload node between SSH - Collecter Logs and Claude N2
prep_node = {
    "parameters": {
        "jsCode": '''const webhookData = $('Webhook Escalade N2').first().json;
const incident = webhookData.body || webhookData;
const ragContext = $('Contexte RAG N2').first().json._rag_context || '';
const sshResult = $input.first().json;

// Clean logs - escape special chars for JSON
const cleanLogs = (sshResult.stdout || '')
  .substring(0, 2000)
  .replace(/\\\\/g, '\\\\\\\\')
  .replace(/"/g, '\\\\"')
  .replace(/\\n/g, '\\\\n')
  .replace(/\\r/g, '')
  .replace(/\\t/g, ' ');

// Build Claude payload
const claudePayload = {
  model: "claude-sonnet-4-20250514",
  max_tokens: 2000,
  messages: [{
    role: "user",
    content: `Expert DevOps N2. Analyse incident.

Service: ${incident.service_name || 'Unknown'}${ragContext}

Logs:
${cleanLogs}

JSON: {"root_cause": "...", "analysis": "...", "severity": "critical|high|medium|low", "action_command": "...", "action_explanation": "...", "requires_human_approval": true, "risks": ["..."]}`
  }]
};

return [{ json: { ...incident, _claude_payload: claudePayload } }];'''
    },
    "id": "prep-claude",
    "name": "Preparer Claude Payload",
    "type": "n8n-nodes-base.code",
    "typeVersion": 2,
    "position": [1216, 400]  # Between SSH Collect and Claude N2
}

# Check if node already exists
exists = any(n['name'] == 'Preparer Claude Payload' for n in w['nodes'])
if not exists:
    w['nodes'].append(prep_node)
    print("[OK] Added Preparer Claude Payload node")

# Update Claude N2 to use the prepared payload
for node in w['nodes']:
    if node['name'] == 'Claude N2':
        node['parameters']['jsonBody'] = "={{ JSON.stringify($json._claude_payload) }}"
        node['position'] = [1440, 400]  # Move to make room
        print("[OK] Updated Claude N2 to use prepared payload")

# Update connections
# Remove old connection: SSH - Collecter Logs -> Claude N2
# Add: SSH - Collecter Logs -> Preparer Claude Payload -> Claude N2
new_connections = {}
for src, conns in w['connections'].items():
    new_connections[src] = conns

# Update SSH - Collecter Logs to connect to Preparer Claude Payload
if 'SSH - Collecter Logs' in new_connections:
    new_connections['SSH - Collecter Logs'] = {"main": [[{"node": "Preparer Claude Payload", "type": "main", "index": 0}]]}

# Add connection from Preparer Claude Payload to Claude N2
new_connections['Preparer Claude Payload'] = {"main": [[{"node": "Claude N2", "type": "main", "index": 0}]]}

w['connections'] = new_connections
print("[OK] Updated connections")

# Update workflow
clean_data = {
    "name": w["name"],
    "nodes": w["nodes"],
    "connections": w["connections"],
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
