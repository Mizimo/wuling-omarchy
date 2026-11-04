import QtQuick
import "kit" as Kit

Item {
    property string label: ""
    property string value: "—"
    property color ink:Kit.Runtime.c("paper-2")
    property real labelWidth:Kit.Runtime.px(76)
    // A fixed label is never cut: one that doesn't fit puts its Chinese half
    // under the English one (as the bar's cells do), otherwise wraps at spaces,
    // and the row grows.
    implicitHeight:Math.max(Kit.Runtime.px(21),content.implicitHeight+Kit.Runtime.px(5),caption.height+Kit.Runtime.px(1))
    Kit.Micro { id:measure;visible:false;text:parent.label;pixels:7.5;elide:Text.ElideNone }
    Kit.Micro {
        id:caption;width:parent.labelWidth;height:Math.max(Kit.Runtime.px(20),implicitHeight);pixels:7.5;wrapMode:Text.Wrap;elide:Text.ElideNone
        text:measure.implicitWidth<=width?parent.label:parent.label.replace(/ · (?=[^\x00-\x7f])/,"\n")
    }
    Kit.Label { id:content;x:parent.labelWidth+Kit.Runtime.px(6);width:Math.max(0,parent.width-x);text:parent.value || "—";color:parent.ink;font.pixelSize:Kit.Runtime.px(10);wrapMode:Text.Wrap;elide:Text.ElideNone }
}
