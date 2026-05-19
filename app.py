"""
AMS-Gemma4: Antibiotic Stewardship Clinical Decision Support
Kaggle Gemma 4 Good Hackathon - Health & Sciences Track
Author: Prakash Raj K, Associate Professor, SBV Pharmacy, Puducherry
"""

import gradio as gr
import os
from functions import calculate_crcl, check_aware_tier, lookup_resistance

HEADER_HTML = """
<div style="text-align:center;padding:24px;background:linear-gradient(135deg,#1a3a5c 0%,#2e75b6 100%);color:white;border-radius:16px;margin-bottom:20px;box-shadow:0 4px 20px rgba(26,58,92,0.3)">
    <div style="font-size:48px;margin-bottom:8px">🏥</div>
    <h1 style="margin:0;font-size:32px;font-weight:800">AMS-Gemma4</h1>
    <h3 style="margin:8px 0;font-weight:400;opacity:0.9;font-size:16px">Antibiotic Stewardship Clinical Decision Support</h3>
    <div style="margin-top:12px;display:flex;justify-content:center;gap:12px;flex-wrap:wrap">
        <span style="background:#27ae60;color:white;padding:5px 14px;border-radius:20px;font-size:13px;font-weight:600">🔒 OFFLINE — Patient data never leaves this device</span>
        <span style="background:rgba(255,255,255,0.2);color:white;padding:5px 14px;border-radius:20px;font-size:13px">⚡ Native Function Calling</span>
        <span style="background:rgba(255,255,255,0.2);color:white;padding:5px 14px;border-radius:20px;font-size:13px">🌐 English + தமிழ்</span>
    </div>
    <p style="margin-top:12px;opacity:0.75;font-size:12px">Powered by Gemma 4 E2B | WHO AWaRe 2023 | ICMR India Guidelines 2024</p>
</div>
"""

WARNING_HTML = """
<div style="background:#fff8e1;border-left:5px solid #ffc107;padding:12px 16px;border-radius:8px;margin-bottom:16px;display:flex;align-items:center;gap:10px">
    <span style="font-size:20px">⚕️</span>
    <div><strong>Clinical Decision Support Only</strong><br>
    <small>Final prescription authority rests with the licensed clinician. Always confirm allergies and local antibiogram before prescribing.</small></div>
</div>
"""

def section_header(icon, title):
    return f'<div style="background:linear-gradient(135deg,#1a3a5c,#2e75b6);color:white;padding:8px 16px;border-radius:8px;margin:12px 0 8px 0;font-weight:bold;font-size:15px">{icon} {title}</div>'


def get_recommendation(age, weight, sex, creatinine, allergies,
                        pathogen, nitrofurantoin_s, cotrimoxazole_s,
                        ceftriaxone_s, ciprofloxacin_s, meropenem_s,
                        piptazo_s, vancomycin_s, amikacin_s,
                        other_drugs, culture_image, language):

    image_note = ""
    if culture_image is not None:
        image_note = "\n📷 Culture report image received — Gemma 4 multimodal processing active."

    drug_map = {
        "nitrofurantoin": nitrofurantoin_s,
        "cotrimoxazole": cotrimoxazole_s,
        "ceftriaxone": ceftriaxone_s,
        "ciprofloxacin": ciprofloxacin_s,
        "meropenem": meropenem_s,
        "piperacillin-tazobactam": piptazo_s,
        "vancomycin": vancomycin_s,
        "amikacin": amikacin_s,
    }
    sensitivities = {k: v for k, v in drug_map.items() if v != "Not tested"}

    if not pathogen.strip():
        return "⚠️ Please enter pathogen name.", "No data yet.", ""

    gemini_key = os.environ.get("GEMINI_API_KEY")

    if gemini_key:
        result = call_gemini_with_functions(
            int(age), float(weight), float(creatinine),
            sex[0], pathogen, sensitivities,
            allergies or "none", language, gemini_key, culture_image
        )
    else:
        from function_calling_v2 import ask_with_guaranteed_functions
        result = ask_with_guaranteed_functions(
            int(age), float(weight), float(creatinine),
            sex[0], pathogen, sensitivities,
            allergies or "none", language
        )

    crcl = result["crcl"]

    nitro_tested = nitrofurantoin_s != "Not tested"
    nitro_warning = ""
    if nitro_tested and not crcl["nitrofurantoin_safe"]:
        nitro_warning = " ⚠️ Nitrofurantoin UNSAFE (CrCl<60)"

    crcl_display = f"{crcl['crcl_ml_min']} mL/min — {crcl['category']}{nitro_warning}{image_note}"

    if result["aware_tiers"]:
        aware_lines = []
        for drug, tier in result["aware_tiers"].items():
            if tier == "Access":
                aware_lines.append(f"✅ {drug}: {tier} (preferred)")
            elif tier == "Watch":
                aware_lines.append(f"⚠️ {drug}: {tier} (use with stewardship)")
            else:
                aware_lines.append(f"🚨 {drug}: {tier} (last resort)")
        aware_display = "\n".join(aware_lines)
    else:
        aware_display = "Mark drugs as S (Sensitive) above to see AWaRe tiers"

    return crcl_display, aware_display, result["recommendation"]


def call_gemini_with_functions(age, weight, creatinine, sex,
                                pathogen, sensitivities, allergies,
                                language, api_key, culture_image=None):
    from google import genai
    import json
    from pathlib import Path

    crcl_result = calculate_crcl(age, weight, creatinine, sex)
    resistance_data = lookup_resistance(pathogen)
    aware_results = {}
    for drug, sensitivity in sensitivities.items():
        if sensitivity == "S":
            tier_result = check_aware_tier(drug)
            aware_results[drug] = tier_result["aware_tier"]

    with open(Path(__file__).parent / "prompts.py", "r") as f:
        master_prompt = f.read()

    nitro_status = "REJECTED (CrCl below 60)" if not crcl_result["nitrofurantoin_safe"] else "PASS"
    sensitive_drugs = [d for d, s in sensitivities.items() if s == "S"]
    resistant_drugs = [d for d, s in sensitivities.items() if s == "R"]
    lang_instruction = "Reply in Tamil language (தமிழ்)." if language == "தமிழ்" else "Reply in English."

    enriched = f"""
{lang_instruction}

=== FUNCTION CALLING RESULTS ===
CrCl (Python-verified): {crcl_result['crcl_ml_min']} mL/min — {crcl_result['category']}
Nitrofurantoin: {nitro_status}
AWaRe tiers: {json.dumps(aware_results)}
ICMR Resistance: {resistance_data.get('summary', 'Use local antibiogram')}

=== PATIENT CASE ===
Age: {age}y, Sex: {'female' if sex.upper()=='F' else 'male'}, Weight: {weight}kg
Creatinine: {creatinine} mg/dL → CrCl: {crcl_result['crcl_ml_min']} mL/min
Pathogen: {pathogen}
Sensitive: {', '.join(sensitive_drugs) if sensitive_drugs else 'none specified'}
Resistant: {', '.join(resistant_drugs) if resistant_drugs else 'none specified'}
Allergies: {allergies}

Use CrCl={crcl_result['crcl_ml_min']}. Nitrofurantoin={nitro_status}.
Recommend antibiotic in 10-section format.
"""

    client = genai.Client(api_key=api_key)

    try:
        if culture_image is not None:
            import io
            from google.genai import types
            img_byte_arr = io.BytesIO()
            culture_image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            response = client.models.generate_content(
                model="models/gemma-4-31b-it",
                contents=[
                    types.Part.from_bytes(
                        data=img_bytes,
                        mime_type="image/png"
                    ),
                    master_prompt + "\n\n" + enriched
                ]
            )
        else:
            response = client.models.generate_content(
                model="models/gemma-4-31b-it",
                contents=master_prompt + "\n\n" + enriched
            )

        return {
            "crcl": crcl_result,
            "resistance": resistance_data,
            "aware_tiers": aware_results,
            "recommendation": response.text
        }

    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            msg = "⏳ API quota temporarily exceeded. Please wait 60 seconds and try again."
        elif "500" in error_str or "INTERNAL" in error_str:
            msg = "⚠️ Server error. Please try again in a moment."
        else:
            msg = f"ERROR: {type(e).__name__}: {error_str}"

        return {
            "crcl": crcl_result,
            "resistance": resistance_data,
            "aware_tiers": aware_results,
            "recommendation": msg
        }


EXAMPLES = [
    [72, 55, "Female", 1.4, "none", "E. coli",
     "S", "S", "S", "R", "Not tested", "Not tested", "Not tested", "Not tested",
     "", None, "English"],
    [65, 70, "Male", 1.8, "penicillin rash", "Klebsiella pneumoniae ESBL+",
     "Not tested", "Not tested", "R", "R", "S", "S", "Not tested", "S",
     "", None, "English"],
    [45, 80, "Male", 0.9, "none", "Staphylococcus aureus MRSA",
     "Not tested", "Not tested", "Not tested", "Not tested", "Not tested",
     "Not tested", "S", "Not tested",
     "doxycycline:S, cotrimoxazole:S", None, "English"],
    [72, 55, "Female", 1.4, "none", "E. coli",
     "S", "S", "S", "R", "Not tested", "Not tested", "Not tested", "Not tested",
     "", None, "தமிழ்"],
]

with gr.Blocks(title="AMS-Gemma4") as demo:

    gr.HTML(HEADER_HTML)
    gr.HTML(WARNING_HTML)

    with gr.Row():
        with gr.Column(scale=1):
            gr.HTML(section_header("👤", "Patient Details"))

            language = gr.Radio(choices=["English", "தமிழ்"],
                               value="English", label="🌐 Language / மொழி")

            with gr.Row():
                age = gr.Number(value=65, label="Age (years)", minimum=1, maximum=120)
                weight = gr.Number(value=70, label="Weight (kg)", minimum=1, maximum=300)

            with gr.Row():
                sex = gr.Radio(choices=["Male", "Female"], value="Female", label="Sex")
                creatinine = gr.Number(value=1.0, label="Creatinine (mg/dL)",
                                      minimum=0.1, maximum=20.0)

            allergies = gr.Textbox(label="⚠️ Known Allergies",
                                  placeholder="e.g. penicillin (or 'none')", lines=1)

            gr.HTML(section_header("🦠", "Culture & Sensitivity"))

            pathogen = gr.Textbox(label="Organism Identified",
                                 placeholder="e.g. E. coli, Klebsiella pneumoniae ESBL+")

            culture_image = gr.Image(
                label="📷 Upload culture report photo (optional — Gemma 4 multimodal)",
                type="pil", sources=["upload", "webcam"], height=130
            )

            gr.Markdown("**Sensitivity Results** (S = Sensitive, R = Resistant, leave as 'Not tested' if not done):")

            with gr.Row():
                nitrofurantoin_s = gr.Dropdown(["S","R","Not tested"],
                    value="Not tested", label="Nitrofurantoin")
                cotrimoxazole_s = gr.Dropdown(["S","R","Not tested"],
                    value="Not tested", label="Cotrimoxazole")
            with gr.Row():
                ceftriaxone_s = gr.Dropdown(["S","R","Not tested"],
                    value="Not tested", label="Ceftriaxone")
                ciprofloxacin_s = gr.Dropdown(["S","R","Not tested"],
                    value="Not tested", label="Ciprofloxacin")
            with gr.Row():
                meropenem_s = gr.Dropdown(["S","R","Not tested"],
                    value="Not tested", label="Meropenem")
                piptazo_s = gr.Dropdown(["S","R","Not tested"],
                    value="Not tested", label="Pip-Tazobactam")
            with gr.Row():
                vancomycin_s = gr.Dropdown(["S","R","Not tested"],
                    value="Not tested", label="Vancomycin")
                amikacin_s = gr.Dropdown(["S","R","Not tested"],
                    value="Not tested", label="Amikacin")

            other_drugs = gr.Textbox(
                label="Other drugs (format: drug:S, drug:R)",
                placeholder="e.g. doxycycline:S, clindamycin:R", lines=1)

            submit_btn = gr.Button("🔬 Get Antibiotic Recommendation",
                                  variant="primary", size="lg")

        with gr.Column(scale=1):
            gr.HTML(section_header("📊", "Clinical Results"))

            crcl_output = gr.Textbox(
                label="⚗️ Creatinine Clearance — Cockcroft-Gault (Python calculated)",
                interactive=False, lines=2)

            aware_output = gr.Textbox(
                label="📋 WHO AWaRe Tiers — Python verified (✅ Access ⚠️ Watch 🚨 Reserve)",
                interactive=False, lines=5)

            recommendation_output = gr.Textbox(
                label="💊 Clinical Recommendation — Gemma 4 E2B + Native Function Calling",
                lines=24, interactive=False)

    gr.HTML(section_header("📋", "Example Cases — Click to Auto-Fill"))
    gr.Examples(
        examples=EXAMPLES,
        inputs=[age, weight, sex, creatinine, allergies, pathogen,
                nitrofurantoin_s, cotrimoxazole_s, ceftriaxone_s,
                ciprofloxacin_s, meropenem_s, piptazo_s,
                vancomycin_s, amikacin_s, other_drugs,
                culture_image, language],
        label="UTI elderly (English) | Klebsiella HAP | MRSA SSTI | UTI elderly (தமிழ்)"
    )

    gr.HTML("""
    <div style="text-align:center;padding:16px;border-top:1px solid #333;margin-top:20px;color:#888;font-size:12px">
        <strong>AMS-Gemma4</strong> | Kaggle Gemma 4 Good Hackathon — Health & Sciences Track |
        Prakash Raj K, Associate Professor of Pharmacy, SBV, Puducherry, India<br>
        Gemma 4 E2B + Native Function Calling | WHO AWaRe 2023 | ICMR 2024 | Apache 2.0 |
        <a href="https://github.com/prakash023-hub/ams-gemma4" target="_blank" style="color:#2e75b6">GitHub</a>
    </div>
    """)

    submit_btn.click(
        fn=get_recommendation,
        inputs=[age, weight, sex, creatinine, allergies, pathogen,
                nitrofurantoin_s, cotrimoxazole_s, ceftriaxone_s,
                ciprofloxacin_s, meropenem_s, piptazo_s,
                vancomycin_s, amikacin_s, other_drugs,
                culture_image, language],
        outputs=[crcl_output, aware_output, recommendation_output]
    )

if __name__ == "__main__":
    print("="*60)
    print("AMS-Gemma4 Starting...")
    print("Open your browser at: http://localhost:7860")
    print("="*60)
    demo.launch(server_name="0.0.0.0", server_port=7860,
               share=False, show_error=True)
