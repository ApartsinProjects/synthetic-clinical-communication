import os
import json
import uuid
import random
import concurrent.futures
from pathlib import Path
from tqdm import tqdm
from openai import OpenAI

# Project root is two levels up from this file (src/<subpackage>/<file>.py), so
# paths work regardless of the current working directory the script is launched
# from. NOTE: must stay parents[2] as long as this file lives in a subpackage of
# src/ — parent.parent would resolve to src/ itself and every default path below
# would silently point at a non-existent src/data/... location.
ROOT = Path(__file__).resolve().parents[2]

QUALITY_CONTROL_CRITERIA = {
    "MAX_GENERATION_RETRIES_PER_SAMPLE": 3,
    "GENERATION_STRATEGY": "Conditional attribute-based tactical dialogue synthesis"
}
DATASET_SIZES = {"MVP_SIZE": 500}

def initialize_openai_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    return OpenAI(api_key=api_key)

def generate_clinical_profile_attributes(noise_level: str) -> dict:
    mechanism = random.choice(["gunshot", "shrapnel", "blast", "burn", "blunt_trauma", "penetrating_trauma", "amputation"])
    
    if mechanism == "amputation":
        site = random.choice(["right_arm", "left_arm", "right_leg", "left_leg"])
    else:
        site = random.choice(["head", "neck", "chest", "abdomen", "right_arm", "left_arm", "right_leg", "left_leg", "back", "pelvis", "multiple"])

    if site in ["head", "chest", "neck"] or mechanism in ["blast", "penetrating_trauma", "amputation"]:
        vital_avpu_scale = random.choice(["V", "P", "U"])
        vital_respiratory_status = random.choice(["labored", "absent"])
        vital_circulation_status = random.choice(["weak_pulse", "absent_pulse"])
        condition_shock = "yes" if vital_circulation_status == "weak_pulse" else "no"
        evacuation_priority = "immediate"
    else:
        vital_avpu_scale = "A"
        vital_respiratory_status = "normal"
        vital_circulation_status = "stable"
        condition_shock = "no"
        evacuation_priority = "not immediate"

    treatment_CAT_applied = "no"
    treatment_CAT_time = "unknown"
    if "leg" in site or "arm" in site:
        if mechanism == "amputation":
            treatment_CAT_applied = "yes"
            treatment_CAT_time = f"{random.randint(0,23):02d}:{random.randint(0,59):02d}"
        elif random.random() > 0.2: 
            treatment_CAT_applied = "yes"
            treatment_CAT_time = f"{random.randint(0,23):02d}:{random.randint(0,59):02d}"

    medications = []
    procedures = []
    
    if vital_respiratory_status == "labored" and site == "chest":
        procedures.append("needle")
    if vital_avpu_scale in ["P", "U"]:
        procedures.append("airway")
        procedures.append("intubation")
    if condition_shock == "yes" or mechanism == "amputation":
        medications.extend(["TXA", "plasma", "hartmann_solution"])
    if vital_avpu_scale == "A" and random.random() > 0.4 and mechanism != "amputation":
        medications.append(random.choice(["actiq", "morphine"]))
    elif mechanism == "amputation" and vital_avpu_scale == "A":
        medications.append(random.choice(["morphine", "actiq"]))

    r_status = vital_respiratory_status

    if noise_level == "Clean":
        reliability = random.choices(["confirmed", "uncertain", "conflicting"], weights=[80, 15, 5])[0]
    elif noise_level == "Medium Noise":
        reliability = random.choices(["confirmed", "uncertain", "conflicting"], weights=[40, 40, 20])[0]
    else:  # High Noise
        reliability = random.choices(["confirmed", "uncertain", "conflicting"], weights=[10, 45, 45])[0]

    return {
        "patient_gender": random.choice(["male", "female"]),
        "mechanism_of_injury": mechanism,
        "anatomical_site": site,
        "evacuation_priority": evacuation_priority,
        "vital_circulation_status": vital_circulation_status,
        "vital_respiratory_status": r_status,
        "vital_oxygen_saturation": str(random.randint(75, 92)) if r_status != "normal" else str(random.randint(95, 100)),
        "vital_avpu_scale": vital_avpu_scale,
        "condition_airway_injury": "yes" if site in ["head", "neck"] else "no",
        "condition_breathing_injury": "yes" if site == "chest" or r_status == "labored" else "no",
        "condition_shock": condition_shock,
        "treatment_exposure_and_warming_applied": random.choice(["yes", "no"]),
        "treatment_splint_applied": "yes" if ("leg" in site or "arm" in site) and mechanism != "amputation" else "no",
        "treatment_spine_immobilization_applied": "yes" if mechanism in ["blast", "blunt_trauma"] else "no",
        "treatment_CAT_applied": treatment_CAT_applied,
        "treatment_CAT_time": treatment_CAT_time,
        "treatment_hemostatic_dressing_applied": "yes" if mechanism in ["gunshot", "shrapnel"] and treatment_CAT_applied == "no" else "no",
        "treatment_medications_given": medications if medications else ["unknown"],
        "treatment_procedures_performed": procedures if procedures else ["unknown"],
        "information_reliability": reliability

    }

def construct_generation_prompts(ground_truth_profile: dict, noise_level: str) -> tuple:
    system_prompt = (
        "You are an expert battlefield combat simulation engine designed to generate synthetic evaluation datasets.\n"
        "Your task is to take a pre-determined structured 'Ground Truth Medical Profile' of a military casualty and transform it into a highly realistic, messy, and chaotic radio communication transcript (Hebrew dialogue) between combat medical personal roles.\n\n"
        f"MANDATORY TRANSCRIPT SIMULATION CONSTRAINTS BASED ON NOISE LEVEL [{noise_level}]:\n"
        "1. Stress & Redundancy: The medic/caregiver must sound stressed, repeat crucial clinical words, and speak in a fragmented, non-linear fashion but in military order.\n"
        "2. Network Environment Noise: Actively inject transmission dropouts like  '[רעש סטטי]', '[קטיעה בקשר]',  '[פיצוץ ברקע]', or '[התפרצות לקשר]' inside sentences.\n"
        "3. Phonetic ASR Corruptions: Intentionally warp 2-3 clinical terms into sounding-alike Hebrew words to simulate Speech-to-Text transmission failure (e.g., 'נוזלים' -> 'הרטמן', 'פירסטקאר' -> 'תחבושת').\n"
        "4. Military Slang: Utilize authentic IDF combat-medical vernacular (e.g., 'עשינו קוניו', 'תוציאו לי פינוי, פינוי דחוף' ,'מתחילים פרוצדורה', 'מה הזמן הגעה').\n"
    )

    user_prompt = (
        f"Generate a chaotic Hebrew radio transcript that perfectly communicates and hides the following objective patient clinical state:\n\n"
        f"Objective Patient Profile to Describe:\n"
        f"{json.dumps(ground_truth_profile, indent=2)}\n\n"
        "Output Requirements:\n"
        "You must output a perfectly valid JSON object with exactly two top-level keys:\n"
        "1. 'ground_truth': Copy the exact profile input dictionary provided to you without modifying a single value.\n"
        "2. 'transcript': The generated messy, chaotic Hebrew text dialogue string.\n"
        "Do not include any text outside the JSON structure."
    )

    return system_prompt, user_prompt

def validate_sample_quality(sample_json: dict) -> bool:
    if not sample_json or "ground_truth" not in sample_json or "transcript" not in sample_json:
        return False
        
    gt = sample_json["ground_truth"]
    
    required_keys = [
        "patient_gender", "mechanism_of_injury", "anatomical_site", 
        "evacuation_priority", "vital_circulation_status", "vital_respiratory_status",
        "vital_oxygen_saturation", "vital_avpu_scale", "condition_airway_injury",
        "condition_breathing_injury", "condition_shock", 
        "treatment_exposure_and_warming_applied", "treatment_splint_applied",
        "treatment_spine_immobilization_applied", "treatment_CAT_applied",
        "treatment_CAT_time", "treatment_hemostatic_dressing_applied",
        "treatment_medications_given", "treatment_procedures_performed", 
        "information_reliability"
    ]
    
    return all(key in gt for key in required_keys)

def generate_synthetic_sample(client: OpenAI, model_name: str = "gpt-4o") -> dict:
    noise_levels = ["Clean", "Medium Noise", "High Noise"]
    selected_noise = random.choice(noise_levels)
    gt_profile = generate_clinical_profile_attributes(selected_noise)
    
    system_prompt, user_prompt = construct_generation_prompts(gt_profile, selected_noise)
    
    for attempt in range(QUALITY_CONTROL_CRITERIA.get("MAX_GENERATION_RETRIES_PER_SAMPLE", 3)):
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.9 
            )
            
            raw_content = response.choices[0].message.content.strip()
            parsed_json = json.loads(raw_content)
            
            if validate_sample_quality(parsed_json):
                return {
                    "metadata": {
                        "example_id": str(uuid.uuid4()),
                        "noise_level": selected_noise,
                        "starter_role": "Medic" if random.random() > 0.3 else "Commander"
                    },
                    "ground_truth": parsed_json["ground_truth"],
                    "transcript": parsed_json["transcript"],
                    "target_output": {} 
                }
        except Exception as e:
            print(f"ERROR: {e}")
        continue
            
    return None

def bulk_dataset_generation_pipeline(output_path: str = None):
    output_path = str(output_path) if output_path else str(ROOT / "data" / "battlefield_dataset.json")
    client = initialize_openai_client()
    dataset = []
    target_size = DATASET_SIZES["MVP_SIZE"]
    
    print(f"Starting pipeline: generating {target_size} structured battlefield samples...\n")

    buffer_size = int(target_size * 1.25)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(generate_synthetic_sample, client) for _ in range(buffer_size)]
        
        with tqdm(total=target_size, desc="Synthesizing Chaotic Transcripts", unit="sample") as pbar:
            for future in concurrent.futures.as_completed(futures):
                if len(dataset) >= target_size:
                    break 
                
                sample = future.result()
                if sample:
                    dataset.append(sample)
                    pbar.update(1)
                    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
        
    print(f"\nSuccess! Exactly {len(dataset)} robust dataset samples stored safely at: {output_path}")

if __name__ == "__main__":
    bulk_dataset_generation_pipeline()