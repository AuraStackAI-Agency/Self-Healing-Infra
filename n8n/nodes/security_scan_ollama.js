/**
 * Security Scan - Check Ollama Models
 * 100% déterministe, 0 LLM
 * 
 * Vérifie que seuls les modèles autorisés sont installés
 * Détecte les modèles suspects (potentiellement installés par un attaquant)
 */

// Configuration - Liste des modèles autorisés
const ALLOWED_MODELS = [
  'qwen2.5-coder:3b-instruct',
  'phi3:mini',
  'nomic-embed-text:latest',
  'llava:7b',
  'llama3.2-vision:11b'
];

// Input: résultat de curl localhost:11434/api/tags
let ollamaResponse;
try {
  ollamaResponse = JSON.parse($input.first().json.stdout);
} catch (e) {
  return {
    json: {
      scan_type: 'ollama_models',
      timestamp: new Date().toISOString(),
      status: 'ERROR',
      error: 'Failed to parse Ollama response - is Ollama running?',
      has_anomaly: true,
      anomalies: [{
        severity: 'medium',
        message: 'Impossible de contacter Ollama API'
      }]
    }
  };
}

const installedModels = ollamaResponse.models?.map(m => m.name) || [];
const anomalies = [];

for (const model of installedModels) {
  if (!ALLOWED_MODELS.includes(model)) {
    anomalies.push({
      model: model,
      severity: 'critical',
      message: `Modèle non autorisé détecté: ${model}`
    });
  }
}

// Vérifier les modèles suspects (patterns connus d'attaques)
const SUSPICIOUS_PATTERNS = ['gemini', 'gpt', 'claude', 'smollm'];
for (const model of installedModels) {
  const modelLower = model.toLowerCase();
  for (const pattern of SUSPICIOUS_PATTERNS) {
    if (modelLower.includes(pattern) && !ALLOWED_MODELS.includes(model)) {
      // Marquer comme suspect si pattern trouvé et pas dans whitelist
      const existing = anomalies.find(a => a.model === model);
      if (existing) {
        existing.suspicious = true;
        existing.message += ' [SUSPECT: imitation de modèle propriétaire]';
      }
    }
  }
}

return {
  json: {
    scan_type: 'ollama_models',
    timestamp: new Date().toISOString(),
    installed_models: installedModels,
    allowed_models: ALLOWED_MODELS,
    unauthorized_models: installedModels.filter(m => !ALLOWED_MODELS.includes(m)),
    anomalies: anomalies,
    has_anomaly: anomalies.length > 0,
    status: anomalies.length > 0 ? 'ALERT' : 'OK'
  }
};
