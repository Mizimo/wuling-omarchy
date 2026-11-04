import QtQuick
import "kit" as Kit

Flow {
    id: packs
    property var rows: []
    spacing: Kit.Runtime.px(6)
    topPadding: rows.length ? Kit.Runtime.px(10) : 0
    Repeater {
        model:packs.rows
        Rectangle {
            required property var modelData
            readonly property bool present:modelData.present && modelData.percent!==null
            readonly property color ink:!present?Kit.Runtime.c("mist-5"):modelData.percent<=8?Kit.Runtime.c("vermilion"):modelData.state==="charging"?Kit.Runtime.c("jade"):Kit.Runtime.c("paper-2")
            width:(packs.width-Kit.Runtime.px(6))/2;height:Kit.Runtime.px(40)
            color:"transparent";border.width:1;border.color:Kit.Runtime.c("line")
            Kit.Micro { x:Kit.Runtime.px(8);y:Kit.Runtime.px(5);width:parent.width-Kit.Runtime.px(70);text:modelData.name;pixels:8 }
            Kit.Micro { x:Kit.Runtime.px(8);y:Kit.Runtime.px(23);width:parent.width-Kit.Runtime.px(16);text:Kit.Runtime.label("battery-"+modelData.state).toUpperCase();color:parent.ink;pixels:7 }
            Row {
                anchors.right:parent.right;anchors.rightMargin:Kit.Runtime.px(8);y:Kit.Runtime.px(5);spacing:Kit.Runtime.px(5)
                Rectangle {
                    width:Kit.Runtime.px(18);height:Kit.Runtime.px(10);anchors.verticalCenter:parent.verticalCenter;color:"transparent";border.width:1;border.color:parent.parent.ink
                    Rectangle { x:Kit.Runtime.px(2);y:Kit.Runtime.px(2);height:parent.height-Kit.Runtime.px(4);width:(parent.width-Kit.Runtime.px(4))*(parent.parent.parent.present?modelData.percent/100:0);color:parent.parent.parent.ink }
                    Rectangle { anchors.left:parent.right;anchors.verticalCenter:parent.verticalCenter;width:Kit.Runtime.px(2);height:Kit.Runtime.px(4);color:parent.parent.parent.ink }
                }
                Kit.Label { text:parent.parent.present?Math.round(modelData.percent)+"%":"—";color:parent.parent.ink;font.family:Kit.Runtime.display;font.pixelSize:Kit.Runtime.px(16) }
            }
        }
    }
}
