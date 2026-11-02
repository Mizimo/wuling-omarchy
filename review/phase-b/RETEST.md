# Phase B: three-finding retest

Inbox v163 (the v162 retest scope), product `5cc562f8e4cc27db9e65ec071fecb40df9077bdf`. Both independent Omarchy 4.0.6 and 4.5.0-rc2 VMs started from the verifier's retained clean checkpoint. All three findings in the [original report](README.md) are closed in this retest.

| Finding | Independent check | Result on both versions |
|---|---|---|
| P1 broad native-theme rollback | Repeat the original pause around the real native theme setter; write an unrelated application setting concurrently; uninstall | Concurrent write survives and its value never enters the rollback journal |
| P1 narrow ownership boundary | Activate the real native Code JSONC writer with a separate no-op launcher; add a concurrent unrelated member/comment, preserve mode, then explicitly change the color theme before uninstall | Unrelated content, mode and subsequent explicit theme choice survive; all three managed dconf keys restore while an unrelated cursor-size change survives |
| P3 empty state residue | Fail against a read-only skill destination; distinguish newly created empty state from a pre-existing empty directory; interrupt late fc-cache and recover | New empty state removed; pre-existing directory retained; interrupted transaction recovers |
| P3 argument errors | Unknown verb, incomplete command and invalid options | Schema 1 JSON error and nonzero exit |

Native menu, calendar, terminal and GTK before/after pairs were inspected. The original native theme and visible appearance return; final configuration/font/skill inventories match exactly. The first 4.5 preinstall menu/calendar frames had black surroundings, but later preinstall app frames were normal, so this is not attributed to WULING. These VMs have no editor GUI: the Code test exercises the real native file writer, not an editor rendering claim. Native cache maintenance is outside the configuration restoration claim.

Private evidence: `wb1/verifier-v162/vm{406,450}/b-*.txt`, `b-final-diff.json` (both empty), `b-final-guest-evidence.tar.gz`, and `shots/b-before-*`, `shots/b-after-*`. The completed original B acceptance was not repeated beyond these fixes and their ownership controls. See [phase C](../phase-c/README.md) for this round's hardware work, limitations and cleanup.
