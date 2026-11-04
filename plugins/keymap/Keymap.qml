import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import "kit" as Kit

Item {
    id:keys
    property var shell:null
    property bool opened:false
    property string outputName:""
    property real appearance:0
    property var listing:({rows:[],groups:[]})
    property string error:""
    readonly property var targetScreen:Quickshell.screens.find(screen=>screen.name===outputName) || Quickshell.screens[0] || null
    function open(payload) {
        if(opened)return;
        Kit.Runtime.cue("open");outputName=Hyprland.focusedMonitor?Hyprland.focusedMonitor.name:"";
        error="";listing=({rows:[],groups:[]});opened=true;leaving.stop();entering.restart();reader.running=true;
    }
    function close() {
        if(!opened)return;
        Kit.Runtime.cue("close");opened=false;reader.running=false;entering.stop();leaving.restart();
    }
    function dismiss() { close();if(shell)shell.hide("wuling.keymap"); }
    NumberAnimation { id:entering;target:keys;property:"appearance";from:0;to:1;duration:Kit.Runtime.reduced?90:150 }
    NumberAnimation { id:leaving;target:keys;property:"appearance";to:0;duration:90;onFinished: { keys.listing=({rows:[],groups:[]});keys.error=""; } }
    Process {
        id:reader;command:["wuling","keymap","--json"]
        stdout:StdioCollector {
            onStreamFinished: {
                if(!keys.opened)return;
                try {
                    const value=JSON.parse(text);
                    if(value.schema_version!==1 || !Array.isArray(value.rows) || !Array.isArray(value.groups))throw new Error("Unavailable");
                    keys.listing=value;keys.error="";
                } catch(_) { keys.error=Kit.Runtime.tr("unavailable"); }
            }
        }
        onRunningChanged:if(!running && keys.opened && !keys.listing.rows.length)keys.error=Kit.Runtime.tr("unavailable")
    }
    Loader {
        id:content;active:keys.opened || keys.appearance>0
        sourceComponent:KeymapView { controller:keys }
    }
    IpcHandler {
        target:"wuling.keymap"
        function state():string { return JSON.stringify({opened:keys.opened,loaded:content.active,busy:reader.running,rows:keys.listing.rows.length,error:keys.error,query:content.item?content.item.query:"",scrollY:content.item?content.item.scrollY:0,inhibited:content.item?content.item.inhibited:false}); }
    }
}
