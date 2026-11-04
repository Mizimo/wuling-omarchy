import QtQuick
import Quickshell.Io
import "kit" as Kit

Item {
    id: signalView
    property var player: null
    property bool collecting: false
    property var bars: []
    property bool analyzer: false
    readonly property bool playing:!!player && player.playing
    readonly property bool monitoring:collecting && playing
    property var lastPlayer: player
    onPlayerChanged: if(player)lastPlayer=player
    onCollectingChanged: lastPlayer=collecting?player:null
    property real live:player?1:0
    signal action(string name)
    implicitHeight:Kit.Runtime.px(100)
    Behavior on live { enabled:signalView.collecting;NumberAnimation { duration:Kit.Runtime.reduced?90:220;onStopped:if(!signalView.player)signalView.lastPlayer=null } }
    function stamp(value) { return value<0?"--:--":Math.floor(value/60)+":"+String(Math.floor(value)%60).padStart(2,"0"); }
    function inspection() { return {active:monitoring,source:!monitoring?"off":analyzer?"cava":peak.item && peak.item.selected?"peak":"flat",peak:peak.item?peak.item.peak:0,bars:bars}; }
    onMonitoringChanged: { bars=[];analyzer=false; }
    Process {
        command:["wuling","status","--spectrum"];running:signalView.monitoring
        stdout:SplitParser { onRead:line=> { try { const row=JSON.parse(line);signalView.analyzer=row.available===true;signalView.bars=row.bars || []; } catch(_) {} } }
        onExited: { signalView.analyzer=false;signalView.bars=[]; }
    }
    Loader {
        id:peak;active:signalView.monitoring && !signalView.analyzer
        sourceComponent:StreamPeak { identity:signalView.player?signalView.player.identity:"";desktopEntry:signalView.player?signalView.player.desktop_entry:"" }
    }
    component Presentation: Item {
        id:presentation
        property var entry:null
        readonly property bool playing:!!entry && entry.playing
        readonly property real duration:entry && entry.length!==undefined && entry.length!==null?entry.length:0
        readonly property real position:entry && entry.position!==undefined && entry.position!==null?entry.position:-1
        width:signalView.width;height:signalView.height
    Item {
        width:Kit.Runtime.px(64);height:width
        Canvas {
            id:artOutline;anchors.fill:parent
            property color ink:Kit.Runtime.c("line")
            onInkChanged:requestPaint()
            onWidthChanged:requestPaint()
            onPaint: { const c=getContext("2d");c.reset();c.strokeStyle=ink;c.lineWidth=1;c.setLineDash([3,3]);c.strokeRect(.5,.5,width-1,height-1); }
        }
        Kit.Icon { anchors.centerIn:parent;name:"graphic_eq";font.pixelSize:Kit.Runtime.px(24);color:Kit.Runtime.c("mist-5") }
        Image { anchors.fill:parent;source:signalView.collecting && presentation.entry?presentation.entry.art_url || "":"";sourceSize.width:Kit.Runtime.px(64);sourceSize.height:Kit.Runtime.px(64);fillMode:Image.PreserveAspectCrop;asynchronous:true;cache:false }
    }
    Item {
        x:Kit.Runtime.px(76);width:parent.width-x;height:Kit.Runtime.px(68)
        Kit.Label { width:parent.width;y:0;text:presentation.entry?presentation.entry.title || presentation.entry.identity:Kit.Runtime.tr("no-signal");font.family:Kit.Runtime.sans;font.pixelSize:Kit.Runtime.px(12);font.weight:Font.DemiBold;color:Kit.Runtime.c("paper-1") }
        Kit.Label { width:parent.width;y:Kit.Runtime.px(19);text:presentation.entry?presentation.entry.artist || Kit.Runtime.tr(presentation.playing?"playing":"paused"):Kit.Runtime.tr("no-player");font.family:Kit.Runtime.sans;font.pixelSize:Kit.Runtime.px(10);color:Kit.Runtime.c("mist-4") }
        Item {
            y:Kit.Runtime.px(40);width:parent.width;height:Kit.Runtime.px(2)
            Rectangle { anchors.fill:parent;color:Kit.Runtime.c("line");visible:!!presentation.entry }
            Row { visible:!presentation.entry;spacing:Kit.Runtime.px(3);Repeater { model:Math.floor(parent.parent.width/Kit.Runtime.px(7));Rectangle { width:Kit.Runtime.px(4);height:1;color:Kit.Runtime.c("line") } } }
            Rectangle { height:parent.height;width:parent.width*Math.min(1,Math.max(0,presentation.duration>0?presentation.position/presentation.duration:0));color:Kit.Runtime.c("jade") }
        }
        Kit.Micro { y:Kit.Runtime.px(47);text:signalView.stamp(presentation.position);pixels:8 }
        Kit.Micro { anchors.right:parent.right;y:Kit.Runtime.px(47);text:signalView.stamp(presentation.duration || -1);pixels:8 }
    }
    Row {
        y:Kit.Runtime.px(74);spacing:Kit.Runtime.px(4)
        Kit.Button { width:Kit.Runtime.px(30);height:Kit.Runtime.px(24);icon:"skip_previous";Accessible.name:Kit.Runtime.tr("previous");enabled:!!presentation.entry && presentation.entry.can_previous;onClicked:signalView.action("previous") }
        Kit.Button { width:Kit.Runtime.px(30);height:Kit.Runtime.px(24);icon:presentation.playing?"pause":"play_arrow";accent:!!presentation.entry;Accessible.name:Kit.Runtime.tr(presentation.playing?"pause":"play");enabled:!!presentation.entry && presentation.entry.can_toggle;onClicked:signalView.action("play-pause") }
        Kit.Button { width:Kit.Runtime.px(30);height:Kit.Runtime.px(24);icon:"skip_next";Accessible.name:Kit.Runtime.tr("next");enabled:!!presentation.entry && presentation.entry.can_next;onClicked:signalView.action("next") }
    }
    }
    Presentation { entry:null;opacity:1-signalView.live;visible:opacity>0;enabled:false }
    Presentation { entry:signalView.lastPlayer;opacity:signalView.live;visible:opacity>0 && signalView.collecting;enabled:!!signalView.player }
    Row {
        id:spectrum;x:Kit.Runtime.px(110);y:Kit.Runtime.px(72);width:parent.width-x;height:Kit.Runtime.px(26);spacing:Kit.Runtime.px(3)
        Repeater {
            model:20
            Rectangle {
                required property int index
                width:Math.max(1,(spectrum.width-spectrum.spacing*19)/20)
                height:Kit.Runtime.px(2)+Kit.Runtime.px(24)*Math.max(0,Math.min(1,signalView.monitoring?(signalView.analyzer?(signalView.bars[index] || 0):peak.item?peak.item.peak:0):0))
                anchors.bottom:parent.bottom;color:Kit.Runtime.c("jade");opacity:.4+.6*signalView.live
            }
        }
    }
}
