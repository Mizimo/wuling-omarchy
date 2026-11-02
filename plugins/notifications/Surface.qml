import QtQuick
import Quickshell
import Quickshell.Wayland
import qs.Commons as Native
import "kit" as Kit

PanelWindow {
    id: surface
    required property var service
    readonly property string displayName: screen ? screen.name : ""
    readonly property bool showingNotifications: service.showsOn(displayName) && visibleKeys.length > 0
    readonly property bool stepAside: !showingNotifications
    readonly property var terminal: service.terminals[displayName] || ({open:false,width:0})
    readonly property var bar: service.shell ? service.shell.bar : null
    readonly property string position: service.shell && service.shell.barConfig ? service.shell.barConfig.position || "top" : "top"
    readonly property real barSize: bar && !bar.barHidden ? Number(bar.barSize) || 0 : 0
    readonly property real topSpace: Kit.Runtime.px(10) + (position === "top" ? barSize : 0)
    readonly property real rightSpace: Kit.Runtime.px(10) + (position === "right" ? barSize : 0)
    readonly property real leftSpace: Kit.Runtime.px(10) + (position === "left" ? barSize : 0)
    readonly property real cardWidth: Kit.Runtime.px(340)
    readonly property real cardX: {
        const normal=Math.max(0,width-rightSpace-cardWidth), gap=Kit.Runtime.px(10);
        if(!terminal.open || !Number.isFinite(terminal.x) || !Number.isFinite(terminal.y))return normal;
        const overlaps=terminal.x<normal+cardWidth && terminal.x+terminal.width>normal
            && terminal.y<topSpace+Math.min(room,cards.height) && terminal.y+terminal.height>topSpace;
        if(!overlaps)return normal;
        const left=terminal.x-gap-cardWidth, right=terminal.x+terminal.width+gap;
        if(left>=leftSpace)return left;
        if(right+cardWidth<=width-rightSpace)return right;
        return normal;
    }
    readonly property real room: Math.max(1,height-topSpace-Kit.Runtime.px(10) - (position === "bottom" ? barSize : 0))
    property var heights: ({})
    property var pendingMeasurements: ({})
    property var visibleKeys: []
    function arrange() {
        const eligible=[]; const reserve=Kit.Runtime.px(26);
        for(let i=0;i<service.live.count;i++)if(!service.live.get(i).held)eligible.push(service.live.get(i).key);
        function fit(start) {
            const result=[]; let used=0;
            for(let i=start;i<eligible.length;i++) {
                const key=eligible[i], size=Math.min(room-reserve,heights[key] || Kit.Runtime.px(140));
                if(result.length && used+size+reserve>room)break;
                result.push(key); used+=size+Kit.Runtime.px(8);
            }
            return result;
        }
        let result=fit(0);
        const selected=eligible.indexOf(service.keyboardKey);
        if(keyboardHere && selected>=0 && result.indexOf(service.keyboardKey)<0)result=fit(selected);
        if(JSON.stringify(result)!==JSON.stringify(visibleKeys))visibleKeys=result;
        service.presented(displayName,service.showsOn(displayName)?result:[]);
    }
    Timer { id:layoutFlush; interval:0; onTriggered:surface.arrange() }
    onRoomChanged:layoutFlush.restart()
    onKeyboardHereChanged: { layoutFlush.restart(); if(keyboardHere)stack.forceActiveFocus(); }
    Connections {
        target:surface.service
        function onRevisionChanged() { layoutFlush.restart(); }
        function onKeyboardKeyChanged() { layoutFlush.restart(); }
        function onTargetDisplayChanged() { layoutFlush.restart(); }
    }
    Component.onCompleted:layoutFlush.restart()
    readonly property int waiting: Math.max(0,service.live.count-visibleKeys.length)
    readonly property bool keyboardHere: service.keyboardMode && service.keyboardOutput===displayName && service.showsOn(displayName)
    anchors { top:true; bottom:true; left:true; right:true }
    color:"transparent"; exclusionMode:ExclusionMode.Ignore
    visible: showingNotifications
    WlrLayershell.namespace:"wuling-notifications"
    WlrLayershell.layer:WlrLayer.Overlay
    WlrLayershell.keyboardFocus:keyboardHere ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    mask: Region { item:stack }
    function measure(key,height) { if(heights[key]===height)return; pendingMeasurements[key]=height; measureFlush.restart(); }
    Timer { id:measureFlush; interval:0; onTriggered: { surface.heights=Object.assign({},surface.heights,surface.pendingMeasurements); surface.pendingMeasurements=({}); layoutFlush.restart(); } }
    function forget(key) { delete pendingMeasurements[key]; const next=Object.assign({},heights); delete next[key]; heights=next; layoutFlush.restart(); }
    Component.onDestruction: if(!service.stopping) { service.pointer(displayName,false); service.presented(displayName,[]); }
    FocusScope {
        id:stack
        x:surface.cardX; y:surface.topSpace
        width:surface.cardWidth; height:Math.min(surface.room,cards.height)
        focus:surface.keyboardHere
        clip:true
        Keys.onPressed:event => service.keyPressed(event)
        HoverHandler { onHoveredChanged:service.pointer(surface.displayName,hovered) }
        Column {
            id:cards; width:parent.width; spacing:Kit.Runtime.px(8)
            Repeater {
                model:service.live
                Item {
                    id:slot
                    required property var model
                    required property int index
                    readonly property bool fits: surface.visibleKeys.indexOf(model.key)>=0
                    width:cards.width; height:fits?toast.height:0
                    visible:fits
                    Toast {
                        id:toast; width:parent.width
                        row:slot.model; service:surface.service
                        maximumHeight:Math.max(Kit.Runtime.px(70),surface.room-Kit.Runtime.px(26))
                        onImplicitHeightChanged:surface.measure(row.key,implicitHeight)
                        Component.onCompleted:surface.measure(row.key,implicitHeight)
                        Component.onDestruction:if(!service.stopping)surface.forget(row.key)
                    }
                }
            }
            Kit.Micro {
                visible:surface.waiting>0; width:parent.width; height:visible?Kit.Runtime.px(18):0
                text:"+"+surface.waiting; horizontalAlignment:Text.AlignRight
                color:Kit.Runtime.c("paper-2")
            }
        }
    }
}
