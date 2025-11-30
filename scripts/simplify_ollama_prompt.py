#!/usr/bin/env python3
"""Simplify Ollama prompt and reduce logs size"""
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

# Simplify Ollama prompt with shorter logs
for node in w['nodes']:
    if node['name'] == 'Preparer Ollama Payload':
        node['parameters']['jsCode'] = '''const incident = $input.first().json;

// Take only last 1000 chars of logs to speed up
const cleanLogs = (incident.error_logs || '')
  .substring(0, 1000)
  .replace(/\\\\/g, '\\\\\\\\')
  .replace(/"/g, '\\\\"')
  .replace(/\\n/g, '\\\\n')
  .replace(/\\r/g, '')
  .replace(/\\t/g, ' ');

// Simplified prompt for faster response
const prompt = `Analyze this DOWN service. Service: ${incident.service_name}

Logs: ${cleanLogs}

Return ONLY valid JSON:
{"cause":"brief cause","confidence":0.8,"action_command":"systemctl restart ${incident.service_name} OR ESCALATE","action_type":"restart","is_safe":true,"explanation":"brief"}`;

const ollamaPayload = {
  model: "qwen2.5-coder:3b-instruct",
  prompt: prompt,
  stream: false,
  options: { temperature: 0.1, num_predict: 200 }
};

return [{ json: { ...incident, _ollama_payload: ollamaPayload } }];'''
        print("[OK] Simplified Ollama prompt")

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
