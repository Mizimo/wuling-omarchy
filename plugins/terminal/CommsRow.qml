import QtQuick
import "kit" as Kit

Column {
    id: row
    required property var entry
    property bool expanded: false
    property bool expandable: true
    signal toggled()
    signal invoke(int index)
    spacing: Kit.Runtime.px(6)
    Kit.Button {
        id: summary
        width: parent.width; height: content.implicitHeight + Kit.Runtime.px(12)
        borderVisible: false; enabled: row.expandable; activeFocusOnTab: row.expandable
        sound: "select"
        Accessible.name: row.entry.app + ": " + row.entry.summary
        onClicked: row.toggled()
        Column {
            id: content; x:Kit.Runtime.px(6); y:Kit.Runtime.px(6); width:parent.width-Kit.Runtime.px(12)
            spacing:Kit.Runtime.px(5)
            Item {
                width:parent.width;height:Kit.Runtime.px(12)
                Kit.Micro { width:parent.width-time.width-Kit.Runtime.px(10);text:String(row.entry.app || "").toUpperCase();color:summary.highlighted?summary.foreground:Kit.Runtime.c("mist-4") }
                Kit.Micro { id:time;anchors.right:parent.right;text:Qt.formatDateTime(new Date(row.entry.time*1000),"HH:mm");color:summary.highlighted?summary.foreground:Kit.Runtime.c("mist-5") }
            }
            Kit.Label { width:parent.width;text:row.entry.summary;font.family:Kit.Runtime.sans;font.weight:Font.DemiBold;color:summary.foreground;wrapMode:Text.Wrap;maximumLineCount:row.expanded?2147483647:2 }
            Kit.Label { width:parent.width;text:row.entry.body || "";visible:text.length>0;font.family:Kit.Runtime.sans;color:summary.highlighted?summary.foreground:Kit.Runtime.c("mist-4");wrapMode:Text.Wrap;maximumLineCount:row.expanded?2147483647:2 }
        }
    }
    Flow {
        x:Kit.Runtime.px(6);width:parent.width-Kit.Runtime.px(12);spacing:Kit.Runtime.px(6)
        visible:row.expanded && (row.entry.actions || []).length>0
        Repeater {
            model:parent.visible?row.entry.actions || []:[]
            Kit.Button {
                id:deedButton
                required property var modelData
                Accessible.name:modelData.label || Kit.Runtime.label("open-action")
                width:Math.min(deedLabel.implicitWidth+Kit.Runtime.px(16),row.width-Kit.Runtime.px(12));height:Kit.Runtime.px(25)
                Kit.Label { id:deedLabel;x:Kit.Runtime.px(8);width:parent.width-Kit.Runtime.px(16);height:parent.height;text:deedButton.Accessible.name;color:deedButton.foreground;font.pixelSize:Kit.Runtime.px(10) }
                onClicked:row.invoke(modelData.index)
            }
        }
    }
    Rectangle { width:parent.width;height:1;color:Kit.Runtime.c("line-soft") }
}
