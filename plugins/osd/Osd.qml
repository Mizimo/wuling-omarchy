import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import qs.Commons as Native
import "kit" as Kit
import "Model.js" as Model

Item {
    id: osd
    property var shell: null
    property bool opened: false
    property var state: Model.state("{}")
    property string outputName: ""
    readonly property var outputNames: Quickshell.screens.map(s => s.name)
    readonly property string targetOutput: outputNames.indexOf(outputName)>=0 ? outputName : outputNames[0] || ""
    property string deviceName: ""
    property string probeKind: ""
    property bool probePending: false
    readonly property string deviceKind: Model.kind(state.icon)
    readonly property real fraction: state.value / state.max
    readonly property string symbol: Model.symbol(state.icon)
    readonly property string label: {
        const key = deviceKind === "output" ? "volume" : deviceKind === "input" ? "microphone" : deviceKind === "brightness" ? "brightness" : "level";
        if (!Kit.Runtime.hud) return Kit.Runtime.label(key).toUpperCase();
        const title = deviceKind === "output" ? "AUDIO OUT" : deviceKind === "input" ? "AUDIO IN" : deviceKind === "brightness" ? "DISPLAY" : "LEVEL";
        return title + (deviceName ? " · " + deviceName.toUpperCase() : deviceKind === "brightness" ? " · " + targetOutput.toUpperCase() : "");
    }
    function readDevice() {
        if (!opened || !Kit.Runtime.hud || ["input", "output"].indexOf(deviceKind) < 0) return;
        if (deviceProbe.running) { probePending = true; return; }
        probeKind = deviceKind;
        deviceProbe.command = ["wuling", "osd", "device", probeKind];
        deviceProbe.running = true;
    }
    function open(payload) {
        // An on-demand, bounded lease: no connection to the session plugin,
        // file watcher or idle polling. A dead worker cannot hide future OSDs.
        exitLease.reload();
        try {
            const lease=JSON.parse(exitLease.text()),remaining=lease.until-Date.now();
            if(lease.owner==="wuling.session" && remaining>0 && remaining<=11500) { close();return; }
        } catch (_) {}
        const next = Model.state(payload);
        if (!next) return;
        const refreshDevice = !opened || Model.kind(next.icon) !== deviceKind;
        state = next;
        const monitor = Hyprland.focusedMonitor;
        outputName = monitor ? monitor.name : "";
        opened = true;
        if (refreshDevice) { deviceName = ""; readDevice(); }
        if (state.duration > 0) expiry.restart(); else expiry.stop();
    }
    function close() { opened = false; expiry.stop(); deviceProbe.running = false; probePending = false; deviceName = ""; }
    FileView {
        id:exitLease;path:(Quickshell.env("XDG_RUNTIME_DIR") || "/nonexistent")+"/wuling/exit-osd.json"
        preload:false;blockAllReads:true;printErrors:false;watchChanges:false
    }
    Connections { target: Kit.Runtime; function onHudChanged() { osd.readDevice(); } }
    Process {
        id: deviceProbe
        stdout: StdioCollector {
            onStreamFinished: {
                try { const data = JSON.parse(text); if (osd.opened && osd.probeKind === osd.deviceKind && data.schema_version === 1) osd.deviceName = data.name || ""; } catch (_) {}
            }
        }
        onExited: if (osd.probePending) { osd.probePending = false; Qt.callLater(osd.readDevice); }
    }
    Timer { id: expiry; interval: Math.min(2147483647, osd.state.duration); onTriggered: osd.close() }
    IpcHandler {
        target: "osd"
        function show(payloadJson: string): string { osd.open(payloadJson); return "ok"; }
        function close(): string { osd.close(); return "ok"; }
        function state(): string { return osd.opened ? "open" : "closed"; }
        function ping(): string { return "ok"; }
    }
    Variants {
      model:Quickshell.screens
      PanelWindow {
        id: surface
        required property var modelData
        screen:modelData
        readonly property bool showHere:osd.opened && modelData && modelData.name===osd.targetOutput
        visible: showHere || card.opacity > 0
        anchors { top: true; bottom: true; left: true; right: true }
        color: "transparent"
        exclusionMode: ExclusionMode.Ignore
        mask: Region {}
        WlrLayershell.namespace: "wuling-osd"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
        Rectangle {
            id: card
            readonly property color ink: Kit.Runtime.c("ink-2")
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom; anchors.bottomMargin: Kit.Runtime.px(67)
            width: Math.min(parent.width - Kit.Runtime.px(20), Kit.Runtime.g("osd_width"))
            height: Kit.Runtime.g("osd_height")
            color: Qt.rgba(ink.r, ink.g, ink.b, .97)
            border.width: 1; border.color: Kit.Runtime.c(Kit.Runtime.hud ? "accent-ink" : "line")
            opacity: surface.showHere ? 1 : 0
            Behavior on opacity { NumberAnimation { duration: Kit.Runtime.reduced ? 90 : surface.showHere ? 160 : 120 } }
            Kit.Icon { id: icon; x: Kit.Runtime.px(14); anchors.verticalCenter: parent.verticalCenter; width: Kit.Runtime.px(24); font.pixelSize: Kit.Runtime.px(24); visible: !!osd.symbol; name: osd.symbol }
            Kit.Label { x: icon.x; width: icon.width; anchors.verticalCenter: parent.verticalCenter; visible: !osd.symbol; text: osd.state.icon; font.family: Native.Style.font.family; font.pixelSize: Kit.Runtime.px(24) }
            Column {
                x: icon.x + icon.width + Kit.Runtime.px(12); anchors.verticalCenter: parent.verticalCenter
                width: number.x - x - Kit.Runtime.px(12); spacing: Kit.Runtime.px(5)
                visible: osd.state.progress
                Kit.Micro { width: parent.width; text: osd.label; pixels: 8 }
                Row {
                    id: segments; width: parent.width; spacing: Kit.Runtime.px(2)
                    Repeater {
                        model: Kit.Runtime.hud ? 22 : 20
                        Rectangle {
                            required property int index
                            readonly property bool filled: index < Math.ceil(osd.fraction * (Kit.Runtime.hud ? 22 : 20))
                            width: (segments.width - segments.spacing * ((Kit.Runtime.hud ? 22 : 20) - 1)) / (Kit.Runtime.hud ? 22 : 20)
                            height: Kit.Runtime.px(Kit.Runtime.hud ? 14 : 8)
                            color: filled ? Kit.Runtime.c("fill") : Kit.Runtime.c("ink-5")
                            border.width: Kit.Runtime.hud && filled && index === Math.ceil(osd.fraction * 22) - 1 ? 1 : 0
                            border.color: Kit.Runtime.c("paper-0")
                            Behavior on color { ColorAnimation { duration: Kit.Runtime.reduced ? 0 : 60 } }
                        }
                    }
                }
            }
            Kit.Label {
                id: number; anchors.right: parent.right; anchors.rightMargin: Kit.Runtime.px(14); anchors.verticalCenter: parent.verticalCenter
                visible: osd.state.progress; width: Math.min(Kit.Runtime.px(90),Math.max(implicitWidth,Kit.Runtime.px(Kit.Runtime.hud ? 40 : 30))); horizontalAlignment: Text.AlignRight
                text: osd.state.progressText ? osd.state.progressText.replace(/%$/, "") : Math.round(osd.fraction * 100)
                font.family: Kit.Runtime.display; font.weight: Font.DemiBold; font.pixelSize: Kit.Runtime.px(Kit.Runtime.hud ? 30 : 24)
                color: Kit.Runtime.c(Kit.Runtime.hud ? "accent-ink" : "paper-1")
            }
            Kit.Label {
                visible: !osd.state.progress; x: icon.x + icon.width + Kit.Runtime.px(12); anchors.right: parent.right; anchors.rightMargin: Kit.Runtime.px(14); anchors.verticalCenter: parent.verticalCenter
                text: osd.state.text; font.family: Kit.Runtime.sans; font.weight: Font.Medium; font.pixelSize: Kit.Runtime.px(12)
            }
            Rectangle {
                width: 1; height: parent.height - 2; y: 1; color: Kit.Runtime.c("accent-ink")
                visible: scan.running && Kit.Runtime.hud && !Kit.Runtime.reduced
                NumberAnimation on x { id: scan; from: 1; to: card.width - 2; duration: 160; running: surface.showHere && Kit.Runtime.hud && !Kit.Runtime.reduced }
            }
        }
      }
    }
}
