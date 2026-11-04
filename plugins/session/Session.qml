import QtQuick
import QtQuick.Window
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import "Gate.js" as Gate
import "kit/SessionIdentity.js" as SessionIdentity

// No font, theme resolver or animation imports before the first ink swap.
Item {
    id: session
    property var shell: null
    property string token: ""
    property bool watchReady:false
    Timer { interval:1;running:!session.arriving && !session.watchReady;onTriggered:session.watchReady=true }
    Loader { id:themeWatcher;active:session.watchReady;source:"ThemeWatch.qml";onLoaded:item.owner=session }
    readonly property string identity:Quickshell.env("HYPRLAND_INSTANCE_SIGNATURE") || ""
    property bool arriving:false
    property bool previewing:false
    property double firstSwap:0
    property var swapped:({})
    property bool visualReady:false
    property string primary:""
    readonly property var outputNames:Quickshell.screens.map(s=>s.name)
    onOutputNamesChanged:if(arriving && outputNames.indexOf(primary)<0)primary=outputNames[0] || ""
    FileView {
        id:arrivalMarker;path:(Quickshell.env("XDG_RUNTIME_DIR") || "/nonexistent")+"/wuling/arrival-"+Qt.md5(session.identity)
        preload:false;blockAllReads:true;blockWrites:true;printErrors:false
    }
    FileView {
        id:startupSettings;path:(Quickshell.env("XDG_CONFIG_HOME") || Quickshell.env("HOME")+"/.config")+"/wuling/overrides.toml"
        preload:false;blockAllReads:true;printErrors:false
    }
    Component.onCompleted: {
        if(!identity || !Quickshell.env("XDG_RUNTIME_DIR"))return;
        if(arrivalMarker.text().trim()===identity)return;
        // Mark even an intentionally disabled arrival: enabling it later in
        // this session must not turn a plugin reload into a new login.
        arrivalMarker.setText(identity);
        if(SessionIdentity.fresh(identity,Date.now()) && Gate.arrivalEnabled(startupSettings.text()))beginArrival(false);
    }
    function beginArrival(preview) {
        if(arriving || token)return "busy";
        previewing=preview;firstSwap=0;swapped=({});visualReady=false;
        primary=Hyprland.focusedMonitor?Hyprland.focusedMonitor.name:Quickshell.screens.length?Quickshell.screens[0].name:"";
        arriving=true;arrivalWatchdog.restart();return "ready";
    }
    function inkSwapped(name) {
        if(!arriving || swapped[name])return;
        const next=Object.assign({},swapped);next[name]=Date.now();swapped=next;
        if(firstSwap)return;
        firstSwap=Date.now();arrivalWatchdog.restart();
        // The callback runs only after the minimal window has submitted ink.
        presentation.setSource("Arrival.qml",{owner:session});presentation.active=true;
    }
    function releaseArrival() {
        arriving=false;visualReady=false;arrivalWatchdog.stop();
        presentation.active=false;presentation.source="";
    }
    function skipArrival() { if(presentation.item)presentation.item.skip();else releaseArrival(); }
    Timer { id:arrivalWatchdog;interval:3500;onTriggered:session.releaseArrival() }
    FrameAnimation { running:session.arriving;onTriggered:if(session.firstSwap && Date.now()-session.firstSwap>=3490)session.releaseArrival() }
    Loader { id:presentation;active:false;onLoaded:session.visualReady=true }
    Connections { target:presentation.item;ignoreUnknownSignals:true;function onFinished() { Qt.callLater(session.releaseArrival); } }
    Variants {
        model:session.arriving?Quickshell.screens:[]
        PanelWindow {
            id:ink
            required property var modelData
            property bool hadFocus:false
            screen:modelData;visible:true;exclusionMode:ExclusionMode.Ignore
            anchors { top:true;bottom:true;left:true;right:true }
            // Allocate an alpha surface from creation. Changing an initially
            // opaque window to transparent later can reveal black, not the
            // desktop, during the wave and wipe.
            color:"transparent"
            WlrLayershell.namespace:"wuling-session-arrival"
            WlrLayershell.layer:WlrLayer.Overlay
            WlrLayershell.keyboardFocus:!session.primary || session.primary===modelData.name?WlrKeyboardFocus.Exclusive:WlrKeyboardFocus.None
            Rectangle { anchors.fill:parent;color:"#050707";visible:view.status!==Loader.Ready }
            Connections {
                target:ink.contentItem.Window.window
                function onFrameSwapped() { session.inkSwapped(ink.modelData.name); }
                function onActiveChanged() {
                    const window=ink.contentItem.Window.window;
                    if(window && window.active)ink.hadFocus=true;
                    else if(ink.hadFocus && (!session.primary || session.primary===ink.modelData.name))session.releaseArrival();
                }
            }
            FocusScope {
                anchors.fill:parent;focus:true
                Keys.onPressed:event=>{if(!event.isAutoRepeat)session.skipArrival();event.accepted=true;}
                Keys.onReleased:event=>{event.accepted=true;}
                MouseArea { anchors.fill:parent;acceptedButtons:Qt.AllButtons;onClicked:session.skipArrival();onWheel:event=>{event.accepted=true;} }
            }
            Loader {
                id:view;anchors.fill:parent;active:session.visualReady
                source:active?"ArrivalView.qml":""
                onLoaded: { item.controller=presentation.item;item.outputName=ink.modelData.name; }
            }
        }
    }
    function begin(raw) {
        if(token)return "busy";
        let value;try { value=JSON.parse(raw); }catch(_) { return "unavailable"; }
        if(!value.token || !Number.isFinite(value.started))return "unavailable";
        releaseArrival();
        token=value.token;
        body.setSource("Exit.qml",{payload:value});body.active=true;
        if(body.status!==Loader.Ready) { release();return "unavailable"; }
        watchdog.interval=Math.max(1,value.started+(value.reduced?120:560)+10120-Date.now());
        watchdog.restart();return "ready";
    }
    function release() { watchdog.stop();body.active=false;body.source="";token=""; }
    Loader { id:body;active:false }
    Connections { target:body.item;ignoreUnknownSignals:true;function onFinished() { Qt.callLater(session.release); } }
    Timer { id:watchdog;interval:12000;onTriggered:session.release() }
    IpcHandler {
        target:"wuling.session"
        function arrival(unused:string):string { return session.beginArrival(true); }
        function themeState():string { return themeWatcher.item?themeWatcher.item.inspect():"{}"; }
        function inspect():string { return JSON.stringify({schema_version:1,arrival:session.arriving,first_swap:session.firstSwap,outputs:session.swapped,visual:session.visualReady,controller_loaded:!!presentation.item,watchdog:arrivalWatchdog.running,preview:session.previewing}); }
        function begin(payload:string):string { return session.begin(payload); }
        function finish(token:string):string {
            if(session.token!==token)return "stale";
            if(body.item)body.item.finish();else session.release();return "ok";
        }
        function state(token:string):string { return session.token && (!token || token===session.token) && body.status===Loader.Ready?"active":"idle"; }
    }
}
