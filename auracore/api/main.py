"""
AuraCore API V2 - Self-Healing Infrastructure avec Consensus AILCP
Dual-LLM: Qwen (DIAGNOSTICIAN) + Phi-3 (VALIDATOR)

Protocole AILCP (AI-to-LLM Communication Protocol) pour communication
structurée entre modèles de langage dans un système de consensus.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
import httpx
import json
import asyncio
from datetime import datetime
import logging
import random
import string
import os

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auracore")

app = FastAPI(
    title="AuraCore API V2",
    description="Self-Healing Infrastructure avec consensus dual-LLM AILCP",
    version="2.0.0"
)

# Configuration (utiliser variables d'environnement en production)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODELS = {
    "diagnostic": os.getenv("DIAGNOSTIC_MODEL", "qwen2.5-coder:3b-instruct"),
    "validation": os.getenv("VALIDATION_MODEL", "phi3:mini")
}
TIMEOUT = float(os.getenv("LLM_TIMEOUT", "180.0"))
PROMPTS_DIR = os.getenv("PROMPTS_DIR", "/opt/auracore/prompts")

# ============== AILCP PROTOCOL MODELS ==============

class SystemContext(BaseModel):
    cpu: str = "0%"
    ram: str = "0GB/0GB"
    disk: str = "0%"

class IncidentInput(BaseModel):
    incident_id: str
    service: str
    status: str = "DOWN"
    logs: List[str] = []
    system_context: SystemContext = SystemContext()
    previous_actions: List[str] = []

class AlternativeHypothesis(BaseModel):
    cause: str
    confidence: float
    action: str

class DiagnosisPayload(BaseModel):
    diagnosis_id: str
    incident_id: str
    cause: str
    confidence: float
    action_command: str
    action_type: str
    is_safe: bool
    reasoning: str
    supporting_evidence: List[str] = []
    alternative_hypotheses: List[AlternativeHypothesis] = []

class DiagnosisResponse(BaseModel):
    protocol: str = "AILCP"
    version: str = "1.0"
    message_type: str = "DIAGNOSIS"
    payload: DiagnosisPayload


class RiskAssessment(BaseModel):
    """Évaluation des risques avec validateurs robustes pour parsing LLM"""
    level: str = "MEDIUM"
    factors: List[str] = []
    mitigation: Optional[str] = ""
    
    @field_validator('level', mode='before')
    @classmethod
    def clean_level(cls, v):
        """Nettoie le niveau de risque - gère les templates littéraux"""
        if v and '|' in str(v):
            return str(v).split('|')[0]
        return v or "MEDIUM"
    
    @field_validator('mitigation', mode='before')
    @classmethod
    def clean_mitigation(cls, v):
        """Convertit None ou dict en string"""
        if v is None:
            return ""
        if isinstance(v, dict):
            return str(v)
        return str(v)
    
    @field_validator('factors', mode='before')
    @classmethod
    def clean_factors(cls, v):
        """Assure que factors est une liste de strings"""
        if v is None:
            return []
        if isinstance(v, list):
            return [str(x) if not isinstance(x, str) else x for x in v]
        return []

class ValidationPayload(BaseModel):
    """Payload de validation avec validateurs pour réponses LLM imparfaites"""
    validation_id: str
    diagnosis_id: str
    agreement: str = "PARTIAL"
    validation_score: float = 0.5
    concerns: List[str] = []
    recommendation: str = "REVIEW"
    counter_analysis: Optional[str] = None
    risk_assessment: RiskAssessment
    
    @field_validator('agreement', mode='before')
    @classmethod
    def clean_agreement(cls, v):
        """Nettoie agreement - gère les templates comme 'AGREE|PARTIAL|DISAGREE'"""
        if v and '|' in str(v):
            return "PARTIAL"  # Défaut safe si template non résolu
        valid = ["AGREE", "PARTIAL", "DISAGREE"]
        return v if v in valid else "PARTIAL"
    
    @field_validator('concerns', mode='before')
    @classmethod  
    def clean_concerns(cls, v):
        """Convertit les objets en strings dans la liste"""
        if v is None:
            return []
        if isinstance(v, list):
            result = []
            for x in v:
                if isinstance(x, dict):
                    result.append(str(x))
                else:
                    result.append(str(x))
            return result
        return []
    
    @field_validator('counter_analysis', mode='before')
    @classmethod
    def clean_counter(cls, v):
        """Convertit dict en string si nécessaire"""
        if v is None:
            return None
        if isinstance(v, dict):
            return str(v)
        return str(v)

class ValidationResponse(BaseModel):
    protocol: str = "AILCP"
    version: str = "1.0"
    message_type: str = "VALIDATION"
    payload: ValidationPayload

class ConsensusPayload(BaseModel):
    consensus_id: str
    incident_id: str
    decision: str  # AUTO_EXECUTE, EXECUTE_WITH_LOG, HUMAN_REVIEW, ESCALATE_N2
    final_action: str
    combined_confidence: float
    execute_action: bool
    requires_human: bool
    escalate_n2: bool
    diagnosis: DiagnosisPayload
    validation: ValidationPayload
    timestamp: str

class ConsensusResponse(BaseModel):
    protocol: str = "AILCP"
    version: str = "1.0"
    message_type: str = "CONSENSUS"
    payload: ConsensusPayload

# ============== HELPER FUNCTIONS ==============

def generate_id(prefix: str) -> str:
    """Génère un ID unique avec timestamp et suffixe aléatoire"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{prefix}_{timestamp}_{random_suffix}"

def load_prompt(filename: str) -> str:
    """Charge un prompt système depuis un fichier"""
    try:
        with open(f"{PROMPTS_DIR}/{filename}", 'r') as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"Prompt file not found: {filename}")
        return ""

# ============== LLM FUNCTIONS ==============

async def query_llm(model: str, prompt: str) -> str:
    """Interroge un modèle Ollama et retourne la réponse"""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }
        )
        response.raise_for_status()
        return response.json().get("response", "")

async def get_diagnosis(incident: IncidentInput) -> DiagnosisResponse:
    """Qwen DIAGNOSTICIAN analyse l'incident"""
    
    system_prompt = load_prompt("qwen_diagnostician.md")
    
    prompt = f"""{system_prompt}

---

## INCIDENT A ANALYSER

```json
{{
  "incident_id": "{incident.incident_id}",
  "service": "{incident.service}",
  "status": "{incident.status}",
  "logs": {json.dumps(incident.logs)},
  "system_context": {{
    "cpu": "{incident.system_context.cpu}",
    "ram": "{incident.system_context.ram}",
    "disk": "{incident.system_context.disk}"
  }}
}}
```

Réponds UNIQUEMENT avec le JSON AILCP DIAGNOSIS. Aucun texte avant ou après.

JSON:"""

    try:
        response = await query_llm(MODELS["diagnostic"], prompt)
        logger.info(f"Qwen raw response: {response[:500]}...")
        
        # Extraction JSON de la réponse
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        
        data = json.loads(response)
        
        # Gère format AILCP complet ou simplifié
        if "payload" in data:
            payload = data["payload"]
        else:
            payload = data
        
        diagnosis_id = payload.get("diagnosis_id", generate_id("diag"))
        
        return DiagnosisResponse(
            payload=DiagnosisPayload(
                diagnosis_id=diagnosis_id,
                incident_id=incident.incident_id,
                cause=payload.get("cause", "Unknown"),
                confidence=float(payload.get("confidence", 0.5)),
                action_command=payload.get("action_command", "ESCALATE"),
                action_type=payload.get("action_type", "ESCALATE"),
                is_safe=payload.get("is_safe", False),
                reasoning=payload.get("reasoning", ""),
                supporting_evidence=payload.get("supporting_evidence", []),
                alternative_hypotheses=[
                    AlternativeHypothesis(**h) for h in payload.get("alternative_hypotheses", [])
                ]
            )
        )
    except json.JSONDecodeError as e:
        logger.error(f"Qwen JSON parse error: {e}, response: {response[:200]}")
        return DiagnosisResponse(
            payload=DiagnosisPayload(
                diagnosis_id=generate_id("diag"),
                incident_id=incident.incident_id,
                cause="LLM response parse error",
                confidence=0.0,
                action_command="ESCALATE",
                action_type="ESCALATE",
                is_safe=False,
                reasoning=f"Could not parse Qwen response: {str(e)}",
                supporting_evidence=[]
            )
        )
    except Exception as e:
        logger.error(f"Qwen error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def validate_diagnosis(incident: IncidentInput, diagnosis: DiagnosisResponse) -> ValidationResponse:
    """Phi-3 VALIDATOR valide le diagnostic"""
    
    system_prompt = load_prompt("phi3_validator.md")
    diag = diagnosis.payload
    
    prompt = f"""{system_prompt}

---

## DIAGNOSTIC A VALIDER

**Diagnostic Qwen (DIAGNOSTICIAN):**
```json
{{
  "diagnosis_id": "{diag.diagnosis_id}",
  "cause": "{diag.cause}",
  "confidence": {diag.confidence},
  "action_command": "{diag.action_command}",
  "is_safe": {str(diag.is_safe).lower()},
  "reasoning": "{diag.reasoning}",
  "supporting_evidence": {json.dumps(diag.supporting_evidence)}
}}
```

**Alerte originale:**
```json
{{
  "service": "{incident.service}",
  "logs": {json.dumps(incident.logs[:5])},
  "system_context": {{
    "cpu": "{incident.system_context.cpu}",
    "ram": "{incident.system_context.ram}",
    "disk": "{incident.system_context.disk}"
  }}
}}
```

Réponds UNIQUEMENT avec le JSON AILCP VALIDATION. Aucun texte avant ou après.

JSON:"""

    try:
        response = await query_llm(MODELS["validation"], prompt)
        logger.info(f"Phi raw response: {response[:500]}...")
        
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        
        data = json.loads(response)
        
        if "payload" in data:
            payload = data["payload"]
        else:
            payload = data
        
        validation_id = payload.get("validation_id", generate_id("val"))
        
        risk_data = payload.get("risk_assessment", {})
        if isinstance(risk_data, str):
            risk_data = {"level": risk_data, "factors": [], "mitigation": ""}
        
        return ValidationResponse(
            payload=ValidationPayload(
                validation_id=validation_id,
                diagnosis_id=diag.diagnosis_id,
                agreement=payload.get("agreement", "PARTIAL"),
                validation_score=float(payload.get("validation_score", 0.5)),
                concerns=payload.get("concerns", []),
                recommendation=payload.get("recommendation", "REVIEW"),
                counter_analysis=payload.get("counter_analysis"),
                risk_assessment=RiskAssessment(
                    level=risk_data.get("level", "MEDIUM"),
                    factors=risk_data.get("factors", []),
                    mitigation=risk_data.get("mitigation", "")
                )
            )
        )
    except json.JSONDecodeError as e:
        logger.error(f"Phi JSON parse error: {e}, response: {response[:200]}")
        return ValidationResponse(
            payload=ValidationPayload(
                validation_id=generate_id("val"),
                diagnosis_id=diag.diagnosis_id,
                agreement="PARTIAL",
                validation_score=0.5,
                concerns=["Could not parse validation response"],
                recommendation="REVIEW",
                risk_assessment=RiskAssessment(
                    level="MEDIUM",
                    factors=["Parse error"],
                    mitigation="Manual review recommended"
                )
            )
        )
    except Exception as e:
        logger.error(f"Phi error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def compute_consensus(
    incident: IncidentInput,
    diagnosis: DiagnosisResponse,
    validation: ValidationResponse
) -> ConsensusResponse:
    """
    Calcule le consensus selon la matrice de décision AILCP
    
    Matrice de Décision:
    ┌─────────────────┬───────────────┬──────────────┬─────────────────────┐
    │ Qwen Confidence │ Phi Agreement │ Phi Score    │ Décision            │
    ├─────────────────┼───────────────┼──────────────┼─────────────────────┤
    │ >= 0.8          │ AGREE         │ >= 0.8       │ AUTO_EXECUTE        │
    │ >= 0.6          │ AGREE         │ >= 0.6       │ EXECUTE_WITH_LOG    │
    │ any             │ PARTIAL       │ any          │ HUMAN_REVIEW        │
    │ < 0.6           │ any           │ any          │ ESCALATE_N2         │
    │ any             │ DISAGREE      │ any          │ ESCALATE_N2         │
    └─────────────────┴───────────────┴──────────────┴─────────────────────┘
    """
    
    diag = diagnosis.payload
    val = validation.payload
    
    qwen_conf = diag.confidence
    phi3_agree = val.agreement
    phi3_score = val.validation_score
    is_safe = diag.is_safe
    
    # Application de la matrice de consensus
    execute_action = False
    requires_human = False
    escalate_n2 = False
    
    if qwen_conf >= 0.8 and phi3_agree == "AGREE" and phi3_score >= 0.8 and is_safe:
        decision = "AUTO_EXECUTE"
        execute_action = True
    elif qwen_conf >= 0.6 and phi3_agree == "AGREE" and phi3_score >= 0.6 and is_safe:
        decision = "EXECUTE_WITH_LOG"
        execute_action = True
    elif phi3_agree == "PARTIAL":
        decision = "HUMAN_REVIEW"
        requires_human = True
    elif phi3_agree == "DISAGREE" or qwen_conf < 0.6:
        decision = "ESCALATE_N2"
        escalate_n2 = True
    else:
        decision = "HUMAN_REVIEW"
        requires_human = True
    
    combined_confidence = (qwen_conf + phi3_score) / 2
    final_action = diag.action_command if execute_action else "PENDING_REVIEW"
    
    return ConsensusResponse(
        payload=ConsensusPayload(
            consensus_id=generate_id("cons"),
            incident_id=incident.incident_id,
            decision=decision,
            final_action=final_action,
            combined_confidence=combined_confidence,
            execute_action=execute_action,
            requires_human=requires_human,
            escalate_n2=escalate_n2,
            diagnosis=diag,
            validation=val,
            timestamp=datetime.utcnow().isoformat()
        )
    )

# ============== API ENDPOINTS ==============

@app.get("/")
async def root():
    return {
        "service": "AuraCore API V2",
        "version": "2.0.0",
        "protocol": "AILCP",
        "status": "running",
        "models": MODELS
    }

@app.get("/health")
async def health():
    """Health check avec status des modèles Ollama"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            ollama_base = OLLAMA_URL.replace("/api/generate", "/api/tags")
            response = await client.get(ollama_base)
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            
            return {
                "status": "healthy",
                "protocol": "AILCP",
                "ollama": "connected",
                "models_available": model_names,
                "qwen_ready": any(MODELS["diagnostic"] in m for m in model_names),
                "phi_ready": any(MODELS["validation"] in m for m in model_names)
            }
    except Exception as e:
        return {
            "status": "degraded",
            "ollama": "disconnected",
            "error": str(e)
        }

@app.post("/diagnose", response_model=ConsensusResponse)
async def diagnose(incident: IncidentInput):
    """
    Endpoint principal AILCP: diagnostic avec consensus dual-LLM
    
    Pipeline:
    1. Qwen (DIAGNOSTICIAN) analyse l'incident
    2. Phi-3 (VALIDATOR) valide/challenge le diagnostic
    3. Consensus engine détermine la décision finale
    
    Returns:
        ConsensusResponse avec décision AUTO_EXECUTE, EXECUTE_WITH_LOG,
        HUMAN_REVIEW ou ESCALATE_N2
    """
    logger.info(f"[AILCP] Processing incident: {incident.incident_id}")
    
    # Step 1: Qwen DIAGNOSTICIAN
    logger.info("[AILCP] Step 1: Qwen DIAGNOSTICIAN analysis...")
    diagnosis = await get_diagnosis(incident)
    logger.info(f"[AILCP] Qwen diagnosis: {diagnosis.payload.cause} (conf: {diagnosis.payload.confidence})")
    
    # Step 2: Phi-3 VALIDATOR
    logger.info("[AILCP] Step 2: Phi-3 VALIDATOR challenge...")
    validation = await validate_diagnosis(incident, diagnosis)
    logger.info(f"[AILCP] Phi validation: {validation.payload.agreement} (score: {validation.payload.validation_score})")
    
    # Step 3: Consensus
    logger.info("[AILCP] Step 3: Computing consensus...")
    consensus = compute_consensus(incident, diagnosis, validation)
    logger.info(f"[AILCP] Consensus: {consensus.payload.decision}, Execute: {consensus.payload.execute_action}")
    
    return consensus

@app.post("/diagnose/qwen-only", response_model=DiagnosisResponse)
async def diagnose_qwen_only(incident: IncidentInput):
    """Diagnostic Qwen seul (sans validation Phi) - pour debug/tests"""
    return await get_diagnosis(incident)

@app.post("/validate", response_model=ValidationResponse)
async def validate_only(incident: IncidentInput, diagnosis: DiagnosisResponse):
    """Validation Phi seule - pour debug/tests"""
    return await validate_diagnosis(incident, diagnosis)

@app.get("/prompts")
async def get_prompts():
    """Récupérer les prompts système actuels"""
    return {
        "qwen_diagnostician": load_prompt("qwen_diagnostician.md"),
        "phi3_validator": load_prompt("phi3_validator.md")
    }

# ============== STARTUP ==============

@app.on_event("startup")
async def startup():
    """Initialisation des répertoires"""
    import os
    os.makedirs(PROMPTS_DIR, exist_ok=True)
    logger.info("[AILCP] AuraCore V2 started - Dual-LLM Consensus System ready")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8900)
