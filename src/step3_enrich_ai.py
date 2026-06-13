# src/step3_enrich_ai.py
import json
import sys
import argparse
from pathlib import Path
from config import Config
from ai_enricher import AIEnricher

# Fields to enrich per database (empty or "unknown"/"UNKNOWN" triggers enrichment)
FIELDS_TO_ENRICH = {
    "capec_database.json": ["severity"],                            # if UNKNOWN
    "cwe_database.json": ["category"],                              # if unknown
    "cve_database.json": ["attack_type", "severity"],               # attack_type if unknown, severity if UNKNOWN
    "mitre_attack.json": ["tactic", "detection"]                    # tactic if empty, detection if empty
}

def should_enrich(value: str) -> bool:
    """Check if value is empty or generic unknown marker."""
    if not value or not isinstance(value, str):
        return True
    return value.strip().lower() in ("", "unknown", "n/a")

def build_prompt(db_name: str, field: str, record: dict) -> str:
    """Create a prompt for the AI to fill a specific field."""
    # Use description and other fields as context
    context = json.dumps(record, indent=2)
    # Trim context to a safe length (e.g., 2000 chars)
    context = context[:2000]
    
    prompts = {
        "capec_database.json": {
            "severity": f"Given the following CAPEC attack pattern, assign a severity level (choose from: VERY LOW, LOW, MEDIUM, HIGH, VERY HIGH, UNKNOWN). Output only the severity.\n\n{context}\n\nSeverity:"
        },
        "cwe_database.json": {
            "category": f"Given the following CWE weakness, assign a category (e.g., 'input validation', 'memory management', 'authentication', 'unknown'). Output only the category.\n\n{context}\n\nCategory:"
        },
        "cve_database.json": {
            "attack_type": f"Given the following CVE vulnerability description, determine the attack type from the list: sql_injection, cross_site_scripting, remote_code_execution, privilege_escalation, denial_of_service, deserialization_attack, brute_force, unknown. Output only the attack type.\n\n{context}\n\nAttack type:",
            "severity": f"Given the following CVE vulnerability, assign a severity level (choose from: LOW, MEDIUM, HIGH, CRITICAL, UNKNOWN). Output only the severity.\n\n{context}\n\nSeverity:"
        },
        "mitre_attack.json": {
            "tactic": f"Given the following MITRE ATT&CK technique description, determine the primary tactic (e.g., 'Execution', 'Persistence', 'Privilege Escalation', 'Defense Evasion', 'Credential Access', 'Discovery', 'Lateral Movement', 'Collection', 'Command and Control', 'Exfiltration', 'Impact'). Output only the tactic.\n\n{context}\n\nTactic:",
            "detection": f"Given the following MITRE ATT&CK technique, generate a brief detection strategy (2-3 sentences). Output only the detection text.\n\n{context}\n\nDetection:"
        }
    }
    return prompts.get(db_name, {}).get(field, "")

def enrich_file(filepath: Path, fields: list, enricher: AIEnricher, dry_run: bool = False):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    db_name = filepath.name
    updated = 0
    for item in data:
        for field in fields:
            if field in item and should_enrich(item[field]):
                prompt = build_prompt(db_name, field, item)
                if not prompt:
                    continue
                try:
                    if not dry_run:
                        generated = enricher.generate(prompt, max_tokens=50)
                        # Clean up response: sometimes model adds extra text
                        generated = generated.strip().split('\n')[0]  # take first line
                        item[field] = generated
                        updated += 1
                        print(f"    🧠 {item.get('id', '?')}: {field} = {generated}")
                    else:
                        print(f"    [DRY RUN] {item.get('id', '?')}: would generate {field}")
                except Exception as e:
                    print(f"    ⚠️ Error enriching {item.get('id', '?')}/{field}: {e}")

    if not dry_run and updated > 0:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ {db_name}: updated {updated} fields")

def main():
    parser = argparse.ArgumentParser(description="AI enrichment for MPDB JSON files")
    parser.add_argument('--dry-run', action='store_true', help='Simulate without saving')
    args = parser.parse_args()

    print("🧠 AI Enrichment (Step 3)")
    enricher = AIEnricher()
    output_dir = Config.OUTPUT_DIR

    for filename, fields in FIELDS_TO_ENRICH.items():
        filepath = output_dir / filename
        if filepath.exists():
            enrich_file(filepath, fields, enricher, dry_run=args.dry_run)
        else:
            print(f"⚠️ {filename} not found, skipping")

if __name__ == "__main__":
    main()