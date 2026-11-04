import QtQuick
import "kit" as Kit

Column {
    id:page
    property var snapshot:({})
    property bool busy:false
    readonly property bool running:snapshot.state==="Running"
    signal action(string name,string value)
    function key(event) {}
    spacing:Kit.Runtime.px(10)
    Row {
        width:parent.width;spacing:Kit.Runtime.px(10)
        Kit.Icon { name:"hub";font.pixelSize:Kit.Runtime.px(25);color:Kit.Runtime.c(page.running?"jade":"mist-5") }
        Kit.Label { width:parent.width-Kit.Runtime.px(40);text:page.snapshot.state===undefined?"—":Kit.Runtime.label(page.running?"connected-devices":page.snapshot.state==="NeedsLogin"?"needs-login":page.snapshot.state==="Stopped"?"stopped":"unavailable");font.pixelSize:Kit.Runtime.px(12);color:Kit.Runtime.c(page.running?"jade":"mist-5");wrapMode:Text.Wrap }
    }
    Kit.Label { width:parent.width;text:page.snapshot.name || "—";font.family:Kit.Runtime.display;font.pixelSize:Kit.Runtime.px(28);elide:Text.ElideRight }
    DetailValue { width:parent.width;labelWidth:width*.43;label:Kit.Runtime.label("address");value:page.snapshot.address || "—" }
    DetailValue { width:parent.width;labelWidth:width*.43;label:Kit.Runtime.label("exit-node");value:page.snapshot.state===undefined?"—":page.snapshot.exit_node || Kit.Runtime.tr("none") }
    HoldButton { width:parent.width;text:Kit.Runtime.label(page.running?"stop":"start");holdRequired:page.running;enabled:page.snapshot.present===true && !page.busy;onTriggered:page.action("tailnet",page.running?"stop":"start") }
    DetailHeading { width:parent.width;text:page.snapshot.peers===undefined?"—":(page.snapshot.online || 0)+"/"+(page.snapshot.peers || []).length+" "+Kit.Runtime.tr("online") }
    Repeater {
        model:page.snapshot.peers || []
        Item {
            required property var modelData
            width:page.width;height:Kit.Runtime.px(32)
            Rectangle { y:Kit.Runtime.px(13);width:Kit.Runtime.px(5);height:width;radius:width/2;color:Kit.Runtime.c(modelData.online?"jade":"mist-6") }
            Kit.Label { x:Kit.Runtime.px(15);width:parent.width-x-Kit.Runtime.px(55);height:parent.height;text:modelData.name;elide:Text.ElideRight;font.family:Kit.Runtime.sans;font.pixelSize:Kit.Runtime.px(12);color:Kit.Runtime.c(modelData.online?"paper-2":"mist-5") }
            Kit.Micro { anchors.right:parent.right;height:parent.height;text:modelData.online?modelData.route.toUpperCase():Kit.Runtime.tr("offline");pixels:7;color:Kit.Runtime.c("mist-5") }
        }
    }
}
