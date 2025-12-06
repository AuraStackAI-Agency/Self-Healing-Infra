# Workflows N8N - Self-Healing V3

## Structure

Les workflows ne sont pas inclus dans ce repo pour des raisons de sécurité (ils contiennent des références aux credentials).

## Import

1. Créez les workflows dans N8N
2. Utilisez les nœuds Code avec les fichiers JS de `../nodes/`
3. Configurez les credentials (SSH, SMTP, etc.)

## Architecture des workflows

### 1. Main Supervisor V3

```
Webhook (Uptime Kuma)
    │
    ▼
Parallel Context Fetch
    ├─ HTTP Request → Qdrant
    └─ HTTP Request → AuraCore (optionnel)
    │
    ▼
Rate Limiter Gate (Code node: rate_limiter_gate.js)
    │
    ├─ [blocked=true] → Notification "Rate Limited"
    │
    ▼
Fast Track Gate (Code node: fast_track_gate.js)
    │
    ├─ [eligible=true] → Intent Engine → Execute
    │
    ▼
SSH Collect Logs
    │
    ▼
Qwen Analysis (HTTP Request → Ollama)
    │
    ▼
Intent Engine (Code node: intent_engine.js)
    │
    ├─ [valid=false] → Escalade N2
    │
    ▼
Audit Pre (Code node: audit_trail_pre.js)
    │
    ▼
SSH Execute
    │
    ▼
Audit Post (Code node: audit_trail_post.js)
    │
    ▼
Rate Limiter Increment (Code node: rate_limiter_increment.js)
    │
    ▼
Qdrant Feedback (Code node: qdrant_feedback.js)
    │
    ▼
HTTP Request → Qdrant Upsert
    │
    ▼
Notification Success
```

### 2. Escalation Handler

Gère les escalades N2 vers Claude ou validation humaine.

## Credentials nécessaires

| Credential | Type | Usage |
|------------|------|-------|
| SSH VPS | SSH Private Key | Exécution commandes |
| SMTP | Email | Notifications |
| Anthropic (optionnel) | API Key | Escalade N2 Claude |

## Variables d'environnement

Ne stockez JAMAIS de credentials dans les workflows.
Utilisez les credentials N8N ou des variables d'environnement.
