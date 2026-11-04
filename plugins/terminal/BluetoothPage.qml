import QtQuick
import "kit" as Kit

Column {
    id:page
    property var snapshot:({})
    property bool busy:false
    property bool scanning:false
    property var devices:[]
    property string selectedId:""
    readonly property var deviceIcons:({headphones:"headphones",keyboard:"keyboard",mouse:"mouse",smartphone:"smartphone",bluetooth:"bluetooth"})
    signal action(string name,string value)
    signal discovery()
    spacing:Kit.Runtime.px(8)
    onSnapshotChanged:if(JSON.stringify(snapshot.devices || [])!==JSON.stringify(devices))devices=snapshot.devices || []
    function key(event) { if(event.key===Qt.Key_S) { if(snapshot.enabled)discovery();event.accepted=true; } }
    function send(operation,row) { action("bluetooth-"+operation,JSON.stringify({id:row.id,adapter:snapshot.adapter})); }
    RadioSwitch { width:parent.width;icon:"bluetooth";description:page.snapshot.name || "";powered:page.snapshot.enabled===true;known:typeof page.snapshot.enabled==="boolean";available:page.snapshot.present===true && !page.busy;onChanged:powered=>page.action("bluetooth-radio",JSON.stringify({enabled:powered})) }
    Row {
        width:parent.width;height:Kit.Runtime.px(30)
        Kit.Micro { width:parent.width-scan.width;anchors.verticalCenter:parent.verticalCenter;text:Kit.Runtime.label(page.scanning?"scanning":"devices");pixels:8 }
        Kit.Button { id:scan;icon:page.scanning?"stop":"refresh";text:Kit.Runtime.tr(page.scanning?"stop-scan":"scan");height:parent.height;enabled:page.snapshot.enabled===true && !page.busy;onClicked:page.discovery() }
    }
    Item {
        visible:page.scanning;width:parent.width;height:visible?1:0;clip:true
        Rectangle { width:parent.width*.25;height:1;color:Kit.Runtime.c("accent-ink")
            SequentialAnimation on x { running:page.scanning && !Kit.Runtime.reduced;loops:Animation.Infinite;NumberAnimation { from:-page.width*.25;to:page.width;duration:900 } }
        }
    }
    Repeater {
        model:["connected-devices","paired","available"]
        Column {
            id:group
            required property string modelData
            required property int index
            property var rows:page.devices.filter(row=>index===0?row.connected:index===1?row.paired && !row.connected:!row.paired && !row.connected)
            width:page.width;visible:rows.length>0;spacing:Kit.Runtime.px(5)
            DetailHeading { width:parent.width;text:(group.index===0?"● ":"")+Kit.Runtime.label(group.modelData);ink:Kit.Runtime.c(group.index===0?"jade":"mist-5") }
            Repeater {
                model:group.rows
                Column {
                    id:device
                    required property var modelData
                    width:group.width;spacing:Kit.Runtime.px(4)
                    Kit.Button {
                        id:row;width:parent.width;height:Kit.Runtime.px(36);borderVisible:false;enabled:!page.busy
                        Accessible.name:device.modelData.name
                        onClicked: { page.selectedId=page.selectedId===device.modelData.id?"":device.modelData.id; }
                        Rectangle { visible:device.modelData.connected;anchors.fill:parent;z:-1;color:Kit.Runtime.c("ink-3");Rectangle { width:Kit.Runtime.px(2);height:parent.height;color:Kit.Runtime.c("jade") } }
                        Kit.Icon { x:Kit.Runtime.px(8);height:parent.height;name:page.deviceIcons[device.modelData.icon] || "bluetooth";color:row.foreground;font.pixelSize:Kit.Runtime.px(17) }
                        Kit.Label { x:Kit.Runtime.px(34);width:parent.width-x-Kit.Runtime.px(57);height:parent.height;text:device.modelData.name;elide:Text.ElideRight;font.family:Kit.Runtime.sans;font.pixelSize:Kit.Runtime.px(12);color:row.foreground }
                        Kit.Micro { anchors.right:parent.right;anchors.rightMargin:Kit.Runtime.px(8);height:parent.height;text:device.modelData.battery===null?"":Math.round(device.modelData.battery)+"%";color:row.foreground;pixels:8 }
                    }
                    Row {
                        visible:page.selectedId===device.modelData.id;width:parent.width;spacing:Kit.Runtime.px(6);enabled:!page.busy
                        Kit.Button { width:(parent.width-Kit.Runtime.px(6))/2;text:Kit.Runtime.label(device.modelData.connected?"disconnect":device.modelData.paired?"connect":"pair");onClicked:page.send(device.modelData.connected?"disconnect":device.modelData.paired?"connect":"pair",device.modelData) }
                        Kit.Button { visible:device.modelData.paired;width:(parent.width-Kit.Runtime.px(6))/2;text:Kit.Runtime.label("forget");baseForeground:Kit.Runtime.c("vermilion");onClicked:page.send("forget",device.modelData) }
                    }
                }
            }
        }
    }
    Kit.Label { visible:page.snapshot.devices!==undefined && page.devices.length===0;width:parent.width;text:Kit.Runtime.label("no-devices");color:Kit.Runtime.c("mist-5");font.pixelSize:Kit.Runtime.px(11) }
}
