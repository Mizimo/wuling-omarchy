import QtQuick
import "kit" as Kit
import "Detail.js" as Format

Column {
    id:page
    property var snapshot:({})
    property bool memorySort:false
    readonly property var memory:snapshot.memory || ({})
    readonly property var processes:(snapshot.processes || []).slice().sort((a,b)=>memorySort?b.rss-a.rss:(b.cpu || 0)-(a.cpu || 0)).slice(0,12)
    signal action(string name,string value)
    function key(event) {
        if(event.key===Qt.Key_S) { memorySort=!memorySort;event.accepted=true; }
        else if(event.key===Qt.Key_Return || event.key===Qt.Key_Enter) { action("performance-monitor","");event.accepted=true; }
    }
    spacing:Kit.Runtime.px(6)
    Item {
        width:parent.width;height:Kit.Runtime.px(88)
        Kit.Micro { text:"CPU";y:Kit.Runtime.px(5) }
        Kit.Label { y:Kit.Runtime.px(15);text:Format.number(page.snapshot.cpu_percent)+"%";font.family:Kit.Runtime.display;font.pixelSize:Kit.Runtime.px(46);font.weight:Font.DemiBold;color:Kit.Runtime.c("paper-1") }
        Column {
            x:parent.width*.43;width:parent.width-x
            Repeater {
                model:[{label:"LOAD 1 · 5 · 15",value:(page.snapshot.load || []).map(v=>Format.number(v,2)).join(" · ")},
                    {label:Kit.Runtime.label("temperature"),value:Format.number(page.snapshot.temperature_c)+" °C"},
                    {label:Kit.Runtime.label("frequency"),value:Format.number(page.snapshot.frequency_mhz/1000,2)+" GHz"},
                    {label:"UPTIME",value:Format.uptime(page.snapshot.uptime_seconds)}]
                DetailValue { required property var modelData;width:parent.width;label:modelData.label;value:modelData.value }
            }
        }
    }
    DetailChart { width:parent.width;height:Kit.Runtime.px(44);samples:page.snapshot.history || [] }
    Kit.Micro { text:"−60 S";width:parent.width;pixels:7 }
    DetailHeading { width:parent.width;text:Kit.Runtime.label("threads");note:(page.snapshot.threads || []).length+" THREADS" }
    Grid {
        width:parent.width;columns:(page.snapshot.threads || []).length>8?2:1;columnSpacing:Kit.Runtime.px(12);rowSpacing:Kit.Runtime.px(5)
        Repeater {
            model:page.snapshot.threads || []
            Item {
                required property var modelData
                width:(parent.width-parent.columnSpacing*(parent.columns-1))/parent.columns;height:Kit.Runtime.px(18)
                Kit.Micro { width:Kit.Runtime.px(34);height:parent.height;text:modelData.name.toUpperCase();pixels:7 }
                DetailGauge { x:Kit.Runtime.px(34);anchors.verticalCenter:parent.verticalCenter;width:parent.width-x-Kit.Runtime.px(30);value:modelData.percent || 0;ink:modelData.percent>80?Kit.Runtime.c("fill"):Kit.Runtime.c("paper-1") }
                Kit.Micro { anchors.right:parent.right;height:parent.height;text:Format.number(modelData.percent);pixels:7 }
            }
        }
    }
    DetailHeading { width:parent.width;text:Kit.Runtime.label("memory");note:Format.bytes(page.memory.used)+" / "+Format.bytes(page.memory.total) }
    DetailGauge { width:parent.width;height:Kit.Runtime.px(10);value:page.memory.total?100*page.memory.used/page.memory.total:0;cached:page.memory.total?100*page.memory.cache/page.memory.total:0 }
    Flow {
        width:parent.width;spacing:Kit.Runtime.px(10)
        Repeater {
            model:[{key:"used",ink:"paper-1"},{key:"cache",ink:"mist-6"},{key:"free",ink:"ink-5"}]
            Row {
                required property var modelData;spacing:Kit.Runtime.px(4);height:Kit.Runtime.px(18)
                Rectangle { anchors.verticalCenter:parent.verticalCenter;width:Kit.Runtime.px(5);height:width;color:Kit.Runtime.c(modelData.ink) }
                Kit.Micro { anchors.verticalCenter:parent.verticalCenter;text:Kit.Runtime.tr(modelData.key)+" "+Format.bytes(page.memory[modelData.key]);pixels:7 }
            }
        }
    }
    DetailValue { width:parent.width;label:"SWAP";value:Format.bytes(page.memory.swap_used)+" / "+Format.bytes(page.memory.swap_total) }
    DetailHeading { width:parent.width;text:Kit.Runtime.label("processes");note:"S · "+(page.memorySort?"RSS":"CPU") }
    Repeater {
        model:page.processes
        Kit.Button {
            required property var modelData;width:page.width;height:Kit.Runtime.px(26);borderVisible:false
            Accessible.name:modelData.name;onClicked:page.action("performance-monitor","")
            Kit.Label { x:Kit.Runtime.px(5);width:parent.width-Kit.Runtime.px(123);height:parent.height;text:modelData.name;color:parent.foreground;font.pixelSize:Kit.Runtime.px(10) }
            Kit.Label { anchors.right:rss.left;anchors.rightMargin:Kit.Runtime.px(10);height:parent.height;text:Format.number(modelData.cpu,1)+"%";color:parent.foreground;font.pixelSize:Kit.Runtime.px(9) }
            Kit.Label { id:rss;anchors.right:parent.right;anchors.rightMargin:Kit.Runtime.px(5);height:parent.height;text:Format.bytes(modelData.rss);color:parent.foreground;font.pixelSize:Kit.Runtime.px(9) }
        }
    }
    Kit.Button { width:parent.width;text:Kit.Runtime.label("open-monitor");onClicked:page.action("performance-monitor","") }
}
