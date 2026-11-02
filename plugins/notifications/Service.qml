import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import Quickshell.Services.Notifications
import "kit" as Kit

Item {
    id: daemon
    property var shell: null
    property bool ready: false
    property bool stopping: false
    property var rules: null
    property string contract: ""
    property bool doNotDisturb: false
    property var history: []
    property var refs: ({})
    property var wires: ({})
    property int sequence: 0
    property int revision: 0
    property string pinnedOutput: ""
    property var pointerOutputs: ({})
    property var presentedOutputs: ({})
    readonly property bool pointerIn: Object.keys(pointerOutputs).some(key => pointerOutputs[key])
    property bool expanded: false
    property bool keyboardMode: false
    property string keyboardKey: ""
    property string keyboardOutput: ""
    readonly property bool paused: pointerIn || expanded || keyboardMode
    property var terminals: ({})
    readonly property var displayNames: Quickshell.screens.map(s => s.name)
    readonly property string focusedDisplay: Hyprland.focusedMonitor ? Hyprland.focusedMonitor.name : displayNames[0] || ""
    readonly property string targetDisplay: displayNames.indexOf(pinnedOutput) >= 0 ? pinnedOutput : focusedDisplay
    ListModel { id: live; dynamicRoles: true }
    property alias live: live
    function indexOf(key) { for (let i=0;i<live.count;i++) if (live.get(i).key === key) return i; return -1; }
    function row(key) { const at=indexOf(key); return at < 0 ? null : JSON.parse(JSON.stringify(live.get(at))); }
    function showsOn(name) { return contract === "4.0.6" || name === targetDisplay; }
    function presented(name,keys) {
        if(JSON.stringify(presentedOutputs[name] || [])===JSON.stringify(keys))return;
        if(keys.length)presentedOutputs[name]=keys; else delete presentedOutputs[name];
        refreshDeadlines(); schedule(); saveSoon();
    }
    function refreshDeadlines() {
        const now=Date.now(), shown={};
        for(const name in presentedOutputs)for(const key of presentedOutputs[name])shown[key]=true;
        for(let i=0;i<live.count;i++) {
            const r=live.get(i), active=!paused && !r.held && shown[r.key];
            if(!active && r.deadline) { live.setProperty(i,"remaining",Math.max(1,r.deadline-now)); live.setProperty(i,"deadline",0); }
            else if(active && !r.deadline && r.remaining)live.setProperty(i,"deadline",now+r.remaining);
        }
    }
    function setDoNotDisturb(value) { doNotDisturb = !!value; saveSoon(); }
    function duration(urgency, requested) { return urgency === 2 ? 0 : Math.min(30000, Math.max(urgency === 0 ? 5000 : 8000, Number(requested) || 0)); }
    function sentActions(key) {
        const out=[]; const n=refs[key];
        try {
            const actions=n ? n.actions : [];
            for (let i=0;i<Math.min(actions.length,16);i++) {
                const a=actions[i], id=String(a.identifier || ""), label=String(a.text || id);
                if (!id || id === "default" || contract !== "4.0.6" && /^settings$/i.test(id + "") || contract !== "4.0.6" && /^settings$/i.test(label)) continue;
                out.push({id:id.slice(0,256),text:label.slice(0,256)});
            }
        } catch (_) {}
        return out;
    }
    function deeds(key) { revision; const r=row(key); return r ? rules.actions(r, sentActions(key)) : []; }
    function shape(raw, replay) {
        const r=Object.assign({key:"",originalId:0,senderPid:0,app:"",appIcon:"",summary:"",body:"",bodyRich:"",rawBody:"",image:"",glyph:"",execArgv:"",execActions:"",source:"",link:"",code:"",codes:"",urgency:1,expireTimeout:0,ts:Date.now()/1000},raw);
        r.replay=!!replay; r.held=false; r.heldUntil=0;
        r.duration=duration(r.urgency,r.expireTimeout); r.remaining=r.duration; r.deadline=0;
        r.actionData="[]";
        return r;
    }
    function readNotification(n, key) { const r=shape(rules.snapshot(n,key),false); r.actionData=JSON.stringify(rules.actions(r,sentActions(key))); return r; }
    function wire(n,key) {
        const changed=function() { daemon.updateNotification(key); };
        const closed=function() { daemon.senderClosed(key); };
        const names=["summaryChanged","bodyChanged","urgencyChanged","expireTimeoutChanged","imageChanged","appNameChanged","appIconChanged","hintsChanged","actionsChanged"];
        const connected=[];
        for (let i=0;i<names.length;i++) try { n[names[i]].connect(changed); connected.push(names[i]); } catch (_) {}
        n.closed.connect(closed);
        wires[key]={notification:n,changed:changed,closed:closed,names:connected};
    }
    function unwire(key) {
        const w=wires[key]; if (!w) return;
        for (let i=0;i<w.names.length;i++) try { w.notification[w.names[i]].disconnect(w.changed); } catch (_) {}
        try { w.notification.closed.disconnect(w.closed); } catch (_) {}
        delete wires[key];
    }
    function receive(n) {
        if (!ready || stopping) return;
        n.tracked=true;
        const key="n-"+Date.now()+"-"+(++sequence);
        refs[key]=n; wire(n,key);
        // The closure belongs to this service, not to a transient toast delegate.
        Qt.callLater(function() { if (!daemon.stopping && daemon.refs[key]) daemon.insertNotification(key); });
    }
    function insertNotification(key) {
        let r; try { r=readNotification(refs[key],key); } catch (_) { return; }
        if (rules.quiet(r,doNotDisturb)) {
            if (!rules.ephemeral(r)) archive(r,"silenced");
            release(key,"silent"); return;
        }
        if (live.count === 0) pinnedOutput=focusedDisplay;
        r.held=pointerIn; r.heldUntil=r.held ? Date.now()+30000 : 0;
        r.deadline=0;
        live.insert(0,r); revision++;
        Kit.Runtime.cue(r.urgency === 2 ? "alert" : "notify");
        if (live.count>100) closeToast(live.get(live.count-1).key,"overflow");
        schedule(); saveSoon();
    }
    function updateNotification(key) {
        if (stopping || !refs[key]) return;
        const at=indexOf(key); if (at<0) return;
        let r; try { r=readNotification(refs[key],key); } catch (_) { return; }
        const old=row(key); r.held=old.held; r.heldUntil=old.heldUntil;
        r.deadline=0;
        for (const name in r) if (live.get(at)[name] !== r[name]) live.setProperty(at,name,r[name]);
        revision++; refreshDeadlines(); schedule(); saveSoon();
    }
    function release(key, reason) {
        const n=refs[key]; unwire(key); delete refs[key];
        if (!n) return;
        try { if (reason === "expired") n.expire(); else if (reason === "silent") n.tracked=false; else n.dismiss(); } catch (_) {}
    }
    function senderClosed(key) {
        if (stopping) return;
        unwire(key); delete refs[key];
        closeToast(key,"closed");
    }
    function archive(r, reason) {
        if (r.replay) return;
        const entry=rules.persisted(r,4096); entry.closed_ts=Date.now()/1000; entry.closed_reason=reason;
        history=[entry].concat(history.filter(x => x.key !== r.key && x.closed_ts > Date.now()/1000-86400)).slice(0,100);
        saveSoon();
    }
    function closeToast(key,reason) {
        const at=indexOf(key); if (at<0) return;
        const old=row(key); live.remove(at); archive(old,reason); release(key,reason); revision++;
        if (!live.count) { pinnedOutput=""; expanded=false; stopKeyboard(); }
        else if (keyboardMode && keyboardKey === key) keyboardKey=live.get(Math.min(at,live.count-1)).key;
        schedule(); saveSoon();
    }
    function dismissAll() { while(live.count) closeToast(live.get(0).key,"dismissed"); }
    function pointer(name,entered) { const next=Object.assign({},pointerOutputs); if(entered)next[name]=true; else delete next[name]; pointerOutputs=next; }
    onPointerInChanged: { if(!pointerIn)releaseHeld(); schedule(); }
    onPausedChanged: {
        refreshDeadlines();
        if(!pointerIn) releaseHeld();
        schedule(); saveSoon();
    }
    function releaseHeld() {
        const now=Date.now(); let changed=false;
        for(let i=0;i<live.count;i++) if(live.get(i).held && (!pointerIn || live.get(i).heldUntil<=now)) {
            live.setProperty(i,"held",false); live.setProperty(i,"heldUntil",0);
            changed=true;
        }
        if(changed)revision++;
    }
    function schedule() {
        expiry.stop(); if(!ready)return;
        let next=Infinity; const now=Date.now();
        for(let i=0;i<live.count;i++) {
            const r=live.get(i); if(r.deadline>0)next=Math.min(next,r.deadline);
            if(r.held)next=Math.min(next,r.heldUntil);
        }
        if(Number.isFinite(next)) { expiry.interval=Math.max(1,Math.min(2147483647,next-now)); expiry.start(); }
    }
    Timer { id:expiry; onTriggered: { daemon.releaseHeld(); const now=Date.now(); for(let i=live.count-1;i>=0;i--) if(live.get(i).deadline>0 && live.get(i).deadline<=now)daemon.closeToast(live.get(i).key,"expired"); daemon.schedule(); } }
    function windowFor(r) {
        const windows=Hyprland.toplevels ? Hyprland.toplevels.values : [];
        for(let i=0;i<windows.length;i++) { const info=windows[i].lastIpcObject || {}; if(r.senderPid>0 && Number(info.pid)===r.senderPid)return info; }
        return null;
    }
    function senderDefault(key,execute) {
        const n=refs[key];
        try { const actions=n ? n.actions : []; for(let i=0;i<Math.min(actions.length,16);i++)if(actions[i].identifier==="default") { if(execute)actions[i].invoke(); return true; } } catch(_) {}
        return false;
    }
    function clickable(key) { const r=row(key); return r && (!!rules.argv(r.execArgv) || senderDefault(key,false) || !!windowFor(r) || contract!=="4.0.6" && rules.destination(r)); }
    function activate(key) {
        const r=row(key); if(!r)return false;
        const argv=rules.argv(r.execArgv);
        if(argv)Quickshell.execDetached(argv);
        else if(!senderDefault(key,true)) {
            const win=windowFor(r);
            if(win && /^0x[0-9a-f]+$/i.test(String(win.address)))Hyprland.dispatch('hl.dsp.focus({window = hl.get_window("address:'+win.address+'")})');
            else if(contract!=="4.0.6" && rules.destination(r))rules.navigate(r);
            else if(r.app)Quickshell.execDetached(["omarchy-hyprland-focus-app",r.app]);
        }
        stopKeyboard(); closeToast(key,"activated"); return true;
    }
    function runDeed(key,index) {
        const r=row(key), choices=deeds(key), choice=choices[index]; if(!r || !choice)return false;
        if(choice.kind==="exec") { const argv=rules.execAction(r,Number(choice.value)); if(!argv)return false; Quickshell.execDetached(argv); }
        else if(choice.kind==="code") { Quickshell.execDetached(["wl-copy","--sensitive","--",String(choice.value)]); heldSecret=String(choice.value); secretLife.restart(); }
        else {
            let invoked=false;
            try { const actions=refs[key] ? refs[key].actions : []; for(let i=0;i<actions.length;i++)if(String(actions[i].identifier)===choice.value) { actions[i].invoke(); invoked=true; break; } } catch(_) {}
            if(!invoked)return false;
        }
        stopKeyboard(); closeToast(key,"activated"); return true;
    }
    property string heldSecret: ""
    Timer { id:secretLife; interval:60000; onTriggered:clipboardRead.running=true }
    Process { id:clipboardRead; command:["wl-paste","--no-newline"]; stdout:StdioCollector { onStreamFinished: { if(daemon.heldSecret && text===daemon.heldSecret)Quickshell.execDetached(["wl-copy","--clear"]); daemon.heldSecret=""; } } }
    function act() {
        if(!live.count)return "none"; const key=live.get(0).key, count=deeds(key).length, click=clickable(key);
        if(count+(click?1:0)>1)startKeyboard(key); else if(click)activate(key); else if(count)runDeed(key,0); else closeToast(key,"dismissed");
        return "ok";
    }
    function startKeyboard(key) { if(!live.count)return false; keyboardKey=key || live.get(0).key; keyboardOutput=contract==="4.0.6"?focusedDisplay:targetDisplay; keyboardMode=true; keyboardIdle.restart(); return true; }
    function stopKeyboard() { keyboardMode=false; keyboardKey=""; keyboardIdle.stop(); }
    Timer { id:keyboardIdle; interval:10000; onTriggered:daemon.stopKeyboard() }
    function keyPressed(event) {
        if(!keyboardMode)return;
        keyboardIdle.restart(); event.accepted=true; const key=keyboardKey;
        if(event.key===Qt.Key_Escape)stopKeyboard();
        else if([Qt.Key_Down,Qt.Key_J,Qt.Key_Tab,Qt.Key_Up,Qt.Key_K,Qt.Key_Backtab].indexOf(event.key)>=0) {
            const backwards=event.key===Qt.Key_Up || event.key===Qt.Key_K || event.key===Qt.Key_Backtab || event.key===Qt.Key_Tab && (event.modifiers&Qt.ShiftModifier);
            keyboardKey=live.get((Math.max(0,indexOf(key))+(backwards?-1:1)+live.count)%live.count).key;
        } else if(event.key===Qt.Key_Return || event.key===Qt.Key_Enter)activate(key);
        else if(event.key===Qt.Key_Delete || event.key===Qt.Key_Backspace)closeToast(key,"dismissed");
        else if(/^[1-9]$/.test(event.text))runDeed(key,Number(event.text)-1);
    }
    function saveSoon() { if(ready && !stopping)saveTimer.restart(); }
    function showHistory() { if(!historyOpen.running)historyOpen.running=true; }
    Process {
        id:historyOpen; command:["wuling","notifications","open-history"]
        stdout:StdioCollector { onStreamFinished: { let opened=false; try { opened=JSON.parse(text).opened===true; } catch(_) {} if(!opened)daemon.replay(); } }
    }
    function replay() {
        const rows=history.filter(r => r.closed_ts>Date.now()/1000-86400).slice(0,6);
        if(!rows.length)rows.push({key:"empty",app:"WULING",summary:Kit.Runtime.tr("no-recent"),body:"",urgency:0,ts:Date.now()/1000});
        if(!live.count)pinnedOutput=focusedDisplay;
        for(let i=rows.length-1;i>=0;i--) {
            const r=shape(rules.restored(Object.assign({},rows[i])),true);
            r.key="r-"+Date.now()+"-"+(++sequence); r.remaining=r.urgency===2?0:rows[i].key==="empty"?5000:20000; r.duration=r.remaining;
            r.deadline=0;
            live.insert(0,r);
        }
        while(live.count>100)closeToast(live.get(live.count-1).key,"overflow");
        revision++;schedule();
    }
    function historyAction(key) {
        const entry=history.find(r => r.key===key && r.closed_ts>Date.now()/1000-86400);
        const argv=entry ? rules.argv(entry.execArgv) : null;
        if(!argv)return false;
        Quickshell.execDetached(argv);return true;
    }
    function probe() {
        const states=[]; const instances=surfaces.instances || [];
        for(let i=0;i<instances.length;i++)states.push({display:instances[i].displayName,mapped:instances[i].visible,stepAside:instances[i].stepAside,showing:instances[i].showingNotifications});
        return {toasts:live.count,doNotDisturb:doNotDisturb,expanded:expanded,keyboardMode:keyboardMode,keyboardKey:keyboardKey,
            displays:displayNames,focusedDisplay:focusedDisplay,targetDisplay:targetDisplay,
            notificationDisplays:displayNames.filter(n => daemon.showsOn(n)),surfaces:states};
    }
    Timer { id:saveTimer; interval:30; onTriggered:daemon.queueSave() }
    function queueSave() {
        if(!ready || stopping)return;
        const rows=[];
        for(let i=0;i<live.count;i++) { const r=row(live.get(i).key); if(!r.replay)rows.push(rules.persisted(r,16384)); }
        writer.enqueue(JSON.stringify({schema_version:1,dnd:doNotDisturb,live:rows,history:history})+"\n");
    }
    function writerHealth() { return writer.health(); }
    Writer { id:writer;onExhausted:warningClaim.running=true }
    function writerWarning() {
        if(stopping || !ready)return;
        if(!live.count)pinnedOutput=focusedDisplay;
        const r=shape({key:"writer-"+Date.now(),app:"WULING",summary:Kit.Runtime.tr("writer-failed"),urgency:0},true);
        live.insert(0,r);revision++;schedule();
    }
    Process {
        id:warningClaim;command:["wuling","notifications","claim-warning"]
        stdout:StdioCollector { onStreamFinished: { try { if(JSON.parse(text).claimed)daemon.writerWarning(); }catch(_) {} } }
    }
    Process {
        id:boot; command:["wuling","notifications","boot"]; running:true
        stdout:StdioCollector {
            onStreamFinished: {
                try {
                    const data=JSON.parse(text);
                    if(!data.ok) { daemon.fallback(); return; }
                    daemon.rules=Qt.createQmlObject(data.qml,daemon,"WulingNativeNotificationRules");
                    daemon.contract=data.contract; daemon.doNotDisturb=data.state.dnd; daemon.history=data.state.history;
                    const now=Date.now();
                    for(let i=0;i<data.state.live.length;i++) {
                        if(daemon.contract==="4.0.6" && data.state.live[i].deadline>0 && data.state.live[i].deadline<=now) {
                            daemon.archive(data.state.live[i],"expired"); continue;
                        }
                        const r=daemon.shape(daemon.rules.restored(data.state.live[i]),false);
                        r.remaining=r.urgency===2?0:daemon.contract==="4.0.6"?daemon.duration(r.urgency,r.expireTimeout):20000; r.duration=r.remaining; r.deadline=0;
                        live.append(r);
                    }
                    if(live.count)daemon.pinnedOutput=daemon.focusedDisplay;
                    daemon.ready=true; writer.start(); daemon.schedule(); daemon.saveSoon();
                } catch(_) { daemon.fallback(); }
            }
        }
    }
    function fallback() { Quickshell.execDetached(["wuling","notifications","fallback"]); }
    // Optional panel geometry must never delay D-Bus registration. Native
    // restart waits only briefly after core shell IPC becomes available.
    Process {
        running:daemon.ready; command:["wuling","notifications","terminals"]
        stdout:StdioCollector { onStreamFinished: { try { daemon.terminals=JSON.parse(text).terminals || {}; } catch(_) {} } }
    }
    Component.onDestruction: {
        stopping=true;
        for(const key in wires)unwire(key);
        writer.stop();
    }
    Loader {
        active:daemon.ready
        sourceComponent:Component {
            NotificationServer {
                keepOnReload:false; imageSupported:true; actionsSupported:true
                bodyMarkupSupported:true; bodyHyperlinksSupported:false; persistenceSupported:true
                onNotification: n => daemon.receive(n)
            }
        }
    }
    Loader { active:daemon.ready; sourceComponent:Component { Ipc { service:daemon } } }
    Variants {
        id: surfaces
        model:daemon.ready ? Quickshell.screens : []
        Surface { required property var modelData; screen:modelData; service:daemon }
    }
}
