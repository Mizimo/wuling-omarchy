import QtQuick
import Quickshell
import Quickshell.Io
import "kit/Motion.js" as Motion

Item {
    id: sequence
    required property var owner
    property var payload:({})
    property real elapsed:Math.max(0,Date.now()-owner.firstSwap)
    property real armedAt:-1
    property real wipeAt:-1
    property real reducedAt:-1
    property bool done:false
    property bool waveCued:false
    property bool wipeCued:false
    property int ticks:0
    readonly property bool reduced:!!payload.resolved && payload.resolved.settings.motion.value==="reduced"
    readonly property real phase:reduced?2000:armedAt<0?-1:elapsed-armedAt
    readonly property real wave:reduced?1:Math.max(0,Math.min(1,(phase-1400)/420))
    readonly property real wipe:reduced?0:wipeAt<0?0:Motion.snap((elapsed-wipeAt)/300)
    readonly property real fade:reduced && reducedAt>=0?Math.max(0,Math.min(1,(elapsed-reducedAt-600)/120)):0
    signal finished()
    function cue(name,level) {
        const mode=payload.resolved?payload.resolved.settings.sounds.value:"essential";
        if(mode==="off" || mode!=="full" && /^(tick|hover)/.test(name))return;
        Quickshell.execDetached(["omarchy-shell","-q","wuling.sound","play",name,String(level===undefined?1:level)]);
    }
    function finish() { if(done)return;done=true;reader.running=false;finished(); }
    function skip() {
        if(reduced) { finish();return; }
        if(wipeAt<0) { wipeAt=elapsed;reveal(); }
    }
    function reveal() {
        if(wipeCued)return;wipeCued=true;cue("drop");
        Quickshell.execDetached(["omarchy-shell","-q","wuling.bar","arrival",reduced?"fade":"reveal",String(Date.now()+(reduced?0:20))]);
    }
    function update() {
        if(done)return;
        if(reduced) {
            if(reducedAt<0) {
                reducedAt=elapsed;cue("boot");
                if(!owner.previewing)Quickshell.execDetached(["omarchy-shell","-q","wuling.sound","login"]);
            }
            if(elapsed>=reducedAt+600)reveal();
            if(elapsed>=reducedAt+720)finish();return;
        }
        // Background has no public presented-frame signal. The documented
        // one-second bound is used unless every readiness condition is known.
        if(armedAt<0 && elapsed>=1000) {
            armedAt=1000;cue("boot");
            if(!owner.previewing)Quickshell.execDetached(["omarchy-shell","-q","wuling.sound","login"]);
        }
        if(phase>=720) {
            const desired=Math.min((payload.rows || []).length,1+Math.floor((phase-720)/110));
            while(ticks<desired)cue("tick-"+Math.min(7,++ticks));
        }
        if(phase>=1400 && !waveCued) { waveCued=true;cue("open",.5); }
        if(phase>=2000 && wipeAt<0) { wipeAt=elapsed;reveal(); }
        if(wipe>=1 || elapsed>=3490)finish();
    }
    onElapsedChanged:update()
    Component.onCompleted: {
        Quickshell.execDetached(["omarchy-shell","-q","wuling.bar","arrival","hold",String(owner.firstSwap+3500)]);
    }
    // Qt's animation clock can smooth out a startup stall. This sequence is
    // measured from the submitted ink frame, so catch up to wall time instead.
    FrameAnimation { running:!sequence.done;onTriggered:sequence.elapsed=Math.max(0,Date.now()-sequence.owner.firstSwap) }
    Process {
        id:reader;running:true;command:["wuling","session","prepare-arrival"]
        stdout:StdioCollector {
            onStreamFinished: {
                try { const data=JSON.parse(text);if(data.schema_version===1 && data.rows)sequence.payload=data; }catch(_) {}
                sequence.update();
            }
        }
    }
    Component.onDestruction:Quickshell.execDetached(["omarchy-shell","-q","wuling.bar","arrival","release","0"])
}
