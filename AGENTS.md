# Working on WULING

WULING is a set of Omarchy themes and independent omarchy-shell plugins. Read
`design/DECISIONS.md`, then `design/DESIGN.md`, then `docs/BRIEF.md`. Decisions
take precedence. `research/omarchy-shell-api.md` records the tested 4.0.6 and
4.5.0 boundaries; observations are not promises about later releases.

## Ownership

- Design owns `design/`, `docs/BRIEF.md`, `README.md` and `LICENSE`.
- Implementation owns `tokens/`, `theme/`, `kit/`, `plugins/`, `bin/`, `tools/`,
  `fonts/`, `sounds/`, `install`, `tests/`, agent guides and `research/`.
- Verification owns `review/`. Preserve other contributors' changes in this
  shared working tree. Stage and commit only the paths belonging to your task.
- Generated themes and style data are committed; edit their source in `tokens/`
  and regenerate. User overrides are separate and never replaced by updates.

## Boundaries

- Use Omarchy's extension points. Never modify, copy or fork Omarchy code.
  Runtime imports of installed modules need the documented compatibility gate.
- Runtime dependencies are stock Omarchy: Python's standard library, bash, jq,
  Quickshell and official Omarchy commands. Installation never uses sudo.
- Preserve Omarchy keys and authentication. Add only the keys in DESIGN.
- Keep credentials, personal data, network addresses, raw logs/captures, canon
  artwork and music out of git. Use synthetic data in fixtures. Approved logos
  and the designed backgrounds are distributable project assets.
- Graphical/system tests belong in disposable VMs. Do not operate another
  person's desktop or shared services merely to validate a change.
- Follow the current task's commit identity and publication instructions.

## Verification

Run `tools/check` before delivery. It checks token generation, metadata,
syntax, runtime tests and staged-file privacy. `tools/generate --check` compares
generated text byte for byte and image hashes; it does not render VM previews.
For graphical work, use the matrix in BRIEF and record actual versions,
input method, observed state and remaining hardware limitations. IPC success
alone is insufficient. Keep evidence outside the repository.

Task guides: [themes](agents/skills/themes.md),
[plugins](agents/skills/plugins.md),
[verification](agents/skills/verification.md).
