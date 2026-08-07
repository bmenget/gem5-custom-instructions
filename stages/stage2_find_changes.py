import shared.paths as paths
from shared.io_utils import load_json, write_json
from shared.paths import (
    architectureInfo
)


def new_instructions(manifest_instructions: dict, registry_instructions: dict) -> set:
    '''Find new instructions in the current instructions.yaml that are not present in the last saved state. Returns a set of new instructions.'''
    new_instructions = set()
    registry_names = set()

    for entry in registry_instructions:
        registry_names.add(entry["name"])

    for instruction in manifest_instructions:
        if instruction["name"] not in registry_names:
            new_instructions.add(instruction["name"])
    return new_instructions

def removed_instructions(manifest_instructions: dict, registry_instructions: dict) -> set:
    '''Find instructions that were removed from the current instructions.yaml compared to the last saved state. Returns a set of removed instructions.'''
    removed_instructions = set()
    manifest_names = set()

    for instruction in manifest_instructions:
        manifest_names.add(instruction["name"])

    for instruction in registry_instructions:
        if instruction["name"] not in manifest_names:
            removed_instructions.add(instruction["name"])
    return removed_instructions


def changed_instructions(arch: str, manifest_instructions: dict, registry_instructions: dict) -> set:
    '''Find instructions that have changed in the current instructions.yaml compared to the last saved state. Returns a set of changed instructions.'''
    changed_instructions = set()
    registry_names = set()

    for instruction in registry_instructions:
        registry_names.add(instruction["name"])

    for instruction in manifest_instructions:
        name = instruction["name"]
        if instruction["auto_manage"] is False:
            print(f"🔒 {arch} instruction '{name}' is not auto-managed. Instruction will not be updated in gem5.")
            continue  # Only check auto-managed instructions for changes

        if name in registry_names:
            # Find the corresponding instruction in the registry
            registry_instruction = next((item for item in registry_instructions if item["name"] == name), None)

            if registry_instruction["opclass"] != instruction["opclass"]:
                changed_instructions.add(name)
            elif registry_instruction["oplat"] != instruction["oplat"]:
                changed_instructions.add(name)
            elif registry_instruction["fu_count"] != instruction["fu_count"]:
                changed_instructions.add(name)
            elif registry_instruction["pipelined"] != instruction["pipelined"]:
                changed_instructions.add(name)
            
    return changed_instructions

def create_change_log(arch: str, new_instructions: set, removed_instructions: set, changed_instructions: set) -> list[dict]:
    '''Write the changes to a JSON file for the given architecture.'''
    overlap = new_instructions & removed_instructions & changed_instructions
    if overlap:
        raise ValueError(f"❗ Instructions cannot be new, removed, and changed at the same time: {overlap}")

    current_changes_path = architectureInfo[arch]["changes_path"]
    try:
        current_changes = load_json(current_changes_path)
    except:
        current_changes = {}  # If the file doesn't exist or is invalid, start fresh
    
    current_version = current_changes.get("version")

    if current_version is not None:
        new_version = current_version + 1
    else:
        new_version = 0
        
    change_log = {
        "version": new_version,
        "architecture": arch,
        "instructions": []
    }

    for instruction in new_instructions:
        change_log["instructions"].append({
            "name": instruction,
            "new": True,
            "removed": False,
            "changed": False
        })
    for instruction in removed_instructions:
        change_log["instructions"].append({
            "name": instruction,
            "new": False,
            "removed": True,
            "changed": False
        })
    for instruction in changed_instructions:
        change_log["instructions"].append({
            "name": instruction,
            "new": False,
            "removed": False,
            "changed": True
        })
    return change_log



def write_changes(change_log: dict) -> None:
    '''Write the changes to a JSON file for each architecture.'''
    arch = change_log["architecture"]
    changes_path = architectureInfo[arch]["changes_path"]
    write_json(changes_path, change_log)

def record_changes(manifest: dict, registries: list[dict]) -> None:
    for registry in registries:
        arch = registry["architecture"]
        if arch not in manifest:
            continue
        new_set = new_instructions(manifest[arch], registry["instructions"])
        removed_set = removed_instructions(manifest[arch], registry["instructions"])
        changed_set = changed_instructions(arch, manifest[arch], registry["instructions"])
        change_log = create_change_log(arch, new_set, removed_set, changed_set)
        write_changes(change_log)
        if new_set:
            print(f"🔶 New {arch} instructions: {', '.join(new_set)}")
        if removed_set:
            print(f"🔶 Removed {arch} instructions: {', '.join(removed_set)}")
        if changed_set:
            print(f"🔶 Updated {arch} instructions: {', '.join(changed_set)}")