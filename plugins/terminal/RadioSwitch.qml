import QtQuick
import "kit" as Kit

Item {
    id:radio
    property string icon:"wifi"
    property string description:""
    property bool powered:false
    property bool known:true
    property bool guarded:false
    property bool available:true
    signal changed(bool powered)
    implicitHeight:Kit.Runtime.px(48)
    Kit.Icon { y:Kit.Runtime.px(6);name:radio.icon;font.pixelSize:Kit.Runtime.px(21) }
    Column {
        x:Kit.Runtime.px(31);width:Math.max(0,parent.width-x-switches.width-Kit.Runtime.px(6));spacing:Kit.Runtime.px(5)
        Kit.Micro { text:Kit.Runtime.label("radio") }
        Kit.Label { width:parent.width;text:radio.description || "—";elide:Text.ElideRight;color:Kit.Runtime.c("mist-4");font.pixelSize:Kit.Runtime.px(10) }
    }
    Row {
        id:switches;anchors.right:parent.right;spacing:1;enabled:radio.available && radio.known
        HoldButton { text:"OFF";width:Kit.Runtime.px(38);selected:radio.known && !radio.powered;holdRequired:radio.guarded && radio.powered;onTriggered:if(radio.powered)radio.changed(false) }
        HoldButton { text:"ON";width:Kit.Runtime.px(38);selected:radio.known && radio.powered;holdRequired:false;onTriggered:if(!radio.powered)radio.changed(true) }
    }
}
