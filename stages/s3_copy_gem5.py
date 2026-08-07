import shutil
from pathlib import Path
import shared.paths as paths
from shared.paths import architectureInfo

def is_arch_diff(change_file: dict) -> bool:
    if change_file["architecture"] not in architectureInfo:
        print(f"⚠️ Unknown architecture '{change_file['architecture']}' in change files. Skipping.")
        return False
    if len(change_file["instructions"]) == 0:
        print(f"ℹ️ No changes for architecture '{change_file['architecture']}'. Skipping.")
        return False
    return True

def copy_gem5_arch_files(arch_file: dict) -> None:
    verify_paths(arch_file)
    arch = arch_file["architecture"]
    if arch not in architectureInfo:
        print(f"⚠️ Unknown architecture '{arch}' in change files. Skipping.")
        return

    print(f"Copying files for architecture '{arch}'...")
    for file in arch_file["files"]:
        filename = file["file name"]
        relative_path = Path(file["path"])
        source = paths.GEM5_DIR / relative_path
        destination = paths.WORKING_DIR / arch / filename
        copy_file(source, destination)
    return

def copy_gem5_fu_files(fu_file: dict) -> None:
    verify_paths(fu_file)
    
    print(f"Copying files for FUs...")
    for file in fu_file["files"]:
        filename = file["file name"]
        relative_path = Path(file["path"])
        source = paths.GEM5_DIR / relative_path
        destination = paths.WORKING_DIR / "FU" / filename
        copy_file(source, destination)
    return

def copy_file(source: Path, destination: Path) -> None:
    '''Copy a single file from source to destination, creating destination directories as needed.'''
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(source, destination)
    except FileNotFoundError as error:
        raise FileNotFoundError(f"⛔ Source file not found: {source}") from error
    except PermissionError as error:
        raise PermissionError(f"⛔ Permission denied copying file to: {destination}") from error
    except OSError as error:
        raise OSError(f"⛔ Unable to copy file from {source} to {destination}: {error}") from error

    print(f"✅ Copied '{source.name}' to '{destination.relative_to(paths.ROOT_DIR)}'")

def verify_paths(template_file: dict) -> None:
    for file in template_file["files"]:
        filename = file["file name"]
        relative_path = Path(file["path"])
        source = paths.GEM5_DIR / relative_path
        if not source.exists():
            raise FileNotFoundError(f"⛔ Source file not found: {source}")

def copy_gem5_files(change_files: list[dict], template_files: list[dict], fu_mappings: dict) -> None:
    copied_FU = False
    for template_file in template_files:
        arch = template_file["architecture"]
        if arch not in architectureInfo:
            print(f"⚠️ Unknown architecture '{arch}' in template files. Skipping.")
            continue

        change_file = next((cf for cf in change_files if cf["architecture"] == arch), None)
        if change_file is None:
            print(f"ℹ️ No changes for architecture '{arch}'. Skipping.")
            continue

        if not is_arch_diff(change_file):
            continue

        copy_gem5_arch_files(template_file)

        if not copied_FU:
            copy_gem5_fu_files(fu_mappings)
            copied_FU = True