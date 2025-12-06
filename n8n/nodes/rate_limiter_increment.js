/**
 * Rate Limiter - Increment
 * 
 * À appeler APRÈS une exécution réussie pour incrémenter les compteurs.
 * 
 * @input {Object} incident - L'incident avec _rate_limit_key
 * @output {Object} incident - L'incident inchangé
 */

const incident = $input.first().json;
const serviceName = incident._rate_limit_key;

if (serviceName) {
  const rateLimits = $workflow.staticData.rateLimits || {};
  const globalCounter = $workflow.staticData.globalCounter || { count: 0, resetAt: Date.now() + 3600000 };
  
  if (rateLimits[serviceName]) {
    rateLimits[serviceName].count++;
  }
  globalCounter.count++;
  
  $workflow.staticData.rateLimits = rateLimits;
  $workflow.staticData.globalCounter = globalCounter;
  
  incident.rate_limit_incremented = true;
}

return [{ json: incident }];
