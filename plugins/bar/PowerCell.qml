import QtQuick
import Quickshell
import "kit" as Kit
Kit.Button {
    property var bar: null
    property var settings: ({})
    property string moduleName: "wuling.power-cell"
    host: bar
    implicitWidth: bar ? bar.barSize : Kit.Runtime.px(30)
    implicitHeight: implicitWidth
    borderVisible: false
    baseForeground: Kit.Runtime.c(Kit.Runtime.hud ? "paper-0" : "mist-4")
    icon: "power_settings_new"
    Accessible.name: Kit.Runtime.tr("power")
    Rectangle { z: -1; anchors.fill: parent; color: Kit.Runtime.hud ? Kit.Runtime.c("vermilion") : "transparent" }
    onClicked: Quickshell.execDetached(["wuling", "action", "power-menu"])
}
