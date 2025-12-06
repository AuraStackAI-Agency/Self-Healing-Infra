# Architecture Self-Healing V3 - Documentation Technique

## Vue d'ensemble

La V3 "Hardenized" représente une refonte majeure de la sécurité du système d'auto-healing. Le changement fondamental est que **le LLM ne génère plus de commandes shell**, mais des **intents structurés** validés par du code déterministe.

## Principe de sécurité

```
┌─────────────────────────────────────────────────────────────┐
│                    AVANT (V2)                               │
│                                                             │
│  LLM → "systemctl restart nginx" → Regex → Execute         │
│                  ↑                                          │
│         Risque: injection, hallucination                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    APRÈS (V3)                               │
│                                                             │
│  LLM → {intent: "restart_service", target: "nginx"}        │
│                          ↓                                  │
│  Intent Engine → Validate → Map → "systemctl restart nginx" │
│                          ↓                                  │
│                       Execute                               │
└─────────────────────────────────────────────────────────────┘
```

## Composants

### 1. Parallel Context Fetch

Au déclenchement d'une alerte, deux requêtes parallèles sont lancées :

**Qdrant (RAG)** :
- Recherche vectorielle sur les incidents passés
- Retourne les 3 incidents les plus similaires
- Inclut : solution appliquée, succès/échec, intent utilisé

**AuraCore (Règles)** :
- Récupère les intents valides
- Récupère les targets autorisés
- Récupère les règles métier spécifiques

### 2. Rate Limiting Gate

```javascript
const LIMITS = {
  per_service_per_hour: 3,
  global_per_hour: 10
};
```

Protection contre :
- Boucles de redémarrage infinies
- Attaques DoS via alertes spam
- Épuisement des ressources

### 3. Fast Track Gate

Conditions pour bypass du LLM :
1. Score RAG > 0.85
2. Résolution précédente réussie
3. Intent dans la liste low-risk
4. Target identique

**Avantages** :
- Temps de résolution ~5s au lieu de ~90s
- Pas d'appel LLM = pas de risque d'hallucination
- Réduit la charge CPU

### 4. Qwen "Technicien"

Prompt optimisé pour générer uniquement des intents valides :

```json
{
  "observation": "Erreur 502 sur nginx",
  "intent": "restart_service",
  "target": "nginx",
  "confidence": 0.85,
  "reasoning": "Process crashed, restart should fix"
}
```

**Règles du prompt** :
- Liste explicite des intents valides
- Liste explicite des targets par intent
- Instruction d'utiliser ESCALATE si incertain
- Seuil de confidence à 0.6 minimum

### 5. Intent & Target Validation Engine

Cœur de la sécurité V3 :

```javascript
// Validation en 5 étapes
1. Intent existe dans INTENT_MAP ?
2. Target ne contient pas de patterns bloqués (;|&&`$) ?
3. Target est dans validTargets pour cet intent ?
4. Confidence >= 0.6 ?
5. Intent != ESCALATE ?

// Si tout OK → Génère la commande
const command = INTENT_MAP[intent].template(target);
```

**Patterns bloqués** :
```javascript
const BLOCKED = [';', '|', '&&', '||', '`', '$(', '${', '>', '<'];
```

### 6. Audit Trail

**Avant exécution** :
```json
{
  "audit_id": "AUDIT-1234567890-abc123",
  "timestamp_decision": "2024-12-06T10:00:00Z",
  "decision_source": "llm_analysis",
  "intent": "restart_service",
  "target": "nginx",
  "validated_command": "systemctl restart nginx",
  "status": "pending_execution"
}
```

**Après exécution** :
```json
{
  "timestamp_execution": "2024-12-06T10:00:05Z",
  "status": "success",
  "execution_result": {
    "exit_code": 0,
    "stdout": "...",
    "stderr": ""
  }
}
```

## Configuration

### Intents (config/intents.json)

```json
{
  "restart_service": {
    "command_template": "systemctl restart {target}",
    "valid_targets": ["nginx", "php8.1-fpm", "postgresql"],
    "risk_level": "low",
    "requires_approval": false,
    "cooldown_seconds": 300
  }
}
```

### Targets (config/targets.json)

Fichier séparé pour faciliter la mise à jour des services autorisés.

## Métriques

| Métrique | Objectif | Mesure |
|----------|----------|--------|
| Temps N0 (Fast Track) | < 10s | Monitoring workflow |
| Temps N1 (LLM) | < 120s | Monitoring workflow |
| Taux de Fast Track | > 60% | Compteur N0/total |
| Faux positifs | 0 | Audit trail |
| Injections bloquées | 100% | Security alerts |

## Déploiement

1. Importer les workflows N8N
2. Configurer les credentials (SSH, SMTP)
3. Créer la collection Qdrant `incidents`
4. Configurer AuraCore avec les intents
5. Activer les workflows
6. Configurer Uptime Kuma webhooks

## Troubleshooting

### Le LLM génère un intent invalide
→ L'Intent Engine rejette et escalade. Vérifier les logs.

### Rate limit atteint
→ Attendre 1h ou investiguer la cause des alertes répétées.

### Fast Track ne fonctionne pas
→ Vérifier que Qdrant contient des incidents avec `resolution_success: true`.
