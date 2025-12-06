# Changelog

Toutes les modifications notables de ce projet sont documentées ici.

## [3.0.0] - 2024-12-06

### ⚠️ BREAKING CHANGES

- Le LLM ne génère plus de commandes shell, seulement des intents
- Nouveau format de réponse Qwen requis
- Nouveaux nœuds N8N obligatoires

### Ajouté

- **Intent Engine** : Validation et mapping des intents vers commandes sécurisées
- **Fast Track Gate** : Bypass LLM si solution connue (RAG > 0.85)
- **Rate Limiter** : Protection anti-boucle (3/h/service, 10/h global)
- **Audit Trail** : Logging complet avant/après exécution
- **Injection Blocker** : Détection patterns dangereux (`;`, `|`, `&&`, etc.)
- **Qdrant Feedback** : Enrichissement automatique du RAG
- Documentation complète V3

### Modifié

- Prompt Qwen restructuré pour format Intent
- Architecture des workflows simplifiée
- Séparation code/configuration

### Supprimé

- Dual-LLM consensus systématique (remplacé par validation code)
- Génération directe de commandes par LLM

### Sécurité

- Score sécurité : 5/10 → 7.5/10
- Élimination du risque d'hallucination de commande
- Protection contre prompt injection
- Whitelist stricte des targets

## [2.2.0] - 2024-11

### Ajouté

- Architecture Dual-LLM (Qwen + Phi consensus)
- Intégration AuraCore basique

### Problèmes identifiés

- Biais corrélés entre Qwen et Phi
- Sécurité théâtre (consensus ≠ correction)
- Overhead temps significatif

## [2.1.0] - 2024-10

### Ajouté

- Notifications email différenciées
- Support HTTP 3xx (redirections)
- Escalade N2 avec Claude

## [2.0.0] - 2024-09

### Ajouté

- Architecture multi-workflows
- Intégration Uptime Kuma
- RAG avec Qdrant

## [1.0.0] - 2024-08

### Ajouté

- Version initiale
- Workflow monolithique
- Qwen local uniquement
