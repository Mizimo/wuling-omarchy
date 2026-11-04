import QtQuick
import "kit" as Kit
import "Detail.js" as Format

Column {
    id:page
    property var snapshot:({})
    property int selected:-1
    readonly property var profiles:["power-saver","balanced","performance"]
    signal action(string name,string value)
    signal focusMoved(var control)
    function key(event) {
        if(event.key!==Qt.Key_Right && event.key!==Qt.Key_Left)return;
        let index=selected<0?profiles.indexOf(snapshot.profile):selected;
        for(let step=0;step<3;step++) {
            index=(index+(event.key===Qt.Key_Right?1:2))%3;
            if((snapshot.profiles || []).indexOf(profiles[index])>=0) {
                selected=index;
                const control=profileButtons.itemAt(index);
                control.forceActiveFocus();focusMoved(control);break;
            }
        }
        event.accepted=true;
    }
    spacing:Kit.Runtime.px(7)
    Item {
        width:parent.width;height:Kit.Runtime.px(84)
        Kit.Micro { y:Kit.Runtime.px(3);text:Kit.Runtime.label("combined") }
        Kit.Label { y:Kit.Runtime.px(15);text:Format.number(page.snapshot.percent)+"%";font.family:Kit.Runtime.display;font.pixelSize:Kit.Runtime.px(46);font.weight:Font.DemiBold;color:Kit.Runtime.c("paper-1") }
        Column {
            x:parent.width*.43;width:parent.width-x;spacing:Kit.Runtime.px(7)
            Kit.Label { width:parent.width;text:Kit.Runtime.label("battery-"+(page.snapshot.state || "unknown"));font.pixelSize:Kit.Runtime.px(10);color:Kit.Runtime.c(page.snapshot.state==="charging"?"jade":"paper-2") }
            Kit.Micro { text:Format.duration(page.snapshot.seconds)+" · "+Format.number(page.snapshot.watts,1)+" W" }
            Kit.Micro { text:Kit.Runtime.label("supply-"+(page.snapshot.supply || "unknown"));pixels:7.5 }
        }
    }
    DetailChart { width:parent.width;height:Kit.Runtime.px(50);samples:page.snapshot.history || [];timed:true;ink:Kit.Runtime.c("jade") }
    Row {
        width:parent.width
        Kit.Micro { width:parent.width/2;text:"−24 H";pixels:7 }
        Kit.Micro { width:parent.width/2;text:Kit.Runtime.tr((page.snapshot.history || []).length?"now":"no-history");horizontalAlignment:Text.AlignRight;pixels:7 }
    }
    DetailHeading { width:parent.width;text:Kit.Runtime.label("packs") }
    Kit.Label { visible:!(page.snapshot.packs || []).length;width:parent.width;text:Kit.Runtime.tr("no-battery");color:Kit.Runtime.c("mist-5") }
    Repeater {
        model:page.snapshot.packs || []
        Rectangle {
            required property var modelData
            readonly property color ink:Kit.Runtime.c(!modelData.present?"mist-5":modelData.percent<=8?"vermilion":modelData.state==="charging"?"jade":"paper-1")
            width:page.width;height:Math.max(Kit.Runtime.px(94),health.y+health.height+Kit.Runtime.px(8));color:Kit.Runtime.c("ink-3");border.width:1;border.color:Kit.Runtime.c("line")
            Kit.Micro { x:Kit.Runtime.px(10);y:Kit.Runtime.px(10);text:modelData.name;color:parent.ink }
            Kit.Micro { anchors.right:parent.right;anchors.rightMargin:Kit.Runtime.px(10);y:Kit.Runtime.px(10);text:Kit.Runtime.label("battery-"+modelData.state);pixels:7;color:parent.ink }
            Kit.Label { x:Kit.Runtime.px(10);y:Kit.Runtime.px(24);text:Format.number(modelData.percent)+"%";font.family:Kit.Runtime.display;font.pixelSize:Kit.Runtime.px(28);color:parent.ink }
            DetailGauge { x:parent.width*.3;y:Kit.Runtime.px(34);width:parent.width-x-Kit.Runtime.px(12);value:modelData.present?modelData.percent || 0:0;ink:parent.ink }
            DetailValue { id:health;x:Kit.Runtime.px(10);y:Kit.Runtime.px(65);height:implicitHeight;width:parent.width-Kit.Runtime.px(20);label:Kit.Runtime.label("health");value:Format.number(modelData.health)+"% · "+Format.number(modelData.full,1)+" Wh" }
        }
    }
    DetailHeading { width:parent.width;text:Kit.Runtime.label("profile") }
    Row {
        width:parent.width;spacing:Kit.Runtime.px(3)
        Repeater {
            id:profileButtons;model:page.profiles
            Kit.Button {
                required property string modelData
                required property int index
                width:(page.width-Kit.Runtime.px(6))/3;height:Kit.Runtime.px(44)
                selected:page.snapshot.profile===modelData;enabled:(page.snapshot.profiles || []).indexOf(modelData)>=0;opacity:enabled?1:.4
                Accessible.name:Kit.Runtime.tr(modelData)
                onClicked: { page.selected=index;page.action("profile",modelData); }
                Keys.onPressed:event=> {
                    event.accepted=false;page.key(event);
                    if(event.key===Qt.Key_Return || event.key===Qt.Key_Enter || event.key===Qt.Key_Space) { clicked();event.accepted=true; }
                }
                Column { anchors.centerIn:parent;spacing:Kit.Runtime.px(5)
                    Kit.Micro { anchors.horizontalCenter:parent.horizontalCenter;text:["SAVER","BALANCED","PERFORMANCE"][index];pixels:7;color:parent.parent.foreground }
                    Kit.Label { visible:Kit.Runtime.language!=="en";anchors.horizontalCenter:parent.horizontalCenter;text:Kit.Runtime.tr(modelData);font.pixelSize:Kit.Runtime.px(10);color:parent.parent.foreground }
                }
            }
        }
    }
}
