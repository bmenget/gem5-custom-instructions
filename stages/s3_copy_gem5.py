import shutil
from pathlib import Path
import shared.paths as paths
from shared.paths import architectureInfo

def is_arch_diff(change_file: dict) -> bool:
    if change_file["architecture"] not in architectureInfo:
        return False
    if len(change_file["instructions"]) == 0:
        return False
    return True

def copy_gem5_arch_files(arch_file: dict) -> None:
    verify_paths(arch_file)
    arch = arch_file["architecture"]
    if arch not in architectureInfo:
        print(f"⚠️ Unknown architecture '{arch}' in change files. Skipping.")
        return

    for file in arch_file["files"]:
        filename = file["file name"]
        relative_path = Path(file["path"])
        source = paths.GEM5_DIR / relative_path
        destination = paths.WORKING_DIR / arch / filename
        copy_file(source, destination)
    return

def copy_gem5_fu_files(fu_file: dict) -> None:
    verify_paths(fu_file)
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

    #print(f"✅ Copied '{source.name}' to '{destination.relative_to(paths.ROOT_DIR)}'")

def verify_paths(patch_file: dict) -> None:
    for file in patch_file["files"]:
        filename = file["file name"]
        relative_path = Path(file["path"])
        source = paths.GEM5_DIR / relative_path
        if not source.exists():
            raise FileNotFoundError(f"⛔ Source file not found: {source}")

def copy_gem5_files(change_files: dict[str, dict], patch_files: dict[str, dict], fu_map: dict) -> None:
    copied_FU = False
    for arch, patch_file in patch_files.items():
        change_file = change_files.get(arch)
        if change_file is None:
            print(f"ℹ️ No changes for architecture '{arch}'. Skipping.")
            continue

        if not is_arch_diff(change_file):
            print(f"ℹ️ No changes for architecture '{change_file['architecture']}'. Skipping.")
            continue

        copy_gem5_arch_files(patch_file)

        if not copied_FU:
            copy_gem5_fu_files(fu_map)
            copied_FU = True
            
    if copied_FU:
        print("✅ All relevant files copied successfully.")
    else:
        print("ℹ️ No files were copied. No changes detected for any architecture.")