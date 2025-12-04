# Self-Healing Infra - Dual LLM Agentic System

![Status](https://img.shields.io/badge/Status-PRODUCTION-success)
![Version](https://img.shields.io/badge/Version-3.0.0-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Architecture](https://img.shields.io/badge/Architecture-Dual_LLM-purple)

Architecture AIOps Enterprise-Grade avec systeme multi-agent : **Qwen 2.5 (Acteur)** + **Phi-3 (Critique)** avec protocole de consensus et controle humain strict.

> **v3.0** - Integration du systeme dual-LLM avec validation croisee pour les actions de remediation.

## Nouveautes v3.0

- **Architecture Multi-Agent** : Qwen propose, Phi-3 valide
- **Protocole de Consensus** : Communication inter-LLM en YAML
- **3 Niveaux d'Action** : N1 (autonome), N2 (consensus), N3 (humain)
- **Detection Faux Positifs** : Gestion automatique du flapping
- **Securite Renforcee** : Double validation pour actions sensibles

## Architecture Dual-LLM

```
                         UPTIME KUMA
                              |
                         [ALERTE DOWN]
                              |
                              v
                    +------------------+
                    |  Main Supervisor |
                    +--------+---------+
                             |
          +------------------+------------------+
          |                                     |
          v                                     v
    +----------+                         +----------+
    | RAG Fast |                         | Flapping |
    | Track    |                         | Detect   |
    +----+-----+                         +----+-----+
         |                                    |
         | (score > 0.85)                     | (HTTP 2xx?)
         v                                    v
    [EXECUTE]                            [FALSE_POS]
                                              |
                                              | (non)
                                              v
                              +---------------------------+
                              |    CONSENSUS VALIDATOR    |
                              +---------------------------+
                              |                           |
                              v                           v
                      +-------------+             +-------------+
                      |  Qwen 2.5   |    YAML    |  Phi-3      |
                      |  (Acteur)   | ---------> |  (Critique) |
                      | 3B params   |            | 3.8B params |
                      +------+------+             +------+------+
                             |                           |
                             |    +---------------+      |
                             +--->|   CONSENSUS   |<-----+
                                  +-------+-------+
                                          |
                    +---------------------+---------------------+
                    |                     |                     |
                    v                     v                     v
             [APPROVED]            [REJECTED]            [ESCALATE]
                    |                     |                     |
                    v                     v                     v
              +----------+         +------------+        +-----------+
              | EXECUTE  |         | CONFLIT IA |        | HUMAIN N3 |
              | ACTION   |         | NOTIFICATION|        | VALIDATION|
              +----------+         +------------+        +-----------+
```

## Niveaux d'Action (CAPABILITIES)

| Niveau | Description | Validation | Exemples |
|--------|-------------|------------|----------|
| **N1** | Autonome (lecture seule) | Auto si conf >= 0.8 | `curl -I`, `systemctl status`, `docker ps` |
| **N2** | Remediation | Consensus Qwen+Phi | `systemctl restart`, `docker restart`, `apt-get clean` |
| **N3** | Escalade humaine | Toujours | Modif config, SQL, firewall |

## Protocole de Consensus (YAML)

Les LLM communiquent en YAML, converti en JSON par N8N :

### Proposition Qwen (Acteur)
```yaml
---
cause: "Port 80 deja utilise par un autre processus"
confidence: 0.90
action_command: "systemctl restart nginx"
action_type: restart
action_level: 2
is_safe: true
explanation: "Le port est bloque par une instance zombie"
logs_summary: "nginx bind() failed port 80"
expected_result: "nginx operationnel, port 80 en ecoute"
```

### Validation Phi (Critique)
```yaml
---
decision: APPROVED
checks:
  whitelist_valid: true
  diagnostic_justified: true
  no_collateral_risk: true
  action_coherent: true
confidence: 0.95
reason: "Action appropriee et reversible"
alternative: null
```

## Stack Technique

| Composant | Role | Port | Ressources |
|-----------|------|------|------------|
| **N8N** | Orchestrateur workflows | 5678 | - |
| **Uptime Kuma** | Monitoring & alertes | 3001 | - |
| **Ollama** | LLM Server | 11434 | 8-16GB RAM |
| **Qwen 2.5** | Acteur (diagnostic) | - | 1.9GB |
| **Phi-3 Mini** | Critique (validation) | - | 2.2GB |
| **Qdrant** | Vector Store (RAG) | 6333 | - |
| **PostgreSQL** | Base N8N | 5432 | - |
| **Redis** | Queue workers | 6379 | 512MB |

## Workflows N8N

### 1. Main Supervisor (v3)
- Reception des alertes Uptime Kuma
- Detection des faux positifs (flapping)
- Fast-track RAG pour solutions connues
- Delegation au Consensus Validator

### 2. Consensus Validator (NOUVEAU)
- Appel Qwen pour proposition (YAML)
- Conversion YAML -> JSON
- Appel Phi pour validation (YAML)
- Decision finale (APPROVED/REJECTED/ESCALATE)

### 3. Action Executor
- Execution des actions validees via SSH
- Verification du retablissement
- Stockage dans RAG (apprentissage)
- Notification succes/echec

### 4. Notification Manager
- Emails HTML differencies par type
- Liens de validation pour N2/N3
- Gestion des conflits IA

## Securite

### Whitelist Stricte (safe_commands.json)
```json
{
  "level_2_commands": {
    "service_management": {
      "allowed_services": ["nginx", "apache2", "postgresql", "redis", "docker", "ssh"]
    },
    "disk_cleanup": {
      "allowed_operations": ["apt-get clean", "docker system prune -f", "journalctl --vacuum-size=500M"]
    }
  },
  "blocked_patterns": ["rm -rf", "chmod 777", "DROP DATABASE", "iptables -F"]
}
```

### Blacklist Absolue
- `rm -rf`, `dd if=`, `mkfs`, `fdisk`
- `chmod 777`, `chown -R root`
- `DROP DATABASE`, `TRUNCATE`
- `wget|sh`, `curl|bash`
- `iptables -F`, `ufw disable`

## Installation

### Prerequis
- VPS Linux (Debian/Ubuntu) - 8 vCPUs, 32GB RAM minimum
- Docker et Docker Compose
- N8N installe

### Quick Start

```bash
# Cloner le repo
git clone https://github.com/AuraStackAI-Agency/Self-Healing-Infra.git
cd Self-Healing-Infra

# Configurer l'environnement
cp .env.template .env
# Editer .env avec vos valeurs

# Demarrer les services
docker-compose up -d

# Les modeles LLM seront telecharges automatiquement
# Qwen 2.5 Coder 3B (1.9GB)
# Phi-3 Mini 3.8B (2.2GB)
# Nomic Embed Text (embeddings)

# Verifier les modeles
curl http://localhost:11434/api/tags
```

### Import Workflows N8N

1. Importer `workflows/Main_Supervisor.json`
2. Importer `workflows/Consensus_Validator.json`
3. Importer `workflows/Action_Executor.json`
4. Importer `workflows/Notification_Manager.json`
5. Configurer les credentials SSH et SMTP

## Structure du Projet

```
self-healing-infra/
├── workflows/                    # Workflows N8N
│   ├── Main_Supervisor.json      # Orchestrateur principal
│   ├── Consensus_Validator.json  # Validation Qwen+Phi
│   ├── Action_Executor.json      # Execution et verification
│   └── Notification_Manager.json # Emails et validation
├── config/
│   ├── safe_commands.json        # Whitelist v3 (3 niveaux)
│   └── monitors.json             # Monitors Uptime Kuma
├── prompts/
│   ├── qwen_n1_analyst.md        # Prompt Acteur (YAML)
│   ├── phi3_critic.md            # Prompt Critique (YAML)
│   └── claude_n2_expert.md       # Prompt fallback N2
├── docs/
│   └── ARCHITECTURE_V2.md        # Documentation technique
├── scripts/                      # Utilitaires
├── CAPABILITIES.md               # Definition des 3 niveaux
├── CHANGELOG.md                  # Historique des versions
├── docker-compose.yml            # Stack complete
├── .env.template                 # Configuration
└── README.md
```

## Metriques

| Metrique | Cible | Description |
|----------|-------|-------------|
| Detection | < 60s | Uptime Kuma polling |
| Resolution N1 | < 4min | Qwen analysis + execution |
| Consensus rate | > 90% | Qwen-Phi agreement |
| Faux positifs | < 5% | Flapping detection |
| Escalade | < 20% | Actions requiring human |

## Documentation

- [CAPABILITIES.md](CAPABILITIES.md) - Definition des niveaux d'action
- [ARCHITECTURE_V2.md](docs/ARCHITECTURE_V2.md) - Architecture technique
- [CHANGELOG.md](CHANGELOG.md) - Historique des versions

## Roadmap

- [x] Architecture multi-workflows v2
- [x] Integration dual-LLM (Qwen + Phi-3)
- [x] Protocole consensus YAML
- [x] Detection faux positifs (flapping)
- [x] 3 niveaux d'action avec whitelist
- [x] Docker Compose complet
- [ ] Dashboard monitoring
- [ ] Metriques Prometheus
- [ ] Tests automatises

## Licence

MIT - Voir [LICENSE](LICENSE)

---

**Projet realise par AuraStack AI Agency**

*Architecture d'infrastructures autonomes et intelligentes*
