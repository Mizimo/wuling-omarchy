import QtQuick
import Quickshell
import "kit" as Kit
Kit.Button {
    property var bar: null
    property var settings: ({})
    property string moduleName: "omarchy.menu"
    host: bar
    borderVisible: false
    accent: true
    chamfer: Kit.Runtime.px(Kit.Runtime.hud ? 9 : 7)
    implicitWidth: bar && bar.vertical ? bar.barSize : Kit.Runtime.px(Kit.Runtime.hud ? 64 : 30)
    implicitHeight: bar ? bar.barSize : Kit.Runtime.px(30)
    Accessible.name: Kit.Runtime.tr("menu")
    Image { width: Kit.Runtime.px(30); height: width; anchors.verticalCenter: parent.verticalCenter; source: "assets/emblem.svg"; sourceSize.width: width; sourceSize.height: height }
    Kit.Label { visible: Kit.Runtime.hud && !(parent.bar && parent.bar.vertical); x: Kit.Runtime.px(32); height: parent.height; text: "EF"; color: Kit.Runtime.c("on-accent"); font.weight: Font.Bold }
    onClicked: Quickshell.execDetached(["omarchy-menu", "toggle", "root"])
    onRightClicked: Quickshell.execDetached(["omarchy-launch-terminal"])
}
