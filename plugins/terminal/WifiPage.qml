import QtQuick
import "kit" as Kit
import "Detail.js" as Format

Column {
    id:page
    property var snapshot:({})
    property bool busy:false
    property var networks:[]
    property var networkIds:[]
    property string promptId:""
    property string selectedId:""
    property var connecting:null
    readonly property var linked:snapshot.linked || ({})
    signal action(string name,string value)
    signal credential(string value,string secret)
    signal focusMoved(var control)
    spacing:Kit.Runtime.px(8)
    onSnapshotChanged: {
        const rows=snapshot.networks || [];
        if(JSON.stringify(rows)!==JSON.stringify(networks))networks=rows;
        const ids=networkIds.filter(id=>rows.some(row=>row.id===id));
        for(const row of rows)if(ids.indexOf(row.id)<0)ids.push(row.id);
        if(JSON.stringify(ids)!==JSON.stringify(networkIds))networkIds=ids;
        if(snapshot.linked && snapshot.linked.id===promptId)promptId="";
    }
    function payload(row) { return {interface:snapshot.interface,id:row?row.id:""}; }
    function send(name,row) { action(name,JSON.stringify(payload(row))); }
    function connect(row) {
        connecting=row;
        if(!row.uuid && ["open","owe","enterprise"].indexOf(row.security)<0)promptId=row.id;
        else send("wifi-connect",row);
    }
    function result(name,ok) {
        if(name==="wifi-connect" && connecting) {
            if(!ok && ["open","owe","enterprise"].indexOf(connecting.security)<0)promptId=connecting.id;
            else if(ok)promptId="";
        }
    }
    function key(event) {
        if(event.key===Qt.Key_S && !(event.modifiers & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier))) {
            if(snapshot.enabled && !busy)send("wifi-scan",null);event.accepted=true;
        }
    }
    RadioSwitch { width:parent.width;description:page.snapshot.interface || "";powered:page.snapshot.enabled===true;known:typeof page.snapshot.enabled==="boolean";guarded:true;available:page.snapshot.present===true && !page.busy;onChanged:powered=>page.action("wifi-radio",JSON.stringify({interface:page.snapshot.interface,enabled:powered})) }
    Rectangle {
        visible:!!page.snapshot.linked;width:parent.width;height:visible?linkedContent.implicitHeight+Kit.Runtime.px(20):0;color:Kit.Runtime.c("ink-3")
        Rectangle { width:Kit.Runtime.px(2);height:parent.height;color:Kit.Runtime.c("jade") }
        Column {
            id:linkedContent;x:Kit.Runtime.px(10);y:Kit.Runtime.px(10);width:parent.width-Kit.Runtime.px(20);spacing:Kit.Runtime.px(9)
            Kit.Micro { text:"● "+Kit.Runtime.label("linked");color:Kit.Runtime.c("jade") }
            Row {
                width:parent.width;spacing:Kit.Runtime.px(6)
                WifiBars { strength:page.linked.signal || 0;anchors.verticalCenter:parent.verticalCenter;ink:Kit.Runtime.c("jade") }
                Kit.Label { width:parent.width-Kit.Runtime.px(95);text:page.linked.name || "";elide:Text.ElideRight;font.family:Kit.Runtime.sans;font.weight:Font.DemiBold;font.pixelSize:Kit.Runtime.px(13) }
                Kit.Icon { visible:["open","owe"].indexOf(page.linked.security)<0;name:"lock";font.pixelSize:Kit.Runtime.px(12) }
                Kit.Micro { text:page.linked.band || "";pixels:8 }
            }
            Grid {
                columns:2;width:parent.width;rowSpacing:Kit.Runtime.px(8);columnSpacing:Kit.Runtime.px(8)
                Repeater {
                    model:[{label:"IPv4",value:page.linked.ipv4},{label:"GATEWAY",value:page.linked.gateway},{label:"RATE · "+(page.linked.security || "").toUpperCase(),value:Format.number(page.linked.rate,1)+" Mb/s"},{label:"SIGNAL",value:Format.number(page.linked.signal)+"%"}]
                    Column { required property var modelData;width:(linkedContent.width-Kit.Runtime.px(8))/2;spacing:Kit.Runtime.px(4)
                        Kit.Micro { text:modelData.label;pixels:7 }
                        Kit.Label { width:parent.width;text:modelData.value || "—";elide:Text.ElideRight;font.pixelSize:Kit.Runtime.px(10) }
                    }
                }
            }
            Row { width:parent.width;spacing:Kit.Runtime.px(6);enabled:!page.busy
                HoldButton { text:Kit.Runtime.label("disconnect");width:(parent.width-Kit.Runtime.px(6))/2;onTriggered:page.send("wifi-disconnect",page.linked) }
                HoldButton { text:Kit.Runtime.label("forget");width:(parent.width-Kit.Runtime.px(6))/2;danger:true;onTriggered:page.send("wifi-forget",page.linked) }
            }
            Row { visible:page.linked.tailnet===true;spacing:Kit.Runtime.px(5);Kit.Icon { name:"hub";font.pixelSize:Kit.Runtime.px(12);color:Kit.Runtime.c("jade") } Kit.Micro { text:Kit.Runtime.label("tailnet-link");color:Kit.Runtime.c("jade");pixels:8 } }
        }
    }
    Row {
        width:parent.width;height:Kit.Runtime.px(30)
        Kit.Micro { width:parent.width-scan.width;anchors.verticalCenter:parent.verticalCenter;text:Kit.Runtime.label("available")+" · "+(page.snapshot.networks===undefined?"—":page.networks.length)+(page.snapshot.age===null || page.snapshot.age===undefined?"":" · "+Format.age(page.snapshot.age));pixels:8 }
        Kit.Button { id:scan;text:Kit.Runtime.tr("scan");icon:"refresh";height:parent.height;enabled:page.snapshot.enabled===true && !page.busy;onClicked:page.send("wifi-scan",null) }
    }
    Repeater {
        model:page.networkIds
        Column {
            id:network
            required property var modelData
            required property int index
            readonly property var entry:page.networks.find(row=>row.id===modelData) || ({id:"",name:"",signal:0,band:"",security:"",uuid:""})
            width:page.width;spacing:Kit.Runtime.px(7);visible:network.entry.id!==""
            Kit.Button {
                id:row;width:parent.width;height:Kit.Runtime.px(34);borderVisible:false;enabled:network.entry.id!=="" && page.snapshot.enabled===true && !page.busy
                Accessible.name:network.entry.name;onClicked:page.connect(network.entry)
                onActiveFocusChanged:if(activeFocus)page.selectedId=network.entry.id
                onRightClicked:page.selectedId=network.entry.id
                Row { anchors.fill:parent;anchors.leftMargin:Kit.Runtime.px(5);anchors.rightMargin:Kit.Runtime.px(5);spacing:Kit.Runtime.px(6)
                    Kit.Micro { width:Kit.Runtime.px(15);height:parent.height;text:String(network.index+1).padStart(2,"0");color:row.foreground;pixels:7 }
                    WifiBars { anchors.verticalCenter:parent.verticalCenter;strength:network.entry.signal;ink:row.foreground }
                    Kit.Label { width:Math.max(0,parent.width-Kit.Runtime.px(163));height:parent.height;text:network.entry.name;elide:Text.ElideRight;font.family:Kit.Runtime.sans;font.pixelSize:Kit.Runtime.px(12);color:row.foreground }
                    Kit.Icon { height:parent.height;width:Kit.Runtime.px(12);name:network.entry.security==="enterprise"?"badge":["open","owe"].indexOf(network.entry.security)>=0?"":"lock";font.pixelSize:Kit.Runtime.px(11);color:row.foreground }
                    Kit.Micro { height:parent.height;text:network.entry.band;pixels:7;color:row.foreground }
                    Kit.Micro { width:Kit.Runtime.px(62);height:parent.height;horizontalAlignment:Text.AlignRight;text:row.highlighted?"↵ "+Kit.Runtime.tr("connect"):network.entry.uuid?Kit.Runtime.tr("saved"):["open","owe"].indexOf(network.entry.security)>=0?Kit.Runtime.tr("open-network"):"";pixels:7;color:row.foreground }
                }
            }
            Loader {
                width:parent.width;active:page.promptId===network.entry.id;sourceComponent:Passphrase {
                    width:network.width;busy:page.busy
                    onSubmitted:secret=> { const value=page.payload(network.entry);value.credentials=true;page.credential(JSON.stringify(value),secret); }
                    onCancelled:page.promptId=""
                    onFocusMoved:control=>page.focusMoved(control)
                }
            }
            Kit.Button { visible:!!network.entry.uuid && (page.promptId===network.entry.id || page.selectedId===network.entry.id);text:Kit.Runtime.label("forget");baseForeground:Kit.Runtime.c("vermilion");enabled:!page.busy;onClicked:page.send("wifi-forget",network.entry) }
        }
    }
    Kit.Label { visible:page.snapshot.networks!==undefined && !page.networks.length;width:parent.width;text:Kit.Runtime.tr(page.snapshot.present===false?"unavailable":page.snapshot.enabled?"no-networks":"radio-off");color:Kit.Runtime.c("mist-5");font.pixelSize:Kit.Runtime.px(11) }
}
