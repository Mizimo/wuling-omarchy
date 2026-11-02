import QtQuick
import Quickshell
import "kit" as Kit
Item {
    property var bar: null
    property var settings: ({})
    property string moduleName: "wuling.identity"
    readonly property var window: QsWindow.window
    visible: !!bar && !bar.vertical && !!window && window.screen.width >= Kit.Runtime.px(1280)
    implicitWidth: visible ? Kit.Runtime.px(110) : 0
    implicitHeight: bar ? bar.barSize : Kit.Runtime.px(30)
    Column {
        x: Kit.Runtime.px(10); anchors.verticalCenter: parent.verticalCenter
        Kit.Label { visible: Kit.Runtime.setting("labels"); text: "WULING · 武陵"; font.pixelSize: Kit.Runtime.px(8); color: Kit.Runtime.c("mist-5"); font.letterSpacing: Kit.Runtime.px(.8) }
        Kit.Label { width: Kit.Runtime.px(95); text: parent.parent.bar ? parent.parent.bar.hostname : ""; font.pixelSize: Kit.Runtime.px(10); font.weight: Font.DemiBold; font.letterSpacing: Kit.Runtime.px(.7) }
    }
}
