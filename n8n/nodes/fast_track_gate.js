/**
 * Fast Track Gate
 * 
 * Bypass du LLM si une solution connue avec haute confiance existe dans le RAG.
 * 
 * Conditions pour Fast Track :
 * 1. Score RAG > 0.85
 * 2. Résolution précédente réussie
 * 3. Intent dans la liste low-risk
 * 
 * @input {Object} incident - L'incident avec rag_results de Qdrant
 * @output {Object} incident - L'incident avec fast_track decision
 */

const incident = $input.first().json;
const ragResults = incident.rag_results || [];

// Configuration
const CONFIDENCE_THRESHOLD = 0.85;

// Intents autorisés en Fast Track (low risk uniquement)
const FAST_TRACK_INTENTS = [
  'restart_service',
  'docker_restart',
  'clear_system_logs',
  'check_disk',
  'check_memory'
];

let fastTrack = {
  eligible: false,
  reason: null,
  matched_incident: null,
  suggested_intent: null,
  suggested_target: null
};

// Chercher un match de haute confiance
if (ragResults.length > 0) {
  const bestMatch = ragResults[0];
  const score = bestMatch.score || 0;
  const payload = bestMatch.payload || {};
  
  if (score >= CONFIDENCE_THRESHOLD) {
    const wasSuccessful = payload.resolution_success === true;
    const intent = payload.resolution_intent || null;
    const target = payload.resolution_target || null;
    
    if (wasSuccessful && intent && FAST_TRACK_INTENTS.includes(intent)) {
      fastTrack.eligible = true;
      fastTrack.reason = `High confidence match (${(score * 100).toFixed(1)}%) with successful resolution`;
      fastTrack.matched_incident = payload.incident_id;
      fastTrack.suggested_intent = intent;
      fastTrack.suggested_target = target;
      
      // Pré-remplir le diagnosis pour l'Intent Engine
      incident.diagnosis = {
        intent: intent,
        target: target,
        confidence: score,
        source: 'fast_track_rag',
        matched_incident_id: payload.incident_id
      };
    } else if (!wasSuccessful) {
      fastTrack.reason = `Match found but previous resolution failed - need fresh analysis`;
    } else if (!FAST_TRACK_INTENTS.includes(intent)) {
      fastTrack.reason = `Match found but intent "${intent}" not allowed for fast track`;
    }
  } else {
    fastTrack.reason = `Best match score (${(score * 100).toFixed(1)}%) below threshold (${CONFIDENCE_THRESHOLD * 100}%)`;
  }
} else {
  fastTrack.reason = 'No similar incidents found in RAG';
}

incident.fast_track = fastTrack;

return [{ json: incident }];
