from shared import paths
from stages.s3_copy_gem5 import is_arch_diff

def find_anchor(source_lines: list[str], anchor_lines: list[str]) -> int | None:
    """
    Search for a contiguous, whitespace-insensitive match of anchor_lines
    within source_lines. Each anchor line is matched as a substring of the
    corresponding source line. Returns the starting line index if found, else None.
    """
    stripped_source = [line.strip() for line in source_lines]
    stripped_anchor = [line.strip() for line in anchor_lines]
    anchor_len = len(stripped_anchor)

    for i in range(len(stripped_source) - anchor_len + 1):
        window = stripped_source[i:i + anchor_len]
        if all(a in s for a, s in zip(window, stripped_anchor)):
            return i

    return None


def verify_anchors(patch_file: dict) -> None:

    arch = patch_file["architecture"]
    for file in patch_file["files"]:
        filename = file["file name"]
        relative_path = paths.WORKING_DIR / arch / filename
        if not relative_path.exists():
            raise FileNotFoundError(f"⛔ Source file not found: {relative_path}")

        with open(relative_path, 'r') as f:
            source_lines = f.readlines()

        for edit in file["edits"]:
            anchor_lines = edit["anchor"]
            match_index = find_anchor(source_lines, anchor_lines)

            if match_index is None:
                anchor_text = "\n".join(anchor_lines)
                raise ValueError(f"⛔ {arch}-map anchor text not found in {filename}:\n{anchor_text}")
            # else:
            #     print(f"✅ {arch}-map anchor text found in {filename} for edit ID {edit['id']}.")

def verify_gem5(change_files: dict[str, dict], patch_files: dict[str, dict], fu_map: dict) -> None:
    verify_anchors(fu_map)
    for arch, patch_file in patch_files.items():
        change_file = change_files.get(arch)
        if not change_file:
            print(f"⚠️ No change file found for architecture '{arch}'. Skipping gem5 verification.")
            continue

        if not is_arch_diff(change_file):
            #print(f"ℹ️ No changes for architecture '{change_file['architecture']}'. Skipping gem5 verification.")
            continue

        verify_anchors(patch_file)
    print("✅ All anchors verified successfully for all architectures.")