/**
 * Security Scan - Generate Report
 * Agrège les résultats des 3 scans et génère un rapport
 * 
 * Inputs attendus (via $() references):
 * - 'Scan Ports': résultat de security_scan_ports.js
 * - 'Scan Ollama': résultat de security_scan_ollama.js  
 * - 'Scan Iptables': résultat de security_scan_iptables.js
 */

const portsScan = $('Scan Ports').first().json;
const ollamaScan = $('Scan Ollama').first().json;
const iptablesScan = $('Scan Iptables').first().json;

// Agrégation des anomalies avec catégorie
const allAnomalies = [
  ...portsScan.anomalies.map(a => ({...a, category: 'exposed_ports'})),
  ...ollamaScan.anomalies.map(a => ({...a, category: 'ollama_models'})),
  ...iptablesScan.anomalies.map(a => ({...a, category: 'iptables_rules'}))
];

const overallStatus = allAnomalies.length > 0 ? 'ALERT' : 'OK';
const hasCritical = allAnomalies.some(a => a.severity === 'critical');
const hasHigh = allAnomalies.some(a => a.severity === 'high');

const report = {
  scan_id: `sec-${Date.now()}`,
  timestamp: new Date().toISOString(),
  overall_status: overallStatus,
  severity_level: hasCritical ? 'CRITICAL' : (hasHigh ? 'HIGH' : (allAnomalies.length > 0 ? 'MEDIUM' : 'NONE')),
  summary: {
    ports: portsScan.status,
    ollama: ollamaScan.status,
    iptables: iptablesScan.status
  },
  stats: {
    total_anomalies: allAnomalies.length,
    critical_count: allAnomalies.filter(a => a.severity === 'critical').length,
    high_count: allAnomalies.filter(a => a.severity === 'high').length,
    medium_count: allAnomalies.filter(a => a.severity === 'medium').length
  },
  anomalies: allAnomalies,
  details: {
    ports: portsScan,
    ollama: ollamaScan,
    iptables: iptablesScan
  }
};

// Format email si anomalies détectées
if (overallStatus === 'ALERT') {
  const severityEmoji = hasCritical ? '🚨' : (hasHigh ? '⚠️' : '📋');
  
  report.email_subject = `${severityEmoji} [SECURITY ${report.severity_level}] ${allAnomalies.length} anomalie(s) détectée(s)`;
  
  report.email_body = `
# Rapport de Sécurité - ${new Date().toLocaleString('fr-FR')}

## Statut Global: ${overallStatus}

| Catégorie | Statut |
|-----------|--------|
| Ports exposés | ${portsScan.status} |
| Modèles Ollama | ${ollamaScan.status} |
| Règles iptables | ${iptablesScan.status} |

## Statistiques

- Total anomalies: **${allAnomalies.length}**
- Critiques: ${report.stats.critical_count}
- Hautes: ${report.stats.high_count}
- Moyennes: ${report.stats.medium_count}

## Anomalies Détectées

${allAnomalies.map(a => `- [${a.severity.toUpperCase()}] [${a.category}] ${a.message}`).join('\n')}

---
*Self-Healing Infrastructure - Security Scan Daily*
*Généré automatiquement le ${new Date().toISOString()}*
  `.trim();
}

return { json: report };
