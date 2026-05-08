"""
AMS-Gemma4 Guaranteed Function Calling v2
We call functions in Python, pass results to Gemma.
This guarantees 100% accurate clinical math.
Author: Prakash Raj K, SBV Pharmacy
"""

import requests
import json
from functions import calculate_crcl, check_aware_tier, lookup_resistance

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma4:e2b"

def ask_with_guaranteed_functions(
    age: int,
    weight_kg: float,
    creatinine: float,
    sex: str,
    pathogen: str,
    sensitivities: dict,
    allergies: str = "none",
    language: str = "English"
) -> dict:
    """
    Full clinical recommendation with guaranteed function calling.
    Returns both the function results AND Gemma's recommendation.
    """

    # STEP 1: Call functions in Python (100% accurate)
    print("🔧 Calling calculate_crcl()...")
    crcl_result = calculate_crcl(age, weight_kg, creatinine, sex)
    print(f"✅ CrCl: {crcl_result['crcl_ml_min']} mL/min — {crcl_result['category']}")

    print("🔧 Calling lookup_resistance()...")
    resistance_data = lookup_resistance(pathogen)
    print(f"✅ Resistance: {resistance_data.get('summary', 'N/A')}")

    print("🔧 Calling check_aware_tier() for each sensitive drug...")
    aware_results = {}
    for drug, sensitivity in sensitivities.items():
        if sensitivity == "S":
            tier_result = check_aware_tier(drug)
            aware_results[drug] = tier_result["aware_tier"]
            print(f"✅ {drug}: {tier_result['aware_tier']} tier")

    # STEP 2: Build enriched prompt with function results baked in
    lang_instruction = "Reply in Tamil language (தமிழ்)." if language == "தமிழ்" else "Reply in English."

    sensitive_drugs = [d for d, s in sensitivities.items() if s == "S"]
    resistant_drugs = [d for d, s in sensitivities.items() if s == "R"]

    # Build safety gate pre-calculation
    nitro_status = "REJECTED (CrCl below 60 — contraindicated)" if not crcl_result["nitrofurantoin_safe"] else "PASS"
    amino_status = "REJECTED (CrCl below 30)" if not crcl_result["aminoglycoside_safe"] else "PASS"

    with open("prompts.py", "r") as f:
        master_prompt = f.read()

    enriched_case = f"""
{lang_instruction}

=== FUNCTION CALLING RESULTS (use these exact values) ===

CALCULATED CrCl (Cockcroft-Gault, Python-verified):
- CrCl = {crcl_result['crcl_ml_min']} mL/min
- Category: {crcl_result['category']}
- Nitrofurantoin safety: {nitro_status}
- Aminoglycoside safety: {amino_status}

WHO AWaRe TIERS (Python-verified):
{chr(10).join([f"- {drug}: {tier} tier" for drug, tier in aware_results.items()])}

RESISTANCE PATTERNS for {pathogen} in India (ICMR data):
- {resistance_data.get('summary', 'Use local antibiogram')}

=== PATIENT CASE ===
- Age: {age} years, Sex: {'female' if sex.upper() == 'F' else 'male'}, Weight: {weight_kg} kg
- Creatinine: {creatinine} mg/dL → CrCl: {crcl_result['crcl_ml_min']} mL/min
- Pathogen: {pathogen}
- Sensitive to: {', '.join(sensitive_drugs)}
- Resistant to: {', '.join(resistant_drugs)}
- Allergies: {allergies}

IMPORTANT: Use ONLY the CrCl value of {crcl_result['crcl_ml_min']} mL/min calculated above.
Do NOT recalculate. The safety gate has been pre-applied:
- Nitrofurantoin: {nitro_status}

Now provide your antibiotic recommendation following the 10-section format.
The recommended drug MUST be from the sensitive list AND pass the safety gate.
"""

    # STEP 3: Send to Gemma with pre-calculated results
    print("\n🏥 Sending enriched case to Gemma 4...")

    payload = {
        "model": MODEL,
        "prompt": master_prompt + "\n\n" + enriched_case,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 3000}
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=180)
    response.raise_for_status()
    gemma_answer = response.json()["response"]

    return {
        "crcl": crcl_result,
        "resistance": resistance_data,
        "aware_tiers": aware_results,
        "recommendation": gemma_answer
    }


# Self test
if __name__ == "__main__":
    print("=" * 60)
    print("AMS-Gemma4 Guaranteed Function Calling v2")
    print("=" * 60)

    result = ask_with_guaranteed_functions(
        age=72,
        weight_kg=55,
        creatinine=1.4,
        sex="F",
        pathogen="E. coli",
        sensitivities={
            "nitrofurantoin": "S",
            "ceftriaxone": "S",
            "ciprofloxacin": "R"
        },
        allergies="none",
        language="English"
    )

    print("\n" + "=" * 60)
    print("FUNCTION CALL RESULTS:")
    print(f"CrCl: {result['crcl']['crcl_ml_min']} mL/min")
    print(f"Nitrofurantoin safe: {result['crcl']['nitrofurantoin_safe']}")
    print(f"AWaRe tiers: {result['aware_tiers']}")
    print("=" * 60)
    print("GEMMA RECOMMENDATION:")
    print(result["recommendation"])
