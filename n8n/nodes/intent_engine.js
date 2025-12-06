/**
 * Intent & Target Validation Engine V3
 * 
 * Ce nœud est le cœur de la sécurité du système Self-Healing.
 * Il valide les intents générés par le LLM et les mappe vers des commandes sécurisées.
 * 
 * RÈGLE FONDAMENTALE : Le LLM ne génère JAMAIS de commande, seulement des intents.
 * 
 * @input {Object} incident - L'incident avec diagnosis.intent et diagnosis.target
 * @output {Object} incident - L'incident avec validated_command ou rejection
 */

// === CONFIGURATION ===
// À personnaliser selon votre infrastructure

const INTENT_MAP = {
  "restart_service": {
    template: (target) => `systemctl restart ${target}`,
    validTargets: ["nginx", "php8.1-fpm", "php8.2-fpm", "postgresql", "redis-server", "docker"],
    riskLevel: "low",
    requiresApproval: false
  },
  "stop_service": {
    template: (target) => `systemctl stop ${target}`,
    validTargets: ["nginx", "php8.1-fpm", "php8.2-fpm"],
    riskLevel: "medium",
    requiresApproval: true
  },
  "docker_restart": {
    template: (target) => `docker restart ${target}`,
    // Remplacez par vos noms de containers
    validTargets: ["app-main", "app-worker", "redis", "ollama", "qdrant"],
    riskLevel: "low",
    requiresApproval: false
  },
  "docker_stop": {
    template: (target) => `docker stop ${target}`,
    validTargets: ["app-worker"],
    riskLevel: "medium",
    requiresApproval: true
  },
  "clear_system_logs": {
    template: () => `journalctl --vacuum-size=500M`,
    validTargets: [],
    riskLevel: "low",
    requiresApproval: false
  },
  "docker_prune": {
    template: () => `docker system prune -f`,
    validTargets: [],
    riskLevel: "medium",
    requiresApproval: true
  },
  "docker_logs": {
    template: (target) => `docker logs --tail 100 ${target}`,
    validTargets: ["app-main", "app-worker", "ollama", "qdrant", "redis", "postgres"],
    riskLevel: "none",
    requiresApproval: false
  },
  "check_disk": {
    template: () => `df -h /`,
    validTargets: [],
    riskLevel: "none",
    requiresApproval: false
  },
  "check_memory": {
    template: () => `free -h`,
    validTargets: [],
    riskLevel: "none",
    requiresApproval: false
  },
  "ESCALATE": {
    template: () => null,
    validTargets: [],
    riskLevel: "none",
    requiresApproval: false
  }
};

// Patterns bloqués - Protection contre injection
const BLOCKED_PATTERNS = [';', '|', '&&', '||', '`', '$(', '${', '>', '<', '\n', '\r'];

// === LOGIC ===

const incident = $input.first().json;
const diagnosis = incident.diagnosis || incident.level_1_diagnosis || {};

const intent = diagnosis.intent || '';
const target = diagnosis.target || '';
const confidence = diagnosis.confidence || 0;

let validation = {
  valid: false,
  command: null,
  rejection_reason: null,
  risk_level: 'unknown',
  requires_approval: false,
  escalate: false
};

// Step 1: Check if intent exists in whitelist
if (!INTENT_MAP[intent]) {
  validation.rejection_reason = `Unknown intent: "${intent}". Not in whitelist.`;
  validation.escalate = true;
}
// Step 2: Check for injection patterns in target
else if (target && BLOCKED_PATTERNS.some(p => target.includes(p))) {
  validation.rejection_reason = `SECURITY ALERT: Blocked pattern detected in target "${target}"`;
  validation.escalate = true;
  incident.security_alert = {
    type: 'injection_attempt',
    target: target,
    timestamp: new Date().toISOString()
  };
}
// Step 3: Check if target is valid for this intent
else if (INTENT_MAP[intent].validTargets.length > 0 && !INTENT_MAP[intent].validTargets.includes(target)) {
  validation.rejection_reason = `Invalid target "${target}" for intent "${intent}". Valid: ${INTENT_MAP[intent].validTargets.join(', ')}`;
  validation.escalate = true;
}
// Step 4: Check confidence threshold
else if (confidence < 0.6 && intent !== 'ESCALATE') {
  validation.rejection_reason = `Confidence too low (${confidence}). Threshold: 0.6`;
  validation.escalate = true;
}
// Step 5: Handle ESCALATE intent
else if (intent === 'ESCALATE') {
  validation.valid = false;
  validation.escalate = true;
  validation.rejection_reason = 'LLM requested escalation';
}
// Step 6: All checks passed - generate command
else {
  const intentConfig = INTENT_MAP[intent];
  validation.valid = true;
  validation.command = intentConfig.template(target);
  validation.risk_level = intentConfig.riskLevel;
  validation.requires_approval = intentConfig.requiresApproval;
}

incident.intent_validation = validation;
incident.validated_command = validation.command;

return [{ json: incident }];
