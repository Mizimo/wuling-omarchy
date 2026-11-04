import QtQuick
import "kit" as Kit

Item {
    property string text: ""
    property string note: ""
    property color ink:Kit.Runtime.c("paper-2")
    implicitHeight:Kit.Runtime.px(26)
    Kit.Micro { id:title;y:Kit.Runtime.px(10);text:parent.text;color:parent.ink }
    Rectangle { anchors.left:title.right;anchors.leftMargin:Kit.Runtime.px(10);anchors.right:note.left;anchors.rightMargin:Kit.Runtime.px(8);y:Kit.Runtime.px(14);height:1;color:Kit.Runtime.c("line") }
    Kit.Micro { id:note;anchors.right:parent.right;y:Kit.Runtime.px(10);text:parent.note;pixels:7 }
}
