"""
AMS-Gemma4 Inference Module
Calls Ollama (local) or Gemini (cloud fallback) with the master prompt.
Author: Prakash Raj K, SBV Pharmacy
"""

import os
import requests
from pathlib import Path

# ----- Configuration -----
PROMPT_FILE = Path(__file__).parent / "prompts.py"
OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "gemma4:e2b"
FALLBACK_MODEL = "gemma3n:e2b"


def load_master_prompt() -> str:
    """Load the master clinical prompt from prompts.py file."""
    with open(PROMPT_FILE, "r") as f:
        return f.read()


def build_full_prompt(master: str, patient_case: str) -> str:
    """Combine master prompt with the patient case using a clear separator."""
    return f"{master}\n\n===PATIENT CASE===\n{patient_case}"


def ask_gemma(patient_case: str, model: str = DEFAULT_MODEL) -> str:
    """
    Send a clinical question to Gemma via Ollama. Returns the recommendation text.

    patient_case: a plain-English description of the patient
    model: 'gemma4:e2b' (default) or 'gemma3n:e2b' (fallback)
    """
    master = load_master_prompt()
    full_prompt = build_full_prompt(master, patient_case)

    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,   # low for clinical consistency
            "num_predict": 3000   # enough room for 10-section answer
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=180)
        response.raise_for_status()
        return response.json()["response"]
    except requests.exceptions.ConnectionError:
        return "ERROR: Ollama server not running. Start with: ollama serve"
    except requests.exceptions.Timeout:
        return "ERROR: Request timed out. Model may be loading; try again."
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {str(e)}"


# ----- Quick self-test when running this file directly -----
if __name__ == "__main__":
    test_case = (
        "72-year-old woman, 55 kg, E. coli UTI, sensitive to nitrofurantoin "
        "and ceftriaxone, creatinine 1.4 mg/dL. Recommend antibiotic following "
        "the rules above."
    )

    print("=" * 60)
    print("AMS-Gemma4 Inference Self-Test")
    print("=" * 60)
    print(f"Model: {DEFAULT_MODEL}")
    print(f"Test case: {test_case[:80]}...")
    print("-" * 60)
    print("Calling Gemma... (may take 30-90 seconds)")
    print()

    result = ask_gemma(test_case)
    print(result)
    print()
    print("=" * 60)
    print("Test complete.")
