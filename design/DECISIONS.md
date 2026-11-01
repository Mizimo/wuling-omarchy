# Decisions

Owner decisions that bind the design. Newest first.

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
