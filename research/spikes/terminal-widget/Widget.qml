import QtQuick
import Quickshell.Io
import qs.Ui

// Imports the installed Panel and KeyboardPanel; this is not a terminal.
Panel {
    id: probe
    moduleName: "research.terminal-widget"
    implicitWidth: button.implicitWidth
    implicitHeight: button.implicitHeight
    property int escapes: 0
    WidgetButton {
        id: button
        anchors.fill: parent
        bar: probe.bar
        text: "TEST"
        tooltipText: "Disposable shared-panel probe"
        onPressed: probe.toggle()
    }
    KeyboardPanel {
        id: popup
        anchorItem: button
        bar: probe.bar
        owner: probe
        open: probe.opened
        contentWidth: 320
        contentHeight: 160
        focusTarget: keys
        PanelKeyCatcher {
            id: keys
            anchors.fill: parent
            onCloseRequested: { probe.escapes++; probe.close(); }
            onTabRequested: direction => probe.switchPanel(direction)
            onMoveRequested: (dx,dy) => { if(dx) probe.switchPanel(dx); }
            Text { anchors.centerIn:parent; text:"SHARED PANEL PROBE"; textFormat:Text.PlainText; color:"white" }
        }
    }
    IpcHandler {
        target: "research.terminal-widget"
        function inspect(): string { return JSON.stringify({opened:probe.opened,escapes:probe.escapes,hasBar:!!probe.bar,hasShell:!!(probe.bar && probe.bar.shell)}); }
    }
}
