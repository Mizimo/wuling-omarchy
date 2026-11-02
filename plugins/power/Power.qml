import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import "kit" as Kit

Item {
    id: power
    property var shell:null
    property bool opened:false
    property string outputName:""
    property var rows:[]
    property int selected:0
    property bool holding:false
    property string holdInput:""
    property real holdProgress:0
    property bool committed:false
    property real exitElapsed:0
    property bool preview:false
    property string error:""
    property real appearance:0
    property real buildElapsed:0
    property bool workerReady:false
    readonly property var outputNames:Quickshell.screens.map(s=>s.name)
    readonly property string targetOutput:outputNames.indexOf(outputName)>=0?outputName:outputNames[0] || ""
    function open(raw) {
        if(committed)return;
        let value;try { value=JSON.parse(raw || "{}"); }catch(_) { value=({}); }
        preview=value.previewExit===true;selected=0;error="";rows=[];
        outputName=Hyprland.focusedMonitor?Hyprland.focusedMonitor.name:"";
        opened=true;fadeOut.stop();appearance=0;buildElapsed=0;entering.restart();build.restart();reader.running=true;
        if(!worker.running) { workerReady=false;worker.running=true; }
    }
    function close() { if(committed)return;cancelHold();opened=false;entering.stop();build.stop();fadeOut.restart();reader.running=false;if(!confirmationSent)worker.running=false; }
    property bool confirmationSent:false
    Process {
        id:worker;command:["wuling","session","arm"];stdinEnabled:true
        stdout:SplitParser { onRead:line=>{ if(line==="ready")power.workerReady=true; } }
        onExited: { power.workerReady=false;power.confirmationSent=false; }
    }
    NumberAnimation { id:entering;target:power;property:"appearance";from:0;to:1;duration:Kit.Runtime.reduced?90:150 }
    NumberAnimation { id:fadeOut;target:power;property:"appearance";to:0;duration:130;onFinished:if(!power.opened)power.rows=[] }
    NumberAnimation { id:build;target:power;property:"buildElapsed";from:0;to:760;duration:760 }
    function dismiss() { close();if(shell && !committed)shell.hide("wuling.power"); }
    function cancelHold() { hold.stop();holding=false;holdInput="";holdProgress=0; }
    function choose(index) { if(committed)return;cancelHold();selected=Math.max(0,Math.min(rows.length-1,index)); }
    function press(source) {
        const row=rows[selected];if(!row || row.disabled || committed || holding)return;
        if(!row.dangerous) {
            Quickshell.execDetached(["bash","-c",row.action]);dismiss();return;
        }
        holding=true;holdInput=source;holdProgress=0;hold.start();
    }
    function commit() {
        if(committed || !rows[selected])return;
        const row=rows[selected],started=Date.now();
        committed=true;holding=false;holdInput="";holdProgress=1;exitElapsed=0;
        const request=JSON.stringify({id:row.id,action:row.action,started:started,preview:preview});
        if(worker.running && workerReady) { confirmationSent=true;worker.write(request+"\n"); }
        else Quickshell.execDetached(["wuling","session","exit",request]);
        if(!preview && !Kit.Runtime.setting("session.exit")) { committed=false;dismiss(); }
        else leaving.start();
    }
    NumberAnimation { id:hold;target:power;property:"holdProgress";from:0;to:1;duration:800;onFinished:power.commit() }
    NumberAnimation {
        id:leaving;target:power;property:"exitElapsed";from:0;to:Kit.Runtime.reduced?120:560;duration:Kit.Runtime.reduced?120:560
        onFinished: { power.committed=false;power.dismiss(); }
    }
    function pressed(event) {
        if(committed) { event.accepted=true;return; }
        if(event.key===Qt.Key_Escape)dismiss();
        else if(event.key===Qt.Key_Left)choose(selected-1);
        else if(event.key===Qt.Key_Right)choose(selected+1);
        else if(event.key===Qt.Key_Return || event.key===Qt.Key_Enter) { if(!event.isAutoRepeat)press("key"); }
        else {
            const letter=event.text.toUpperCase(),index=rows.findIndex(r=>r.key===letter);
            if(index<0)return;choose(index);
        }
        event.accepted=true;
    }
    function released(event) {
        if(!event.isAutoRepeat && (event.key===Qt.Key_Return || event.key===Qt.Key_Enter) && holdInput==="key")cancelHold();
        event.accepted=true;
    }
    Process {
        id:reader;command:["wuling","power","snapshot"]
        stdout:StdioCollector {
            onStreamFinished: {
                if(!power.opened)return;
                try {
                    const value=JSON.parse(text);
                    if(value.schema_version!==1 || !Array.isArray(value.rows))throw Error("data");
                    power.rows=value.rows;
                    if(power.preview) { power.selected=Math.max(0,power.rows.findIndex(r=>r.name==="logout"));previewDelay.restart(); }
                }catch(_) { power.error=Kit.Runtime.tr("unavailable"); }
            }
        }
    }
    Timer { id:previewDelay;interval:300;onTriggered:if(power.opened)power.commit() }
    IpcHandler {
        target:"wuling.power"
        function state():string { return JSON.stringify({opened:power.opened,selected:power.selected,rows:power.rows.map(r=>r.name),holding:power.holding,committed:power.committed}); }
    }
    Variants {
        model:Quickshell.screens
        PanelWindow {
            id:surface
            required property var modelData
            readonly property bool showing:power.opened && modelData.name===power.targetOutput
            visible:(power.opened || power.appearance>0) && modelData.name===power.targetOutput;screen:modelData;color:"transparent";exclusionMode:ExclusionMode.Ignore
            anchors { top:true;bottom:true;left:true;right:true }
            WlrLayershell.namespace:"wuling-power"
            WlrLayershell.layer:WlrLayer.Overlay
            WlrLayershell.keyboardFocus:showing?WlrKeyboardFocus.Exclusive:WlrKeyboardFocus.None
            onShowingChanged:if(showing)Qt.callLater(function(){catcher.forceActiveFocus();})
            FocusScope {
                id:catcher;anchors.fill:parent;focus:true
                Keys.onPressed:event=>power.pressed(event)
                Keys.onReleased:event=>power.released(event)
                Rectangle {
                    anchors.fill:parent
                    readonly property color ink:Kit.Runtime.c("ink-0")
                    color:Qt.rgba(ink.r,ink.g,ink.b,Kit.Runtime.resolved.palette==="paper"?.88:.86)
                    opacity:power.opened?1:power.appearance
                }
                MouseArea { anchors.fill:parent;onClicked:power.dismiss() }
                Item {
                    id:panel;width:Kit.Runtime.px(1086);height:Kit.Runtime.px(360);anchors.centerIn:parent
                    scale:Math.min(1,(surface.width-32)/width,(surface.height-32)/height)
                    opacity:power.committed?Math.max(0,1-(power.exitElapsed-120)/160):power.appearance
                    transform:Scale { origin.x:panel.width/2;origin.y:panel.height/2;yScale:power.committed && !Kit.Runtime.reduced?Math.max(.02,1-Math.max(0,power.exitElapsed-120)/160):1 }
                    Kit.Micro { x:0;y:0;text:"04";color:Kit.Runtime.c("accent-ink") }
                    Kit.Micro { x:Kit.Runtime.px(28);y:0;text:"TERMINATION PROTOCOL" }
                    Kit.Label { y:Kit.Runtime.px(20);text:Kit.Runtime.language==="en"?"TERMINATION PROTOCOL":"終止協議";font.family:Kit.Runtime.language==="en"?Kit.Runtime.display:Kit.Runtime.serif;font.pixelSize:Kit.Runtime.px(34);font.weight:Font.Black;font.letterSpacing:Kit.Runtime.px(2) }
                    Row {
                        id:cards;y:Kit.Runtime.px(84);width:parent.width;spacing:Kit.Runtime.px(8)
                        Repeater {
                            model:power.rows
                            Rectangle {
                                id:card;required property var modelData;required property int index
                                readonly property bool chosen:index===power.selected
                                readonly property color ground:Kit.Runtime.c("ink-2")
                                readonly property color ink:Kit.Runtime.c(chosen?"on-accent":"paper-1")
                                width:(cards.width-(power.rows.length-1)*cards.spacing)/Math.max(1,power.rows.length);height:Kit.Runtime.px(214)
                                color:chosen?Kit.Runtime.c("fill"):Qt.rgba(ground.r,ground.g,ground.b,.88)
                                border.width:1;border.color:Kit.Runtime.c(chosen?"fill":"line");opacity:(modelData.disabled?.4:1)*(Kit.Runtime.reduced?1:Math.max(0,Math.min(1,(power.buildElapsed-150-Math.min(index,11)*45)/70)))
                                scale:power.committed && chosen && power.exitElapsed<120?.98:1
                                Kit.Hazard { visible:card.modelData.dangerous;x:-1;y:-1;width:parent.width+2;height:Kit.Runtime.px(5);ink:Kit.Runtime.c("fill") }
                                Kit.Label { x:Kit.Runtime.px(14);y:Kit.Runtime.px(14);text:String(card.index+1).padStart(2,"0");font.family:Kit.Runtime.display;font.pixelSize:Kit.Runtime.px(28);font.weight:Font.DemiBold;color:Kit.Runtime.c(card.chosen?"on-accent":"mist-6") }
                                Rectangle { anchors.right:parent.right;anchors.rightMargin:Kit.Runtime.px(12);y:Kit.Runtime.px(14);width:Kit.Runtime.px(16);height:width;color:"transparent";border.width:1;border.color:Kit.Runtime.c(card.chosen?"on-accent":"mist-5");Kit.Micro { anchors.centerIn:parent;text:card.modelData.key;pixels:8;color:card.ink } }
                                Kit.Icon { x:Kit.Runtime.px(14);y:Kit.Runtime.px(113);name:card.modelData.icon;font.pixelSize:Kit.Runtime.px(24);color:card.ink }
                                Kit.Label { x:Kit.Runtime.px(14);y:Kit.Runtime.px(149);width:parent.width-x*2;text:card.modelData.label.toUpperCase();font.family:Kit.Runtime.display;font.pixelSize:Kit.Runtime.px(13);font.weight:Font.DemiBold;font.letterSpacing:Kit.Runtime.px(2);color:card.ink }
                                Kit.Label { visible:Kit.Runtime.language!=="en";x:Kit.Runtime.px(14);y:Kit.Runtime.px(168);width:parent.width-x*2;text:card.modelData.translated?Kit.Runtime.tr(card.modelData.name):card.modelData.label;font.family:Kit.Runtime.sans;font.pixelSize:Kit.Runtime.px(11.5);color:Kit.Runtime.c(card.chosen?"on-accent":"mist-4") }
                                Rectangle { anchors.bottom:parent.bottom;width:parent.width*(card.chosen?power.holdProgress:0);height:Kit.Runtime.px(4);color:Kit.Runtime.c("on-accent") }
                                Kit.Label { visible:power.committed && card.chosen;anchors.right:parent.right;anchors.bottom:parent.bottom;anchors.margins:Kit.Runtime.px(10);text:"終";font.family:Kit.Runtime.serif;font.weight:Font.Black;font.pixelSize:Kit.Runtime.px(34);color:Kit.Runtime.c("vermilion");scale:1+.4*Math.max(0,1-power.exitElapsed/60) }
                                MouseArea {
                                    anchors.fill:parent;hoverEnabled:true;enabled:!power.committed && !card.modelData.disabled
                                    onPressed: { power.choose(card.index);power.press("pointer"); }
                                    onReleased:if(power.holdInput==="pointer")power.cancelHold()
                                    onCanceled:if(power.holdInput==="pointer")power.cancelHold()
                                    onExited:if(power.holdInput==="pointer")power.cancelHold()
                                }
                            }
                        }
                    }
                    Kit.Label { visible:!!power.error;anchors.centerIn:parent;text:power.error;color:Kit.Runtime.c("vermilion") }
                    Rectangle { y:Kit.Runtime.px(322);width:parent.width;height:1;color:Kit.Runtime.c("line") }
                    Kit.Micro { y:Kit.Runtime.px(335);text:"←→ "+Kit.Runtime.tr("select")+"     "+Kit.Runtime.tr("hold")+" ↵ 0.8S     ESC "+Kit.Runtime.tr("abort") }
                    Kit.Micro { y:Kit.Runtime.px(335);anchors.right:parent.right;text:Kit.Runtime.tr("native-entries") }
                }
            }
        }
    }
}
