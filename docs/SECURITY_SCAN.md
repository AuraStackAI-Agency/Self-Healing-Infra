# Security Scan Daily - Documentation V3.1

## Contexte

Ce workflow a été créé suite à l'incident du 2025-12-06 où le port Ollama (11434) exposé sur 0.0.0.0 a été exploité par un attaquant (IP: 103.192.152.218) pour installer des modèles malveillants.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ TRIGGER: Cron 03:00 UTC (quotidien)                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. SCAN PORTS EXPOSÉS                                       │
│    Commande: ss -tlnp | grep "0.0.0.0"                      │
│    Compare avec: ALLOWED_EXPOSED_PORTS = [22, 80, 443]      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. SCAN MODÈLES OLLAMA                                      │
│    Commande: curl localhost:11434/api/tags                  │
│    Compare avec: ALLOWED_MODELS (whitelist)                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. VÉRIFICATION IPTABLES                                    │
│    Vérifie règles DROP pour ports critiques                 │
│    Ports: 11434, 6333, 6334, 5432, 8080, 3000, 3001...     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. AGRÉGATION & RAPPORT                                     │
│    SI anomalie détectée → Email + Log Qdrant                │
│    SI tout OK → Log silencieux                              │
└─────────────────────────────────────────────────────────────┘
```

## Caractéristiques

| Propriété | Valeur |
|-----------|--------|
| LLM requis | **AUCUN** (100% déterministe) |
| Durée exécution | ~10 secondes |
| Fréquence | Quotidien 03:00 UTC |
| Alertes | Email si anomalie |
| Logging | Qdrant (collection: security_scans) |

## Fichiers

### Nœuds N8N

| Fichier | Description |
|---------|-------------|
| `security_scan_ports.js` | Scan des ports exposés sur 0.0.0.0 |
| `security_scan_ollama.js` | Vérification modèles Ollama |
| `security_scan_iptables.js` | Vérification règles firewall |
| `security_scan_report.js` | Agrégation et génération rapport |

### Configuration

| Fichier | Description |
|---------|-------------|
| `config/security_whitelists.example.json` | Template de configuration |

## Configuration

### 1. Copier le template

```bash
cp config/security_whitelists.example.json config/security_whitelists.json
```

### 2. Personnaliser les whitelists

```json
{
  "allowed_exposed_ports": {
    "values": [22, 80, 443]
  },
  "allowed_ollama_models": {
    "values": [
      "qwen2.5-coder:3b-instruct",
      "votre-modele:tag"
    ]
  },
  "critical_ports_require_drop": {
    "values": [
      {"port": 11434, "service": "ollama"}
    ]
  }
}
```

### 3. Mettre à jour les constantes dans les nœuds

Chaque fichier `.js` contient des constantes à adapter:

- `ALLOWED_EXPOSED_PORTS` dans `security_scan_ports.js`
- `ALLOWED_MODELS` dans `security_scan_ollama.js`
- `CRITICAL_PORTS` dans `security_scan_iptables.js`

## Niveaux de sévérité

| Niveau | Déclencheur |
|--------|-------------|
| **CRITICAL** | Modèle Ollama non autorisé |
| **HIGH** | Port critique sans règle DROP |
| **MEDIUM** | Port non-privilégié exposé |

## Intégration avec Self-Healing V3

### Nouveaux Intents de sécurité

Le fichier `intent_engine_security.js` ajoute:

**Intents READ-ONLY:**
- `audit_exposed_ports`
- `check_ollama_models`
- `verify_iptables_critical`
- `check_fail2ban_status`
- `list_ssh_connections`

**Intents ACTION:**
- `block_ip` - Bloque une IP via fail2ban
- `unblock_ip` - Débloque une IP
- `delete_ollama_model` - Supprime un modèle (avec approbation)

## Limites connues

1. **Fenêtre de 24h**: Entre deux scans, un attaquant peut agir
2. **Détection post-hoc**: Ne prévient pas l'attaque initiale
3. **Dépendance aux whitelists**: Nécessite maintenance manuelle

## Recommandations

1. **Prévention** > Détection: Configurer correctement dès le départ
2. **Docker**: Toujours bind sur `127.0.0.1`, pas `0.0.0.0`
3. **iptables**: Règles DROP par défaut pour tous les ports internes
4. **Monitoring temps réel**: Compléter avec des outils comme OSSEC ou Wazuh

## Historique

- **2025-12-06**: Création suite à l'incident Ollama
