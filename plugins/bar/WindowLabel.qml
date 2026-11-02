import QtQuick
import Quickshell
import Quickshell.Wayland
import "kit" as Kit
Item {
    property var bar: null
    property var settings: ({})
    property string moduleName: "wuling.window"
    readonly property var window: QsWindow.window
    readonly property var active: ToplevelManager.activeToplevel
    visible: !!bar && !bar.vertical && !!window && window.screen.width >= Kit.Runtime.px(1024) && !!active
    implicitWidth: visible ? Math.min(Kit.Runtime.px(230), Math.max(Kit.Runtime.px(90), window.screen.width * .16)) : 0
    implicitHeight: bar ? bar.barSize : Kit.Runtime.px(30)
    Rectangle { x: Kit.Runtime.px(6); anchors.verticalCenter: parent.verticalCenter; width: 1; height: Kit.Runtime.px(14); color: Kit.Runtime.c("line") }
    Column {
        x: Kit.Runtime.px(20); anchors.verticalCenter: parent.verticalCenter; width: parent.width - x - Kit.Runtime.px(8)
        Kit.Label { visible: Kit.Runtime.setting("labels"); width: parent.width; text: parent.parent.active ? parent.parent.active.appId.toUpperCase() : ""; color: Kit.Runtime.c("mist-5"); font.pixelSize: Kit.Runtime.px(8); font.letterSpacing: Kit.Runtime.px(.6) }
        Kit.Label { width: parent.width; text: parent.parent.active ? parent.parent.active.title : ""; font.family: Kit.Runtime.sans; font.pixelSize: Kit.Runtime.px(11.5) }
    }
}
