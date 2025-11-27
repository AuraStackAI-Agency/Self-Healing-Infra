#!/bin/bash
# ============================================
# AUTO-REPARE - Script de redémarrage sécurisé
# ============================================
# Usage: ./restart_service.sh <service_type> <service_name>
# Types: systemd, docker

set -euo pipefail

SERVICE_TYPE="${1:-}"
SERVICE_NAME="${2:-}"
LOG_FILE="/var/log/auto-repare/restart.log"

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

# Créer le dossier de logs si nécessaire
mkdir -p /var/log/auto-repare

# Validation des arguments
if [[ -z "$SERVICE_TYPE" ]] || [[ -z "$SERVICE_NAME" ]]; then
    log "ERROR" "Usage: $0 <systemd|docker> <service_name>"
    exit 1
fi

# Liste blanche des services autorisés
ALLOWED_SYSTEMD_SERVICES=("nginx" "apache2" "postgresql" "redis" "docker" "ssh" "fail2ban")
ALLOWED_DOCKER_CONTAINERS=("n8n-main-prod" "n8n-worker-1-prod" "n8n-worker-2-prod" "n8n-redis-prod" "n8n-postgres-prod" "uptime-kuma" "ollama" "nocodb")

# Vérification liste blanche
check_allowed() {
    local service="$1"
    local -n allowed_list="$2"

    for allowed in "${allowed_list[@]}"; do
        if [[ "$service" == "$allowed" ]]; then
            return 0
        fi
    done
    return 1
}

# Redémarrage systemd
restart_systemd() {
    local service="$1"

    if ! check_allowed "$service" ALLOWED_SYSTEMD_SERVICES; then
        log "ERROR" "Service systemd '$service' non autorisé"
        exit 2
    fi

    log "INFO" "Arrêt du service systemd: $service"
    systemctl stop "$service" 2>&1 || true
    sleep 2

    log "INFO" "Démarrage du service systemd: $service"
    systemctl start "$service" 2>&1
    sleep 3

    # Vérification
    if systemctl is-active --quiet "$service"; then
        log "SUCCESS" "Service $service redémarré avec succès"
        systemctl status "$service" --no-pager | head -10
        exit 0
    else
        log "ERROR" "Échec du redémarrage de $service"
        systemctl status "$service" --no-pager | head -20
        exit 1
    fi
}

# Redémarrage Docker
restart_docker() {
    local container="$1"

    if ! check_allowed "$container" ALLOWED_DOCKER_CONTAINERS; then
        log "ERROR" "Conteneur Docker '$container' non autorisé"
        exit 2
    fi

    # Vérifier que le conteneur existe
    if ! docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
        log "ERROR" "Conteneur '$container' non trouvé"
        exit 3
    fi

    log "INFO" "Redémarrage du conteneur Docker: $container"
    docker restart "$container" 2>&1
    sleep 5

    # Vérification
    local status=$(docker inspect -f '{{.State.Status}}' "$container" 2>/dev/null)
    if [[ "$status" == "running" ]]; then
        log "SUCCESS" "Conteneur $container redémarré avec succès"
        docker ps --filter "name=$container" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        exit 0
    else
        log "ERROR" "Échec du redémarrage de $container (status: $status)"
        docker logs --tail 20 "$container" 2>&1
        exit 1
    fi
}

# Exécution principale
case "$SERVICE_TYPE" in
    systemd)
        restart_systemd "$SERVICE_NAME"
        ;;
    docker)
        restart_docker "$SERVICE_NAME"
        ;;
    *)
        log "ERROR" "Type de service inconnu: $SERVICE_TYPE (utiliser: systemd ou docker)"
        exit 1
        ;;
esac
