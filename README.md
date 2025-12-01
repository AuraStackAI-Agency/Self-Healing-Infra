# Self-Healing Infra - Agentic Auto-Fix System

![Status](https://img.shields.io/badge/Status-COMPLETED-success)
![Version](https://img.shields.io/badge/Version-2.2.0-blue)
![License](https://img.shields.io/badge/License-MIT-green)

Architecture AIOps Enterprise-Grade : Orchestration N8N + IA Hybride (Qwen/Claude) avec controle humain strict.

> **Projet termine et valide en production** - Systeme d'auto-guerison fonctionnel avec notifications email et monitoring Uptime Kuma.

## Fonctionnalites Cles

- **Auto-diagnostic** : Analyse automatique des pannes via IA locale (Qwen 2.5)
- **Auto-reparation** : Execution securisee des actions correctives
- **Notifications intelligentes** : Emails HTML avec statut de resolution
- **Escalade N2** : Analyse approfondie Claude si echec N1
- **Validation humaine** : Approbation requise pour actions sensibles
- **Historique RAG** : Apprentissage des incidents passes via Qdrant

## Architecture

```
┌─────────────────┐     Webhook      ┌──────────────────────────────────────┐
│  Uptime Kuma    │ ───────────────► │           N8N Workflows               │
│  (Monitoring)   │                  │                                       │
└─────────────────┘                  │  ┌─────────────────────────────────┐  │
                                     │  │     Main Supervisor             │  │
                                     │  │  • Reception alerte             │  │
                                     │  │  • Collecte logs SSH            │  │
                                     │  │  • Analyse Qwen (N1)            │  │
                                     │  │  • Validation commande          │  │
                                     │  └──────────────┬──────────────────┘  │
                                     │                 │                     │
                                     │  ┌──────────────▼──────────────────┐  │
                                     │  │     Action Executor             │  │
                                     │  │  • Execution action safe        │  │
                                     │  │  • Verification HTTP/service    │  │
                                     │  │  • Notification succes/echec    │  │
                                     │  │  • Escalade N2 si echec         │  │
                                     │  └──────────────┬──────────────────┘  │
                                     │                 │                     │
                                     │  ┌──────────────▼──────────────────┐  │
                                     │  │   Notification Manager          │  │
                                     │  │  • Email succes (auto-guerison) │  │
                                     │  │  • Email echec (escalade N2)    │  │
                                     │  │  • Email validation humaine     │  │
                                     │  └─────────────────────────────────┘  │
                                     └──────────────────────────────────────┘
```

## Stack Technique

| Composant | Role | Port |
|-----------|------|------|
| **N8N** | Orchestrateur workflows | 5678 |
| **Uptime Kuma** | Monitoring & alertes | 3001 |
| **Ollama** | LLM local (Qwen 2.5 Coder 3B) | 11434 |
| **Qdrant** | Vector Store (RAG) | 6333 |
| **PostgreSQL** | Base N8N | 5432 |

## Workflows N8N

### 1. Main Supervisor
- Reception des alertes Uptime Kuma via webhook
- Collecte des logs systeme et Docker via SSH
- Analyse IA niveau 1 avec Qwen 2.5
- Validation des commandes contre whitelist
- Routage vers Action Executor ou escalade

### 2. Action Executor
- Execution des actions correctives via SSH
- Verification du retablissement du service
- Support des codes HTTP 2xx et 3xx (redirections)
- Notification de succes avec details complets
- Escalade automatique N2 en cas d'echec

### 3. Notification Manager
- Routage intelligent selon le type (success/failure/escalation)
- Generation d'emails HTML professionnels
- Liens de validation pour approbation humaine
- Confirmation d'execution post-validation

## Niveaux de Resolution

### Niveau 1 - Qwen (Local)
- Analyse rapide des logs (~3-4 minutes)
- Actions simples : restart service, restart container
- Validation automatique si commande dans whitelist
- **Cout : Gratuit (local)**

### Niveau 2 - Claude (Cloud)
- Analyse approfondie root cause
- Diagnostic complexe avec recommandations
- **Validation humaine obligatoire**
- Enrichissement du contexte RAG
- **Cout : API Anthropic**

## Securite

### Whitelist des Commandes
Seules les commandes pre-approuvees sont executees :
- `docker restart {container}`
- `systemctl restart {service}`
- Services autorises configures dans le workflow

### Validation Humaine
- Escalade N2 requiert approbation par email
- Tokens uniques avec expiration
- Audit trail complet

## Types d'Emails

| Type | Declencheur | Contenu |
|------|-------------|---------|
| **Succes** | Auto-guerison reussie | Incident ID, Service, Action executee |
| **Echec** | N1 echoue, escalade N2 | Diagnostic, Action tentee, Statut escalade |
| **Validation** | Action N2 en attente | Boutons Valider/Ignorer, Details action |

## Installation

### Prerequis
- VPS Linux (Debian/Ubuntu)
- Docker et Docker Compose
- N8N installe
- Ollama avec modele Qwen 2.5

### Configuration

1. **Importer les workflows** dans N8N
2. **Configurer les credentials** :
   - SSH vers le serveur cible
   - SMTP pour les emails
   - API Anthropic (optionnel, pour N2)
3. **Configurer Uptime Kuma** :
   - Ajouter les monitors avec endpoint `/health`
   - Configurer le webhook vers N8N
4. **Configurer le reseau Docker** :
   - Autoriser le trafic entre containers et host

## Structure du Projet

```
self-healing-infra/
├── workflows/                    # Workflows N8N (structure uniquement)
│   ├── Main_Supervisor.json
│   ├── Action_Executor.json
│   └── Notification_Manager.json
├── config/
│   └── safe_commands.json        # Whitelist des commandes
├── prompts/
│   ├── qwen_n1_analyst.md        # Prompt analyse N1
│   └── claude_n2_expert.md       # Prompt analyse N2
├── docs/
│   └── ARCHITECTURE_V2.md        # Documentation technique
├── CHANGELOG.md                  # Historique des versions
└── README.md
```

## Metriques de Production

| Metrique | Valeur |
|----------|--------|
| Temps moyen de detection | < 60s |
| Temps moyen de resolution N1 | ~4 min |
| Taux de succes auto-guerison | Variable selon service |
| Faux positifs | Minimises par whitelist |

## Roadmap (Complete)

- [x] Architecture multi-workflows
- [x] Integration Uptime Kuma
- [x] Analyse IA N1 (Qwen local)
- [x] Execution securisee via SSH
- [x] Notifications email differenciees
- [x] Support HTTP 3xx (redirections)
- [x] Extraction correcte des donnees webhook
- [x] Routage conditionnel des notifications
- [x] Monitoring avec endpoint /health
- [x] Escalade N2 avec Claude (structure)
- [x] RAG avec Qdrant (structure)

## Licence

MIT - Voir [LICENSE](LICENSE)

---

**Projet realise par AuraStack AI Agency**

*Architecture d'infrastructures autonomes et intelligentes*
