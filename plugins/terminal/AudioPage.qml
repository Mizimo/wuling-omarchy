import QtQuick
import "kit" as Kit
import "Detail.js" as Format

Column {
    id:page
    property var snapshot:({})
    signal action(string name,string value)
    function key(event) {}
    function send(name,row,value) {
        const data={id:row.id,serial:row.serial};if(value!==undefined)data.value=value;
        action(name,JSON.stringify(data));
    }
    function volumeRow(row,kind) {
        if(kind!=="outputs" || !row.active)return row;
        return (snapshot.outputs || []).find(item=>item.volume_target) || row;
    }
    spacing:Kit.Runtime.px(6)
    Repeater {
        model:["outputs","inputs","streams"]
        Column {
            id:group
            required property string modelData
            readonly property var rows:page.snapshot[modelData] || []
            property var keys:[]
            onRowsChanged: {
                const next=rows.map(row=>row.id+":"+row.serial);
                if(JSON.stringify(next)!==JSON.stringify(keys))keys=next;
            }
            width:page.width;spacing:Kit.Runtime.px(6)
            DetailHeading { width:parent.width;text:Kit.Runtime.label(group.modelData) }
            Kit.Label { width:parent.width;visible:!group.rows.length;text:Kit.Runtime.tr("no-"+group.modelData);color:Kit.Runtime.c("mist-5");font.pixelSize:Kit.Runtime.px(10) }
            Repeater {
                // Keep controls stable while levels change underneath a drag.
                model:group.keys
                Rectangle {
                    id:card
                    required property string modelData
                    readonly property var row:group.rows.find(row=>row.id+":"+row.serial===modelData) || ({})
                    readonly property var volumeRow:page.volumeRow(row,group.modelData)
                    readonly property bool expanded:row.active || group.modelData==="streams"
                    width:group.width;height:Kit.Runtime.px(expanded?91:34);color:expanded?Kit.Runtime.c("ink-3"):"transparent";border.width:expanded?1:0;border.color:Kit.Runtime.c("line")
                    Rectangle { visible:card.row.active;width:Kit.Runtime.px(2);height:parent.height;color:Kit.Runtime.c("jade") }
                    Kit.Button {
                        x:Kit.Runtime.px(6);y:Kit.Runtime.px(2);width:parent.width-Kit.Runtime.px(12);height:Kit.Runtime.px(30);borderVisible:false
                        enabled:group.modelData!=="streams" && !!card.row.available;opacity:card.row.available?1:.45
                        Accessible.name:card.row.label || ""
                        onClicked:page.send("audio-default",card.row)
                        Kit.Label { x:Kit.Runtime.px(5);width:parent.width-Kit.Runtime.px(28);height:parent.height;text:card.row.label || "";font.family:Kit.Runtime.sans;font.pixelSize:Kit.Runtime.px(11);color:parent.foreground }
                        Kit.Micro { visible:group.modelData!=="streams";anchors.right:parent.right;anchors.rightMargin:Kit.Runtime.px(5);height:parent.height;text:card.row.active?"◆":"›";color:card.row.active?Kit.Runtime.c("jade"):parent.foreground }
                    }
                    Kit.Level {
                        visible:card.expanded;x:Kit.Runtime.px(10);y:Kit.Runtime.px(35);width:parent.width-Kit.Runtime.px(20)
                        name:card.row.label || "";icon:group.modelData==="inputs"?"mic":card.volumeRow.muted?"volume_off":"volume_up"
                        value:card.volumeRow.volume || 0;enabled:card.volumeRow.volume!==null
                        fill:Kit.Runtime.c(card.volumeRow.muted?"mist-6":group.modelData==="inputs"?"paper-1":"fill")
                        onAdjusted:percent=>page.send("audio-volume",card.row,Math.round(percent))
                    }
                    Kit.Micro { visible:card.expanded;x:Kit.Runtime.px(10);y:Kit.Runtime.px(73);text:Kit.Runtime.tr("wheel-level");pixels:7 }
                    Kit.Button {
                        visible:card.expanded;anchors.right:parent.right;anchors.rightMargin:Kit.Runtime.px(8);y:Kit.Runtime.px(63);height:Kit.Runtime.px(23)
                        text:Kit.Runtime.label(card.volumeRow.muted?"unmute":"mute");labelSize:8;selected:card.volumeRow.muted
                        onClicked:page.send("audio-mute",card.row)
                    }
                }
            }
        }
    }
}
