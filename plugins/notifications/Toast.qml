import QtQuick
import Quickshell
import "kit" as Kit

Item {
    id:toast
    required property var row
    required property var service
    property real maximumHeight: 600
    readonly property bool selected: service.keyboardMode && service.keyboardKey===row.key
    readonly property bool expanded: service.expanded || selected
    readonly property var actions: { service.revision; return service.deeds(row.key); }
    readonly property color edge: Kit.Runtime.c(row.urgency===2 ? "vermilion" : actions.length || service.rules.argv(row.execArgv) ? "fill" : "jade")
    readonly property bool important: actions.length>0 || !!service.rules.argv(row.execArgv)
    readonly property color backgroundInk: Kit.Runtime.c("ink-3")
    readonly property real contentLimit: Math.max(20,maximumHeight-header.height-Kit.Runtime.px(42)-actionBox.implicitHeight)
    implicitHeight:Math.min(maximumHeight,(actions.length?actionBox.y+actionBox.implicitHeight:content.y+content.height)+Kit.Runtime.px(10))
    property real arrival: 0
    opacity:arrival
    transform:Translate { x:Kit.Runtime.reduced?0:(1-toast.arrival)*Kit.Runtime.px(8) }
    Component.onCompleted:arrival=1
    Behavior on arrival { NumberAnimation { duration:Kit.Runtime.reduced?90:200; easing.type:Easing.OutCubic } }
    // The canvas belongs to this card. It retains neither native QObject
    // notifications nor callbacks in the service after the card is destroyed.
    Canvas {
        id:plate; anchors.fill:parent
        property color ink:toast.backgroundInk
        property color line:Kit.Runtime.c(toast.selected?"accent-ink":"line")
        onInkChanged:requestPaint(); onLineChanged:requestPaint(); onWidthChanged:requestPaint(); onHeightChanged:requestPaint()
        onPaint: {
            const c=getContext("2d"),cut=Kit.Runtime.px(10); c.reset(); c.beginPath(); c.moveTo(.5,.5);c.lineTo(width-.5,.5);c.lineTo(width-.5,height-cut);c.lineTo(width-cut,height-.5);c.lineTo(.5,height-.5);c.closePath();
            c.globalAlpha=.97;c.fillStyle=ink;c.fill();c.globalAlpha=1;c.strokeStyle=line;c.lineWidth=1;c.stroke();
        }
    }
    Rectangle { width:Kit.Runtime.px(2); height:parent.height; color:toast.edge }
    MouseArea { x:Kit.Runtime.px(2); y:header.height; width:parent.width-x; height:content.height+Kit.Runtime.px(20); onClicked:service.activate(row.key) }
    Rectangle {
        id:header; x:Kit.Runtime.px(2); width:parent.width-x; height:Kit.Runtime.px(Kit.Runtime.hud?26:22)
        color:Kit.Runtime.hud && toast.important ? Kit.Runtime.c("fill") : "transparent"
        Rectangle { anchors.bottom:parent.bottom; width:parent.width; height:1; color:Kit.Runtime.c("line-soft") }
        Kit.Micro { id:caption; x:Kit.Runtime.px(10); anchors.verticalCenter:parent.verticalCenter; text:Kit.Runtime.label("comms").toUpperCase(); color:Kit.Runtime.c(Kit.Runtime.hud && toast.important?"on-accent":"mist-5") }
        Kit.Micro { x:caption.x+caption.width+Kit.Runtime.px(8); anchors.verticalCenter:parent.verticalCenter; width:Math.max(0,stamp.x-x-Kit.Runtime.px(8)); text:row.app.toUpperCase(); color:Kit.Runtime.c(Kit.Runtime.hud && toast.important?"on-accent":"paper-2") }
        Kit.Micro { id:stamp; anchors.right:close.left; anchors.rightMargin:Kit.Runtime.px(6); anchors.verticalCenter:parent.verticalCenter; text:Qt.formatDateTime(new Date(row.ts*1000),"HH:mm"); color:caption.color }
        Kit.Button {
            id:close; anchors.right:parent.right; anchors.rightMargin:Kit.Runtime.px(4); width:Kit.Runtime.px(22); height:parent.height
            borderVisible:false; activeFocusOnTab:false; baseForeground:caption.color; Accessible.name:Kit.Runtime.tr("dismiss")
            Kit.Icon { anchors.centerIn:parent; name:"close"; font.pixelSize:Kit.Runtime.px(14); color:close.foreground }
            onClicked:service.closeToast(row.key,"dismissed")
        }
    }
    Row {
        id:content; x:Kit.Runtime.px(12); y:header.height+Kit.Runtime.px(10); width:parent.width-Kit.Runtime.px(24); spacing:Kit.Runtime.px(10)
        Rectangle {
            width:Kit.Runtime.px(38); height:width; color:Kit.Runtime.c("ink-1"); border.width:1; border.color:Kit.Runtime.c("line")
            Image {
                id:art; anchors.fill:parent; anchors.margins:Kit.Runtime.px(3); fillMode:Image.PreserveAspectFit
                source: { const value=String(row.image || ""); if(/^image:\/\/qsimage\/[0-9]+\/[0-9]+$/.test(value))return value; if(value[0]==="/" && !/^\/(proc|sys|dev|run)(\/|$)/.test(value))return "file://"+value; return row.appIcon && !/[/:]/.test(row.appIcon) ? Quickshell.iconPath(row.appIcon,true) : ""; }
                sourceSize.width:Kit.Runtime.px(38); sourceSize.height:Kit.Runtime.px(38)
            }
            Kit.Icon { anchors.centerIn:parent; visible:art.status!==Image.Ready; name:row.urgency===2?"error":"notifications"; font.pixelSize:Kit.Runtime.px(20); color:toast.edge }
        }
        Column {
            width:parent.width-Kit.Runtime.px(48); spacing:Kit.Runtime.px(3)
            Kit.Label { width:parent.width; text:row.summary; wrapMode:Text.Wrap; maximumLineCount:toast.expanded?6:2; font.family:Kit.Runtime.sans; font.pixelSize:Kit.Runtime.px(12.5); font.weight:Font.DemiBold; color:Kit.Runtime.c("paper-1"); lineHeight:1.25; lineHeightMode:Text.ProportionalHeight }
            Kit.Label { width:parent.width; visible:!!row.body; text:row.bodyRich || row.body; textFormat:Text.StyledText; wrapMode:Text.Wrap; maximumLineCount:toast.expanded?Math.max(1,Math.floor((toast.contentLimit-parent.children[0].height)/Kit.Runtime.px(16.1))):3; font.family:Kit.Runtime.sans; font.pixelSize:Kit.Runtime.px(11.5); color:Kit.Runtime.c("mist-4"); lineHeight:1.4; lineHeightMode:Text.ProportionalHeight }
        }
    }
    Flow {
        id:actionBox; x:Kit.Runtime.px(60); y:content.y+content.height+Kit.Runtime.px(10); width:parent.width-x-Kit.Runtime.px(12); spacing:Kit.Runtime.px(6)
        Repeater {
            model:toast.actions
            Kit.Button {
                required property var modelData; required property int index
                readonly property string actionLabel:(service.keyboardMode && index<9?String(index+1)+" ":"")+(modelData.kind==="code"?Kit.Runtime.tr("copy-code"):modelData.label)
                height:Kit.Runtime.px(22); width:Math.min(actionBox.width,actionText.implicitWidth+Kit.Runtime.px(16))
                activeFocusOnTab:false; accent:index===0; Accessible.name:actionLabel
                Kit.Label { id:actionText; x:Kit.Runtime.px(8); width:parent.width-Kit.Runtime.px(16); anchors.verticalCenter:parent.verticalCenter; text:parent.actionLabel; font.pixelSize:Kit.Runtime.px(9); color:parent.foreground }
                onClicked:service.runDeed(row.key,index)
            }
        }
    }
    Rectangle {
        id:life; x:Kit.Runtime.px(2); anchors.bottom:parent.bottom; height:1; color:Kit.Runtime.c("accent-ink")
        property real fraction:1
        width:(parent.width-x)*fraction; visible:row.duration>0
        function update() { run.stop(); fraction=row.duration ? Math.max(0,Math.min(1,(row.deadline?row.deadline-Date.now():row.remaining)/row.duration)) : 1; if(row.deadline && toast.visible) { run.from=fraction; run.duration=Math.max(1,row.deadline-Date.now()); run.start(); } }
        NumberAnimation { id:run; target:life; property:"fraction"; to:0 }
        Connections { target:toast.row; ignoreUnknownSignals:true; function onDeadlineChanged() { life.update(); } function onRemainingChanged() { life.update(); } }
        Connections { target:toast; function onVisibleChanged() { life.update(); } }
        Component.onCompleted:update()
    }
    Repeater {
        model:Kit.Runtime.hud?3:0
        Rectangle { required property int index; x:toast.width-Kit.Runtime.px(36); y:header.height+Kit.Runtime.px(4+index*4); width:Kit.Runtime.px(22); height:1; color:Kit.Runtime.c("mist-6"); opacity:.4 }
    }
}
