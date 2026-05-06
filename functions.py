"""
AMS-Gemma4 Function Calling Tools
These are real Python functions Gemma 4 can call for accurate clinical math.

Author: Prakash Raj K, SBV Pharmacy
"""


def calculate_crcl(age: int, weight_kg: float, creatinine_mg_dl: float, sex: str) -> dict:
    """
    Calculate Creatinine Clearance using the Cockcroft-Gault formula.

    Args:
        age: patient age in years
        weight_kg: patient weight in kilograms
        creatinine_mg_dl: serum creatinine in mg/dL
        sex: "M" for male, "F" for female

    Returns:
        dict with crcl value and renal function category
    """
    if creatinine_mg_dl <= 0:
        return {"error": "Creatinine must be positive"}

    crcl = ((140 - age) * weight_kg) / (72 * creatinine_mg_dl)
    if sex.upper() == "F":
        crcl *= 0.85

    crcl = round(crcl, 1)

    if crcl >= 90:
        category = "Normal"
    elif crcl >= 60:
        category = "Mild impairment"
    elif crcl >= 30:
        category = "Moderate impairment"
    elif crcl >= 15:
        category = "Severe impairment"
    else:
        category = "Kidney failure"

    nitrofurantoin_safe = crcl >= 60
    aminoglycoside_safe = crcl >= 30

    return {
        "crcl_ml_min": crcl,
        "category": category,
        "nitrofurantoin_safe": nitrofurantoin_safe,
        "aminoglycoside_safe": aminoglycoside_safe,
        "note": f"CrCl {crcl} mL/min - {category}"
    }


# WHO AWaRe Classification 2023 - lookup table
AWARE_TIERS = {
    "amoxicillin": "Access",
    "amoxicillin-clavulanate": "Access",
    "nitrofurantoin": "Access",
    "cotrimoxazole": "Access",
    "doxycycline": "Access",
    "cefazolin": "Access",
    "cefalexin": "Access",
    "cephalexin": "Access",
    "cloxacillin": "Access",
    "metronidazole": "Access",
    "gentamicin": "Access",
    "clindamycin": "Access",
    "ciprofloxacin": "Watch",
    "levofloxacin": "Watch",
    "moxifloxacin": "Watch",
    "ceftriaxone": "Watch",
    "cefotaxime": "Watch",
    "cefepime": "Watch",
    "meropenem": "Watch",
    "imipenem": "Watch",
    "ertapenem": "Watch",
    "piperacillin-tazobactam": "Watch",
    "azithromycin": "Watch",
    "clarithromycin": "Watch",
    "vancomycin": "Watch",
    "amikacin": "Watch",
    "colistin": "Reserve",
    "polymyxin b": "Reserve",
    "linezolid": "Reserve",
    "tigecycline": "Reserve",
    "ceftazidime-avibactam": "Reserve",
    "daptomycin": "Reserve",
    "fosfomycin iv": "Reserve",
}


def check_aware_tier(drug_name: str) -> dict:
    """
    Look up the WHO AWaRe tier for an antibiotic.

    Args:
        drug_name: name of the antibiotic (case-insensitive)

    Returns:
        dict with tier and stewardship guidance
    """
    drug_lower = drug_name.lower().strip()
    tier = AWARE_TIERS.get(drug_lower, "Unknown")

    guidance = {
        "Access": "First-line, narrow-spectrum, low resistance risk. Preferred.",
        "Watch": "Broader spectrum, higher resistance potential. Use only if Access tier insufficient.",
        "Reserve": "Last-resort. Only for confirmed multi-drug resistance.",
        "Unknown": "Drug not in AWaRe lookup. Verify category from WHO 2023 list."
    }

    return {
        "drug": drug_name,
        "aware_tier": tier,
        "guidance": guidance[tier]
    }


# ICMR India 2024 resistance data - simplified
RESISTANCE_PATTERNS = {
    "e. coli": {
        "fluoroquinolones": ">70%",
        "esbl_production": "60-80%",
        "carbapenems": "5-15% (rising)",
        "nitrofurantoin": "<10% (still effective for UTI)",
        "summary": "High FQ resistance and ESBL prevalence; empirical use of cipro/3rd-gen ceph often fails."
    },
    "klebsiella pneumoniae": {
        "esbl_production": ">50%",
        "carbapenems": "20-30% (NDM, OXA-48 prevalent)",
        "summary": "ESBL+ common; carbapenem resistance rising in tertiary centers."
    },
    "pseudomonas aeruginosa": {
        "summary": "Highly variable; pip-tazo, meropenem, amikacin common; colistin for pan-drug-resistant."
    },
    "acinetobacter baumannii": {
        "mdr_prevalence": ">80% in ICUs",
        "summary": "Often only colistin + tigecycline effective in Indian ICUs."
    },
    "staphylococcus aureus": {
        "mrsa_prevalence": "25-40%",
        "summary": "Vancomycin remains effective; VRSA rare."
    },
}


def lookup_resistance(pathogen: str, region: str = "India") -> dict:
    """
    Look up resistance patterns for a pathogen in a region.

    Args:
        pathogen: bacteria name (e.g., "E. coli")
        region: geographic region (default "India")

    Returns:
        dict with resistance data
    """
    pathogen_lower = pathogen.lower().strip()

    for key in RESISTANCE_PATTERNS:
        if key in pathogen_lower or pathogen_lower in key:
            data = RESISTANCE_PATTERNS[key].copy()
            data["pathogen"] = pathogen
            data["region"] = region
            data["source"] = "ICMR AMR Surveillance Network 2024"
            return data

    return {
        "pathogen": pathogen,
        "region": region,
        "summary": "No specific data; use local antibiogram if available.",
        "source": "ICMR fallback"
    }


# ----- Self-test -----
if __name__ == "__main__":
    print("=" * 60)
    print("AMS-Gemma4 Functions Self-Test")
    print("=" * 60)

    print("\n1. Test calculate_crcl(age=72, weight=55, creatinine=1.4, sex=F):")
    result = calculate_crcl(72, 55, 1.4, "F")
    for k, v in result.items():
        print(f"   {k}: {v}")

    print("\n2. Test calculate_crcl(age=65, weight=70, creatinine=1.8, sex=M):")
    result = calculate_crcl(65, 70, 1.8, "M")
    for k, v in result.items():
        print(f"   {k}: {v}")

    print("\n3. Test check_aware_tier('Nitrofurantoin'):")
    result = check_aware_tier("Nitrofurantoin")
    for k, v in result.items():
        print(f"   {k}: {v}")

    print("\n4. Test check_aware_tier('Meropenem'):")
    result = check_aware_tier("Meropenem")
    for k, v in result.items():
        print(f"   {k}: {v}")

    print("\n5. Test lookup_resistance('E. coli'):")
    result = lookup_resistance("E. coli")
    for k, v in result.items():
        print(f"   {k}: {v}")

    print("\n6. Test lookup_resistance('Klebsiella pneumoniae'):")
    result = lookup_resistance("Klebsiella pneumoniae")
    for k, v in result.items():
        print(f"   {k}: {v}")

    print("\n" + "=" * 60)
    print("All tests complete.")
