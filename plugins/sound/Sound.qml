import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Services.Pipewire
import "kit" as Kit
import "kit/SessionIdentity.js" as SessionIdentity

Item {
    id: sound
    property var shell: null
    readonly property var sink: Pipewire.defaultAudioSink
    readonly property bool muted: !sink || !sink.audio || sink.audio.muted || sink.audio.volume<=0
    readonly property string directory:(Quickshell.env("XDG_DATA_HOME") || Quickshell.env("HOME")+"/.local/share")+"/wuling/current/sounds/"
    readonly property string identity:Quickshell.env("HYPRLAND_INSTANCE_SIGNATURE") || ""
    property var last:({})
    property var waiting:[]
    property var gated:null
    property bool stopping:false
    property bool loginPending:false
    property int played:0
    property int dropped:0
    PwObjectTracker { objects:sound.sink?[sound.sink]:[] }
    function allowed(cue) {
        return /^(open|close|toggle|select|deny|notify|alert|tick(?:-[1-7])?|hover|boot|drop|seal)$/.test(cue)
            && Kit.Runtime.setting("sounds")!=="off"
            && (Kit.Runtime.setting("sounds")==="full" || !/^(hover|tick)/.test(cue));
    }
    function play(cue,level) {
        if(stopping || !allowed(cue) || muted)return "silent";
        const now=Date.now();
        if(now-(last[cue] || 0)<(cue==="hover"?80:35)) { dropped++;return "limited"; }
        last[cue]=now;
        const request={cue:cue,level:Math.max(0,Math.min(1,Number(level)||0)),music:false};
        if(cue==="notify" || cue==="alert") { waiting=waiting.concat([request]).slice(-4);nextGate();return "queued"; }
        return launch(request);
    }
    function launch(request) {
        if(stopping || muted || (!request.music && !allowed(request.cue)))return "silent";
        if(request.music) {
            const path=String(Kit.Runtime.setting("login_music") || "");
            if(!path)return "silent";
            music.command=["pw-play","--volume","0.6","--",path[0]==="~"?Quickshell.env("HOME")+path.slice(1):path];
            music.running=true;return "playing";
        }
        for(let i=0;i<voices.count;i++) {
            const voice=voices.itemAt(i);
            if(voice && !voice.player.running) {
                voice.player.command=["pw-play","--volume",String(.6*request.level),"--",directory+request.cue+".wav"];
                voice.player.running=true;played++;return "playing";
            }
        }
        dropped++;return "limited";
    }
    function nextGate() {
        if(stopping || gate.running || !waiting.length)return;
        gated=waiting[0];waiting=waiting.slice(1);gate.running=true;
    }
    function login() {
        // This mark records the attempt even when muted, DND, or unset: no
        // deferred replay on an unlock, shell restart, or setting change.
        if(!identity || stopping)return "silent";
        loginPending=true;
        if(!Kit.Runtime.resolved.colors)return "pending";
        loginPending=false;
        marker.reload();if(marker.text().trim()===identity)return "seen";
        marker.setText(identity);
        if(!SessionIdentity.fresh(identity,Date.now()))return "seen";
        if(muted || !Kit.Runtime.setting("login_music"))return "silent";
        waiting=waiting.concat([{music:true}]).slice(-4);nextGate();return "queued";
    }
    function stopVoices() {
        if(!voices)return;
        for(let i=0;i<voices.count;i++) { const v=voices.itemAt(i);if(v && v.player.running)v.player.signal(9); }
    }
    onMutedChanged: if(muted) { stopVoices();if(music.running)music.signal(9); }
    Connections {
        target:Kit.Runtime
        function onResolvedChanged() {
            if(Kit.Runtime.setting("sounds")==="off")sound.stopVoices();
            if(sound.loginPending)sound.login();
        }
    }
    Repeater {
        id:voices;model:4
        Item { property alias player:player;Process { id:player } }
    }
    Process { id:music }
    Process {
        id:gate;command:["omarchy-shell","notifications","dndState"]
        stdout:StdioCollector { onStreamFinished: if(text.trim()==="off" && sound.gated)sound.launch(sound.gated) }
        onExited: { sound.gated=null;Qt.callLater(sound.nextGate); }
    }
    FileView {
        id:marker;path:(Quickshell.env("XDG_RUNTIME_DIR") || "/nonexistent")+"/wuling/login-music-"+Qt.md5(sound.identity)
        preload:false;blockAllReads:true;blockWrites:true;printErrors:false
    }
    // Arrival can claim earlier when its arming ends. This bounded fallback
    // also supports independently disabling the session animation plugin.
    Timer { interval:1000;running:true;onTriggered:arrivalState.running=true }
    Process {
        id:arrivalState;command:["omarchy-shell","-q","wuling.session","inspect"]
        property bool active:false
        stdout:StdioCollector { onStreamFinished: { try { arrivalState.active=JSON.parse(text).arrival===true; }catch(_) {} } }
        onExited: if(!active)sound.login()
    }
    IpcHandler {
        target:"wuling.sound"
        function play(cue:string,level:string):string { return sound.play(cue,level); }
        function login():string { return sound.login(); }
        function state():string {
            let active=0;for(let i=0;i<voices.count;i++)if(voices.itemAt(i).player.running)active++;
            return JSON.stringify({schema_version:1,voices:active,music:music.running,queued:waiting.length,played:sound.played,dropped:sound.dropped,mode:Kit.Runtime.setting("sounds"),muted:sound.muted});
        }
    }
    Component.onDestruction: {
        stopping=true;stopVoices();if(music.running)music.signal(9);if(gate.running)gate.signal(9);if(arrivalState.running)arrivalState.signal(9);
    }
}
