pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons as Native
import "generated/Tokens.js" as Tokens

// Generated copies share this source contract. Only changes to configuration
// start the resolver; this object has no periodic timer or status collector.
Item {
    id: runtime
    visible: false
    property var resolved: ({})
    property var english: ({})
    property var translated: ({})
    property bool pending: false
    readonly property string home: Quickshell.env("HOME")
    readonly property string configRoot: Quickshell.env("XDG_CONFIG_HOME") || home + "/.config"
    readonly property string config: configRoot + "/wuling"
    readonly property string state: home + "/.local/state/omarchy/current"
    readonly property bool hud: resolved.preset === "hud"
    readonly property string language: resolved.language || "en"
    readonly property bool reduced: setting("motion") === "reduced"
    readonly property real scale: Native.Style.font.baseSize / 12
    readonly property string mono: Tokens.data.type.mono
    readonly property string sans: Tokens.data.type.sans
    readonly property string display: Tokens.data.type.display
    readonly property string serif: Tokens.data.type.cjk_serif
    readonly property string iconFont: Tokens.data.type.icon
    function c(role) { return resolved.colors && resolved.colors[role] ? resolved.colors[role].value : Tokens.data.palettes.mist[role] || "transparent"; }
    function g(role) { return (resolved.geometry && resolved.geometry[role] ? resolved.geometry[role].value : Tokens.data.presets.field[role] === undefined ? Tokens.data.geometry[role] : Tokens.data.presets.field[role]) * scale; }
    function px(value) { return value * scale; }
    function duration(role) { return reduced ? 90 : Tokens.data.motion[role]; }
    function setting(key) { return resolved.settings && resolved.settings[key] ? resolved.settings[key].value : Tokens.data.defaults[key]; }
    function icon(name) { return Tokens.icons[name] || ""; }
    function tr(key) { return translated[key] || english[key] || key; }
    function label(key) { const en = english[key] || key; return language === "en" ? en : en + " · " + tr(key); }
    function refresh() { if (resolver.running) pending = true; else resolver.running = true; }
    function rearmOverrides() {
        // A missing file cannot be watched. Watch its parent for first creation
        // and atomic replacement, and reattach the file watch for in-place edits.
        overridesFile.path = "";
        overridesFile.path = config + "/overrides.toml";
        refresh();
    }
    Component.onCompleted: refresh()
    Process {
        id: resolver
        command: ["wuling", "theme", "resolve", "--json"]
        stdout: StdioCollector {
            onStreamFinished: {
                try { const value = JSON.parse(text); if (value.schema_version === 1 && value.colors) runtime.resolved = value; }
                catch (_) { console.warn("WULING theme response unavailable"); }
            }
        }
        onExited: { if (runtime.pending) { runtime.pending = false; Qt.callLater(runtime.refresh); } }
    }
    FileView { id: overridesFile; path: runtime.config + "/overrides.toml"; watchChanges: true; printErrors: false; onFileChanged: { reload(); runtime.refresh(); } }
    FileView { id: overridesDirectory; path: runtime.config; watchChanges: true; printErrors: false; onFileChanged: runtime.rearmOverrides() }
    FileView {
        path: runtime.configRoot; watchChanges: true; printErrors: false
        onFileChanged: { overridesDirectory.path = ""; overridesDirectory.path = runtime.config; runtime.rearmOverrides(); }
    }
    FileView { path: runtime.state + "/theme.name"; watchChanges: true; printErrors: false; onFileChanged: { reload(); runtime.refresh(); } }
    FileView { path: runtime.state + "/theme/colors.toml"; watchChanges: true; printErrors: false; onFileChanged: { reload(); runtime.refresh(); } }
    FileView { path: runtime.home + "/.config/omarchy/language"; watchChanges: true; printErrors: false; onFileChanged: { reload(); runtime.refresh(); } }
    FileView { path: runtime.home + "/.config/omarchy"; watchChanges: true; printErrors: false; onFileChanged: runtime.refresh() }
    FileView {
        path: Qt.resolvedUrl("../i18n/en.json")
        printErrors: false
        onLoaded: { try { runtime.english = JSON.parse(text()); } catch (_) {} }
    }
    FileView {
        path: Qt.resolvedUrl("../i18n/" + runtime.language + ".json")
        printErrors: false
        onLoaded: { try { runtime.translated = JSON.parse(text()); } catch (_) { runtime.translated = ({}); } }
        onLoadFailed: runtime.translated = ({})
    }
}
