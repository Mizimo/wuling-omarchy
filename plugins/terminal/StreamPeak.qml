import QtQuick
import Quickshell.Services.Pipewire

Item {
    id: meter
    property string identity: ""
    property string desktopEntry: ""
    readonly property var streams: Pipewire.nodes.values.filter(node => node.isStream && node.audio && (node.isSink || String(node.type).indexOf("Stream/Output/Audio")>=0))
    function key(value) { return String(value || "").toLowerCase().replace(/[^a-z0-9]/g,""); }
    readonly property var selected: {
        const keys=[key(identity),key(desktopEntry)].filter(value=>value);
        const found=streams.filter(node=> {
            if(!node.ready)return false;
            const props=node.properties || {};
            return [props["application.name"],props["application.id"],node.description].some(value=>keys.indexOf(key(value))>=0);
        });
        if(found.length!==1)return null;
        // The stock monitor negotiates stereo. A mono node otherwise emits a
        // channel-mismatch error for every buffer; use the flat fallback.
        const channels=found[0].audio.channels;
        return channels.indexOf(PwAudioChannel.FrontLeft)>=0 && channels.indexOf(PwAudioChannel.FrontRight)>=0?found[0]:null;
    }
    readonly property real peak: selected?monitor.peak:0
    PwObjectTracker { objects:meter.streams }
    PwNodePeakMonitor { id:monitor;node:meter.selected;enabled:!!meter.selected }
}
