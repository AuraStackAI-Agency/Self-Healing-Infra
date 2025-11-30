#!/usr/bin/env python3
"""Add debug node after Normaliser Payload to see what's happening"""
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

# Replace Normaliser Payload with a simpler version that logs
for node in w['nodes']:
    if node['name'] == 'Normaliser Payload':
        node['parameters']['jsCode'] = '''const input = $input.first().json;

// Log input for debugging
console.log('INPUT:', JSON.stringify(input));

// Generation ID incident unique et deterministe
const timestamp = Date.now();
const serviceKey = (input.monitor?.name || input.monitorName || 'unknown').toLowerCase().replace(/[^a-z0-9]/g, '-');
const incidentId = 'INC-' + timestamp + '-' + serviceKey.substring(0, 8);

// Normalisation du payload
const payload = {
  incident_id: incidentId,
  timestamp: new Date().toISOString(),
  monitor_name: input.monitor?.name || input.monitorName || 'Unknown',
  service_name: serviceKey,
  monitor_url: input.monitor?.url || input.url || '',
  status: input.heartbeat?.status === 0 ? 'DOWN' : (input.heartbeat?.status === 1 ? 'UP' : 'UNKNOWN'),
  message: input.msg || input.heartbeat?.msg || '',
  error_type: input.heartbeat?.msg?.includes('timeout') ? 'timeout' :
              input.heartbeat?.msg?.includes('connection') ? 'connection_error' :
              input.heartbeat?.status === 0 ? 'service_down' : 'unknown',
  attempt_count: 0,
  level_1_diagnosis: null,
  level_1_action: null,
  level_1_success: null,
  level_2_recommendation: null
};

// Log output for debugging
console.log('OUTPUT:', JSON.stringify(payload));
console.log('STATUS:', payload.status);

return [{ json: payload }];'''
        print("[OK] Added debug logs to Normaliser Payload")

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
