import QtQuick
import "kit" as Kit

Item {
    property string label: ""
    property string value: "—"
    property color ink:Kit.Runtime.c("paper-2")
    implicitHeight:Math.max(Kit.Runtime.px(21),content.implicitHeight+Kit.Runtime.px(5))
    Kit.Micro { width:Kit.Runtime.px(76);height:Kit.Runtime.px(20);text:parent.label;pixels:7.5 }
    Kit.Label { id:content;x:Kit.Runtime.px(82);width:Math.max(0,parent.width-x);text:parent.value || "—";color:parent.ink;font.pixelSize:Kit.Runtime.px(10);wrapMode:Text.Wrap;elide:Text.ElideNone }
}
