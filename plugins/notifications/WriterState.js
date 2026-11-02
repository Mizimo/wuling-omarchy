.pragma library

// A single newest full snapshot, retained until that exact snapshot is ACKed.
// This policy has no timers, processes or notification contents in diagnostics.
function create() { return {latest:"",flight:"",started:0,attempts:0,halted:false,reason:""}; }
function enqueue(state, payload) { state.latest=payload; }
function send(state) {
    if(state.halted || state.flight || !state.latest)return "";
    state.flight=state.latest;return state.flight;
}
function acknowledge(state, line) {
    let reply;try { reply=JSON.parse(line); }catch(_) { return false; }
    if(!reply || reply.schema_version!==1 || reply.ok!==true || !state.flight)return false;
    if(state.latest===state.flight)state.latest="";
    state.flight="";state.reason="";return true;
}
function failed(state, now, reason) {
    state.flight="";state.reason=reason;
    if(!state.started || now-state.started>=600000) { state.started=now;state.attempts=0; }
    if(state.attempts===3) { state.halted=true;return 0; }
    return [1000,5000,30000][state.attempts++];
}
