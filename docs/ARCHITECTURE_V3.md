# Architecture Self-Healing Infrastructure V3

## Vue d'ensemble

Le système Self-Healing Infrastructure V3 utilise un **consensus dual-LLM** pour diagnostiquer et résoudre automatiquement les incidents d'infrastructure avec une haute fiabilité.

## Composants Principaux

### 1. Monitoring (Uptime Kuma)
- Surveillance continue des services
- Détection des pannes en temps réel
- Déclenchement des webhooks vers N8N

### 2. Orchestration (N8N Workflows)
- **Main Supervisor**: Point d'entrée, routage intelligent
- **Action Executor**: Exécution sécurisée des actions
- **Notification Manager**: Alertes et escalades humaines
- **N3 Escalation**: Analyse architecte (Claude Opus)

### 3. Intelligence (AuraCore API + Ollama)
- **Qwen 2.5 Coder 3B** (DIAGNOSTICIAN): Analyse rapide des incidents
- **Phi-3 Mini 3.8B** (VALIDATOR): Validation indépendante
- **Protocole AILCP**: Communication structurée inter-LLM

### 4. Mémoire (Qdrant)
- Stockage vectoriel des incidents résolus
- RAG pour amélioration continue
- Apprentissage des patterns de pannes

---

## Flux de Traitement

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         UPTIME KUMA                                      │
│                    (Monitoring & Alerting)                               │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ Webhook (service down)
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         MAIN SUPERVISOR                                  │
│                    (N8N Workflow - Routage)                             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                   │
│  │ Normaliser  │──▶│ Check RAG   │──▶│  Router     │                   │
│  │   Payload   │   │  (Qdrant)   │   │  Niveau     │                   │
│  └─────────────┘   └─────────────┘   └─────────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
              ┌─────────┐   ┌─────────┐   ┌─────────┐
              │ N0: RAG │   │N1: Local│   │N2: Cloud│
              │ (Connu) │   │Consensus│   │ (Sonnet)│
              └─────────┘   └────┬────┘   └─────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         AURACORE API V2                                  │
│                    (Consensus Dual-LLM AILCP)                           │
│                                                                         │
│  ┌──────────────────────┐      ┌──────────────────────┐                │
│  │   QWEN 2.5 CODER     │      │     PHI-3 MINI       │                │
│  │   (DIAGNOSTICIAN)    │      │     (VALIDATOR)      │                │
│  │                      │      │                      │                │
│  │  • Analyse logs      │      │  • Challenge diag    │                │
│  │  • Identifie cause   │─────▶│  • Évalue risques    │                │
│  │  • Propose action    │      │  • Score confiance   │                │
│  │  • Confidence: 0-1   │      │  • AGREE/PARTIAL/    │                │
│  └──────────────────────┘      │    DISAGREE          │                │
│                                └──────────────────────┘                │
│                                         │                              │
│                                         ▼                              │
│                          ┌──────────────────────────┐                  │
│                          │    CONSENSUS ENGINE      │                  │
│                          │                          │                  │
│                          │  Matrice de Décision:    │                  │
│                          │  ├─ AUTO_EXECUTE         │                  │
│                          │  ├─ EXECUTE_WITH_LOG     │                  │
│                          │  ├─ HUMAN_REVIEW         │                  │
│                          │  └─ ESCALATE_N2          │                  │
│                          └──────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
              ┌──────────┐  ┌──────────┐  ┌──────────┐
              │AUTO_EXEC │  │ HUMAN    │  │ESCALATE  │
              │          │  │ REVIEW   │  │   N2     │
              └────┬─────┘  └────┬─────┘  └────┬─────┘
                   │             │             │
                   ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       ACTION EXECUTOR                                    │
│                    (N8N Workflow - Exécution)                           │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                   │
│  │  Valider    │──▶│  Exécuter   │──▶│  Vérifier   │                   │
│  │  Whitelist  │   │   Action    │   │  Résultat   │                   │
│  └─────────────┘   └─────────────┘   └─────────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     NOTIFICATION MANAGER                                 │
│                    (N8N Workflow - Alertes)                             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                   │
│  │   Email     │   │   Discord   │   │   Slack     │                   │
│  │  (Success/  │   │  (Webhook)  │   │  (Webhook)  │                   │
│  │  Escalation)│   │             │   │             │                   │
│  └─────────────┘   └─────────────┘   └─────────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Protocole AILCP

**AI-to-LLM Communication Protocol** - Format JSON structuré pour la communication entre modèles de langage.

### Message Types

| Type | Émetteur | Description |
|------|----------|-------------|
| DIAGNOSIS | Qwen | Analyse initiale de l'incident |
| VALIDATION | Phi-3 | Validation/challenge du diagnostic |
| CONSENSUS | Engine | Décision finale du système |

### Matrice de Décision

| Qwen Conf. | Phi-3 Agreement | Phi-3 Score | Décision |
|------------|-----------------|-------------|----------|
| ≥ 0.8 | AGREE | ≥ 0.8 | AUTO_EXECUTE |
| ≥ 0.6 | AGREE | ≥ 0.6 | EXECUTE_WITH_LOG |
| any | PARTIAL | any | HUMAN_REVIEW |
| < 0.6 | any | any | ESCALATE_N2 |
| any | DISAGREE | any | ESCALATE_N2 |

---

## Niveaux de Résolution

### N0 - RAG (Résolution Instantanée)
- Incident déjà connu dans Qdrant
- Solution appliquée directement
- Temps: < 5 secondes

### N1 - Consensus Local (Dual-LLM)
- Analyse Qwen + Validation Phi-3
- Consensus automatique si confiance élevée
- Temps: 60-90 secondes

### N2 - Claude Sonnet (Analyse Cloud)
- Incidents complexes ou désaccord LLM
- Analyse approfondie avec contexte étendu
- Temps: 30-60 secondes

### N3 - Claude Opus (Architecte)
- Problèmes structurels ou récurrents
- Recommandations architecturales
- Intervention humaine requise

---

## Sécurité

### Actions Whitelistées
```json
{
  "safe_actions": [
    "systemctl restart {service}",
    "systemctl reload {service}",
    "docker restart {container}",
    "docker system prune -f",
    "journalctl --vacuum-size=500M"
  ]
}
```

### Actions Interdites
- Toute commande `rm -rf`
- Opérations disque destructives
- Modifications firewall
- Commandes avec pipe externe

---

## Métriques

| Métrique | Objectif | Actuel |
|----------|----------|--------|
| Temps résolution N1 | < 2 min | ~75s |
| Précision diagnostic | > 90% | 90% |
| Taux auto-résolution | > 80% | En cours |
| Faux positifs | < 5% | En cours |
