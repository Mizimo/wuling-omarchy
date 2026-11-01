# Decisions

Owner decisions that bind the design. Newest first.

## 2026-11-01 — agent-ready and long-lived

The owner: WULING follows Omarchy's way of working with agents, and has to stay easy to maintain and to keep
reshaping for years. Concretely, after Omarchy 4.0.6 (`AGENTS.md`, `agents/skills/`, `default/agents/skills/omarchy/`,
`omarchy commands --json`, `shell/plugins/agents/`):

- **Your agent can change WULING safely.** WULING ships a `wuling` skill beside Omarchy's own in the agents' skill
  folders (`~/.agents/skills`, `~/.claude/skills`, `~/.codex/skills`, …), written like Omarchy's: where everything
  lives, what is never edited, how to change colour, type, motion, sound and layout, how to verify, how to undo.
- **The repository is agent-first, like Omarchy's**: `AGENTS.md` (and `CLAUDE.md` → `@AGENTS.md`) with task guides in
  `agents/skills/` — plugin work, theme work, visual verification, acceptance tests in a disposable VM — style rules
  and test entry points.
- **Self-describing commands.** Every WULING command carries Omarchy-style metadata (summary, args, examples) and can
  be listed in machine-readable form.
- **One source for the look.** Design tokens live in one place. The theme files (`colors.toml`, `shell.toml`,
  `hyprland.lua`, app templates) and the plugins' styling are generated from it or read it; changing the look means
  changing tokens, not hunting through QML.
- **Small, separable parts.** Each component is its own plugin with a manifest and a README that says what each file
  owns; shared visuals come from one WULING UI kit. Any part can be switched off and Omarchy's own takes over.
- **Data apart from display.** As in Omarchy's agents panel, state is gathered by commands that print JSON and the
  QML only displays it, so behaviour can be tested from the command line.
- **Your changes survive updates.** Personal overrides live in user config and hot-reload; updating WULING never
  overwrites them.
- **Verifiable.** Automated checks an agent can run before and after a change: lint, `omarchy plugin validate`,
  screenshot comparison in a VM.
- **Agents in the interface follow Omarchy.** Omarchy's agent features — the agents usage widget and panel,
  Super+Shift+Ctrl+A for the default agent, crash diagnosis — get WULING's look; Claude Code already follows the theme
  through Omarchy's template. How prominent agents are in the bar, the Terminal and Dispatch is offered as options in
  the design report.

## 2026-11-01 — a new project

- **Scope.** WULING is rebuilt from scratch on Omarchy 4. Only the visual language carries over from the earlier
  WULING (niri) project, and it is *adjusted*, not reinvented: the old design spec is the base.
- **Logic follows Omarchy.** Where things live and which keys do what stay Omarchy's; its default keybindings keep
  working.
- **WULING's own components:** a full replacement of the bar; the Terminal panel, which coexists with Omarchy's
  panels; notifications and the OSD, answering the same IPC targets as Omarchy's (`notifications`, `osd`) so
  Omarchy's keys reach them; the power menu with long-press confirmation; UI sounds.
- **Dispatch — two variants; the owner picks after comparing them:**
  - *A · UI only* — takes Super+Space; Omarchy's menu tree, levels and operation logic are unchanged, only the look
    and feel are WULING's.
  - *B · beside Omarchy* — Super+Space stays Omarchy's (themed) menu; Dispatch opens from another key.

  Both are compared in the design report through keyboard-operable web prototypes. Only the chosen one is built.
- **Theme only:** lock screen, polkit dialog, Omarchy's menus and panels, apps, and the boot unlock screen (through
  Omarchy's own Plymouth-from-theme command).
- **Not doing:** a boot animation, an overview, desktop widgets, our own lock screen or polkit agent, copies of
  Omarchy code.
- **Three visual directions** in the design report — *as before*, *more restrained*, *stronger Endfield* — judged
  first on how well they serve daily use.
- **Design gate.** The owner approves the design report before any component is implemented.
- **Public.** Built to public standards: any resolution and multiple monitors, zh-Hant / zh-Hans / en, English
  documentation. License GPL-3.0-or-later.
- **Official assets** (Endfield Industries mark, Hongshan Academy of Sciences crest, the PV quotation, place names)
  live in the repo as in the old design. Canon scene art and the login music never enter the repo; they are
  installed locally.
- **Login music:** kept, off by default.
