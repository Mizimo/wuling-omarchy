# Sound

An independent keep-loaded service plays the original synthesized WULING cues
through `pw-play`. Four cue voices and one optional music stream bound overlap;
busy voices drop new cues. Repeated identical cues are rate limited. There are
no idle timers after the one-second login fallback and no status collector.
System mute stops active playback; cue gain is 0.6 times the requested level,
then the system's sink volume applies. No Qt Multimedia is loaded.

`sounds` selects essential (no hover/tick), full, or off. The native notification
DND target gates notify/alert and login music; a missing response is silent.
The native Omarchy menu has no hook and remains silent. Disabling this plugin
stops its children and leaves all visual components independent.

`wuling.sound play <cue> <level>` is the internal IPC (level 0..1);
`wuling.sound state` exposes bounded counters and playback state, no file path.
`wuling.sound login` attempts the user-supplied `login_music` once per compositor
session; a private runtime marker also prevents replay after shell restarts.
The default is unset. Music is not copied, stored or distributed by WULING.
Previewing Arrival never requests login music. Session motion may request it at
arming; a one-second fallback covers a disabled session component.

Supported: Omarchy 4.0.6 and 4.5.0-rc2. Test on a private null sink only. Restore
the test default sink and remove the null sink afterward.
