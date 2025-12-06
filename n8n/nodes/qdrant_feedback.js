/**
 * Qdrant Feedback Payload
 * 
 * Prépare les données pour enrichir le RAG après résolution.
 * Permet au système d'apprendre de chaque incident.
 * 
 * @input {Object} incident - L'incident avec audit_complete
 * @output {Object} incident - L'incident avec _qdrant_payload et _embedding_text
 */

const incident = $input.first().json;
const audit = incident.audit_complete || {};

const qdrantPayload = {
  incident_id: audit.incident_id,
  service_name: audit.service_name,
  error_type: incident.error_type || 'unknown',
  
  // Solution appliquée
  resolution_intent: audit.intent,
  resolution_target: audit.target,
  resolution_level: audit.decision_source === 'fast_track' ? 'N0' : 'N1',
  
  // Résultat
  resolution_success: audit.status === 'success',
  resolved_at: audit.timestamp_execution,
  
  // Métadonnées pour le RAG
  confidence_original: audit.confidence,
  execution_time_ms: audit.timestamp_execution && audit.timestamp_decision 
    ? new Date(audit.timestamp_execution) - new Date(audit.timestamp_decision)
    : null
};

// Texte pour l'embedding vectoriel
const embeddingText = [
  incident.service_name,
  incident.error_type,
  audit.intent,
  audit.status
].filter(Boolean).join(' ');

incident._qdrant_payload = qdrantPayload;
incident._embedding_text = embeddingText;

return [{ json: incident }];
