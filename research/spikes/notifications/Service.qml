import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Services.Notifications

// A bounded delivery/dismissal probe, not a notification implementation.
Item {
    id: probe
    property var notes: []
    property int received: 0
    property int dismissed: 0
    property string lastMethod: ""
    property bool doNotDisturb: false
    property alias dnd: probe.doNotDisturb
    property string lastSummary: ""
    function setDoNotDisturb(value) { doNotDisturb = value; }
    function dismissLast() {
        if (!notes.length) return;
        var next = notes.slice();
        var note = next.pop();
        notes = next;
        dismissed++;
        note.dismiss();
    }
    function clearNotes() { while (notes.length) dismissLast(); }
    NotificationServer {
        keepOnReload: false
        onNotification: function(notification) {
            notification.tracked = true;
            probe.received++;
            probe.lastSummary = notification.summary;
            if (probe.notes.length >= 8) probe.dismissLast();
            probe.notes = probe.notes.concat([notification]);
        }
    }
    IpcHandler {
        target: "notifications"
        function ping(): string { return "research.notifications"; }
        function dismissOne(): string { probe.lastMethod = "dismissOne"; probe.dismissLast(); return "ok"; }
        // The 4.5 default Super+, calls act. This fixture has no actions,
        // so the tested branch is dismissal of a passive notification only.
        function act(): string { probe.lastMethod = "act"; probe.dismissLast(); return "ok"; }
        function dismissAll(): string { probe.clearNotes(); return "ok"; }
        function toggleDnd(): string { probe.dnd = !probe.dnd; return probe.dnd ? "on" : "off"; }
        function setDnd(value: string): string { probe.dnd = ["true", "1", "on", "yes"].indexOf(value.toLowerCase()) >= 0; return probe.dnd ? "on" : "off"; }
        function isDnd(): string { return probe.dnd ? "on" : "off"; }
        function dndState(): string { return probe.dnd ? "on" : "off"; }
        function inspect(): string {
            return JSON.stringify({received: probe.received, dismissed: probe.dismissed,
                active: probe.notes.length, lastSummary: probe.lastSummary, lastMethod: probe.lastMethod});
        }
    }
    PanelWindow {
        visible: probe.notes.length > 0 && !probe.dnd
        anchors.top: true
        anchors.right: true
        margins.top: 48
        implicitWidth: 360
        implicitHeight: 72
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.namespace: "research-notifications"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
        color: "#243447"
        Text { anchors.centerIn: parent; text: probe.lastSummary; textFormat: Text.PlainText; color: "white" }
    }
}
