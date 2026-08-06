"""
Validate riscv_instructions.yaml for correct structure, required fields,
and data types.

Per-entry validation
---------------------
Each instruction entry must:
    - Include all required fields: name, description, opclass, auto_manage.
    - Have a name that is a valid C-identifier (starts with a letter or
      underscore, followed by letters, digits, or underscores).
    - Have auto_manage defined as a boolean.

Opclass-dependent rules
------------------------
    - If opclass is a known gem5 opclass, latency, fu_count, and pipelined
      must NOT be present (if present, they are ignored rather than
      flagged as errors).
          NOTE: this behavior may change — these fields may become
          meaningful for future extensions.
    - If opclass is not a known gem5 opclass, latency and fu_count must be
      defined as positive integers, and pipelined must be a boolean.

Cross-entry validation
------------------------
    - No duplicate instruction names within a single architecture.
    - No duplicate opclass names across all architectures (known gem5
      opclasses excluded from this check).
"""


import re
from shared.yaml_stuff import (
    baseFields,
    opclassFields,
    architectureInfo
)

# Typical C function name pattern: starts with a letter or underscore, followed by letters, digits, or underscores.
NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
        
def is_gem5_opclass(opclass: str, opclass_file: dict) -> bool:
    '''Check if the given opclass is a known gem5 opclass. Looks at the gem5-opclasses.json file in the data/cache directory.'''
    gem5_opclasses = opclass_file
    known_opclasses = {
        known_opclass.lower(): known_opclass
        for known_opclass in gem5_opclasses.get("opclasses", [])
    }
    canonical_opclass = known_opclasses.get(opclass.lower())
    if canonical_opclass is not None:
        return True
    return False

def verify_entry_fields(entry: dict, opclass_file: dict) -> bool:
    '''Verify that the entry has the required fields, highlights missing, unknown, and ignored fields.'''

    if not isinstance(entry, dict):
        print("Each instruction entry must be a mapping/object.")
        return False

    entry_fields = set(entry.keys())
    
    if "opclass" not in entry:
        print(f"Missing 'opclass' field in '{entry.get('name', '?')}'.")
        return False
    
    if is_gem5_opclass(entry.get("opclass"), opclass_file): 
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

def verify_entry_field_data(entry: dict, opclass_file: dict) -> bool:
    '''Verify that the entry's fields have the correct data types and values.'''
    is_valid = True
    name = entry.get("name", "?")

    if "name" in entry and not NAME_PATTERN.match(entry["name"]):
        print(f"Field 'name' in '{name}' must be a valid C identifier-style name.")
        is_valid = False

    for field, expected_type in baseFields.items():
        if field in entry and not isinstance(entry[field], expected_type):
            print(f"Field '{field}' in '{name}' must be of type {expected_type.__name__}.")
            is_valid = False

    if "opclass" in entry and not is_gem5_opclass(entry["opclass"], opclass_file):
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
    '''Check for duplicate instruction names in the list of instructions.'''
    instruction_names = set()
 
    for entry in instructions:
        name = entry.get("name")
  
        if name is not None:
            if name in instruction_names:
                print(f"Duplicate instruction name found: {name}")
                return True
        instruction_names.add(name)
  
    return False

def duplicate_opclasses(yaml_file: dict, opclass_file: dict) -> bool:
    '''Check for duplicate opclass names across all architectures in the instructions dictionary.'''
    opclass_names = set()
    for arch, entries in yaml_file.items():
        if arch == "schema_version" or not isinstance(entries, list):
            continue

        for entry in entries:
            opclass = entry.get("opclass")
            if opclass is not None:
                if opclass in opclass_names and not is_gem5_opclass(opclass, opclass_file):
                    print(f"Duplicate opclass name found: {opclass}")
                    return True
                opclass_names.add(opclass)
    return False


def verify_yaml(yaml_file: dict, opclass_file: dict) -> bool:
    '''Verify the instructions.yaml file for correct structure, required fields, and data types.'''

    is_valid = True

    for arch in yaml_file.keys():        
        if arch == "schema_version":
            if not isinstance(yaml_file[arch], int):
                print("'schema_version' must be an integer.")
                is_valid = False
            continue

        if arch not in architectureInfo.keys():
            print(f"Unknown architecture field: {arch}")
            is_valid = False

        for entry in yaml_file[arch]:
            if not isinstance(entry, dict):
                print(f"Each instruction entry must be a mapping/object. Found: {entry}")
                is_valid = False
                continue

            if not verify_entry_fields(entry, opclass_file):
                is_valid = False

            if not verify_entry_field_data(entry, opclass_file):
                is_valid = False

        if duplicate_names(yaml_file[arch]):
            is_valid = False

    if duplicate_opclasses(yaml_file, opclass_file):
        is_valid = False

    if is_valid:
        print("YAML validation passed.")
    else:
        print("YAML validation failed.")

    return is_valid