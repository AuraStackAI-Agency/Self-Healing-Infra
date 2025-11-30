#!/usr/bin/env python3
"""Final fix - Use ollama:11434 for Docker network communication"""
import requests
import json

N8N_API_URL = "https://n8n.aurastackai.com/api/v1"
N8N_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkN2Q3ZTM2Mi1kMjJhLTQ4OWYtYTdkMi1lNjNjNGNmNjU3OTAiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzYyNjk5MTUwfQ.Gi6k_zcap4NUNKQTrEf8BM1DAwbv-iV5eVYV2VoS44U"

WORKFLOWS = {
    "main_supervisor": "YPOEAMIDhDEdRLyX",
    "action_executor": "m239OOMCarIbNa7C"
}

headers = {
    "X-N8N-API-KEY": N8N_API_KEY,
    "Content-Type": "application/json"
}

def fix_workflow(workflow_id, name):
    """Fix Ollama URLs in workflow"""
    print(f"\n=== Fixing {name} ===")

    response = requests.get(f"{N8N_API_URL}/workflows/{workflow_id}", headers=headers)
    w = response.json()

    changes = 0
    for node in w['nodes']:
        params = node.get('parameters', {})

        # Fix URL in httpRequest nodes
        if node.get('type') == 'n8n-nodes-base.httpRequest':
            url = params.get('url', '')

            # Fix Ollama URLs
            if '137.74.44.64:11434' in url or 'localhost:11434' in url:
                params['url'] = url.replace('137.74.44.64:11434', 'ollama:11434').replace('localhost:11434', 'ollama:11434')
                print(f"  [OK] Fixed {node['name']}: {params['url']}")
                changes += 1

            # Fix Qdrant URLs (use container name)
            if '137.74.44.64:6333' in url:
                params['url'] = url.replace('137.74.44.64:6333', 'qdrant:6333')
                print(f"  [OK] Fixed {node['name']}: {params['url']}")
                changes += 1

    if changes == 0:
        print("  No URL changes needed")
        return True

    # Update workflow
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
        print(f"  [OK] {name} updated successfully ({changes} changes)")
        return True
    else:
        print(f"  [ERROR] {response.status_code}: {response.text}")
        return False

# Fix all workflows
for name, wf_id in WORKFLOWS.items():
    fix_workflow(wf_id, name)

# Cleanup diagnostic workflow
print("\n=== Cleanup ===")
response = requests.delete(f"{N8N_API_URL}/workflows/5FkQfv4RV10V1uu9", headers=headers)
if response.status_code == 200:
    print("[OK] Deleted diagnostic workflow")
