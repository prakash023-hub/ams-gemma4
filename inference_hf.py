"""
AMS-Gemma4 Inference Module
Calls Ollama (local Mac) or Gemini API (HuggingFace cloud)
Author: Prakash Raj K, SBV Pharmacy
"""

import os
import requests
from pathlib import Path

PROMPT_FILE = Path(__file__).parent / "prompts.py"
OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "gemma4:e2b"

def load_master_prompt() -> str:
    with open(PROMPT_FILE, "r") as f:
        return f.read()

def build_full_prompt(master: str, patient_case: str) -> str:
    return f"{master}\n\n===PATIENT CASE===\n{patient_case}"

def call_ollama(patient_case: str) -> str:
    master = load_master_prompt()
    full_prompt = build_full_prompt(master, patient_case)
    payload = {
        "model": DEFAULT_MODEL,
        "prompt": full_prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 3000}
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=180)
        response.raise_for_status()
        return response.json()["response"]
    except requests.exceptions.ConnectionError:
        return "ERROR: Ollama server not running. Start with: ollama serve"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {str(e)}"

def call_gemini(patient_case: str) -> str:
    import google.generativeai as genai
    master = load_master_prompt()
    full_prompt = build_full_prompt(master, patient_case)
    try:
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(
            full_prompt,
            generation_config={"temperature": 0.2, "max_output_tokens": 3000}
        )
        return response.text
    except Exception as e:
        return f"ERROR (Gemini): {type(e).__name__}: {str(e)}"

def ask_gemma(patient_case: str) -> str:
    """Auto-detect: use Gemini on HuggingFace, Ollama locally."""
    if os.environ.get("GEMINI_API_KEY"):
        return call_gemini(patient_case)
    else:
        return call_ollama(patient_case)
