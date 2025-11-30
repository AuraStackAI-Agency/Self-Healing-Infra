#!/usr/bin/env python3
"""Fix Action Executor to read from body in webhook data"""
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

# Fix all Code nodes that read webhook data
for node in w['nodes']:
    if node['name'] == 'Preparer Query RAG':
        node['parameters']['jsCode'] = '''const webhookData = $input.first().json;
// Webhook data is in body
const incident = webhookData.body || webhookData;
const searchText = (incident.service_name || '') + ' ' + (incident.error_type || '') + ' ' + (incident.monitor_name || '');
incident._search_text = searchText.trim() || 'incident analysis';
return [{ json: incident }];'''
        print("[OK] Fixed Preparer Query RAG")

    if node['name'] == 'Preparer RAG N2':
        node['parameters']['jsCode'] = '''const webhookData = $input.first().json;
const incident = webhookData.body || webhookData;
const searchText = (incident.service_name || '') + ' ' + (incident.error_type || '') + ' escalation N2';
incident._search_text_n2 = searchText.trim() || 'incident escalation N2';
return [{ json: incident }];'''
        print("[OK] Fixed Preparer RAG N2")

    if node['name'] == 'Enrichir avec RAG':
        code = node['parameters'].get('jsCode', '')
        if "const incident = $('Webhook Execute Action')" in code:
            node['parameters']['jsCode'] = code.replace(
                "const incident = $('Webhook Execute Action').first().json;",
                "const webhookData = $('Webhook Execute Action').first().json;\nconst incident = webhookData.body || webhookData;"
            )
            print("[OK] Fixed Enrichir avec RAG")

    if node['name'] == 'Valider Commande':
        code = node['parameters'].get('jsCode', '')
        if 'const incident = $input.first().json;' in code:
            node['parameters']['jsCode'] = code.replace(
                "const incident = $input.first().json;",
                "const inputData = $input.first().json;\nconst incident = inputData.body || inputData;"
            )
            print("[OK] Fixed Valider Commande")

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
