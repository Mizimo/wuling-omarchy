import QtQuick
import Quickshell.Io
import "WriterState.js" as Policy

Item {
    id: owner
    property var state: Policy.create()
    property bool ready: false
    property bool stopping: false
    property bool failedAttempt: false
    property bool starting: false
    property bool everStarted: false
    property bool hasExited: false
    property var exitCode: null
    signal exhausted()
    function health() {
        return {schema_version:1,ok:ready && !state.reason && !state.halted,
            status:state.halted?"given-up":ready?"running":starting?"starting":hasExited?"exited":"never-started",
            ever_started:everStarted,pid:child.processId,
            running:child.running,ready:ready,stopped:state.halted,pending:!!state.latest,
            in_flight:!!state.flight,recovery_attempts:state.attempts,
            retry_ms:retry.running?retry.interval:0,exit_code:exitCode,reason:state.reason};
    }
    function enqueue(payload) { Policy.enqueue(state,payload);flush(); }
    function flush() {
        if(!ready || stopping)return;
        const payload=Policy.send(state);if(payload)child.write(payload);
    }
    function start() {
        if(stopping || state.halted)return;
        starting=true;failedAttempt=false;startup.restart();child.running=true;
    }
    function failed(reason) {
        if(stopping || failedAttempt)return;
        failedAttempt=true;ready=false;starting=false;startup.stop();
        const delay=Policy.failed(state,Date.now(),reason);
        if(child.running)child.signal(9);
        if(delay) { retry.interval=delay;retry.restart(); }
        else exhausted();
    }
    function stop() {
        stopping=true;retry.stop();startup.stop();
        // Never flush or wait during teardown, including a stopped child.
        if(child.running)child.signal(9);
    }
    Timer { id:retry;onTriggered:owner.start() }
    Timer { id:startup;interval:5000;onTriggered:owner.failed("Notification writer did not start") }
    Process {
        id:child;command:["wuling","notifications","persist"];stdinEnabled:true
        onStarted: {
            owner.everStarted=true;owner.starting=false;startup.stop();owner.ready=true;
            if(!owner.state.latest)owner.state.reason="";
            owner.flush();
        }
        // Quickshell emits runningChanged, but not exited, on FailedToStart.
        // Retain the startup deadline as a second bound if no signal arrives.
        onRunningChanged: if(!running && owner.starting)owner.failed("Notification writer failed to start")
        stdout:SplitParser {
            onRead: line => {
                if(owner.stopping || owner.failedAttempt)return;
                if(Policy.acknowledge(owner.state,line))owner.flush();
                else owner.failed("Notification writer did not acknowledge a saved state");
            }
        }
        onExited: (code,status) => {
            owner.hasExited=true;owner.exitCode=code;
            console.warn("WULING notification writer exited: " + code);
            owner.ready=false;
            owner.failed("Notification writer exited (code " + code + ")");
        }
    }
    Component.onDestruction:stop()
}
