import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland

Item {
    id: probe
    property var shell: null
    property bool opened: false
    property int escapeCount: 0
    function open(payloadJson) { opened = true; }
    function close() { opened = false; }
    IpcHandler {
        target: "research.focus"
        function inspect(): string { return JSON.stringify({opened: probe.opened, escapes: probe.escapeCount, focus: catcher.activeFocus}); }
    }
    PanelWindow {
        visible: probe.opened
        screen: Quickshell.screens.find(s => s.name === (Hyprland.focusedMonitor ? Hyprland.focusedMonitor.name : "")) || Quickshell.screens[0]
        anchors { top: true; bottom: true; left: true; right: true }
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.namespace: "research-focus"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: probe.opened ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
        color: "#b0243447"
        Item {
            id: catcher
            anchors.fill: parent
            focus: true
            Keys.onEscapePressed: event => {
                probe.escapeCount++;
                probe.shell.hide("research.focus");
                event.accepted = true;
            }
            Text { anchors.centerIn: parent; text: "FOCUS PROBE — Escape closes"; textFormat: Text.PlainText; color: "white"; font.pixelSize: 24 }
        }
    }
}
