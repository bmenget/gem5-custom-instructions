from pathlib import Path
from shared import verify 

ROOT_DIR = Path(__file__).resolve().parents[1]

INSTRUCTIONS_PATH = ROOT_DIR / "instructions.yaml"
DATA_DIR = ROOT_DIR / "data"

TEMPLATE_DIR = DATA_DIR / "templates"
LOOKUPS_DIR = DATA_DIR / "lookups"
STATE_DIR = DATA_DIR / "state"
CHANGES_DIR = DATA_DIR / "change-logs"
STATES_DIR = DATA_DIR / "state"

OPCLASSES_PATH = LOOKUPS_DIR / "gem5-opclasses.json"
CHANGES_PATH = CHANGES_DIR / "changes.json"

schema_mappings = {
    STATE_DIR / "riscv-registry.json": verify.registry_schema,
    LOOKUPS_DIR / "gem5-opclasses.json": verify.gem5_opclass_schema,
    # Add more mappings for other architectures as needed
}

architectureInfo = {
    "riscv": {
        "registry_path": STATE_DIR / "riscv-registry.json",
        "templates_path": TEMPLATE_DIR / "riscv-configs.json",
        "changes_path": CHANGES_DIR / "riscv-changes.json"
    }
#     "x86": {                                          future support for different archs
#         "registry": paths.STATE_DIR / "x86-registry.json",
#     },
#     "arm": {
#         "registry": paths.STATE_DIR / "arm-registry.json",
#     }
}