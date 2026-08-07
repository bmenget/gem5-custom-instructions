from pathlib import Path
from shared import verify 

ROOT_DIR = Path(__file__).resolve().parents[1]
GEM5_DIR = Path(__file__).resolve().parents[2] / "gem5"

INSTRUCTIONS_PATH = ROOT_DIR / "instructions.yaml"
DATA_DIR = ROOT_DIR / "data"

TEMPLATES_DIR = DATA_DIR / "templates"
LOOKUPS_DIR = DATA_DIR / "lookups"
STATE_DIR = DATA_DIR / "state"
CHANGES_DIR = DATA_DIR / "change-logs"
STATES_DIR = DATA_DIR / "state"
WORKING_DIR = ROOT_DIR / "working-copies"

OPCLASSES_PATH = LOOKUPS_DIR / "gem5-opclasses.json"

schema_mappings = {
    STATE_DIR / "riscv-registry.json": verify.registry_schema,
    LOOKUPS_DIR / "gem5-opclasses.json": verify.gem5_opclass_schema,
    CHANGES_DIR / "riscv-changes.json": verify.changes_schema,
    CHANGES_DIR / "x86-changes.json": verify.changes_schema,
    CHANGES_DIR / "arm-changes.json": verify.changes_schema,
    TEMPLATES_DIR / "riscv-mappings.json": verify.arch_template_schema,
    TEMPLATES_DIR / "x86-mappings.json": verify.arch_template_schema,
    TEMPLATES_DIR / "arm-mappings.json": verify.arch_template_schema,
    # Add more mappings for other architectures as needed
}

architectureInfo = {
    "riscv": {
        "registry_path": STATE_DIR / "riscv-registry.json",
        "template_path": TEMPLATES_DIR / "riscv-mappings.json",
        "changes_path": CHANGES_DIR / "riscv-changes.json"
    },
    "x86": {
        "registry_path": STATE_DIR / "x86-registry.json",
        "template_path": TEMPLATES_DIR / "x86-mappings.json",
        "changes_path": CHANGES_DIR / "x86-changes.json"
    },
    "arm": {
        "registry_path": STATE_DIR / "arm-registry.json",
        "template_path": TEMPLATES_DIR / "arm-mappings.json",
        "changes_path": CHANGES_DIR / "arm-changes.json"
    }
}