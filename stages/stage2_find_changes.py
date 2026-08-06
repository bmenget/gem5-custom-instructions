import shared.paths as paths
from shared.yaml_stuff import (
    architectureInfo,
    architectureFields
)

def find_changed_instructions(instructions: dict, registry: dict) -> set:
    '''Find changes between the current instructions.yaml and the last saved state. Returns a set of changed instructions.'''
    changed_instructions = set()
    for instruction in instructions:
        name = instruction["name"]
        if name is None:
            continue  # Skip entries without a name

def find_new_instructions(instructions: dict, registry: dict) -> set:
    '''Find new instructions in the current instructions.yaml that are not present in the last saved state. Returns a set of new instructions.'''
    new_instructions = set()
    registry_names = set()

    for entry in registry:
        registry_names.add(entry["name"])

    for instruction in instructions:
        if instruction["name"] not in registry_names:
            new_instructions.add(instruction["name"])
    return new_instructions

def find_removed_instructions(instructions: dict, registry: dict) -> set:
    '''Find instructions that were removed from the current instructions.yaml compared to the last saved state. Returns a set of removed instructions.'''
    removed_instructions = set()
    instruction_names = set()

    for instruction in instructions:
        instruction_names.add(instruction["name"])

    for entry in registry:
        if entry["name"] not in instruction_names:
            removed_instructions.add(entry["name"])
    return removed_instructions




def mark_changes(instructions: dict, registry: dict) -> dict:
    '''Mark changes in the instructions.yaml based on the last saved state. Returns a dictionary of marked changes.'''

def save_changes(instructions: dict, registries: list[dict]) -> None:
    for registry in registries:
        arch = registry["architecture"]
        find_changed_instructions(instructions[arch], registry["instructions"])
        find_new_instructions(instructions[arch], registry["instructions"])
        find_removed_instructions(instructions[arch], registry["instructions"])