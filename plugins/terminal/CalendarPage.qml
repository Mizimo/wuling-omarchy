import QtQuick
import "kit" as Kit
import "Detail.js" as Format

Column {
    id:page
    property var snapshot:({})
    property int year:0
    property int month:0
    readonly property var days:year?Format.month(year,month):[]
    signal action(string name,string value)
    onSnapshotChanged:if(!year && snapshot.year)today()
    Component.onCompleted:if(snapshot.year)today()
    function today() { year=snapshot.year;month=snapshot.month; }
    function step(amount) { const date=new Date(year,month-1+amount,1,12);year=date.getFullYear();month=date.getMonth()+1; }
    function key(event) {
        if(event.key===Qt.Key_PageUp || event.key===Qt.Key_PageDown) { step(event.key===Qt.Key_PageUp?-1:1);event.accepted=true; }
        else if(event.key===Qt.Key_T) { today();event.accepted=true; }
    }
    spacing:Kit.Runtime.px(10)
    Item {
        width:parent.width;height:Kit.Runtime.px(36)
        Kit.Button { id:previous;width:Kit.Runtime.px(30);text:"‹";Accessible.name:Kit.Runtime.tr("previous-month");onClicked:page.step(-1) }
        Kit.Label { x:Kit.Runtime.px(38);height:previous.height;width:parent.width-Kit.Runtime.px(160);text:page.year? page.year+" / "+String(page.month).padStart(2,"0"):"—";font.family:Kit.Runtime.display;font.pixelSize:Kit.Runtime.px(26);font.weight:Font.DemiBold }
        Kit.Button { anchors.right:todayButton.left;anchors.rightMargin:Kit.Runtime.px(6);width:Kit.Runtime.px(30);text:"›";Accessible.name:Kit.Runtime.tr("next-month");onClicked:page.step(1) }
        Kit.Button { id:todayButton;anchors.right:parent.right;text:Kit.Runtime.label("today");labelSize:9;onClicked:page.today() }
    }
    Row {
        width:parent.width
        Kit.Micro { width:Kit.Runtime.px(25);text:"W";horizontalAlignment:Text.AlignHCenter;pixels:7 }
        Repeater { model:7
            Kit.Micro { required property int index;width:(page.width-Kit.Runtime.px(25))/7;text:Kit.Runtime.tr("weekday-"+(index+1));horizontalAlignment:Text.AlignHCenter;pixels:7;color:Kit.Runtime.c(index===6?"vermilion":"mist-5") }
        }
    }
    Column {
        width:parent.width;spacing:Kit.Runtime.px(3)
        Repeater { model:6
            Row {
                id:week;required property int index;width:page.width
                Kit.Micro { width:Kit.Runtime.px(25);height:Kit.Runtime.px(34);text:page.days.length?page.days[week.index*7].week:"";pixels:7;horizontalAlignment:Text.AlignHCenter }
                Repeater { model:7
                    Rectangle {
                        required property int index
                        readonly property var date:page.days[week.index*7+index] || ({})
                        readonly property bool current:date.year===page.snapshot.year && date.month===page.snapshot.month && date.day===page.snapshot.day
                        width:(page.width-Kit.Runtime.px(25))/7;height:Kit.Runtime.px(34);color:current?Kit.Runtime.c("fill"):"transparent"
                        Kit.Label { anchors.fill:parent;text:parent.date.day || "";horizontalAlignment:Text.AlignHCenter;color:parent.current?Kit.Runtime.c("on-accent"):Kit.Runtime.c(parent.date.month!==page.month?"mist-6":index===6?"vermilion":"paper-2");font.pixelSize:Kit.Runtime.px(12) }
                    }
                }
            }
        }
    }
    DetailHeading { width:parent.width;text:Kit.Runtime.label("today") }
    Repeater {
        model:[{label:"date",value:page.snapshot.date},{label:"iso-week",value:page.snapshot.iso_year+" · W"+page.snapshot.iso_week},{label:"day-of-year",value:page.snapshot.day_of_year+" / "+page.snapshot.days_in_year},{label:"zone",value:page.snapshot.zone}]
        DetailValue { required property var modelData;width:parent.width;label:Kit.Runtime.tr(modelData.label).toUpperCase();value:modelData.value || "—" }
    }
}
