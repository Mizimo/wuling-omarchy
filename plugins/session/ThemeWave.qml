import QtQuick
import QtQuick.Window
import QtQuick.Effects
import Quickshell
import Quickshell.Wayland

Item {
    id:wave
    property var owner:null
    Variants {
        model:wave.owner?Quickshell.screens:[]
        PanelWindow {
            id:surface
            required property var modelData
            property int coverSwaps:0
            screen:modelData;visible:true;color:"transparent";exclusionMode:ExclusionMode.Ignore
            anchors { top:true;bottom:true;left:true;right:true }
            WlrLayershell.namespace:"wuling-theme-wave"
            WlrLayershell.layer:WlrLayer.Overlay
            WlrLayershell.keyboardFocus:WlrKeyboardFocus.None
            mask:Region { width:0;height:0 }
            Connections {
                target:surface.contentItem.Window.window
                function onFrameSwapped() {
                    if(!wave.owner || !wave.owner.cover || surface.coverSwaps>=2)return;
                    surface.coverSwaps++;
                    if(surface.coverSwaps===2)wave.owner.swapped(surface.modelData.name);
                    else surface.contentItem.Window.window.update();
                }
            }
            ScreencopyView {
                id:frozen;anchors.fill:parent
                captureSource:surface.modelData;live:false;paintCursor:false
                visible:!!wave.owner && wave.owner.cover
                layer.enabled:!!wave.owner && wave.owner.phase==="wave"
                layer.effect:MultiEffect {
                    maskEnabled:true;maskSource:cells;maskThresholdMin:.5;maskSpreadAtMin:1
                }
                onHasContentChanged:if(hasContent && wave.owner)wave.owner.ready(surface.modelData.name)
                onStopped:if(wave.owner && !hasContent)wave.owner.finish("capture-failed")
            }
            Item {
                id:cells;anchors.fill:parent;visible:false
                layer.enabled:!!wave.owner && wave.owner.phase==="wave"
                Repeater {
                    model:144
                    Rectangle {
                        required property int index
                        readonly property real noise:Math.sin(index*127.1+311.7)*43758.5453
                        readonly property real threshold:.55*Math.floor(index/16)/8+.35*(noise-Math.floor(noise))
                        readonly property real progress:Math.max(0,Math.min(1,((wave.owner?wave.owner.progress:0)-threshold)/.1))
                        x:Math.floor(index%16*surface.width/16);y:Math.floor(Math.floor(index/16)*surface.height/9)
                        width:Math.ceil(surface.width/16)+1;height:Math.ceil(surface.height/9)+1
                        color:"white";opacity:1-progress
                    }
                }
            }
            Repeater {
                model:wave.owner && wave.owner.phase==="wave"?144:0
                Rectangle {
                    required property int index
                    readonly property real noise:Math.sin(index*127.1+311.7)*43758.5453
                    readonly property real threshold:.55*Math.floor(index/16)/8+.35*(noise-Math.floor(noise))
                    readonly property real progress:Math.max(0,Math.min(1,(wave.owner.progress-threshold)/.1))
                    x:Math.floor(index%16*surface.width/16);y:Math.floor(Math.floor(index/16)*surface.height/9)
                    width:Math.ceil(surface.width/16)+1;height:Math.ceil(surface.height/9)+1
                    visible:progress>0 && progress<1;color:"#1ffff700";border.width:1;border.color:"#FEF700";opacity:1-progress
                }
            }
        }
    }
}
