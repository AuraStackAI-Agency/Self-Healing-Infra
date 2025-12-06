# Changelog

Toutes les modifications notables de ce projet sont documentées ici.

## [3.1.0] - 2025-12-06

### Contexte

Suite à l'incident de sécurité du 2025-12-06 (exploitation du port Ollama 11434 par IP 103.192.152.218), ajout de capacités de détection proactive.

### Ajouté

- **Security Scan Daily** : Nouveau workflow de scan quotidien (100% déterministe, 0 LLM)
  - `security_scan_ports.js` : Détection des ports exposés sur 0.0.0.0
  - `security_scan_ollama.js` : Vérification des modèles installés vs whitelist
  - `security_scan_iptables.js` : Vérification des règles DROP pour ports critiques
  - `security_scan_report.js` : Agrégation et génération de rapport

- **Security Intents V3.1** : Extension de l'Intent Engine
  - Intents READ-ONLY : `audit_exposed_ports`, `check_ollama_models`, `verify_iptables_critical`, `check_fail2ban_status`, `list_ssh_connections`
  - Intents ACTION : `block_ip`, `unblock_ip`, `delete_ollama_model`

- **Configuration whitelists** : `config/security_whitelists.example.json`

- **Documentation** : `docs/SECURITY_SCAN.md`

### Sécurité

- Détection quotidienne des ports exposés non autorisés
- Détection des modèles Ollama suspects/non autorisés
- Vérification automatique des règles iptables
- Alertes email en cas d'anomalie

### Limites documentées

- Fenêtre de 24h entre les scans
- Détection post-hoc (ne prévient pas l'attaque initiale)
- La vraie sécurité = configuration correcte dès le départ

## [3.0.0] - 2025-12-06

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
