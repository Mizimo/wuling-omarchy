import QtQuick
import Quickshell
import Quickshell.Io

// Keep this service independent of the visual tree. Exit is created only on
// request; Arrival's ink-only startup gate is a separate later phase.
Item {
    id: session
    property var shell: null
    property string token: ""
    function begin(raw) {
        if(token)return "busy";
        let value;try { value=JSON.parse(raw); }catch(_) { return "unavailable"; }
        if(!value.token || !Number.isFinite(value.started))return "unavailable";
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
        function begin(payload:string):string { return session.begin(payload); }
        function finish(token:string):string {
            if(session.token!==token)return "stale";
            if(body.item)body.item.finish();else session.release();return "ok";
        }
        function state(token:string):string { return session.token && (!token || token===session.token) && body.status===Loader.Ready?"active":"idle"; }
    }
}
