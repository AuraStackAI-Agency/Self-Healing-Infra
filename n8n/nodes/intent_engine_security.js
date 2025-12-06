/**
 * Intent Engine - Security Extensions V3.1
 * Ajouts pour la détection proactive et réponse aux incidents sécurité
 * 
 * À intégrer dans intent_engine.js via:
 * Object.assign(INTENT_MAP, SECURITY_INTENTS);
 */

const SECURITY_INTENTS = {
  
  // ============================================
  // READ-ONLY INTENTS (audit - riskLevel: info)
  // ============================================
  
  "audit_exposed_ports": {
    template: () => `ss -tlnp | grep "0.0.0.0" | grep -v "127.0.0.1"`,
    validTargets: [],
    riskLevel: "info",
    category: "security_audit",
    description: "Liste les ports exposés sur toutes les interfaces",
    cooldown: 0
  },
  
  "check_ollama_models": {
    template: () => `curl -s http://localhost:11434/api/tags | jq -r '.models[].name'`,
    validTargets: [],
    riskLevel: "info",
    category: "security_audit",
    description: "Liste les modèles Ollama installés",
    cooldown: 0
  },
  
  "verify_iptables_critical": {
    template: () => `iptables -L INPUT -n | grep -E "(11434|6333|6334|5432|8080|3000|3001)"`,
    validTargets: [],
    riskLevel: "info",
    category: "security_audit",
    description: "Vérifie les règles iptables pour les ports critiques",
    cooldown: 0
  },
  
  "check_fail2ban_status": {
    template: () => `fail2ban-client status sshd`,
    validTargets: [],
    riskLevel: "info",
    category: "security_audit",
    description: "Vérifie le statut de fail2ban",
    cooldown: 0
  },
  
  "list_ssh_connections": {
    template: () => `ss -tnp state established '( sport = :22 )'`,
    validTargets: [],
    riskLevel: "info",
    category: "security_audit",
    description: "Liste les connexions SSH actives",
    cooldown: 0
  },
  
  "check_recent_ssh_failures": {
    template: () => `journalctl -u ssh --since "1 hour ago" | grep -c "Failed password" || echo "0"`,
    validTargets: [],
    riskLevel: "info",
    category: "security_audit",
    description: "Compte les échecs SSH de la dernière heure",
    cooldown: 0
  },
  
  // ============================================
  // ACTION INTENTS (avec validation stricte)
  // ============================================
  
  "block_ip": {
    template: (target) => `fail2ban-client set sshd banip ${target}`,
    validTargets: [], // Validé par regex, pas par liste
    riskLevel: "medium",
    category: "security_response",
    description: "Bloque une IP via fail2ban",
    validation: {
      pattern: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
      errorMessage: "Format IP invalide (attendu: x.x.x.x)"
    },
    requiresApproval: false, // fail2ban est réversible
    cooldown: 0 // Pas de cooldown pour le blocage
  },
  
  "unblock_ip": {
    template: (target) => `fail2ban-client set sshd unbanip ${target}`,
    validTargets: [],
    riskLevel: "low",
    category: "security_response",
    description: "Débloque une IP via fail2ban",
    validation: {
      pattern: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
      errorMessage: "Format IP invalide (attendu: x.x.x.x)"
    },
    cooldown: 0
  },
  
  "delete_ollama_model": {
    template: (target) => `curl -s -X DELETE http://localhost:11434/api/delete -d '{"name": "${target}"}'`,
    validTargets: [], // Validé dynamiquement
    riskLevel: "high",
    category: "security_response",
    description: "Supprime un modèle Ollama non autorisé",
    validation: {
      pattern: /^[a-zA-Z0-9][a-zA-Z0-9._-]*:[a-zA-Z0-9._-]+$/,
      errorMessage: "Format modèle invalide (attendu: name:tag)"
    },
    requiresApproval: true, // Demande confirmation
    cooldown: 60 // 1 minute entre suppressions
  }
};

// Fonction de validation pour les intents avec regex
function validateSecurityIntent(intent, target) {
  const intentConfig = SECURITY_INTENTS[intent];
  
  if (!intentConfig) {
    return { valid: false, error: `Intent inconnu: ${intent}` };
  }
  
  // Si l'intent a une validation regex
  if (intentConfig.validation && target) {
    if (!intentConfig.validation.pattern.test(target)) {
      return { 
        valid: false, 
        error: intentConfig.validation.errorMessage,
        intent: intent,
        target: target
      };
    }
  }
  
  return { valid: true, intent: intent, target: target };
}

// Export pour utilisation dans intent_engine.js
module.exports = { SECURITY_INTENTS, validateSecurityIntent };
