import QtQuick
Item {
    id: section
    property string number: ""
    property string title: ""
    property string detail: ""
    implicitHeight: Runtime.px(Runtime.hud ? 23 : 19)
    Rectangle { visible: Runtime.hud; x: Runtime.px(14); y: Runtime.px(8); width: Runtime.px(23); height: Runtime.px(15); color: Runtime.c("fill") }
    Label { x: Runtime.px(Runtime.hud ? 18 : 14); y: Runtime.px(Runtime.hud ? 11 : 10); height: Runtime.px(9); text: section.number; color: Runtime.c(Runtime.hud ? "on-accent" : "accent-ink"); font.pixelSize: Runtime.px(9); font.weight: Font.DemiBold }
    Label { id: title; x: Runtime.px(Runtime.hud ? 45 : 36); y: Runtime.px(Runtime.hud ? 11 : 10); height: Runtime.px(9); text: section.title.toUpperCase(); font.pixelSize: Runtime.px(9); font.weight: Font.Medium; font.letterSpacing: Runtime.px(1.26) }
    Rectangle { x: title.x + title.width + Runtime.px(8); y: title.y + title.height / 2; width: Math.max(0, parent.width - x - detail.width - Runtime.px(22)); height: 1; color: Runtime.c("line-soft") }
    Label { id: detail; anchors.right: parent.right; anchors.rightMargin: Runtime.px(14); y: title.y; height: title.height; text: section.detail.toUpperCase(); color: Runtime.c("mist-5"); font.pixelSize: Runtime.px(8); font.weight: Font.Medium; font.letterSpacing: Runtime.px(1.12) }
}
