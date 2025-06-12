import json
from typing import Dict

from llama_model import ask_ollama

# Known plan keywords for basic matching
_PLAN_KEYWORDS = {
    "ohip": ["ohip"],
    "uhip": ["uhip"],
    "sunlife": ["sun life", "sunlife"],
    "manulife": ["manulife"],
}

_SERVICE_KEYWORDS = {
    "dental": ["dental", "tooth", "teeth"],
    "prescription": ["prescription", "drug", "rx"],
    "emergency": ["emergency", "er"],
    "physiotherapy": ["physio"],
    "vision": ["vision", "eye"],
}

def _match_keyword(text: str, mapping: Dict[str, list], default: str = "other") -> str:
    """Return the key whose keywords appear in the text."""
    text = text.lower()
    for key, keywords in mapping.items():
        for kw in keywords:
            if kw in text:
                return key
    return default


def _heuristic_classify(claim: Dict) -> Dict[str, str]:
    """Fallback heuristic classification."""
    service = claim.get("service", "")
    plan = claim.get("plan", "")
    service_type = _match_keyword(service, _SERVICE_KEYWORDS)
    plan_type = _match_keyword(plan, _PLAN_KEYWORDS, default="unknown")
    return {"service_type": service_type, "plan_type": plan_type, "action": "rag"}


def classify_claim(claim: Dict) -> Dict[str, str]:
    """Classify a claim using LLM with heuristic fallback."""
    prompt = f"""
You are Ana, an intelligent insurance claim classifier.\n
Known service types: dental, prescription, emergency, physiotherapy, vision, other.\nKnown plan types: ohip, uhip, sunlife, manulife.\n
Given the claim details below, identify the most likely service_type and plan_type.\nDecide an action route: auto_approve, rag, or reject.\n
Claim:\n{json.dumps(claim, indent=2)}\n
Respond only in JSON with keys service_type, plan_type, and action.
"""

    response = ask_ollama(prompt)
    try:
        result = json.loads(response)
        if all(k in result for k in ["service_type", "plan_type", "action"]):
            return result
    except Exception:
        print("⚠️ LLM output not valid JSON. Falling back to heuristic classification.")
    return _heuristic_classify(claim)


if __name__ == "__main__":
    # simple manual test
    sample_claim = {
        "user_id": "U123",
        "service": "Root canal",
        "amount": 800,
        "provider": "XYZ Dental",
        "plan": "Sun Life Enhanced",
        "submitted_on": "2025-06-01",
    }
    print(classify_claim(sample_claim))
