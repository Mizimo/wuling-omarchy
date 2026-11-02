.pragma library
// Interpret Omarchy's public OSD payload, without reading any desktop state.
function state(payload) {
    let p;
    try { p = JSON.parse(payload || "{}"); } catch (_) { return null; }
    if (!p || typeof p !== "object" || Array.isArray(p)) return null;
    const message = String(p.message || "");
    const value = parseInt(p.value, 10);
    const maximum = parseInt(p.max === undefined ? 100 : p.max, 10);
    const duration = parseInt(p.duration === undefined ? 1200 : p.duration, 10);
    const max = Number.isFinite(maximum) ? Math.max(1, maximum) : 100;
    const progress = p.value !== undefined && p.value !== "" && Number.isFinite(value) && !message;
    return {schema_version: 1, icon: String(p.icon || "").slice(0, 256),
        progress: progress, value: progress ? Math.max(0, Math.min(value, max)) : 0, max: max,
        text: message.slice(0, 4096), progressText: String(p.progressText || "").slice(0, 256),
        duration: Number.isFinite(duration) ? Math.max(0, duration) : 1200};
}
function kind(icon) {
    const key = icon.toLowerCase();
    if (/^(mic|microphone)/.test(key)) return "input";
    if (/^(volume|mute)/.test(key) || !key) return "output";
    if (key === "brightness" || key === "display") return "brightness";
    return "other";
}
function symbol(icon) {
    const key = icon.toLowerCase(), type = kind(key);
    if (type === "output") return /mute/.test(key) ? "volume_off" : "volume_up";
    if (type === "input") return /mute|off/.test(key) ? "mic_off" : "mic";
    if (type === "brightness") return "brightness_6";
    return ({keyboard:"keyboard",touchpad:"touchpad_mouse",touch:"touch_app",touchscreen:"touch_app",
        reboot:"restart_alt",restart:"restart_alt",shutdown:"power_settings_new",power:"power_settings_new",poweroff:"power_settings_new",
        logout:"logout",leave:"logout","sign-out":"logout",media:"music_note",player:"music_note",
        "media-play":"play_arrow","player-play":"play_arrow","media-pause":"pause","player-pause":"pause",
        "media-next":"skip_next","player-next":"skip_next","media-previous":"skip_previous","player-previous":"skip_previous",
        "media-source":"music_note","player-source":"music_note"})[key] || "";
}
