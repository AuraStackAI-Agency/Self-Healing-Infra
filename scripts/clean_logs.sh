#!/bin/bash
# ============================================
# AUTO-REPARE - Script de nettoyage des logs
# ============================================
# Usage: ./clean_logs.sh [--aggressive]

set -euo pipefail

AGGRESSIVE_MODE="${1:-}"
LOG_FILE="/var/log/auto-repare/clean.log"

log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

mkdir -p /var/log/auto-repare

log "INFO" "Début du nettoyage des logs"

# Espace disque avant
BEFORE=$(df -h / | awk 'NR==2 {print $4}')
log "INFO" "Espace disponible avant: $BEFORE"

# 1. Nettoyage journald
log "INFO" "Nettoyage journald..."
journalctl --vacuum-size=500M 2>&1 | tail -5

# 2. Rotation et compression des vieux logs
log "INFO" "Rotation des logs..."
logrotate -f /etc/logrotate.conf 2>/dev/null || true

# 3. Suppression des logs anciens (> 7 jours) dans les dossiers autorisés
SAFE_LOG_DIRS=(
    "/var/log/nginx"
    "/var/log/apache2"
    "/tmp"
)

for dir in "${SAFE_LOG_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
        log "INFO" "Nettoyage de $dir (fichiers > 7 jours)..."
        find "$dir" -type f -name "*.log.*" -mtime +7 -delete 2>/dev/null || true
        find "$dir" -type f -name "*.gz" -mtime +7 -delete 2>/dev/null || true
    fi
done

# 4. Nettoyage Docker (logs et cache)
log "INFO" "Nettoyage Docker..."
docker system prune -f 2>&1 | tail -3

# 5. Mode agressif (optionnel)
if [[ "$AGGRESSIVE_MODE" == "--aggressive" ]]; then
    log "WARN" "Mode agressif activé"

    # Nettoyage cache APT
    apt-get clean 2>/dev/null || true
    apt-get autoremove -y 2>/dev/null || true

    # Nettoyage volumes Docker orphelins
    docker volume prune -f 2>&1 | tail -3

    # Journald plus agressif
    journalctl --vacuum-time=3d 2>&1 | tail -3
fi

# Espace disque après
AFTER=$(df -h / | awk 'NR==2 {print $4}')
log "INFO" "Espace disponible après: $AFTER"

log "SUCCESS" "Nettoyage terminé (Avant: $BEFORE → Après: $AFTER)"

# Output JSON pour N8N
echo "{\"success\": true, \"space_before\": \"$BEFORE\", \"space_after\": \"$AFTER\"}"
