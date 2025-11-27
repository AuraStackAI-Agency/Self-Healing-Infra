#!/bin/bash
# ============================================
# AUTO-REPARE - Script de health check global
# ============================================
# Usage: ./health_check.sh

set -euo pipefail

# Collecte des métriques système
collect_metrics() {
    # CPU Load
    local load=$(cat /proc/loadavg | awk '{print $1}')
    local cpu_cores=$(nproc)

    # Memory
    local mem_info=$(free -b | awk 'NR==2')
    local mem_total=$(echo "$mem_info" | awk '{print $2}')
    local mem_used=$(echo "$mem_info" | awk '{print $3}')
    local mem_percent=$((mem_used * 100 / mem_total))

    # Disk
    local disk_info=$(df / | awk 'NR==2')
    local disk_percent=$(echo "$disk_info" | awk '{gsub("%",""); print $5}')
    local disk_available=$(echo "$disk_info" | awk '{print $4}')

    # Swap
    local swap_info=$(free -b | awk 'NR==3')
    local swap_total=$(echo "$swap_info" | awk '{print $2}')
    local swap_used=$(echo "$swap_info" | awk '{print $3}')
    local swap_percent=0
    if [[ "$swap_total" -gt 0 ]]; then
        swap_percent=$((swap_used * 100 / swap_total))
    fi

    # Uptime
    local uptime_seconds=$(awk '{print int($1)}' /proc/uptime)
    local uptime_days=$((uptime_seconds / 86400))

    # Docker containers
    local docker_running=$(docker ps -q 2>/dev/null | wc -l)
    local docker_total=$(docker ps -aq 2>/dev/null | wc -l)
    local docker_unhealthy=$(docker ps --filter "health=unhealthy" -q 2>/dev/null | wc -l)

    # Output JSON
    cat << EOF
{
  "timestamp": "$(date -Iseconds)",
  "hostname": "$(hostname)",
  "uptime_days": ${uptime_days},
  "cpu": {
    "load_1m": ${load},
    "cores": ${cpu_cores},
    "load_percent": $(echo "scale=0; $load * 100 / $cpu_cores" | bc)
  },
  "memory": {
    "used_percent": ${mem_percent},
    "total_bytes": ${mem_total},
    "used_bytes": ${mem_used}
  },
  "disk": {
    "used_percent": ${disk_percent},
    "available_kb": ${disk_available}
  },
  "swap": {
    "used_percent": ${swap_percent}
  },
  "docker": {
    "running": ${docker_running},
    "total": ${docker_total},
    "unhealthy": ${docker_unhealthy}
  },
  "status": "$(determine_status $mem_percent $disk_percent $swap_percent $docker_unhealthy)"
}
EOF
}

determine_status() {
    local mem_percent=$1
    local disk_percent=$2
    local swap_percent=$3
    local unhealthy=$4

    if [[ "$mem_percent" -ge 95 ]] || [[ "$disk_percent" -ge 95 ]] || [[ "$unhealthy" -gt 0 ]]; then
        echo "CRITICAL"
    elif [[ "$mem_percent" -ge 85 ]] || [[ "$disk_percent" -ge 85 ]] || [[ "$swap_percent" -ge 80 ]]; then
        echo "WARNING"
    else
        echo "OK"
    fi
}

# Exécution
collect_metrics
