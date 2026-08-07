from pathlib import Path
from shared import verify 

ROOT_DIR = Path(__file__).resolve().parents[1]
GEM5_DIR = Path(__file__).resolve().parents[2] / "gem5"

INSTRUCTIONS_PATH = ROOT_DIR / "instructions.yaml"
DATA_DIR = ROOT_DIR / "data"

PATCHMAPS_DIR = DATA_DIR / "patch-maps"
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
    PATCHMAPS_DIR / "riscv-map.json": verify.arch_patch_map_schema,
    PATCHMAPS_DIR / "x86-map.json": verify.arch_patch_map_schema,
    PATCHMAPS_DIR / "arm-map.json": verify.arch_patch_map_schema,
    # Add more mappings for other architectures as needed
}

architectureInfo = {
    "riscv": {
        "registry_path": STATE_DIR / "riscv-registry.json",
        "patch_map_path": PATCHMAPS_DIR / "riscv-map.json",
        "changes_path": CHANGES_DIR / "riscv-changes.json"
    },
    "x86": {
        "registry_path": STATE_DIR / "x86-registry.json",
        "patch_map_path": PATCHMAPS_DIR / "x86-map.json",
        "changes_path": CHANGES_DIR / "x86-changes.json"
    },
    "arm": {
        "registry_path": STATE_DIR / "arm-registry.json",
        "patch_map_path": PATCHMAPS_DIR / "arm-map.json",
        "changes_path": CHANGES_DIR / "arm-changes.json"
    }
}