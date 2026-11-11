import QtQuick
import Qt.labs.folderlistmodel
import Quickshell
import Quickshell.Io
import qs.Commons as Native
import "kit" as Kit

Item {
    id:watch
    property var owner:null
    property var contract:({})
    property bool active:false
    property bool staged:false
    property bool initialScan:true
    property bool cover:false
    property bool covered:false
    property bool palette:false
    property bool rechecked:false
    property bool lockChecked:false
    property string phase:"idle"
    property string previous:""
    property string next:""
    property double started:0
    property double paletteAt:0
    property double waveAt:0
    property real progress:0
    property var captured:({})
    property var swaps:({})
    property var checks:({})
    property var outputs:[]
    property int attempts:0
    property int played:0
    property int skipped:0
    property var last:({})
    readonly property bool allowed:!!owner && !owner.arriving && !owner.token && Kit.Runtime.setting("session.theme") && !Kit.Runtime.reduced
    readonly property string stateRoot:Quickshell.env("HOME")+"/.local/state/omarchy/current"
    onAllowedChanged:if(active && !allowed)finish("disabled")
    readonly property string outputNames:Quickshell.screens.map(s=>s.name).join("\n")
    onOutputNamesChanged:if(active)finish("outputs-changed")
    function name() { themeName.reload();return themeName.text().trim(); }
    FileView { id:themeName;path:watch.stateRoot+"/theme.name";preload:false;blockAllReads:true;printErrors:false }
    // The gated files, read only when a switch starts. The startup gate gave
    // their digests; any difference falls back to the full gate.
    FileView { id:gated;preload:false;blockAllReads:true;printErrors:false }
    function unchanged() {
        const sums=contract.recheck;
        if(!sums || !Object.keys(sums).length)return false;
        for(const path in sums) {
            gated.path=path;gated.reload();
            if(Qt.md5(gated.text())!==sums[path])return false;
        }
        return true;
    }
    // No theme-file watch or capture at idle. The staging directory is the
    // early signal shared by the CLI and Omarchy's own picker.
    FolderListModel {
        id:directory;folder:"file://"+watch.stateRoot
        showFiles:false;showDirs:true;showDotAndDotDot:false
        onCountChanged:watch.scan()
        onStatusChanged:if(status===FolderListModel.Ready)watch.scan()
    }
    Connections {
        target:directory
        function onDataChanged() { watch.scan(); }
        function onModelReset() { watch.scan(); }
        function onRowsInserted() { watch.scan(); }
        function onRowsRemoved() { watch.scan(); }
    }
    function scan() {
        let found=false;
        for(let i=0;i<directory.count;i++)if(directory.get(i,"fileName")==="next-theme")found=true;
        const was=staged;staged=found;
        if(initialScan) { if(directory.status===FolderListModel.Ready)initialScan=false;return; }
        if(found && !was)prepare();
        else if(!found && was && active)committed.restart();
    }
    function prepare() {
        if(active) { finish("superseded");return; }
        if(!allowed || !contract.ok)return;
        attempts++;previous=name();next="";phase="capture";started=Date.now();
        palette=false;paletteAt=0;waveAt=0;progress=0;cover=false;covered=false;rechecked=false;lockChecked=false;
        captured=({});swaps=({});checks=({});outputs=Quickshell.screens.map(s=>s.name);
        active=true;deadline.restart();lockQuery.running=true;
        if(unchanged()) { rechecked=true;checks={gate:Date.now()}; }
        else { gate.cancelled=false;gate.running=true; }
    }
    function ready(output) {
        if(!active || phase!=="capture")return;
        const nextCaptured=Object.assign({},captured);nextCaptured[output]=Date.now();captured=nextCaptured;
        considerCover();
    }
    function considerCover() {
        if(!active || phase!=="capture" || !rechecked || !lockChecked)return;
        // theme.name is an even earlier cutoff than applyTheme. A stalled
        // directory notification must never let a mixed WULING frame through.
        if(palette || name()!==previous) { finish("late-capture");return; }
        if(outputs.length && outputs.every(name=>captured[name]))cover=true;
    }
    function swapped(output) {
        if(!active || !cover || swaps[output])return;
        const nextSwaps=Object.assign({},swaps);nextSwaps[output]=Date.now();swaps=nextSwaps;
        covered=outputs.every(name=>swaps[name]);
        if(covered)phase="hold";
    }
    function paletteArrived() {
        if(!active || phase==="wave")return;
        if(!covered) { finish("late-palette");return; }
        palette=true;
        // loadShell follows loadColors in the same native call. Restarting
        // from its last assignment is conservative for the background clock.
        paletteAt=Date.now();
    }
    Connections {
        target:Native.Color;enabled:watch.active
        function onForegroundChanged() { watch.paletteArrived(); }
        function onBackgroundChanged() { watch.paletteArrived(); }
        function onAccentChanged() { watch.paletteArrived(); }
        function onUrgentChanged() { watch.paletteArrived(); }
        function onMutedChanged() { watch.paletteArrived(); }
        function onThemeShellValuesChanged() { watch.paletteArrived(); }
    }
    Connections {
        target:Kit.Runtime;enabled:watch.active && !watch.covered
        function onResolvedChanged() { if(Kit.Runtime.resolved.theme!==watch.previous)watch.finish("late-wuling-palette"); }
    }
    Timer {
        id:committed;interval:30
        onTriggered: {
            if(!watch.active)return;
            watch.next=watch.name();
            if(!watch.next || watch.next===watch.previous)watch.finish("unchanged-or-failed");
        }
    }
    function reveal() {
        if(!covered || !palette || !next || next===previous) { finish("deadline-incomplete");return; }
        phase="wave";waveAt=Date.now();played++;Kit.Runtime.cue("open",.5);
    }
    function tick() {
        if(!active)return;
        if(phase==="wave") {
            progress=Math.min(1,(Date.now()-waveAt)/420);
            if(progress>=1)finish("played");
        } else if(Date.now()-started>=1500)reveal();
        else if(palette && next && next!==previous) {
            const duration=contract.scaled_duration?Native.Style.duration(contract.background_ms):contract.background_ms;
            // On these content-gated natives the palette is applied at the
            // start of the background reveal. Include two 30 Hz frames for
            // its final buffer; the independent deadline always wins.
            if(Date.now()-paletteAt>=duration+contract.settle_ms)reveal();
        }
    }
    FrameAnimation { running:watch.active;onTriggered:watch.tick() }
    Timer { id:deadline;interval:1500;onTriggered: { if(watch.phase!=="wave")watch.reveal(); } }
    function finish(reason) {
        if(!active)return;
        if(phase!=="wave")skipped++;
        last={reason:reason,started:started,finished:Date.now(),captured:captured,swaps:swaps,checks:checks,palette:paletteAt,wave:waveAt};
        active=false;phase="idle";cover=false;covered=false;captured=({});swaps=({});outputs=[];
        deadline.stop();committed.stop();gate.cancelled=true;gate.running=false;lockQuery.running=false;
    }
    function inspect() { return JSON.stringify({active:active,phase:phase,covered:covered,progress:progress,gate:contract,attempts:attempts,played:played,skipped:skipped,last:last,loaded:!!visual.item}); }
    Loader { id:visual;active:watch.active;source:"ThemeWave.qml";onLoaded:item.owner=watch;onStatusChanged:if(status===Loader.Error)watch.finish("overlay-failed") }
    Timer { interval:150;running:watch.active;repeat:true;onTriggered:if(!lockQuery.running)lockQuery.running=true }
    Process {
        id:lockQuery;command:["timeout","1s","omarchy-shell","lock","isLocked"]
        stdout:StdioCollector {
            onStreamFinished: {
                if(!watch.active)return;
                if(text.trim()!=="false")watch.finish("locked-or-unavailable");
                else { watch.lockChecked=true;watch.checks=Object.assign({lock:Date.now()},watch.checks);watch.considerCover(); }
            }
        }
    }
    Process {
        id:gate;property bool cancelled:false
        command:["timeout","1s","wuling","session","theme-compatibility"];running:true
        stdout:StdioCollector {
            onStreamFinished: {
                if(gate.cancelled)return;
                try { watch.contract=JSON.parse(text); }catch(_) { watch.contract=({ok:false}); }
                if(watch.active) {
                    if(!watch.contract.ok)watch.finish("unknown-contract");
                    else { watch.rechecked=true;watch.checks=Object.assign({gate:Date.now()},watch.checks);watch.considerCover(); }
                }
            }
        }
    }
}
