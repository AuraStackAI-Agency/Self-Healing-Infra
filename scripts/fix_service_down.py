#!/usr/bin/env python3
"""Fix Service Down? condition in Main Supervisor workflow"""
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

# Fix Service Down? node - remove strict type validation
for node in w['nodes']:
    if node['name'] == 'Service Down?':
        node['parameters']['conditions']['options'] = {
            'caseSensitive': False,
            'leftValue': '',
            'typeValidation': 'loose'
        }
        print("[OK] Fixed 'Service Down?' - removed strict validation")

    # Also fix Action Safe? node
    if node['name'] == 'Action Safe?':
        node['parameters']['conditions']['options'] = {
            'caseSensitive': True,
            'leftValue': '',
            'typeValidation': 'loose'
        }
        print("[OK] Fixed 'Action Safe?' - removed strict validation")

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
