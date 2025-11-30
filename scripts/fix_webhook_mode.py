#!/usr/bin/env python3
"""Fix webhook to respond immediately and continue workflow"""
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

# Fix webhook to respond immediately
for node in w['nodes']:
    if node['name'] == 'Webhook Uptime Kuma':
        node['parameters']['options'] = {
            'responseMode': 'onReceived',
            'responseData': 'firstEntryJson'
        }
        print("[OK] Webhook set to 'Respond Immediately'")

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
