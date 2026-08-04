import re
from io_utils import load_yaml, load_json
from paths import INSTRUCTIONS_PATH, DATA_DIR

NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

baseFields = {
    "name": str,
    "description": str,
    "opclass": str,
    "auto_manage": bool
}

opclassFields = {
    "latency": int,
    "fu_count": int,
    "pipelined": bool
}

architectureFields = {
    "riscv_instructions",
    "x86_instructions",
    "arm_instructions",
}

        
def is_gem5_opclass(opclass: str) -> bool:
    gem5_opclasses = load_json(DATA_DIR / "cache" / "gem5-opclasses.json")
    known_opclasses = {
        known_opclass.lower(): known_opclass
        for known_opclass in gem5_opclasses.get("opclasses", [])
    }
    canonical_opclass = known_opclasses.get(opclass.lower())
    if canonical_opclass is not None:
        return True
    return False

def verify_entry_fields(entry: dict) -> bool:
    if not isinstance(entry, dict):
        print("Each instruction entry must be a mapping/object.")
        return False

    entry_fields = set(entry.keys())
    
    if "opclass" not in entry:
        print(f"Missing 'opclass' field in '{entry.get('name', '?')}'.")
        return False
    
    if is_gem5_opclass(entry.get("opclass")):
        required_fields = set(baseFields.keys())
        ignored = entry_fields & set(opclassFields.keys())
        unknown = entry_fields - required_fields - ignored
        missing = required_fields - entry_fields
    else:
        required_fields = set(baseFields.keys()) | set(opclassFields.keys())
        unknown = entry_fields - required_fields
        missing = required_fields - entry_fields
        ignored = set()
        
    is_valid = True

    if unknown:
        print(f"Unknown field(s) in '{entry.get('name', '?')}': {unknown}")
        is_valid = False
    if ignored:
        print(f"Ignored field(s) in '{entry.get('name', '?')}': {ignored}")
    if missing:
        print(f"Missing required field(s) in '{entry.get('name', '?')}': {missing}")
        is_valid = False
    
    return is_valid

def verify_entry_field_data(entry: dict) -> bool:
    is_valid = True
    name = entry.get("name", "?")

    if "name" in entry and not NAME_PATTERN.match(entry["name"]):
        print(f"Field 'name' in '{name}' must be a valid C identifier-style name.")
        is_valid = False

    for field, expected_type in baseFields.items():
        if field in entry and not isinstance(entry[field], expected_type):
            print(f"Field '{field}' in '{name}' must be of type {expected_type.__name__}.")
            is_valid = False

    if "opclass" in entry and not is_gem5_opclass(entry["opclass"]):
        for field, expected_type in opclassFields.items():
            if field in entry and not isinstance(entry[field], expected_type):
                print(f"Field '{field}' in '{name}' must be of type {expected_type.__name__}.")
                is_valid = False

    for field in ("latency", "fu_count"):
        if field in entry:
            value = entry[field]
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                print(f"Field '{field}' in '{name}' must be a positive integer.")
                is_valid = False

    return is_valid

def duplicate_names(instructions: list[dict]) -> bool:
    instruction_names = set()
    opclass_names = set()
 
    for entry in instructions:
        name = entry.get("name")
  
        if name is not None:
            if name in instruction_names:
                print(f"Duplicate instruction name found: {name}")
                return True
        instruction_names.add(name)
  
    return False

def duplicate_opclasses(instructions: dict) -> bool:
    opclass_names = set()
    for arch, entries in instructions.items():
        if arch == "schema_version" or not isinstance(entries, list):
            continue

        for entry in entries:
            opclass = entry.get("opclass")
            if opclass is not None:
                if opclass in opclass_names and not is_gem5_opclass(opclass):
                    print(f"Duplicate opclass name found: {opclass}")
                    return True
                opclass_names.add(opclass)
    return False


def verify_yaml():
    try:
        instructions = load_yaml(INSTRUCTIONS_PATH)
    except (OSError, ValueError) as error:
        print(error)
        return False

    is_valid = True
    for arch, entries in instructions.items():
        if not isinstance(entries, list):
            continue
        if arch == "schema_version":
            if not isinstance(entries, int):
                print("'schema_version' must be an integer.")
                is_valid = False
            continue
  
        if arch not in architectureFields:
            print(f"Unknown architecture field: {arch}")
            is_valid = False
  
        for entry in entries:
            if not verify_entry_fields(entry):
                is_valid = False
            if not verify_entry_field_data(entry):
                is_valid = False
  
        if duplicate_names(instructions[arch]):
            is_valid = False

    if duplicate_opclasses(instructions):
        is_valid = False

    if is_valid:
        print("YAML validation passed.")
    else:
        print("YAML validation failed.")
  


if __name__ == "__main__":
    verify_yaml()