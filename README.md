# 🏥 AMS-Gemma4: Antibiotic Stewardship AI for Indian Hospitals

> Offline clinical decision support powered by **Gemma 4 E2B** with native 
> function calling — built for rural India's antibiotic resistance crisis.

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![HuggingFace](https://img.shields.io/badge/🤗-Live_Demo-yellow)](https://prakashrajk-ams-gemma4.hf.space)
[![Kaggle](https://img.shields.io/badge/Kaggle-Gemma_4_Good-blue)](https://www.kaggle.com/competitions/gemma-4-good-hackathon)

---

## The Problem

India has the world's highest antimicrobial resistance burden.
Nearly **300,000 Indians die annually** from antibiotic-resistant infections.
In rural clinics — no pharmacist, no internet, no guidance.

## The Solution

AMS-Gemma4 runs **fully offline** on an 8GB laptop.
Patient data never leaves the device.
Works in English and **தமிழ் (Tamil)**.

---

## Key Features

- 🔒 **Fully offline** — Gemma 4 E2B via Ollama, no internet needed
- ⚡ **Native function calling** — Python calculates CrCl, AWaRe tiers, 
  resistance data before Gemma reasons
- 🛡️ **Safety gate** — automatically rejects contraindicated drugs 
  (e.g. Nitrofurantoin when CrCl < 60 mL/min)
- 🌐 **Tamil + English** — first offline AMS tool with Tamil output
- 📊 **WHO AWaRe 2023** — Access/Watch/Reserve classification built-in
- 🇮🇳 **ICMR India data** — India-specific resistance patterns, not generic global data

---

## Gemma 4 Features Used

| Feature | How Used |
|---------|----------|
| **Gemma 4 E2B edge model** | Runs offline on MacBook M1 8GB RAM |
| **Native function calling** | Calls calculate_crcl(), check_aware_tier(), lookup_resistance() |
| **Multimodal** | Upload culture report photo directly |
| **140+ languages** | Tamil clinical output via prompt engineering |

---

## Clinical Validation

| Case | Patient | CrCl | Expected | Result |
|------|---------|------|----------|--------|
| UTI-001 | 72F, E. coli, Cr 1.4 | 31.5 mL/min | Nitrofurantoin REJECTED → Ceftriaxone | ✅ |
| HAP-002 | 65M, Klebsiella ESBL+, Cr 1.8 | 40.5 mL/min | Meropenem (renal adjusted) | ✅ |
| SSTI-003 | 45M, MRSA, Cr 0.9 | 95.2 mL/min | Doxycycline over Vancomycin | ✅ |
| UTI-004 | 72F, E. coli, Tamil | 31.5 mL/min | Ceftriaxone in Tamil | ✅ |

---

## Quick Start — Local (Offline)

```bash
# Install Ollama
brew install ollama

# Download Gemma 4 E2B
ollama pull gemma4:e2b

# Clone and run
git clone https://github.com/prakash023-hub/ams-gemma4
cd ams-gemma4
pip install -r requirements.txt
python app.py
# Open http://localhost:7860
```

## Quick Start — Cloud Demo
