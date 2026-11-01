# Maintainability proposal

Design input for A-1 under decisions of 2026-11-01 and inbox v399. This is a
proposal, not an installer, product layout or approved implementation. Interface
constraints and pinned source references are in [the API study](omarchy-shell-api.md).

## Repository and ownership

Proposed layout after design approval:

```text
AGENTS.md                    entry point, ownership and verification rules
CLAUDE.md                    refers to AGENTS.md
agents/skills/               repository task guides
  plugins.md                 lifecycle, scoped APIs, data/display separation
  themes.md                  tokens, generation and theme consumers
  verification.md            checks, VM matrix, visual review and restoration
skills/wuling/               user-facing skill installed beside Omarchy skills
tokens/                      one versioned palette/type/spacing/motion/sound source
ui/                          WULING-owned shared visual components
plugins/<component>/         independent manifest, entry points and README
theme/                       generated theme outputs and permitted assets
tools/                       token generation, user-level install/update/remove
tests/                       command/model checks and disposable-VM acceptance
research/                    decisions' evidence and compatibility studies
review/                      verifier reports; raw evidence remains outside git
```

Each component README states its entry points, state owner, public messages,
settings schema, fallback, version requirements and independent removal path.
Do not make the bar own every component's data. Disabling Terminal should not
stop notifications, sound or an Omarchy panel. Share a small WULING UI kit, but
respect the upstream prohibition on internal plugin symlinks. A release can
generate coherent copies of our kit into plugin artifacts, recorded by one
kit version/hash, instead of independent manually edited copies.

## One token source and explicit generation

Use one machine-readable token document with semantic roles and typed units.
Include palettes, type scale, dimensions, state treatments, motion and sound
event mappings. Generate:

- `colors.toml` and `shell.toml` for Omarchy consumers;
- WULING QML/JSON style data from the same resolved tokens;
- permitted app theme outputs or explicitly installed user templates where
  official git-theme filtering excludes executable configuration;
- a manifest linking generated output hashes to token/schema versions.

Generated files carry provenance and are never hand-edited. Generation must be
deterministic; a check regenerates into a temporary directory and compares
bytes. Validate token type/range and contrast at that boundary. Do not treat
shell.toml as a global style sheet: only consumers of a token change. Do not
promise a git-installed theme's hyprland.lua will be used; upstream filters it.
Plymouth customization remains a separate optional official system operation,
outside the no-sudo WULING installer.

## User changes survive updates

Keep the installed release, user configuration and runtime state separate:

- code/themes under documented user-owned installation paths;
- user token overrides in `~/.config/wuling/`, with a versioned schema;
- component options through Omarchy's inline shell.json entries where suitable;
- caches and transient collector output under XDG cache/state directories.

Resolve defaults → selected WULING variant → user overrides. Show the resolved
values and their origin in a diagnostic command. Updating replaces generated
defaults/code, never user overrides. A migration reads the old schema, writes
an explicit new version with a recoverable backup, and reports conflicts.
Avoid hidden settings written into the plugin checkout.

Installation should first construct a concrete plan: plugin ids, files,
built-ins being replaced, effective keys, required Omarchy version and rollback
actions. Record only owned changes. Refuse conflicting existing plugin ids,
skills or user key overrides instead of overwriting them. For shared files,
remove only unchanged owned blocks and preserve concurrent user edits.

## Distribution and lifecycle

One `omarchy plugin add` installs one root manifest; it cannot install the
planned monorepo. Choose between generated per-plugin distribution repositories
and a user-level installer using Omarchy's manual plugin directory mechanism.
The theme needs its own install path. The choice belongs in the design/release
decision, not an accidental build-script convention.

Record the previous active bar and disabled built-ins. Replace targets in an
order that avoids simultaneous notification servers or duplicate IPC targets.
On removal, restore only state still owned by WULING. Use current upstream
defaults when removing an unchanged key override, not a copied old defaults
file. A multi-plugin release should be staged and validated as a whole before
switching any live configuration; a failed validation leaves the prior release
available. Compatibility tests must include partial component enable/disable.

The source study identifies distinct 406/450 contracts for layout sections,
notification methods, keys and locale modules. Put those adaptations behind a
small version/feature boundary. A feature check must include facade lifetime,
not just the presence of a manifest kind: the 406 VM revokes a third-party
menu facade after misclassifying a delegate sequence. Treat that as an upstream
compatibility blocker, and report it rather than copying or patching Omarchy.
For Dispatch A, runtime use of the installed
MenuModel.js needs an explicit maintenance decision: it is an internal helper,
not the full live menu model, and provider orchestration still changes outside it.

## Agent-facing skill and commands

Install a `wuling` skill into each existing supported agent skill directory,
beside Omarchy's own. Its source should live in a stable user-owned WULING
directory, with links recorded in the installation manifest. First verify that
`wuling` is absent or already owned by this installation. Removal unlinks only
links still pointing at our target; it never removes an agent's whole skill
directory or replaces Omarchy's skill. The VM sentinel test covers the current
official update and requested relinking migrations.

The skill explains paths, supported changes, tokens/overrides, forbidden
upstream edits, per-component lifecycle, checks, evidence location and rollback.
It should tell agents how to make a reviewable change without prescribing
provider-specific credentials, permissions or model flags. Repository guides
describe implementation work; the installed skill describes safe user changes.

Provide a separate `wuling` command family with Omarchy-style metadata and
`wuling commands --json`. The upstream command router does not discover
arbitrary PATH executables. Proposed verbs include inspect, validate, status,
theme resolve, component enable/disable and uninstall-plan. Stable JSON output
has a schema version, explicit errors and documented units. Human output may
change wording without breaking QML consumers.

Reuse `omarchy-agent`, `omarchy-agent-prompt`, its default-agent key and crash
diagnosis workflow. Read existing agent usage JSON; do not introduce another
credential store or silently start provider collectors per view. Use synthetic
records for tests of absent agents, stale/error data and new schema fields.

## Verification an agent can run

1. Validate token/settings schemas, deterministic output, command metadata and
   model fixtures without a graphical session.
2. Run `omarchy plugin validate` on every complete plugin artifact. Check
   imports/entry points and exercise them in the pinned VM; validation alone
   is not a QML or rendering test.
3. Install into a disposable stock VM with before/after config inventories.
   Check bar fallback, every screen, focus/Esc/outside-click, native key paths,
   D-Bus ownership and restoration after independent component removal.
4. Compare 1366×768 and 1920×1080, fractional scale, hotplug and the supported
   language set. Inspect captures and short motion recordings. QMP input
   verifies compositor shortcuts; a direct IPC success is insufficient.
5. Measure stock and candidate idle CPU/PSS with the same VM/render backend,
   warmup and paired sessions. Keep shell and host rendering cost distinct.
6. Exercise update with a user's edited tokens, plugin options and key file;
   confirm they survive. Run failure/rollback and no-sudo install checks.
7. Scan staged changes for private paths, addresses, credentials, canon art,
   music and raw evidence before committing. Report exact versions and limits.

Upstream test/all is a dependency regression suite, not a WULING plugin test
entry point. Upstream graphical acceptance supplies useful conventions and
helpers, but runs only in disposable VMs. WULING should expose one concise
test entry point that records which layers ran and which still need the owner
or verifier. No product code is introduced by this proposal.
