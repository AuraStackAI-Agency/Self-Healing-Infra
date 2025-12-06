# Self-Healing Infra - Agentic Auto-Fix System V3

![Status](https://img.shields.io/badge/Status-ACTIVE-success)
![Version](https://img.shields.io/badge/Version-3.0.0-blue)
![Security](https://img.shields.io/badge/Security-Hardenized-orange)
![License](https://img.shields.io/badge/License-MIT-green)

Architecture AIOps Enterprise-Grade : Orchestration N8N + IA Hybride avec **Intent Engine** sécurisé.

> **V3 "Hardenized"** - Le LLM génère des intents, pas des commandes. La sécurité vient du code, pas de l'IA.

## Principe Fondamental V3

> **"L'IA classe, mais c'est le Code (Whitelists) qui autorise."**

Le LLM ne génère **jamais** de commande shell. Il génère un **intent structuré** qui est validé et mappé par du code déterministe.

## Architecture V3 Hardenized

```
ALERT (Uptime Kuma)
   │
   ▼
┌──────────────────────────────────────────┐
│ 1. PARALLEL CONTEXT FETCH                │
│    ├─ Qdrant: incidents similaires       │
│    └─ AuraCore: règles + intents valides │
└──────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────┐
│ 2. RATE LIMITING GATE                    │
│    SI > 3 restarts/h/service → STOP      │
│    SI > 10 global executions/h → STOP    │
└──────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────┐
│ 3. FAST TRACK GATE                       │
│    SI match RAG > 0.85 ET intent connu   │
│    → Execute via Intent Map (0 LLM)      │
└──────────────────────────────────────────┘
   │ SINON
   ▼
┌──────────────────────────────────────────┐
│ 4. QWEN "Technicien"                     │
│    Output: {intent, target, confidence}  │
│    ⚠️ PAS de commande shell              │
└──────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────┐
│ 5. INTENT & TARGET VALIDATION ENGINE     │
│    • Intent in whitelist?                │
│    • Target in valid_targets?            │
│    • No injection patterns?              │
│    → Generate safe command               │
└──────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────┐
│ 6. AUDIT TRAIL                           │
│    Log avant + après exécution           │
│    Feedback loop → Qdrant                │
└──────────────────────────────────────────┘
```

## Composants de Sécurité V3

| Composant | Rôle | Protection |
|-----------|------|------------|
| **Intent Engine** | Map intent → commande | LLM ne peut pas inventer de commande |
| **Target Whitelist** | Valide les cibles | Seuls services prédéfinis acceptés |
| **Injection Blocker** | Détecte `;`, `&&`, `\|` | Empêche le chaînage de commandes |
| **Rate Limiter** | 3/h/service, 10/h global | Anti-boucle et anti-DoS |
| **Fast Track** | Bypass LLM si RAG > 0.85 | Réduit surface d'attaque |
| **Audit Trail** | Log immuable | Forensics et compliance |

## Niveaux de Résolution V3

| Niveau | Condition | Méthode | Temps |
|--------|-----------|---------|-------|
| **N0 Fast Track** | RAG match > 0.85 | 0 LLM, Intent Map direct | ~5s |
| **N1 Standard** | Pas de match RAG | Qwen → Intent Engine | ~90s |
| **N1.5 Dual** | Qwen conf < 0.8 | Qwen → Phi validation | ~150s |
| **N2 Expert** | Escalade | Claude + validation humaine | API |

## Intents Disponibles

```javascript
const INTENTS = {
  // Low Risk - Auto-exécution
  "restart_service": ["nginx", "php8.x-fpm", "postgresql", "redis-server"],
  "docker_restart": ["n8n-main-prod", "ollama", "qdrant"],
  "clear_system_logs": [],
  "check_disk": [],
  "check_memory": [],
  
  // Medium Risk - Approbation requise
  "stop_service": ["nginx", "php8.x-fpm"],
  "docker_stop": ["n8n-worker-prod-1"],
  "docker_prune": [],
  
  // Special
  "ESCALATE": []  // Demande intervention humaine
};
```

## Stack Technique

| Composant | Rôle | Port |
|-----------|------|------|
| **N8N** | Orchestrateur workflows | 5678 |
| **Uptime Kuma** | Monitoring & alertes | 3001 |
| **Ollama** | LLM local (Qwen 2.5 Coder 3B) | 11434 |
| **Qdrant** | Vector Store (RAG) | 6333 |
| **AuraCore MCP** | Règles métier & contexte | MCP |
| **PostgreSQL** | Base N8N | 5432 |
| **Redis** | Cache & Rate Limiting | 6379 |

## Structure du Projet V3

```
self-healing-infra/
├── docs/
│   ├── ARCHITECTURE_V3.md        # Documentation complète V3
│   └── SECURITY.md               # Analyse de sécurité
├── n8n/
│   ├── nodes/
│   │   ├── rate_limiter_gate.js      # Rate limiting
│   │   ├── fast_track_gate.js        # Fast track RAG
│   │   ├── intent_engine.js          # Moteur d'intent (CORE)
│   │   └── audit_trail.js            # Logging
│   └── workflows/
│       └── README.md                 # Instructions import
├── prompts/
│   ├── qwen_technician_v3.md         # Prompt format intent
│   └── phi_auditor.md                # Prompt validation
├── config/
│   ├── intents.example.json          # Template intents
│   └── targets.example.json          # Template targets
├── CHANGELOG.md
└── README.md
```

## Scores de Sécurité V3

| Critère | Score | Commentaire |
|---------|-------|-------------|
| Viabilité | 8/10 | Architecture solide |
| Sécurité | 7.5/10 | Intent Engine + Whitelists |
| Coût/Bénéfice | 8/10 | Fast Track réduit les appels LLM |
| **Global** | **7.5/10** | Production-ready |

## Changelog V3

### v3.0.0 (2024-12)
- ✅ **Intent Engine** : LLM génère des intents, pas des commandes
- ✅ **Target Whitelist** : Validation stricte des cibles
- ✅ **Rate Limiting** : Protection anti-boucle
- ✅ **Fast Track Gate** : Bypass LLM si solution connue
- ✅ **Audit Trail** : Logging complet avant/après
- ✅ **Injection Blocker** : Détection patterns dangereux

### v2.2.0
- Architecture dual-LLM consensus (obsolète en V3)

## Installation

Voir [docs/ARCHITECTURE_V3.md](docs/ARCHITECTURE_V3.md) pour les instructions détaillées.

## Licence

MIT - Voir [LICENSE](LICENSE)

---

**Projet réalisé par AuraStack AI Agency**

*Architecture d'infrastructures autonomes et intelligentes*
