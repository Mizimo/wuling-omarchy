import QtQuick
import "kit" as Kit

Row {
    id:gauge
    property real value:0
    property real cached:0
    property color ink:Kit.Runtime.c("paper-1")
    spacing:Kit.Runtime.px(2);height:Kit.Runtime.px(8)
    Repeater {
        model:24
        Rectangle {
            required property int index
            width:Math.max(1,(gauge.width-gauge.spacing*23)/24);height:gauge.height
            color:index<Math.ceil(gauge.value*.24)?gauge.ink:index<Math.ceil((gauge.value+gauge.cached)*.24)?Kit.Runtime.c("mist-6"):Kit.Runtime.c("ink-5")
        }
    }
}
