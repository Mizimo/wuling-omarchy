import QtQuick
import Quickshell
import Quickshell.Wayland

// Deliberately minimal: measure the earliest a normal service can cover the
// desktop. This is neither the product animation nor its once-per-login gate.
Item {
    id: probe
    property var shell: null
    property bool covering: true
    Component.onCompleted: console.info("ARRIVAL_PROBE created", Date.now())
    Timer {
        interval: 3500; running: true
        onTriggered: { console.info("ARRIVAL_PROBE release", Date.now()); probe.covering = false; }
    }
    Variants {
        model: Quickshell.screens
        PanelWindow {
            required property var modelData
            screen: modelData
            visible: probe.covering
            anchors { top: true; bottom: true; left: true; right: true }
            exclusionMode: ExclusionMode.Ignore
            color: "#050707"
            WlrLayershell.namespace: "research-arrival"
            WlrLayershell.layer: WlrLayer.Overlay
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
            mask: Region {}
            Rectangle { x: 32; y: 32; width: 64; height: 64; color: "#ff00ff" }
            Text { anchors.centerIn: parent; text: "ARRIVAL FIRST-FRAME PROBE"; color: "#ffffff"; font.pixelSize: 28 }
        }
    }
}
