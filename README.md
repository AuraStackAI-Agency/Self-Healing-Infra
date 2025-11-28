# Self-Healing Infra - Agentic Auto-Fix System

Système autonome de supervision serveur (VPS Debian) capable de détecter une panne, tenter une résolution automatique, et escalader si nécessaire.

## Architecture

```
┌─────────────────┐     Webhook      ┌──────────────────────────────────────┐
│  Uptime Kuma    │ ───────────────► │           N8N Workflows               │
│  (Monitoring)   │                  │                                       │
│                 │                  │  ┌─────────────────────────────────┐  │
│                 │                  │  │     Main_Supervisor.json        │  │
│                 │                  │  │  • Réception alerte             │  │
│                 │                  │  │  • Collecte logs SSH            │  │
│                 │                  │  │  • Appel Qwen (N1)              │  │
│                 │                  │  └──────────────┬──────────────────┘  │
│                 │                  │                 │                     │
│                 │                  │  ┌──────────────▼──────────────────┐  │
│                 │                  │  │   Safety Check (Regex Gate)     │  │
│                 │                  │  │  • Validation Commandes         │  │
│                 │                  │  └──────────────┬──────────────────┘  │
│                 │                  │                 │                     │
│                 │                  │  ┌──────────────▼──────────────────┐  │
│                 │                  │  │     Action_Executor.json        │  │
│                 │                  │  │  • Exécution actions safe       │  │
│                 │                  │  │  • Vérification post-action     │  │
│                 │                  │  │  • Escalade N2 si échec         │  │
│                 │                  │  └──────────────┬──────────────────┘  │
│                 │                  │                 │                     │
│                 │                  │  ┌──────────────▼──────────────────┐  │
│                 │                  │  │   Notification_Manager.json     │  │
│                 │                  │  │  • Email HTML actionnable       │  │
│                 │                  │  │  • Webhook validation humaine   │  │
│                 │                  │  │  • Confirmation finale          │  │
│                 │                  │  └─────────────────────────────────┘  │
│                 │                  └──────────────────────────────────────┘
│                                                      │
│                    ┌─────────────────────────────────┼─────────────────────────────────┐
│                    │                                 │                                 │
│             ┌──────▼──────┐                  ┌───────▼───────┐                ┌────────▼────────┐
│             │   Ollama    │                  │  Claude API   │                │   Email SMTP    │
│             │  Qwen 2.5   │                  │  (Niveau 1)   │                │  (Validation)   │
│             │  (Niveau 1) │                  └───────┬───────┘                └─────────────────┘
│             └─────────────┘                          │
│                                              ┌───────▼───────┐
│                                              │ Vector Store  │
│                                              │ (RAG Memory)  │
│                                              └───────────────┘
```

## Stack Technique

| Composant | Rôle | Port |
|-----------|------|------|
| **N8N** | Orchestrateur workflows | 5678 |
| **Uptime Kuma** | Monitoring & alertes | 3001 |
| **Ollama** | LLM local (Qwen 2.5) | 11434 |
| **Redis** | Queue N8N | 6379 |
| **PostgreSQL** | Base N8N | 5432 |
| **Qdrant/Chroma** | Vector Store (RAG) | 6333 |

## Niveaux de Résolution

### Niveau 1 - Qwen (Local)
- Analyse rapide des logs
- Actions simples et sécurisées (restart, clear cache)
- Temps de réponse < 5s
- **Pas de coût API**

### Niveau 2 - Claude (Cloud)
- Analyse approfondie
- Diagnostic root cause
- Recommandations complexes
- **Validation humaine requise**
- **Apprentissage :** Les succès validés enrichissent le contexte RAG pour les futurs incidents (Feedback Loop).

## Sécurité par Design

Le système intègre une "Gate" de sécurité stricte. Aucune commande générée par l'IA n'est exécutée sans validation par liste blanche.

Exemple de configuration `config/safe_commands.json` :

```json
{
  "safe_commands": {
    "service_management": {
      "allowed": [
        "systemctl restart {service}",
        "systemctl start {service}"
      ],
      "allowed_services": ["nginx", "apache2", "docker"]
    },
    "blocked_patterns": [
      "rm -rf",
      "shutdown",
      "mkfs"
    ]
  }
}
```

## Structure du Projet

```
self-healing-infra/
├── workflows/
│   ├── Main_Supervisor.json       # Workflow principal
│   ├── Action_Executor.json       # Exécution des actions
│   └── Notification_Manager.json  # Gestion emails/validation
├── scripts/
│   ├── clean_logs.sh              # Nettoyage logs
│   ├── restart_service.sh         # Restart sécurisé
│   ├── check_disk.sh              # Vérification disque
│   └── health_check.sh            # Check santé global
├── prompts/
│   ├── qwen_n1_analyst.md         # Prompt Niveau 1
│   └── claude_n2_expert.md        # Prompt Niveau 2
├── config/
│   └── safe_commands.json         # Liste blanche commandes
├── docker-compose.yml             # Stack Uptime Kuma
├── .env.template                  # Template credentials
└── README.md
```

## Installation

### 1. Cloner le dépôt
```bash
git clone https://github.com/VOTRE_USER/self-healing-infra.git
cd self-healing-infra
```

### 2. Configurer les variables
```bash
cp .env.template .env
nano .env  # Remplir les credentials
```

### 3. Déployer Uptime Kuma
```bash
docker-compose up -d
```

### 4. Importer les workflows N8N
- Ouvrir N8N → Settings → Import
- Importer les 3 fichiers JSON depuis `/workflows/`

### 5. Configurer Uptime Kuma
- Accéder à http://VOTRE_IP:3001
- Ajouter les monitors pour vos services
- Configurer le webhook vers N8N

## Schéma de Données (Payload)

Structure JSON standardisée circulant entre les nœuds :

```json
{
  "incident_id": "uuid-v4",
  "timestamp": "2025-01-15T10:30:00Z",
  "service_name": "nginx",
  "monitor_name": "Web Server",
  "status": "CRITICAL",
  "error_logs": "...",
  "attempt_count": 1,
  "level_1_diagnosis": {
    "cause": "Service crashed due to OOM",
    "confidence": 0.85,
    "action_command": "systemctl restart nginx"
  },
  "level_1_success": false,
  "level_2_recommendation": {
    "root_cause": "Memory leak in upstream module",
    "action_command": "...",
    "requires_human_approval": true
  },
  "cost_estimation": {
    "ai_cost": "$0.02",
    "tokens_used": 450
  }
}
```

## Licence

MIT
