import QtQuick
import Quickshell
import "kit" as Kit
Item {
    property var bar: null
    property var settings: ({})
    property string moduleName: "wuling.identity"
    readonly property var window: QsWindow.window
    visible: !!bar && !bar.vertical && !!window && window.screen.width >= Kit.Runtime.px(1280)
    implicitWidth: visible ? Kit.Runtime.px(125) : 0
    implicitHeight: bar ? bar.barSize : Kit.Runtime.px(30)
    Rectangle { anchors.right: parent.right; anchors.rightMargin: Kit.Runtime.px(12); anchors.verticalCenter: parent.verticalCenter; width: 1; height: Kit.Runtime.px(14); color: Kit.Runtime.c("line") }
    Column {
        x: Kit.Runtime.px(10); anchors.verticalCenter: parent.verticalCenter
        Kit.Label { visible: Kit.Runtime.setting("labels"); text: "WULING · 武陵"; font.pixelSize: Kit.Runtime.px(8); color: Kit.Runtime.c("mist-5"); font.letterSpacing: Kit.Runtime.px(.8) }
        Kit.Label { width: Kit.Runtime.px(90); text: parent.parent.bar ? parent.parent.bar.hostname : ""; font.pixelSize: Kit.Runtime.px(10); font.weight: Font.DemiBold; font.letterSpacing: Kit.Runtime.px(.7) }
    }
}
