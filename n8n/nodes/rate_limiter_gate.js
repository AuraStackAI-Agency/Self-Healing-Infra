/**
 * Rate Limiter Gate
 * 
 * Protège contre les boucles de redémarrage et les attaques DoS.
 * Utilise le staticData du workflow pour persister les compteurs.
 * 
 * Limites :
 * - 3 actions par service par heure
 * - 10 actions globales par heure
 * 
 * @input {Object} incident - L'incident avec service_name
 * @output {Object} incident - L'incident avec rate_limit_status
 */

const incident = $input.first().json;
const serviceName = incident.service_name || 'unknown';
const now = Date.now();
const ONE_HOUR = 3600000;

// Configuration
const LIMIT_PER_SERVICE = 3;
const LIMIT_GLOBAL = 10;

// Récupérer les compteurs persistés
const rateLimits = $workflow.staticData.rateLimits || {};
const globalCounter = $workflow.staticData.globalCounter || { count: 0, resetAt: now + ONE_HOUR };

// Nettoyer les compteurs expirés
Object.keys(rateLimits).forEach(key => {
  if (rateLimits[key].resetAt < now) {
    delete rateLimits[key];
  }
});

// Reset global si expiré
if (globalCounter.resetAt < now) {
  globalCounter.count = 0;
  globalCounter.resetAt = now + ONE_HOUR;
}

// Initialiser le compteur pour ce service si nécessaire
if (!rateLimits[serviceName]) {
  rateLimits[serviceName] = { count: 0, resetAt: now + ONE_HOUR };
}

// Vérifier les limites
const serviceCount = rateLimits[serviceName].count;
const globalCount = globalCounter.count;

let blocked = false;
let blockReason = null;

if (serviceCount >= LIMIT_PER_SERVICE) {
  blocked = true;
  blockReason = `Service ${serviceName} rate limit exceeded (${serviceCount}/${LIMIT_PER_SERVICE} per hour)`;
} else if (globalCount >= LIMIT_GLOBAL) {
  blocked = true;
  blockReason = `Global rate limit exceeded (${globalCount}/${LIMIT_GLOBAL} per hour)`;
}

incident.rate_limit_status = {
  blocked: blocked,
  block_reason: blockReason,
  service_count: serviceCount,
  global_count: globalCount,
  service_remaining: LIMIT_PER_SERVICE - serviceCount,
  global_remaining: LIMIT_GLOBAL - globalCount
};

// Clé pour incrémenter après exécution
incident._rate_limit_key = serviceName;

// Persister
$workflow.staticData.rateLimits = rateLimits;
$workflow.staticData.globalCounter = globalCounter;

return [{ json: incident }];
