# IA Self-Healing Capabilities: Qwen 2.5 (3B) & Phi-3 (3.8B)

> Ce document definit le perimetre strict des actions autorisees pour le systeme multi-agent (Acteur: Qwen / Critique: Phi).

## Architecture Multi-Agent

```
                    +------------------+
                    |   Uptime Kuma    |
                    |   (Monitoring)   |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |  Main Supervisor |
                    +--------+---------+
                             |
              +--------------+--------------+
              |                             |
              v                             v
    +------------------+          +------------------+
    |  Qwen 2.5 (3B)   |          |  Phi-3 (3.8B)    |
    |     ACTEUR       |   --->   |     CRITIQUE     |
    | (Propose action) |          | (Valide action)  |
    +------------------+          +------------------+
              |                             |
              +-------------+---------------+
                            |
                            v
                    +------------------+
                    |    CONSENSUS?    |
                    +--------+---------+
                    |YES              |NO
                    v                 v
            +------------+    +------------------+
            |  EXECUTE   |    | ESCALADE HUMAINE |
            +------------+    +------------------+
```

---

## NIVEAU 1 : Actions Autonomes (Safe & Read-Only)

**Critere** : Zero risque, zero modification persistante, reversibilite immediate.

### 1.1 Diagnostic & Tri (Log Analysis)

| Attribut | Valeur |
|----------|--------|
| **Capacite** | Lire et correler les logs (Syslog, Docker, Nginx, App) sur une fenetre de 5 minutes |
| **Objectif** | Identifier la nature de l'incident (Infra vs Applicatif vs Faux Positif) |
| **Output** | Qualification de l'incident |

**Format de sortie :**
```json
{
  "severity": "LOW|MEDIUM|HIGH|CRITICAL",
  "category": "NETWORK|DISK|APP|SERVICE|CERTIFICATE|UNKNOWN",
  "confidence": 0.85,
  "requires_action": true
}
```

### 1.2 Sanity Checks (Verifications Actives)

**Capacite** : Executer des commandes de lecture whitelistees.

**Commandes Autorisees :**
| Commande | Description |
|----------|-------------|
| `curl -I <endpoint>` | Test connectivite HTTP (headers only) |
| `systemctl status <service>` | Etat d'un service systemd |
| `docker ps` | Liste des conteneurs actifs |
| `docker logs --tail 50 <container>` | 50 dernieres lignes de logs |
| `df -h` | Espace disque |
| `free -m` | Memoire disponible |
| `openssl x509 -enddate -noout -in <file>` | Date expiration certificat SSL |
| `ss -tlnp` | Ports en ecoute |
| `ping -c 4 <host>` | Test connectivite reseau |
| `cat /proc/loadavg` | Charge systeme |

### 1.3 Gestion des "Flapping" (Fausses Alertes)

| Attribut | Valeur |
|----------|--------|
| **Capacite** | Comparer l'etat actuel avec l'alerte recue |
| **Action** | Si le service repond `200 OK` lors du check, fermer l'incident |
| **Tag** | `FALSE_POSITIVE` |

**Criteres de detection faux positif :**
- Service repond HTTP 2xx/3xx apres alerte DOWN
- Delai < 60 secondes entre alerte et verification
- Pas d'erreurs dans les logs recents

---

## NIVEAU 2 : Actions de Remediation (Conditionnelles)

**Critere** : Modification systeme limitee, scriptee, validation croisee (Qwen+Phi) **OBLIGATOIRE**.

### 2.1 Redemarrage de Services (Service Recovery)

| Attribut | Valeur |
|----------|--------|
| **Condition** | Le service est confirme `dead` ou `unresponsive` (timeout > 30s) |
| **Validation** | Consensus Qwen + Phi requis |

**Commandes Autorisees :**
```bash
# Systemd
systemctl restart <service_name>
systemctl reload <service_name>
systemctl start <service_name>
systemctl stop <service_name>

# Docker
docker restart <container_id>
docker start <container_id>
docker stop <container_id>

# PM2 (Node.js)
pm2 restart <id>
pm2 reload <id>
```

**Services Autorises :**
- `nginx`
- `apache2`
- `postgresql`
- `redis`
- `docker`
- `ssh`

**INTERDIT :** `kill -9` sans tentative de `SIGTERM` prealable.

### 2.2 Nettoyage de Maintenance (Disk/Cache)

| Attribut | Valeur |
|----------|--------|
| **Condition** | Disque > 90% OU Cache corrompu suspecte |
| **Validation** | Consensus Qwen + Phi requis |

**Chemins Autorises (Whitelist stricte) :**
| Chemin | Type | Condition |
|--------|------|-----------|
| `/var/log/*.gz` | Logs rotates | Fichiers comprimes uniquement |
| `/var/log/nginx/*.gz` | Logs Nginx | Fichiers comprimes uniquement |
| `/var/log/apache2/*.gz` | Logs Apache | Fichiers comprimes uniquement |
| `/tmp/*` | Temporaires | Fichiers > 24h uniquement |
| `/var/cache/apt/archives/*.deb` | Cache APT | Tous |

**Commandes Autorisees :**
```bash
# APT
apt-get clean
apt-get autoremove -y

# Docker
docker system prune -f          # Images/conteneurs pendants
docker volume prune -f          # Volumes non utilises

# Journald
journalctl --vacuum-size=500M
journalctl --vacuum-time=7d
```

### 2.3 Renouvellement Certificats (SSL/TLS)

| Attribut | Valeur |
|----------|--------|
| **Condition** | Certificat expirant < 7 jours ET port 80 accessible |
| **Validation** | Consensus Qwen + Phi requis |
| **Fallback** | Si echec, escalade immediate (pas de modification Nginx) |

**Commande Autorisee :**
```bash
certbot renew --non-interactive
```

**Verification pre-action :**
```bash
# Verifier expiration
openssl x509 -enddate -noout -in /etc/letsencrypt/live/<domain>/cert.pem

# Verifier port 80
curl -I http://localhost:80
```

---

## NIVEAU 3 : Escalade Humaine (Hors Perimetre IA)

**Critere** : Actions complexes, irreversibles ou necessitant une comprehension metier.

### Actions TOUJOURS Escaladees

| Categorie | Exemples |
|-----------|----------|
| **Fichiers de configuration** | `.conf`, `.env`, `.json`, `.yaml`, `.toml` |
| **Mises a jour majeures** | `apt upgrade`, `docker pull` (nouvelles versions majeures) |
| **Operations SQL d'ecriture** | `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE` |
| **Gestion des Cles API** | Rotation, generation, revocation |
| **Modifications Reseau** | Regles Firewall UFW, Routage IP, iptables |
| **Gestion des utilisateurs** | `useradd`, `usermod`, `userdel`, passwd |
| **Montage systeme** | `mount`, `umount`, `fstab` |
| **Permissions critiques** | `chmod 777`, `chown root`, permissions recursives |

### Signaux d'Escalade Automatique

L'IA doit escalader immediatement si :
- Confidence < 0.6
- Plusieurs services affectes simultanement
- Logs indiquent compromission potentielle
- Erreur inconnue / non documentee
- Action requise hors whitelist
- Pattern de corruption de donnees detecte

---

## Protocole de Validation (Consensus)

Toute action de **Niveau 2** doit suivre ce protocole strict :

### Etape 1 : Proposition (Qwen - Acteur)

```yaml
# Format de proposition Qwen
action: systemctl restart nginx
reason: Service failed binding port 80
confidence: 0.85
category: SERVICE
level: 2
```

### Etape 2 : Validation (Phi - Critique)

**Checks obligatoires :**

| Check | Description | Critere |
|-------|-------------|---------|
| **Whitelist** | La commande est-elle dans la whitelist ? | PASS/FAIL |
| **Justification** | Le diagnostic justifie-t-il l'action ? | PASS/FAIL |
| **Risque colateral** | Y a-t-il un risque colateral evident ? | PASS/FAIL |
| **Coherence** | L'action est-elle coherente avec les logs ? | PASS/FAIL |

### Etape 3 : Decision

```
+------------------+     +------------------+
|  Phi: APPROVED   | --> | N8N: EXECUTE     |
+------------------+     +------------------+

+------------------+     +------------------+
|  Phi: REJECTED   | --> | ALERTE HUMAINE   |
|  (Conflit IA)    |     | (Email + Log)    |
+------------------+     +------------------+
```

### Format de Reponse Phi

```json
{
  "decision": "APPROVED|REJECTED",
  "checks": {
    "whitelist_valid": true,
    "diagnostic_justified": true,
    "no_collateral_risk": true,
    "action_coherent": true
  },
  "confidence": 0.90,
  "reason": "Action validated: service restart is appropriate for port binding failure",
  "alternative": null
}
```

---

## Matrice de Decision

| Niveau | Qwen Confidence | Phi Decision | Action |
|--------|-----------------|--------------|--------|
| N1 | >= 0.8 | N/A | Execute automatiquement |
| N1 | < 0.8 | N/A | Escalade N2 |
| N2 | >= 0.6 | APPROVED | Execute |
| N2 | >= 0.6 | REJECTED | Escalade humaine |
| N2 | < 0.6 | N/A | Escalade humaine |
| N3 | N/A | N/A | Toujours escalade |

---

## Commandes Bloquees (Blacklist Absolue)

Ces patterns sont **TOUJOURS** refuses, sans exception :

```bash
# Destruction systeme
rm -rf /
rm -rf /*
rm -rf ~/*
dd if=/dev/zero of=/dev/sda
mkfs.*
fdisk.*
> /dev/sda

# Permissions dangereuses
chmod 777 /
chmod -R 777 /
chown -R root:root /

# Fork bomb
:(){ :|:& };:

# Execution distante non autorisee
wget.*|.*sh
curl.*|.*sh
eval
exec

# Base de donnees
DROP DATABASE
DROP TABLE
TRUNCATE TABLE
DELETE FROM.*WHERE 1=1

# Reseau
iptables -F
ufw disable
```

---

## Metriques de Performance

| Metrique | Cible | Mesure |
|----------|-------|--------|
| **Temps detection** | < 60s | Uptime Kuma polling |
| **Temps N1 resolution** | < 4min | Qwen analysis + execution |
| **Taux faux positifs** | < 5% | Flapping detection |
| **Consensus rate** | > 90% | Qwen-Phi agreement |
| **Escalade rate** | < 20% | Actions requiring human |

---

## Changelog

| Version | Date | Description |
|---------|------|-------------|
| 3.0.0 | 2025-12-04 | Integration dual-LLM (Qwen + Phi) avec consensus |
| 2.2.0 | 2025-12-01 | Production release avec validation humaine |
| 2.0.0 | 2025-11-27 | Architecture multi-niveaux initiale |
