# Design: Custom Instruction Integration for gem5

This document captures the *why* behind the system. For step-by-step execution
details (reads/writes/checks per stage), see `workflow.md`.

> **Revision note:** This version reflects a scope change — `FUs.yaml` as a
> separate manifest has been removed. Functional-unit characteristics
> (`latency`, `pipelined`, and `fu_count` as of manifest schema v2) are now
> declared inline on each instruction entry. Each instruction still maps to
> its own dedicated FU only — `fu_count` sets how many parallel instances of
> that private FU exist, it does not enable sharing across instructions. See
> "Key Decisions" and "Open Questions" below for what this changes and what's
> still unresolved.

---

## Problem

gem5 requires hand-editing several source files (decoder tables, opclass
enums, functional unit pools/configs) to add a custom instruction or
functional unit. This is repetitive, error-prone, and easy to do
inconsistently across a team or across time.

This tool lets a user define custom instructions via a manifest, with the
tool automatically validating, diffing, and applying the resulting changes to
gem5 source files in a non-invasive, idempotent way.

## Goals

- Single manifest per architecture as the user-facing source of truth for
  instruction definitions.
- Idempotent runs — re-running with no manifest changes should be a no-op.
- Non-invasive to the gem5 tree — no edit is committed to real gem5 files
  until it has been fully validated.
- Detect drift — if gem5 files were hand-edited outside the tool since the
  last run, catch it rather than silently overwrite it.
- Semi-modular — isolate ISA-side logic per target architecture (RISC-V, x86,
  ARM) so each can evolve independently.
- Favor simplicity of use over configurability where the tradeoff is
  reasonable (see "single FU per instruction," below).

## Non-Goals

- Toolchain/assembler integration (binutils/GCC mnemonic registration). Users
  invoke custom instructions via inline raw encoding; this is explicitly out
  of scope.
- Shared/pooled functional units serving multiple instructions. Each
  instruction owns its own dedicated FU (optionally replicated via
  `fu_count` for parallel in-flight throughput — see "Single dedicated FU
  per instruction" below), but that FU is never shared with a different
  instruction. This is a deliberate reduction in configurability, made in
  exchange for a much simpler manifest, engine, and validation surface. The
  project can be expanded to support true cross-instruction FU pooling later
  if needed.

---

## Architecture Overview

```
instructions_<arch>.yaml (user-authored, one per target architecture)
        │
        ▼
  Orchestrator ── drives the pipeline (see workflow.md)
        │
        ▼
  ISA Engine (arch-specific: riscv / x86 / arm registry)
   — now also responsible for emitting each instruction's dedicated
     FU definition inline, since there is no separate FU manifest
        │
        ▼
  Staging workspace (copies of gem5 files)
        │
        ▼
  gem5 source tree (only written after full validation)
```

> **Open question:** with `FUs.yaml` and the standalone FU engine removed,
> it's not yet decided whether FU-definition emission stays inside the ISA
> engine (as drawn above) or remains a separate sibling engine that the ISA
> engine's output simply depends on more tightly than before. See Open
> Questions.

---

## Key Decisions

### Per-architecture manifest files
**Decision:** Each target architecture gets its own manifest file
(`instructions_riscv.yaml`, `instructions_x86.yaml`, ...) rather than one
file containing multiple `architecture:`/`instructions:` blocks, and rather
than a single shared manifest with an `arch` field per entry.
**Why:** A YAML document can't safely repeat a top-level key (a second
`architecture:`/`instructions:` block in the same file silently overwrites
the first in most parsers). Separate files also mirror the ISA engine
registry directly — the orchestrator discovers manifests, and each file's
`architecture` field selects the engine that handles it — and keeps git
diffs scoped to one architecture at a time.

### Single dedicated FU per instruction; `FUs.yaml` removed
**Decision:** There is no separate functional-unit manifest. Each instruction
declares `latency`, `pipelined`, and `fu_count` directly, and the tool
generates a dedicated FU for that instruction — but only when the
instruction's `opclass` is a **custom** opclass, not an existing
gem5-intrinsic one.

**`fu_count` clarification (schema v2):** `fu_count` controls how many
*parallel instances* of the instruction's own dedicated FU are generated —
i.e. how many of that instruction can be in flight at once. It does **not**
reopen FU sharing across different instructions; each custom instruction
still gets its own private, dedicated FU. Only the number of copies of that
private FU is configurable. This keeps the "single FU per instruction"
simplification intact — `fu_count` is a throughput knob, not a pooling
mechanism.
**Alternative considered:** A shared `FUs.yaml` with FU/OpClass consistency
validation (the earlier design), allowing multiple instructions to share one
FU.
**Why rejected (for now):** FU pooling added real configurability but at the
cost of a second manifest, a second registry, and cross-manifest consistency
checks (`VerifyOpClassInFU.py` and friends). Collapsing FU definition into
the instruction entry removes an entire class of file and validation, at the
cost of not being able to share one FU across instructions. Acceptable
tradeoff for now; revisit if pooling becomes a real need.
**Open sub-question:** when `opclass` matches an existing gem5-intrinsic
class (e.g. `IntALU`), no dedicated FU is created — so `latency`/`pipelined`
have nothing to attach to. These fields should likely be rejected by
validation (not silently ignored) when `opclass` is intrinsic, so a user
doesn't set `latency: 999` on an `IntALU` instruction and wonder why nothing
changed. Not yet confirmed.

### Instruction `id` decoupled from `name`
**Decision:** Each instruction has a user-assigned `id` (bookkeeping number)
in addition to `name`. The behavior file is located by `id` only
(`behavior/<id>.cc`) — never by `name`.
**Why:** Lets a user rename an instruction's `name` freely without orphaning
or needing to regenerate its behavior file. `name` is purely
cosmetic/display; `id` is the only stable link to the behavior file.
**Consequence:** `id` should be treated as immutable once a behavior file
exists for it. Changing `id` after the fact orphans the old file and
scaffolds a new one — this should be an explicit, flagged operation, not a
silent side effect.

### Operands and encoding are auto-determined, not user-supplied
**Decision:** The manifest no longer requires the user to specify `operands`
or `encoding` — the script determines these automatically.
**Why:** Reduces manifest surface area and the chance of a user hand-writing
an inconsistent operand signature. (Mechanism for *how* this is determined —
parsed from the behavior file itself, or some other source — is not yet
specified; see Open Questions.)

### `auto_manage` replaces `managed`/`manual` status naming
**Decision:** The per-instruction flag controlling whether the tool owns the
gem5-side generated block is named `auto_manage` (boolean), using an
underscore rather than a hyphen.
**Why:** Hyphens are valid YAML keys but not valid Python identifiers;
avoiding one avoids needing field-alias handling in code that maps manifest
entries to objects.

---

## Open Questions

- **Does FU-definition emission live inside the ISA engine, or as a separate
  engine the ISA engine depends on?** With `FUs.yaml` gone, the clean
  ISA/FU engine split from the original design no longer maps onto two
  manifests the way it did. Needs a decision before the engine layer is
  restructured.
- **How are `operands`/`encoding` actually auto-determined?** From parsing
  the behavior file's function signature? From the `opclass`/architecture
  combination? Not yet specified.
- **Should `latency`/`pipelined` be rejected (not just ignored) when
  `opclass` is a gem5-intrinsic class?** See "Single dedicated FU per
  instruction" above.
- **Manifest discovery mechanism.** With one file per architecture, does the
  orchestrator glob a fixed directory (e.g. `manifests/instructions_*.yaml`),
  or is the file list explicit/configured? Not yet specified.
- **Step 8 ("Apply Behavioral Edits to gem5") is named in `workflow.md` but
  undocumented.** Likely home for the unconditional behavior-file contract
  validation — still needs to be written up, and now also needs to account
  for operands being auto-determined rather than user-declared.
- **FU-before-ISA sequencing assumption.** Carried over from the earlier
  design; may be moot now that FU definition is inline with the instruction
  rather than a separate changeset category — needs re-evaluation given the
  FU-engine-location question above.
- **Namespacing for per-entry behavior files.** Two entries could
  unknowingly define a same-named helper function, invisible until the
  aggregator pulls both in.
- **Schema versioning for manifest/registry files.** `schema_version` is
  present in the current template; enforcement logic (what happens on
  mismatch) not yet implemented.

---

## Explicitly Rejected Approaches

Documented here so they aren't silently re-proposed later without the
context of why they didn't fit:

- Unconditional overwrite of managed gem5 regions (no drift check).
- Single shared behavior-definition header for all instructions.
- Direct in-place editing of gem5 source files (no staging/copy step).
- Monolithic ISA engine handling all architectures in one implementation.
- A shared `FUs.yaml` manifest with pooled functional units serving multiple
  instructions (superseded — see "Single dedicated FU per instruction").
- Multiple `architecture:` blocks inside one manifest file (invalid YAML
  pattern — repeated top-level keys silently overwrite).