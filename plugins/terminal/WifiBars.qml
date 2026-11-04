import QtQuick
import "kit" as Kit

Row {
    property real strength:0
    property color ink:Kit.Runtime.c("paper-2")
    spacing:Kit.Runtime.px(2);height:Kit.Runtime.px(12)
    Repeater {
        model:4
        Rectangle {
            required property int index
            width:Kit.Runtime.px(3);height:Kit.Runtime.px(4+index*2);anchors.bottom:parent.bottom
            color:index<=Math.floor(Math.min(99,parent.strength)/25)?parent.ink:Kit.Runtime.c("ink-5")
        }
    }
}
