#!/usr/bin/env python3
"""Merge SSH nodes into one to avoid parallel execution issues"""
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

# Merge SSH commands into one node
for node in w['nodes']:
    if node['name'] == 'SSH - Collecter Logs':
        # Combine both commands in one SSH call
        node['parameters']['command'] = """=echo '=== SYSTEM LOGS ===' && (tail -n 100 /var/log/syslog 2>/dev/null || journalctl -n 100 --no-pager 2>/dev/null | tail -100) && echo '\\n=== DOCKER LOGS ===' && (docker logs --tail 50 {{ $json.service_name }} 2>&1 || echo 'No Docker container')"""
        node['name'] = 'SSH - Collecter Tous Logs'
        print("[OK] Merged SSH commands into one node")

# Remove SSH - Docker Logs node
w['nodes'] = [n for n in w['nodes'] if n['name'] != 'SSH - Docker Logs']
print("[OK] Removed SSH - Docker Logs node")

# Update connections - Service Down? now only goes to one SSH node
conns = w['connections']
if 'Service Down?' in conns:
    # Output 0 (TRUE) should only have one target now
    conns['Service Down?']['main'][0] = [
        {"node": "SSH - Collecter Tous Logs", "type": "main", "index": 0}
    ]
    print("[OK] Updated Service Down? connections")

# Update Agreger Logs connections - now only needs one input
if 'SSH - Collecter Logs' in conns:
    # Rename in connections
    conns['SSH - Collecter Tous Logs'] = conns.pop('SSH - Collecter Logs')

# Update Agreger Logs to work with single input
for node in w['nodes']:
    if node['name'] == 'Agreger Logs':
        node['parameters']['jsCode'] = '''const incident = $('Normaliser Payload').first().json;
const allLogs = $input.first().json.stdout || '';

// Parse logs into sections
const sysLogs = allLogs.split('=== DOCKER LOGS ===')[0].replace('=== SYSTEM LOGS ===', '').trim();
const dockerLogs = allLogs.split('=== DOCKER LOGS ===')[1]?.trim() || 'No Docker logs';

incident.error_logs = '=== SYSTEM LOGS ===\\n' + sysLogs.slice(-2000) + '\\n\\n=== DOCKER LOGS ===\\n' + dockerLogs.slice(-2000);
incident.attempt_count = 1;
return [{ json: incident }];'''
        print("[OK] Updated Agreger Logs to parse combined output")

# Remove old SSH - Docker Logs connection from Agreger Logs
if 'SSH - Docker Logs' in conns:
    del conns['SSH - Docker Logs']
    print("[OK] Removed old Docker Logs connection")

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
