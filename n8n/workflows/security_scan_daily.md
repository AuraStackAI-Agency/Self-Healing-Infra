# Security Scan Daily - Instructions de déploiement

## Prérequis

- N8N avec accès SSH au VPS
- Credentials SSH configurées
- Credentials SMTP pour les alertes email

## Structure du workflow

```
[Schedule Trigger] → [SSH: ss -tlnp] → [Code: Scan Ports]
                                              │
                   → [SSH: curl ollama] → [Code: Scan Ollama]
                                              │
                   → [SSH: iptables -L] → [Code: Scan Iptables]
                                              │
                                              ▼
                                    [Code: Generate Report]
                                              │
                              ┌───────────────┴───────────────┐
                              ▼                               ▼
                    [IF: has_anomaly]                  [Qdrant: Log]
                              │
                              ▼
                      [Send Email]
```

## Création dans N8N

### 1. Schedule Trigger

```json
{
  "rule": {
    "interval": [{"field": "cronExpression", "expression": "0 3 * * *"}]
  },
  "options": {
    "timezone": "UTC"
  }
}
```

### 2. Nœuds SSH (Execute Command)

Créer 3 nœuds SSH pour les commandes:

**Scan Ports (SSH):**
```
ss -tlnp | grep "0.0.0.0"
```

**Scan Ollama (SSH):**
```
curl -s http://localhost:11434/api/tags
```

**Scan Iptables (SSH):**
```
iptables -L INPUT -n
```

### 3. Nœuds Code

Créer 4 nœuds Code avec le contenu de:
- `n8n/nodes/security_scan_ports.js`
- `n8n/nodes/security_scan_ollama.js`
- `n8n/nodes/security_scan_iptables.js`
- `n8n/nodes/security_scan_report.js`

### 4. Nœud IF

```json
{
  "conditions": {
    "boolean": [{
      "value1": "={{ $json.has_anomaly }}",
      "value2": true
    }]
  }
}
```

### 5. Nœud Email

```json
{
  "to": "votre-email@domain.com",
  "subject": "={{ $json.email_subject }}",
  "text": "={{ $json.email_body }}"
}
```

### 6. Nœud Qdrant (optionnel)

Upload du rapport vers collection `security_scans`.

## Test manuel

1. Désactiver temporairement une règle iptables
2. Exécuter le workflow manuellement
3. Vérifier que l'alerte email est reçue
4. Réactiver la règle

## Troubleshooting

### Erreur "Failed to parse Ollama response"

Vérifier que Ollama est accessible:
```bash
curl -s http://localhost:11434/api/tags
```

### Pas d'anomalies détectées mais port exposé

Vérifier les constantes dans les fichiers .js:
- `ALLOWED_EXPOSED_PORTS`
- `CRITICAL_PORTS`

### Email non reçu

Vérifier les credentials SMTP dans N8N.
