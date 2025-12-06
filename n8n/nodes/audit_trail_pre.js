/**
 * Audit Trail - Pre-Execution Log
 * 
 * Crée un enregistrement AVANT l'exécution de la commande.
 * Permet la traçabilité et la non-répudiation.
 * 
 * @input {Object} incident - L'incident complet
 * @output {Object} incident - L'incident avec _audit_entry
 */

const incident = $input.first().json;
const now = new Date().toISOString();

const auditEntry = {
  audit_id: `AUDIT-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
  timestamp_decision: now,
  timestamp_execution: null,
  incident_id: incident.incident_id || `INC-${Date.now()}`,
  service_name: incident.service_name,
  
  // Source de la décision
  decision_source: incident.fast_track?.eligible ? 'fast_track' : 'llm_analysis',
  
  // Détails de l'intent
  intent: incident.diagnosis?.intent || null,
  target: incident.diagnosis?.target || null,
  confidence: incident.diagnosis?.confidence || null,
  
  // Commande validée
  validated_command: incident.validated_command || null,
  
  // Statut
  status: 'pending_execution',
  execution_result: null,
  
  // Contexte RAG
  rag_match_score: incident.rag_results?.[0]?.score || null,
  rag_matched_incident: incident.fast_track?.matched_incident || null,
  
  // Rate limiting
  rate_limit_service_count: incident.rate_limit_status?.service_count || 0,
  rate_limit_global_count: incident.rate_limit_status?.global_count || 0,
  
  // Sécurité
  security_alerts: incident.security_alert ? [incident.security_alert] : []
};

incident._audit_entry = auditEntry;

return [{ json: incident }];
