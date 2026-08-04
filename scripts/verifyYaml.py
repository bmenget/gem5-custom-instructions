from pathlib import Path
import re
import yaml
import json

ROOT_DIR = Path(__file__).resolve().parents[1]
INSTRUCTIONS_PATH = ROOT_DIR / "instructions.yaml"
DATA_DIR = ROOT_DIR / "data"

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

def loadFileAsDict(path: Path | str) -> dict:
    path = Path(path)
    with open(path, "r") as f:
        if path.suffix in (".yaml", ".yml"):
            try:
                return yaml.safe_load(f)
            except yaml.YAMLError as error:
                mark = getattr(error, "problem_mark", None)
                problem = getattr(error, "problem", None) or "Invalid YAML syntax."
                context = getattr(error, "context", None)
                location = ""
                if mark is not None:
                    location = f" at line {mark.line + 1}, column {mark.column + 1}"

                message = f"YAML formatting error in {path}{location}: {problem}"
                if context:
                    message = f"{message} ({context})"
                message = (
                    f"{message}\n"
                    "Hint: check indentation, missing ':', and list item '-' markers near that location."
                )
                raise ValueError(message) from error
        elif path.suffix == ".json":
            return json.load(f)
        else:
            raise ValueError(f"Unsupported file type: {path.suffix}")
        
def isGem5Opclass(opclass: str) -> bool:
    gem5_opclasses = loadFileAsDict(DATA_DIR / "cache" / "gem5-opclasses.json")
    known_opclasses = {
        known_opclass.lower(): known_opclass
        for known_opclass in gem5_opclasses.get("opclasses", [])
    }
    canonical_opclass = known_opclasses.get(opclass.lower())
    if canonical_opclass is not None:
        return True
    return False

def verifyEntryFields(entry: dict) -> bool:
    if not isinstance(entry, dict):
        print("Each instruction entry must be a mapping/object.")
        return False

    entry_fields = set(entry.keys())
    
    if "opclass" not in entry:
        print(f"Missing 'opclass' field in '{entry.get('name', '?')}'.")
        return False
    
    if isGem5Opclass(entry.get("opclass")):
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

def verifyEntryFieldData(entry: dict) -> bool:
    is_valid = True
    name = entry.get("name", "?")

    if "name" in entry and not NAME_PATTERN.match(entry["name"]):
        print(f"Field 'name' in '{name}' must be a valid C identifier-style name.")
        is_valid = False

    for field, expected_type in baseFields.items():
        if field in entry and not isinstance(entry[field], expected_type):
            print(f"Field '{field}' in '{name}' must be of type {expected_type.__name__}.")
            is_valid = False

    if "opclass" in entry and not isGem5Opclass(entry["opclass"]):
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

def duplicateNames(instructions: list[dict]) -> bool:
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

def duplicateOpclasses(instructions: dict) -> bool:
    opclass_names = set()
    for arch, entries in instructions.items():
        if arch == "schema_version" or not isinstance(entries, list):
            continue

        for entry in entries:
            opclass = entry.get("opclass")
            if opclass is not None:
                if opclass in opclass_names and not isGem5Opclass(opclass):
                    print(f"Duplicate opclass name found: {opclass}")
                    return True
                opclass_names.add(opclass)
    return False


def verifyYaml():
    try:
        instructions = loadFileAsDict(INSTRUCTIONS_PATH)
    except (OSError, ValueError) as error:
        print(error)
        return False

    if not isinstance(instructions, dict):
        print("YAML root must be a mapping/object.")
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
            if not verifyEntryFields(entry):
                is_valid = False
            if not verifyEntryFieldData(entry):
                is_valid = False
  
        if duplicateNames(instructions[arch]):
            is_valid = False

    if duplicateOpclasses(instructions):
        is_valid = False

    if is_valid:
        print("YAML validation passed.")
    else:
        print("YAML validation failed.")
  


if __name__ == "__main__":
    verifyYaml()