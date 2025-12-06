/**
 * Security Scan - Check Exposed Ports
 * 100% déterministe, 0 LLM
 * 
 * Input: résultat de la commande `ss -tlnp`
 * Output: rapport des ports exposés avec anomalies
 */

// Configuration - À personnaliser selon votre infrastructure
const ALLOWED_EXPOSED_PORTS = [22, 80, 443];

// Input: résultat de la commande ss -tlnp
const ssOutput = $input.first().json.stdout;

const exposedPorts = [];
const anomalies = [];

// Parse ss output
const lines = ssOutput.split('\n').filter(line => line.includes('0.0.0.0'));

for (const line of lines) {
  // Extract port from "0.0.0.0:PORT"
  const match = line.match(/0\.0\.0\.0:(\d+)/);
  if (match) {
    const port = parseInt(match[1]);
    exposedPorts.push(port);
    
    if (!ALLOWED_EXPOSED_PORTS.includes(port)) {
      // Extract process name
      const processMatch = line.match(/users:\(\("([^"]+)"/);
      const processName = processMatch ? processMatch[1] : 'unknown';
      
      anomalies.push({
        port: port,
        process: processName,
        severity: port < 1024 ? 'high' : 'medium',
        message: `Port ${port} (${processName}) exposé sur 0.0.0.0 - non autorisé`
      });
    }
  }
}

return {
  json: {
    scan_type: 'exposed_ports',
    timestamp: new Date().toISOString(),
    total_exposed: exposedPorts.length,
    allowed_exposed: exposedPorts.filter(p => ALLOWED_EXPOSED_PORTS.includes(p)),
    unauthorized_exposed: exposedPorts.filter(p => !ALLOWED_EXPOSED_PORTS.includes(p)),
    anomalies: anomalies,
    has_anomaly: anomalies.length > 0,
    status: anomalies.length > 0 ? 'ALERT' : 'OK'
  }
};
