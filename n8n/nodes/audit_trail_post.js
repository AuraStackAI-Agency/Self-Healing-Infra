/**
 * Audit Trail - Post-Execution Log
 * 
 * Met à jour l'enregistrement APRÈS l'exécution de la commande.
 * Capture le résultat pour forensics et feedback loop.
 * 
 * @input {Object} incident - L'incident avec _audit_entry
 * @output {Object} incident - L'incident avec audit_complete
 */

const incident = $input.first().json;

// Récupérer le résultat SSH (adapter le nom du nœud selon votre workflow)
let execResult = { exitCode: -1, stdout: '', stderr: 'No execution result found' };
try {
  execResult = $('SSH Execute').first().json;
} catch (e) {
  // Nœud SSH non trouvé, utiliser les valeurs par défaut
}

const auditEntry = incident._audit_entry;

if (auditEntry) {
  auditEntry.timestamp_execution = new Date().toISOString();
  auditEntry.status = execResult.exitCode === 0 ? 'success' : 'failed';
  auditEntry.execution_result = {
    exit_code: execResult.exitCode,
    stdout: (execResult.stdout || '').substring(0, 500),
    stderr: (execResult.stderr || '').substring(0, 500)
  };
}

incident.audit_complete = auditEntry;

// Nettoyer les données temporaires
delete incident._audit_entry;
delete incident._rate_limit_key;

return [{ json: incident }];
