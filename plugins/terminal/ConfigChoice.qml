import QtQuick
import "kit" as Kit

Column {
    id:row
    property string title:""
    property var options:[]
    property var value
    signal chosen(var value)
    width:parent.width;spacing:Kit.Runtime.px(7)
    Kit.Label { text:row.title;font.family:Kit.Runtime.sans;font.pixelSize:Kit.Runtime.px(12) }
    Row {
        width:parent.width
        Repeater {
            model:row.options
            Kit.Button {
                required property var modelData
                required property int index
                width:parent.width/row.options.length;height:Kit.Runtime.px(24);labelSize:9
                text:modelData.label;selected:row.value===modelData.value
                Accessible.name:row.title+": "+text
                onClicked:if(!selected)row.chosen(modelData.value)
            }
        }
    }
    Rectangle { width:parent.width;height:1;color:Kit.Runtime.c("line-soft") }
}
