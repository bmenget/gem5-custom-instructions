# Design: Custom Instruction Integration for gem5

This document captures the *why* behind the system. For step-by-step execution
details (reads/writes/checks per stage), see `workflow.md`.

---

## Problem

gem5 requires hand-editing several source files (decoder tables, opclass
enums, functional unit pools/configs) to add a custom instruction or
functional unit. This is repetitive, error-prone, and easy to do
inconsistently across a team or across time.

This tool lets a user define custom instructions and functional units via a
central YAML manifest plus per-instruction behavior files, then automatically
validates, diffs, and applies the resulting changes to gem5 source files in a
non-invasive, idempotent way.

## Goals

- Single manifest as the user-facing source of truth for instruction/FU definitions.
- Idempotent runs — re-running with no manifest changes should be a no-op.
- Non-invasive to the gem5 tree — no edit is committed to real gem5 files
  until it has been fully validated.
- Detect drift — if gem5 files were hand-edited outside the tool since the
  last run, catch it rather than silently overwrite it.
- Semi-modular — isolate ISA logic from FU logic so each can evolve
  independently, and support multiple target architectures (RISC-V, x86, ARM)
  without restructuring the pipeline.

## Non-Goals

- Toolchain/assembler integration (binutils/GCC mnemonic registration). Users
  invoke custom instructions via inline raw encoding; this is explicitly out
  of scope.

---

## Architecture Overview

```
instructions.yaml / FUs.yaml (user-authored)
        │
        ▼
  Orchestrator ── drives the 9-stage pipeline (see workflow.md)
        │
        ├── ISA Engine (arch-specific: riscv / x86 / arm registry)
        └── FU Engine   (shared across archs)
        │
        ▼
  Staging workspace (copies of gem5 files)
        │
        ▼
  gem5 source tree (only written after full validation)
```

Both engines read from and write results into a single shared
`PipelineContext` per run (changeset, resolved arch, instruction↔FU
resolution table, staging paths, anchor hash state). Neither engine calls the
other directly — this keeps them independently testable and swappable while
still letting the orchestrator resolve cross-engine dependencies (e.g., an
ISA decode edit referencing a FU the FU engine just defined this run).

---

## Key Decisions

### Dual-manifest system
**Decision:** `instructions.yaml` (user-editable, current desired state) is
kept separate from `.implemented_manifest.yaml` / registries (last known-
applied state).
**Why:** Gives the tool a clean diff target (Step 2) without needing to parse
gem5 source to infer current state. The registry is the tool's own memory of
what it already did.

### Anchor-based insertion with drift detection
**Decision:** Each managed edit is bounded by START/END markers with a
content hash, checked before overwrite (Option B — warn on drift).
**Alternative considered:** Unconditionally overwrite the managed region
every run.
**Why rejected:** Silent overwrite would clobber any hand-edit a user made
inside a "managed" region without them ever finding out. The added mechanism
(hash storage + drift check) is justified because the failure mode it
prevents — silent data loss — is severe, even though it adds real complexity.

### `auto_manage` status per instruction
**Decision:** Each instruction/FU entry has a status flag controlling whether
the tool touches its gem5-side generated blocks at all.
**Why:** Cleanly separates automation-owned regions from user-owned regions
without ambiguity — a `false` entry is structurally excluded from staging,
not just skipped by convention.

### Behavior files: always live user-space, decoupled from changeset
**Decision:** Behavior files are never frozen, and their manifest-to-file
contract (operand count/type signature) is validated unconditionally every
run, independent of which entries are in this run's changeset.
**Why:** A behavior file can be hand-edited at any time, independent of a
manifest change — validating only the changeset would miss drift introduced
between runs.

### Behavior files: per-entry, not a single shared file
**Decision:** Each instruction/FU gets its own behavior file, aggregated into
a script-generated, script-owned include file (never hand-edited).
**Alternative considered:** One shared header for all entries.
**Why rejected:** Scaffolding a new entry (pre-populating the correct
parameter signature — e.g. GPR count) into a shared file means writing into
a file that already contains other hand-written code — a much riskier
operation than creating a new file. Per-entry files make "does this need
scaffolding" a simple existence check (create-if-absent, never overwrite),
and make orphan detection (entry removed from manifest, file still present)
an explicit diffable check instead of an invisible stale section.

### Staging / copy-based pipeline vs. in-place editing
**Decision:** All edits happen on copies in a staging workspace; the real
gem5 tree is only written at a final atomic apply step.
**Alternative considered:** Edit gem5 files directly, in place.
**Why rejected:** In-place editing risks partially-applied changesets if one
file in a multi-file edit fails after another has already succeeded, with no
clean recovery path. Copy-first makes validation happen against the actual
bytes about to ship (not a prediction of them), makes atomic
write-then-rename possible at apply time, and gives rollback something
concrete to restore from (the untouched pre-edit original).

### ISA engine as a per-architecture registry
**Decision:** `ISAEngine` is an abstract interface; each target architecture
(RISC-V, x86, ARM) is a separate implementation registered by name.
**Why:** ISA-side edits (decode tables, opcode structures) are inherently
architecture-specific and don't share structure. Adding a new target
architecture later means adding one file and one registry entry, with no
changes to the orchestrator or pipeline.

### FU engine kept separate from the ISA engine
**Decision:** FU edits (functional unit pool/config) are handled by a
sibling engine, not folded into the ISA engine.
**Why:** FU-pool mechanics are largely architecture-agnostic even though the
instructions that reference a given FU are architecture-specific. Keeping
them separate — communicating only through the shared `PipelineContext` —
means each can be modified, tested, or extended without touching the other.

### Per-gem5-version target profiles
**Decision:** File-layout knowledge (opclass lists, file paths, sanity-check
strings) for a given gem5 version lives in a dedicated target profile,
separate from the per-instruction anchor JSON.
**Why:** Anchors change per changeset run (new instructions append new
anchors); target profiles change only when gem5 itself changes (new version,
moved files, renamed opclasses) — a much rarer, more deliberate update.
Keeping them separate avoids conflating "the anchor location was wrong" with
"the generated code changed" during drift checks.

---

## Explicitly Rejected Approaches

Documented here so they aren't silently re-proposed later without the
context of why they didn't fit:

- Unconditional overwrite of managed gem5 regions (no drift check).
- Single shared behavior-definition header for all instructions/FUs.
- Direct in-place editing of gem5 source files (no staging/copy step).
- Monolithic ISA engine handling all architectures in one implementation.