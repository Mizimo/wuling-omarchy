import QtQuick
import Quickshell
import Quickshell.Hyprland
import "kit" as Kit

Item {
    id: workspaces
    property var bar: null
    property var settings: ({})
    property string moduleName: "omarchy.workspaces"
    readonly property bool vertical: !!bar && bar.vertical
    readonly property var ids: {
        let present = new Set([1, 2, 3, 4, 5]);
        Hyprland.workspaces.values.forEach(workspace => { if (workspace.id >= 1 && workspace.id <= 10) present.add(workspace.id); });
        return Array.from(present).sort((a, b) => a - b);
    }
    readonly property real tagSpace: Kit.Runtime.hud ? Kit.Runtime.px(24) : 0
    implicitWidth: vertical ? bar.barSize : layout.width + Kit.Runtime.px(20) + tagSpace
    implicitHeight: vertical ? layout.height + tagSpace : bar ? bar.barSize : Kit.Runtime.px(30)
    Kit.Label {
        visible: Kit.Runtime.hud
        text: "WS"; color: Kit.Runtime.c("accent-ink"); font.pixelSize: Kit.Runtime.px(8); font.letterSpacing: Kit.Runtime.px(1)
        x: workspaces.vertical ? (parent.width - width) / 2 : Kit.Runtime.px(10)
        y: workspaces.vertical ? Kit.Runtime.px(5) : (parent.height - height) / 2
    }
    Grid {
        id: layout; columns: workspaces.vertical ? 1 : workspaces.ids.length
        x: (parent.width - width + (workspaces.vertical ? 0 : workspaces.tagSpace)) / 2
        y: (parent.height - height + (workspaces.vertical ? workspaces.tagSpace : 0)) / 2
        spacing: Kit.Runtime.px(2)
        Repeater {
            model: workspaces.ids
            Kit.Button {
                required property int modelData
                readonly property var workspace: Hyprland.workspaces.values.find(item => item.id === modelData) || null
                readonly property bool occupied: !!workspace && workspace.toplevels.values.length > 0
                readonly property bool focused: !!Hyprland.focusedWorkspace && Hyprland.focusedWorkspace.id === modelData
                host: workspaces.bar
                width: Kit.Runtime.px(Kit.Runtime.hud ? 30 : 26); height: Kit.Runtime.px(Kit.Runtime.hud ? 22 : 18); borderVisible: false
                labelSize: Kit.Runtime.hud ? 11 : 10
                text: String(modelData).padStart(2, "0"); accent: focused
                chamfer: Kit.Runtime.hud && focused ? Kit.Runtime.px(5) : 0
                opacity: focused || occupied ? 1 : .5
                Accessible.name: Kit.Runtime.tr("workspace") + " " + modelData
                onClicked: Quickshell.execDetached(["hyprctl", "dispatch", "hl.dsp.focus({ workspace = \"" + modelData + "\" })"])
                Rectangle { visible: parent.occupied && !parent.focused; height: 1; width: Kit.Runtime.px(12); anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom; anchors.bottomMargin: 1; color: Kit.Runtime.c("mist-5") }
            }
        }
    }
}
