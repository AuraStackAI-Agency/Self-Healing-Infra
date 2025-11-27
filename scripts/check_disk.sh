#!/bin/bash
# ============================================
# AUTO-REPARE - Script de vérification disque
# ============================================
# Usage: ./check_disk.sh [threshold_percent]

set -euo pipefail

THRESHOLD="${1:-80}"
LOG_FILE="/var/log/auto-repare/disk.log"

log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} $1" | tee -a "$LOG_FILE"
}

mkdir -p /var/log/auto-repare

# Récupérer l'utilisation du disque principal
DISK_USAGE=$(df / | awk 'NR==2 {gsub("%",""); print $5}')
DISK_AVAILABLE=$(df -h / | awk 'NR==2 {print $4}')
DISK_TOTAL=$(df -h / | awk 'NR==2 {print $2}')

# Vérification des gros répertoires
TOP_DIRS=$(du -sh /var/log /var/lib/docker /tmp /opt 2>/dev/null | sort -rh | head -5)

# Status
if [[ "$DISK_USAGE" -ge "$THRESHOLD" ]]; then
    STATUS="CRITICAL"
    EXIT_CODE=1
elif [[ "$DISK_USAGE" -ge $((THRESHOLD - 10)) ]]; then
    STATUS="WARNING"
    EXIT_CODE=0
else
    STATUS="OK"
    EXIT_CODE=0
fi

log "[${STATUS}] Utilisation disque: ${DISK_USAGE}% (seuil: ${THRESHOLD}%)"

# Output JSON pour N8N
cat << EOF
{
  "status": "${STATUS}",
  "usage_percent": ${DISK_USAGE},
  "threshold_percent": ${THRESHOLD},
  "available": "${DISK_AVAILABLE}",
  "total": "${DISK_TOTAL}",
  "top_directories": [
$(echo "$TOP_DIRS" | awk '{printf "    {\"size\": \"%s\", \"path\": \"%s\"}", $1, $2; if(NR<5) printf ","; print ""}')
  ],
  "timestamp": "$(date -Iseconds)"
}
EOF

exit $EXIT_CODE
