# Custom Instruction Integration — Workflow Reference

This document describes each stage of the automation pipeline, in execution order, including what each stage reads, writes, and validates.

---

## Pipeline Overview

```
0. Setup
1. Verify Manifests
2. Identify Changes
3. Copy gem5 Source Files
4. Verify Local Anchors
5. Edit Local Copies
6. Verify Local Copies
7. Apply Source Edits to gem5
8. Apply Behavioral Edits to gem5    
9. Update Registries
```


---

## 0. Setup

**Purpose:** Generates required config files from current gem5 version

**Reads:**
- `gem5/src/cpu/FuncUnit.py` - parses "class OpClass(Enum)" and records intrinsic gem5 OpClasses

**Writes:**
- `gem5/src/arch/riscv/insts/static_inst.hh` - adds #include all-behaviors.hh
- `all-behaviors.hh` - target file for behavioral updates
- `gem5-opclasses.json` - list of intrinsic gem5 OpClasses


---

## 1. Verify Manifests

**Purpose:** Confirm each user-authored, per-architecture instruction manifest
is syntactically and semantically valid before anything else runs.

**Reads:**
- `manifests/<arch>-instruction.yaml`
- `templates/instruction-entry.json`
- `gem5-intrinsics/OpClassConfig.json` — list of gem5's built-in opclasses, used to distinguish "custom" vs "intrinsic" opclass entries

**Writes:** None.

**Failure behavior:** Hard stop. No further steps run.

**Internal Pipeline**
1. **VerifyConfigs.py** — Confirms all required per-entry YAML fields are
   present and valid (`name`, `opclass`, `auto_manage`, and
   `latency`/`pipelined` where applicable).
   Reads: `instruction-entry-template.json`, `<arch>-instruction.yaml`
2. **CheckOpclassKind.py** — Determines whether each entry's `opclass` is custom or gem5-intrinsic, using `OpClassConfig.json`. Flags entries where
   `latency`/`pipelined` are set on an intrinsic opclass (see `DESIGN.md` open question on whether this should be a hard validation error).
   Reads: `OpClassConfig.json`, `<arch>-instruction.yaml`
3. **IdentifySameNames.py** — Flags name collisions among instructions, within an architecture's manifest and against gem5 intrinsics.
   Reads: `<arch>-instruction.yaml`

---

## 2. Identify Changes

**Purpose:** Diff each architecture's manifest against the last known-good state to determine what actually needs to change (added, modified, removed).

**Reads:**
- `<arch>-instruction.yaml` (per architecture)
- `<arch>-instruction-registry.yaml` (per architecture)

**Writes:**
- `<arch>-instruction-details.json` — flags changed entries

**Failure behavior:** N/A — this step never fails. If no changes are detected for an architecture, only its bookkeeping is touched.

**Internal Pipeline**
1. **CompareManifestAndRegistry.py** — Diffs each architecture's manifest against its registry.
   Reads: `<arch>-instruction.yaml`, `<arch>-instruction-registry.yaml`
   Writes: `<arch>-instruction-details.json`

---

## 3. Copy gem5 Source Files

**Purpose:** Copy every file that requires edits into an isolated workspace before anything is touched live.

**Reads:**
- `<arch>-instruction-details.json` (flagged entries)
- `<arch>-configs.json` — gem5 file paths relevant to this architecture's decode/FU-generation targets

**Writes:**
- `backups/<timestamp>/<mirrored path>` — full pre-edit snapshot of every file about to be touched (also the rollback source)
- `working-copies/<filename>` — copies of source files to be parsed, edited, and later applied

**Failure behavior:** Hard stop if any required file or path is missing or unreadable. No copies have been edited yet, so no cleanup is needed.

**Internal Pipeline**
1. **CheckFilePaths.py** — Confirms every declared file path exists in the gem5 tree.
   Reads: `<arch>-configs.json`
2. **CheckSourceFiles.py** — Confirms every declared file is present and readable.
   Reads: `<arch>-configs.json`
3. **CopySourceFiles.py** — Copies source files into the local working directory.
   Reads: `<arch>-configs.json`
   Writes: `working-copies/`

---

## 4. Verify Local Anchors

**Purpose:** Confirm every anchor and marker the changeset depends on is
present and unambiguous in the copied files, before any edit is attempted.

**Reads:**
- Working copies (from Step 3)
- `anchors/versions/<gem5_target_version>/anchors.json`
- `<arch>-instruction-details.json` (per flagged entry)

**Writes:** None.

**Failure behavior:** Hard stop. Indicates either a gem5 version mismatch or
a corrupted/outdated `<arch>-configs.json` or `FU-configsjson `

**Internal Pipeline**
1. **CheckAnchors.py** — Confirms every anchor referenced by `-configs.json` exists in the working copies.
   Reads: `-configs.json`, working copies
2. **CheckMarkers.py** — Confirms every marker required by a flagged entry exists in the working copies.
   Reads: `-configs.json`, `<arch>-instruction-details.json`, working copies

---

## 5. Edit Local Copies

**Purpose:** Apply insertions, updates, and removals to the working copies,
at block granularity — including both the instruction's decode-side edit and
its dedicated FU definition (when `opclass` is custom).

**Reads:**
- Working copies
- `<arch>-instruction-details.json` Changeset (from Step 2)
- `<arch>-configs.json` Per-instruction templates (render decode boilerplate and, where applicable, dedicated-FU boilerplate around anchor points)

**Writes:**
- Working copies only — `gem5/` and `backups/` are never touched.

**Failure behavior:** If any single block operation fails (e.g., marker not
found for a modify/remove), abort remaining edits on that file, flag it, and
do not proceed to Step 6 for that file's changeset.

**Internal Pipeline**
1. **FindMarker.py** — Locates the marker(s) for each changeset entry.
   Reads: `<arch>-instruction-details.json`, `<arch>-configs.json`, working copies
2. **CreateMarker.py** — Creates new START/END markers for new entries.
   Writes: working copies
3. **RenderInline.py** — Renders the inline code to insert (decode logic and,
   where applicable, dedicated-FU config), from the entry template.
   Reads: `<arch>-instruction-details.json`
4. **InsertInline.py** — Writes the rendered inline code into the
   located/created block(s).
   Writes: working copies

---

## 6. Verify Local Copies

**Purpose:** Final safety gate before any real gem5 file is touched.
Confirms the edited copies are internally consistent.

**Reads:**
- Working copies (post-edit)
- Changeset

**Writes:** None.

**Checks performed:**
- Every `// START` marker has exactly one matching `// END` marker (no
  orphans, no mismatched nesting).
- No duplicate block IDs within a file.
- Each anchor's sanity-check string still appears exactly once post-edit.
- Recomputed block hashes differ from the previously stored hash only for
  entries actually in the changeset — no unrelated block was altered.
- `auto_manage: false` blocks are byte-for-byte unchanged from the pre-edit
  copy.

**Failure behavior:** Hard stop. Working copies are discarded; `gem5/` and
`backups/` remain untouched, so the real tree is guaranteed unaffected.

---

## 7. Apply Source Edits to gem5

**Purpose:** Commit validated changes to the real gem5 tree.

**Reads:**
- Working copies (validated, from Step 6)

**Writes:**
- `gem5/<target paths>` — each file written via write-to-temp + atomic
  rename, one file at a time, so a mid-process crash cannot leave a
  partially-written file in the real tree.

**Failure behavior:** If a write fails partway through the file list,
remaining unwritten files are left alone. Already-written files can be
restored from `backups/<timestamp>/` via the rollback operation. Failure is
logged with the exact list of files committed vs. not.

---

## 8. Apply Behavioral Edits to gem5

**Purpose:** Apply behavioral edits, update behavior directory. 

**Writes:**
- `applied-behaviors/` 
- `all-behaviors/`
- `all-behaviors.hh/`

**Internal Pipeline**
1. **CheckBehaviors.py** — ensures `all-behaviors.hh/` exists and is #include in `static_inst.hh`
2. **UpdateBehaviorDirectories.py** — Identifies any removed/added instructions and updates `applied-behaviors/` and `deprecated-behaviors/`
   Reads: `applied-behaviors/`, `deprecated-behaviors/`, `<arch>-instruction-details.json`
3. **UpdateHeader.py** — Updates header file with necessary #include statements
   Writes: `all-behaviors.hh/`
---

## 9. Update Registries & Details

**Purpose:** Record the new applied state so the next run's comparison
(Step 2) and drift checks are accurate.

**Reads:**
- `<arch>-instruction.yaml` (per architecture)

**Writes:**
- `<arch>-instruction-registry.yaml` (per architecture)
- `<arch>-instruction-details.json` — clears flags

**Failure behavior:** If this step fails after Step 7 has already succeeded,
the real gem5 files are already correct — only bookkeeping failed to update.
Logged as a warning requiring manual reconciliation on the next run
(otherwise Step 2's comparison would mis-detect drift).

**Internal Pipeline**
1. **UpdateRegistries.py** — Overwrites each architecture's implemented
   registry with its current manifest.
   Reads: `<arch>-instruction.yaml`
   Writes: `<arch>-instruction-registry.yaml`
2. **ClearChangesetFlags.py** — Clears the changed-entry flags now that
   they've been applied.
   Writes: `<arch>-instruction-details.json`

---

## Supporting Operation: Rollback

Not part of the linear pipeline — invoked manually, or automatically if
Step 7 fails partway.

**Reads:**
- `backups/<timestamp>/` snapshot corresponding to the failed run.

**Writes:**
- Restores `gem5/<target paths>` to their pre-run state.

**Checks performed:**
- Confirms a backup snapshot exists for every file about to be restored,
  before restoring any of them (avoids a partial rollback).

---

## Reference: Instruction & FU File Locations

### OpClass
- gem5-intrinsic opclasses defined in `gem5/src/cpu/op_class.hh`
- Custom opclasses (generated per-instruction, dedicated FU) built into
  `riscv-workspace/custom-instructions/build/RISCV/enums/OpClass.hh`

### Dedicated Functional Units (custom opclass instructions only)
**Source files (RISC-V):**
- `gem5/src/cpu/FuncUnit.py`
- `gem5/src/cpu/o3/FUPool.py`
- `gem5/src/cpu/o3/FuncUnitConfig.py`
- `gem5/src/cpu/minor/BaseMinorCPU.py`

**Data/config files:**
- `anchors/versions/<gem5_target_version>/anchors.json` — inline local
  anchors (regex), per-instruction templates, marker templates


---
