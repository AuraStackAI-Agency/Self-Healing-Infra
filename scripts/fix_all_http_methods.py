#!/usr/bin/env python3
"""Fix all HTTP nodes to use POST method where needed"""
import requests
import json

N8N_API_URL = "https://n8n.aurastackai.com/api/v1"
N8N_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkN2Q3ZTM2Mi1kMjJhLTQ4OWYtYTdkMi1lNjNjNGNmNjU3OTAiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzYyNjk5MTUwfQ.Gi6k_zcap4NUNKQTrEf8BM1DAwbv-iV5eVYV2VoS44U"

headers = {
    "X-N8N-API-KEY": N8N_API_KEY,
    "Content-Type": "application/json"
}

# Nodes that should use POST (calling webhooks)
POST_NODES = [
    'Appeler Action Executor',
    'Escalader N2',
    'Escalader - Invalide',
    'Notifier Succes',
    'Demander Validation'
]

def fix_workflow(workflow_id, name):
    print(f"\n=== {name} ===")
    response = requests.get(f"{N8N_API_URL}/workflows/{workflow_id}", headers=headers)
    w = response.json()

    fixed = 0
    for node in w['nodes']:
        if node['type'] == 'n8n-nodes-base.httpRequest':
            node_name = node['name']
            url = node['parameters'].get('url', '')
            current_method = node['parameters'].get('method', 'GET')

            # If it's a webhook URL and not already POST, fix it
            if '/webhook/' in url and current_method != 'POST':
                node['parameters']['method'] = 'POST'
                print(f"[FIX] {node_name}: {current_method} -> POST")
                fixed += 1

    if fixed > 0:
        clean_data = {
            "name": w["name"],
            "nodes": w["nodes"],
            "connections": w["connections"],
            "settings": {"executionOrder": "v1"}
        }
        response = requests.put(
            f"{N8N_API_URL}/workflows/{workflow_id}",
            headers=headers,
            json=clean_data
        )
        if response.status_code == 200:
            print(f"[OK] Updated {fixed} nodes")
        else:
            print(f"[ERROR] {response.status_code}: {response.text}")
    else:
        print("[OK] No changes needed")

# Fix Main Supervisor
fix_workflow("YPOEAMIDhDEdRLyX", "Main Supervisor")

# Fix Action Executor
fix_workflow("m239OOMCarIbNa7C", "Action Executor")

# Fix Notification Manager
fix_workflow("Z796nTTfPwJ7Zo90", "Notification Manager")

print("\n[DONE] All workflows checked")
