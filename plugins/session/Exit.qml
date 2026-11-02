import QtQuick
import Quickshell
import Quickshell.Wayland

Item {
    id: exit
    required property var payload
    property real elapsed: Math.max(0,Date.now()-payload.started)
    property real cover:1
    signal finished()
    function finish() { fade.start(); }
    Component.onCompleted: { clock.from=elapsed;clock.duration=Math.max(1,760-elapsed);clock.start(); }
    NumberAnimation { id:clock;target:exit;property:"elapsed";to:760 }
    NumberAnimation { id:fade;target:exit;property:"cover";to:0;duration:120;onFinished:exit.finished() }
    Variants {
        model:Quickshell.screens
        PanelWindow {
            id:surface
            required property var modelData
            screen:modelData;visible:true;color:"transparent";exclusionMode:ExclusionMode.Ignore
            anchors { top:true;bottom:true;left:true;right:true }
            WlrLayershell.namespace:"wuling-session-exit"
            WlrLayershell.layer:WlrLayer.Overlay
            WlrLayershell.keyboardFocus:WlrKeyboardFocus.Exclusive
            FocusScope {
                anchors.fill:parent;focus:true
                Keys.onPressed:event=>{event.accepted=true;}
                Keys.onReleased:event=>{event.accepted=true;}
                MouseArea { anchors.fill:parent;acceptedButtons:Qt.AllButtons;onWheel:event=>{event.accepted=true;} }
            }
            Item {
                anchors.fill:parent;opacity:exit.cover
                Rectangle { anchors.fill:parent;color:exit.payload.ground;visible:exit.payload.reduced;opacity:Math.max(0,Math.min(1,exit.elapsed/120)) }
                Repeater {
                    model:exit.payload.reduced?0:144
                    Rectangle {
                        required property int index
                        readonly property real noise:Math.sin(index*127.1+311.7)*43758.5453
                        readonly property real threshold:.55*Math.floor(index/16)/8+.35*(noise-Math.floor(noise))
                        readonly property real local:Math.max(0,Math.min(1,((exit.elapsed-280)/280-threshold)/.1))
                        x:Math.floor(index%16*surface.width/16);y:Math.floor(Math.floor(index/16)*surface.height/9)
                        width:Math.ceil(surface.width/16)+1;height:Math.ceil(surface.height/9)+1
                        color:local>0 && local<1?Qt.tint(exit.payload.ground,Qt.rgba(1,1,0,.12)):exit.payload.ground
                        opacity:local;border.width:local>0 && local<1?1:0;border.color:exit.payload.accent
                    }
                }
                Image {
                    anchors.centerIn:parent;width:353/surface.devicePixelRatio;height:340/surface.devicePixelRatio
                    source:exit.payload.mark;fillMode:Image.PreserveAspectFit
                    opacity:Math.max(0,Math.min(1,(exit.elapsed-(exit.payload.reduced?120:560))/200))
                    cache:false
                }
            }
        }
    }
}
