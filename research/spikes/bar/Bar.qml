import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import qs.Commons

// A research surface, deliberately without product styling or widget hosting.
Item {
    id: probe
    property var shell: null
    property var manifest: null
    property var pluginRegistry: null
    property var barWidgetRegistry: null
    property var barConfig: ({})
    property string omarchyPath: ""
    property string position: barConfig.position || "top"
    property bool barHidden: false
    property bool vertical: position === "left" || position === "right"
    property int barSize: vertical ? Style.bar.sizeVertical : Style.bar.sizeHorizontal
    property string fontFamily: Style.font.family

    IpcHandler {
        target: "research.bar"
        function inspect(): string {
            var ids = barWidgetRegistry ? barWidgetRegistry.availableIds() : [];
            var entry = shell ? shell.pluginShellForBarEntry("research.bar", "omarchy.audio") : null;
            return JSON.stringify({screens: Quickshell.screens.map(s => s.name),
                position: probe.position, size: probe.barSize, layout: probe.barConfig.layout,
                widgetIds: ids, entryHasFacade: !!entry,
                entryHasService: !!(entry && entry.serviceFor("omarchy.audio")),
                mediaProxy: !!(shell && shell.firstPartyServiceFor("omarchy.media"))});
        }
    }
    Variants {
        model: Quickshell.screens
        PanelWindow {
            required property var modelData
            screen: modelData
            anchors.top: probe.position !== "bottom"
            anchors.bottom: probe.position !== "top"
            anchors.left: probe.position !== "right"
            anchors.right: probe.position !== "left"
            implicitHeight: probe.barSize
            implicitWidth: probe.barSize
            exclusiveZone: probe.barSize
            WlrLayershell.namespace: "research-bar"
            WlrLayershell.layer: WlrLayer.Top
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
            color: "#243447"
            Text {
                anchors.centerIn: parent
                text: "BAR PROBE " + modelData.name
                textFormat: Text.PlainText
                color: "white"
                font.pixelSize: 12
            }
        }
    }
}
