import QtQuick
import "kit" as Kit
import "Detail.js" as Format

Column {
    id:page
    property var snapshot:({})
    signal action(string name,string value)
    function key(event) {
        if(event.key===Qt.Key_C) { action("system-copy","");event.accepted=true; }
        else if(event.key===Qt.Key_F) { action("system-fastfetch","");event.accepted=true; }
    }
    spacing:Kit.Runtime.px(6)
    Item {
        width:parent.width;height:Kit.Runtime.px(70)
        // Small marks use the simplified plate, as on the bar's menu cell.
        Image { width:Kit.Runtime.px(52);height:width;y:Kit.Runtime.px(8);source:"emblem.svg";sourceSize.width:width;sourceSize.height:height }
        Column {
            x:Kit.Runtime.px(64);width:parent.width-x;y:Kit.Runtime.px(9);spacing:Kit.Runtime.px(5)
            Kit.Micro { text:Kit.Runtime.label("designation");pixels:7.5 }
            Kit.Label { width:parent.width;text:(page.snapshot.host || "—").toUpperCase();font.family:Kit.Runtime.display;font.pixelSize:Kit.Runtime.px(34);font.weight:Font.DemiBold;color:Kit.Runtime.c("paper-1") }
        }
    }
    Repeater {
        model:[{head:"host-info",rows:[{key:"host",value:page.snapshot.host},{key:"os",value:page.snapshot.os},{key:"kernel",value:page.snapshot.kernel},{key:"cpu",value:page.snapshot.cpu},{key:"gpu",value:page.snapshot.gpu},{key:"disk",value:Format.bytes(page.snapshot.disk_used)+" / "+Format.bytes(page.snapshot.disk_total)}]},
            {head:"session",rows:[{key:"Omarchy",value:page.snapshot.omarchy},{key:"Hyprland",value:page.snapshot.hyprland},{key:"Quickshell",value:page.snapshot.quickshell},{key:"uptime",value:Format.uptime(page.snapshot.uptime_seconds)},{key:"display",value:(page.snapshot.displays || []).map(d=>d.name+" · "+d.width+"×"+d.height+" @"+Format.number(d.refresh)+" · "+d.scale+"×").join("\n")},{key:"input-method",value:page.snapshot.input_method}]},
            {head:"release",rows:[{key:"WULING",value:(page.snapshot.release || {}).version},{key:"commit",value:((page.snapshot.release || {}).commit || "").slice(0,12)},{key:"date",value:(page.snapshot.release || {}).date}]}]
        Column {
            required property var modelData;width:page.width
            DetailHeading { width:parent.width;text:Kit.Runtime.label(modelData.head) }
            Repeater { model:parent.modelData.rows
                DetailValue { required property var modelData;width:parent.width;label:Kit.Runtime.tr(modelData.key).toUpperCase();value:modelData.value || "—" }
            }
        }
    }
    Row { width:parent.width;spacing:Kit.Runtime.px(6)
        Kit.Button { width:(parent.width-parent.spacing)/2;text:Kit.Runtime.label("copy");onClicked:page.action("system-copy","") }
        Kit.Button { width:(parent.width-parent.spacing)/2;text:"FASTFETCH";onClicked:page.action("system-fastfetch","") }
    }
}
