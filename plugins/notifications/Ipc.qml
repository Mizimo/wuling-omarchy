import QtQuick
import Quickshell.Io
Item {
    required property var service
    IpcHandler {
        target:"notifications"
        function ping(): string { return "ok"; }
        function dndState(): string { return service.doNotDisturb ? "on" : "off"; }
        function isDnd(): string { return dndState(); }
        function setDnd(value: string): string { service.setDoNotDisturb(["true","1","on","yes"].indexOf(value.toLowerCase())>=0); return dndState(); }
        function toggleDnd(): string { service.setDoNotDisturb(!service.doNotDisturb); return dndState(); }
        function showHistory(): string { service.showHistory(); return "ok"; }
        function clear(): string { service.history=[]; service.saveSoon(); return "ok"; }
        function dismissAll(): string { service.dismissAll(); return "ok"; }
        function dismissOne(): string { if(!service.live.count)return "none"; service.closeToast(service.live.get(0).key,"dismissed"); return "ok"; }
        function invokeLast(): string { return service.live.count && service.activate(service.live.get(0).key) ? "ok" : "none"; }
        function invokeAction(n: int): string { return service.live.count && service.runDeed(service.live.get(0).key,n-1) ? "ok" : "none"; }
        function act(): string { return service.act(); }
        function keyboard(): string { if(service.keyboardMode) { service.stopKeyboard(); return "off"; } return service.startKeyboard("") ? "on" : "none"; }
        function count(): string { return String(service.live.count); }
        function expand(): string { service.expanded=!service.expanded; return service.expanded ? "expanded" : "collapsed"; }
        function dismiss(summary: string): string {
            if(!summary)return "none"; let hit=false;
            for(let i=service.live.count-1;i>=0;i--)if(service.live.get(i).summary.indexOf(summary)>=0) { service.closeToast(service.live.get(i).key,"dismissed"); hit=true; }
            return hit?"ok":"none";
        }
        function probe(): string { return JSON.stringify(service.probe()); }
    }
    IpcHandler {
        target:"wuling.notifications"
        function ping(): string { return "ok"; }
        function log(): string { return JSON.stringify({schema_version:1,provider:"wuling.notifications",count:service.history.length}); }
        function terminal(name: string, geometry: string): string {
            try { const value=JSON.parse(geometry); const next=Object.assign({},service.terminals); next[name]={open:value.open===true,x:Number(value.x),y:Number(value.y),width:Math.max(0,Math.min(8192,Number(value.width)||0)),height:Math.max(0,Math.min(8192,Number(value.height)||0))}; service.terminals=next; return "ok"; } catch(_) { return "invalid"; }
        }
        function historyAction(key: string): string { return service.historyAction(key) ? "ok" : "none"; }
    }
}
