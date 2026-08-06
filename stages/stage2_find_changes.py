from io_utils import load_yaml, load_json
from paths import INSTRUCTIONS_PATH, STATE_DIR

registries = {
    "riscv": STATE_DIR / "riscv-registry.json"
    # "x86": STATE_DIR / "x86-registry.json",       future support for x86 instructions
    # "arm": STATE_DIR / "arm-registry.json"        future support for arm instructions
}
def find_changes() -> dict:
    '''Find changes between the current instructions.yaml and the last saved state. Returns a dictionary of changes.'''
    instructions = load_yaml(INSTRUCTIONS_PATH)
    registry_path = STATE_DIR / "riscv-registry.json"
    
    if not registry_path.exists():
        print("No previous state found. Assuming all instructions are new.")
        return {"added": list(instructions.keys()), "removed": [], "modified": []}
    
    last_saved_instructions = load_yaml(registry_path)
    
    added = [name for name in instructions if name not in last_saved_instructions]
    removed = [name for name in last_saved_instructions if name not in instructions]
    modified = [
        name for name in instructions
        if name in last_saved_instructions and instructions[name] != last_saved_instructions[name]
    ]
    
    return {"added": added, "removed": removed, "modified": modified}