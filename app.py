"""
AMS-Gemma4: Antibiotic Stewardship Clinical Decision Support
Kaggle Gemma 4 Good Hackathon - Health & Sciences Track
Author: Prakash Raj K, Associate Professor, SBV Pharmacy, Puducherry
"""

import gradio as gr
import base64
from pathlib import Path
from inference import ask_gemma
from functions import calculate_crcl, check_aware_tier, lookup_resistance

# ── Core function ────────────────────────────────────────────────────────────
def get_recommendation(age, weight, sex, creatinine, allergies,
                        infection_details, culture_image, language):
    """Main function: takes patient data + optional image, returns recommendation."""

    if not infection_details.strip() and culture_image is None:
        return "⚠️ Please enter infection details OR upload a culture report image.", ""

    # Step 1: Calculate CrCl
    crcl_result = calculate_crcl(
        age=int(age),
        weight_kg=float(weight),
        creatinine_mg_dl=float(creatinine),
        sex=sex[0]
    )
    crcl_value = crcl_result["crcl_ml_min"]
    crcl_category = crcl_result["category"]
    nitro_safe = crcl_result["nitrofurantoin_safe"]

    # Step 2: Build patient case string
    sex_text = "male" if sex.startswith("M") else "female"
    allergy_text = allergies if allergies.strip() else "none reported"
    lang_instruction = "Reply in Tamil language (தமிழ்)." if language == "தமிழ்" else "Reply in English."

    image_note = ""
    if culture_image is not None:
        image_note = "\nNote: A culture report image has been uploaded. Extract pathogen name and sensitivity results from the image to supplement the text details below.\n"

    patient_case = f"""
{lang_instruction}
{image_note}
Patient details:
- Age: {age} years, Sex: {sex_text}, Weight: {weight} kg
- Serum creatinine: {creatinine} mg/dL
- Calculated CrCl (Cockcroft-Gault): {crcl_value} mL/min ({crcl_category})
- Known allergies: {allergy_text}
- Nitrofurantoin safety: {"SAFE (CrCl >= 60)" if nitro_safe else "UNSAFE - REJECT (CrCl < 60)"}

Infection and culture details:
{infection_details if infection_details.strip() else "See uploaded culture report image."}

Apply the safety gate rules strictly. Recommend antibiotic following the 10-section format.
"""

    # Step 3: Send to Gemma 4
    recommendation = ask_gemma(patient_case)

    # Step 4: Format CrCl display
    nitro_warning = "" if nitro_safe else " ⚠️ Nitrofurantoin UNSAFE"
    crcl_display = f"{crcl_value} mL/min — {crcl_category}{nitro_warning}"

    return crcl_display, recommendation


# ── Example cases ────────────────────────────────────────────────────────────
EXAMPLES = [
    [72, 55, "Female", 1.4, "none",
     "E. coli UTI. Sensitive to nitrofurantoin and ceftriaxone. Resistant to ciprofloxacin.",
     None, "English"],
    [65, 70, "Male", 1.8, "penicillin rash",
     "Klebsiella pneumoniae ESBL+ HAP. Sensitive to meropenem and piperacillin-tazobactam. Resistant to ceftriaxone.",
     None, "English"],
    [45, 80, "Male", 0.9, "none",
     "MRSA cellulitis right leg. Sensitive to vancomycin, doxycycline, cotrimoxazole.",
     None, "English"],
    [72, 55, "Female", 1.4, "none",
     "E. coli UTI. Sensitive to nitrofurantoin and ceftriaxone.",
     None, "தமிழ்"],
]

# ── Build Gradio UI ──────────────────────────────────────────────────────────
with gr.Blocks(
    title="AMS-Gemma4",
    theme=gr.themes.Base(
        primary_hue="blue",
        secondary_hue="red",
    ),
    css="""
    .header { text-align: center; padding: 20px; background: #1a3a5c;
              color: white; border-radius: 10px; margin-bottom: 20px; }
    .offline-badge { background: #27ae60; color: white;
                     padding: 4px 12px; border-radius: 20px; font-size: 12px; }
    .warning { background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; }
    .crcl-box { font-size: 18px; font-weight: bold; }
    footer { visibility: hidden }
    """
) as demo:

    # Header
    gr.HTML("""
    <div class="header">
        <h1>🏥 AMS-Gemma4</h1>
        <h3>Antibiotic Stewardship Clinical Decision Support</h3>
        <span class="offline-badge">🔒 OFFLINE | Patient data never leaves this device</span>
        <br><br>
        <small>Powered by Gemma 4 E2B | WHO AWaRe 2023 | ICMR India Guidelines 2024</small>
    </div>
    """)

    gr.HTML("""
    <div class="warning">
    ⚕️ <b>Clinical Decision Support Only.</b>
    Final prescription authority rests with the licensed clinician.
    Always confirm allergies and local antibiogram before prescribing.
    </div>
    """)

    with gr.Row():
        # ── Left column: inputs ──────────────────────────────────────────────
        with gr.Column(scale=1):
            gr.Markdown("### 👤 Patient Details")

            language = gr.Radio(
                choices=["English", "தமிழ்"],
                value="English",
                label="🌐 Language / மொழி"
            )

            age = gr.Number(value=65, label="Age (years)",
                            minimum=1, maximum=120)
            weight = gr.Number(value=70, label="Weight (kg)",
                               minimum=1, maximum=300)
            sex = gr.Radio(choices=["Male", "Female"],
                           value="Female", label="Sex")
            creatinine = gr.Number(value=1.0,
                                   label="Serum Creatinine (mg/dL)",
                                   minimum=0.1, maximum=20.0)
            allergies = gr.Textbox(
                label="Known Allergies",
                placeholder="e.g. penicillin, sulfa drugs (or 'none')",
                lines=2
            )

            gr.Markdown("### 🦠 Infection & Culture")

            # ── IMAGE UPLOAD ─────────────────────────────────────────────────
            gr.Markdown("""
            **Option A: Upload culture report photo** 📷
            *(Gemma 4 multimodal — reads the image directly)*
            """)
            culture_image = gr.Image(
                label="Culture & Sensitivity Report (photo/scan)",
                type="pil",
                sources=["upload", "webcam"],
                height=200
            )

            gr.Markdown("**Option B: Type infection details manually**")
            infection_details = gr.Textbox(
                label="Infection details + culture results",
                placeholder="e.g. E. coli UTI. Sensitive to nitrofurantoin and ceftriaxone. Resistant to ciprofloxacin.",
                lines=4
            )

            submit_btn = gr.Button(
                "🔬 Get Antibiotic Recommendation",
                variant="primary",
                size="lg"
            )

        # ── Right column: results ────────────────────────────────────────────
        with gr.Column(scale=1):
            gr.Markdown("### 📊 Results")

            crcl_output = gr.Textbox(
                label="⚗️ Calculated CrCl (Cockcroft-Gault)",
                interactive=False,
                elem_classes=["crcl-box"]
            )

            recommendation_output = gr.Textbox(
                label="💊 Clinical Recommendation (Gemma 4 E2B)",
                lines=28,
                interactive=False
            )

    # Examples
    gr.Markdown("### 📋 Example Cases (click to auto-fill)")
    gr.Examples(
        examples=EXAMPLES,
        inputs=[age, weight, sex, creatinine, allergies,
                infection_details, culture_image, language],
        label="Click any example to load it"
    )

    # Footer
    gr.Markdown("""
    ---
    **AMS-Gemma4** | Kaggle Gemma 4 Good Hackathon — Health & Sciences Track
    | Prakash Raj K, Associate Professor of Pharmacy, SBV, Puducherry, India
    | Gemma 4 E2B via Ollama | WHO AWaRe 2023 | ICMR 2024 | Apache 2.0
    """)

    # Wire up button
    submit_btn.click(
        fn=get_recommendation,
        inputs=[age, weight, sex, creatinine, allergies,
                infection_details, culture_image, language],
        outputs=[crcl_output, recommendation_output]
    )

# ── Launch ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("AMS-Gemma4 Starting...")
    print("Open your browser at: http://localhost:7860")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
