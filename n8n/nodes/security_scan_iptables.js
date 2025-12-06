/**
 * Security Scan - Verify iptables Rules
 * 100% déterministe, 0 LLM
 * 
 * Vérifie que les ports critiques ont des règles DROP
 * pour bloquer l'accès externe
 */

// Configuration - Ports qui DOIVENT être protégés
const CRITICAL_PORTS = [
  {port: 11434, service: 'ollama'},
  {port: 6333, service: 'qdrant-http'},
  {port: 6334, service: 'qdrant-grpc'},
  {port: 5432, service: 'postgresql'},
  {port: 8080, service: 'n8n'},
  {port: 3000, service: 'internal-api'},
  {port: 3001, service: 'n8n-webhook'},
  {port: 8000, service: 'fastapi'},
  {port: 8001, service: 'fastapi-alt'},
  {port: 8096, service: 'whisper'},
  {port: 8100, service: 'mcp-server'},
  {port: 8200, service: 'health-api'},
  {port: 8900, service: 'auracore'}
];

// Input: résultat de iptables -L INPUT -n
const iptablesOutput = $input.first().json.stdout;

const anomalies = [];
const protectedPorts = [];
const unprotectedPorts = [];

for (const {port, service} of CRITICAL_PORTS) {
  // Check if there's a DROP rule for this port
  const dropRegex = new RegExp(`DROP.*dpt:${port}\\b`);
  
  if (dropRegex.test(iptablesOutput)) {
    protectedPorts.push({port, service, status: 'protected'});
  } else {
    unprotectedPorts.push({port, service});
    anomalies.push({
      port: port,
      service: service,
      severity: 'high',
      message: `Port ${port} (${service}) n'a pas de règle DROP dans iptables - vulnérable`
    });
  }
}

return {
  json: {
    scan_type: 'iptables_rules',
    timestamp: new Date().toISOString(),
    total_critical_ports: CRITICAL_PORTS.length,
    protected_ports: protectedPorts,
    unprotected_ports: unprotectedPorts,
    protection_rate: `${Math.round(protectedPorts.length / CRITICAL_PORTS.length * 100)}%`,
    anomalies: anomalies,
    has_anomaly: anomalies.length > 0,
    status: anomalies.length > 0 ? 'ALERT' : 'OK'
  }
};
