import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

Item {
    id: probe
    property int received: 0
    property string payload: ""
    property bool opened: false
    function open(payloadJson) {
        payload = payloadJson;
        received++;
        opened = true;
        hideTimer.restart();
    }
    function close() { opened = false; }
    IpcHandler {
        target: "osd"
        function show(payloadJson: string): string {
            probe.open(payloadJson);
            return "ok";
        }
        function close(): string { probe.opened = false; return "ok"; }
        function state(): string { return probe.opened ? "open" : "closed"; }
        function ping(): string { return "research.osd"; }
        function inspect(): string { return JSON.stringify({received: probe.received, payload: probe.payload}); }
    }
    Timer { id: hideTimer; interval: 1200; onTriggered: probe.opened = false }
    PanelWindow {
        visible: probe.opened
        anchors.bottom: true
        implicitWidth: 540
        implicitHeight: 64
        exclusionMode: ExclusionMode.Ignore
        WlrLayershell.namespace: "research-osd"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
        mask: Region {}
        color: "#243447"
        Text { anchors.centerIn: parent; text: probe.payload; textFormat: Text.PlainText; color: "white"; font.pixelSize: 12 }
    }
}
