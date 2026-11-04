import QtQuick
import "kit" as Kit

Column {
    id:row
    required property var entry
    spacing:Kit.Runtime.px(6)
    bottomPadding:Kit.Runtime.px(8)
    Kit.Label {
        width:parent.width;text:row.entry.description_key?Kit.Runtime.tr(row.entry.description_key):row.entry.description;wrapMode:Text.Wrap;elide:Text.ElideNone
        font.family:Kit.Runtime.sans;font.pixelSize:Kit.Runtime.px(12);color:Kit.Runtime.c("paper-1")
    }
    Repeater {
        model:row.entry.keys
        Flow {
            required property var modelData
            width:row.width;spacing:Kit.Runtime.px(4)
            Repeater {
                model:parent.modelData
                Rectangle {
                    required property string modelData
                    width:Math.min(row.width,cap.implicitWidth+Kit.Runtime.px(12));height:Kit.Runtime.px(20)
                    color:modelData==="SUPER"?Kit.Runtime.c("fill"):"transparent"
                    border.width:1;border.color:Kit.Runtime.c(modelData==="SUPER"?"fill":"line")
                    Kit.Label {
                        id:cap;anchors.centerIn:parent;width:Math.min(implicitWidth,parent.width-Kit.Runtime.px(8))
                        text:parent.modelData==="SUPER"?"◆":parent.modelData;font.pixelSize:Kit.Runtime.px(10)
                        color:Kit.Runtime.c(parent.modelData==="SUPER"?"on-accent":"paper-2")
                    }
                }
            }
        }
    }
}
