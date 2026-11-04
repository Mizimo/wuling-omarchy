import QtQuick
import "kit" as Kit

FocusScope {
    id:button
    property string text:""
    property bool holdRequired:true
    property bool selected:false
    property bool danger:false
    property real progress:0
    property string source:""
    readonly property bool highlighted:activeFocus || mouse.containsMouse || selected
    readonly property color foreground:Kit.Runtime.c(highlighted?"ink-2":danger?"vermilion":"paper-2")
    signal triggered()
    implicitWidth:Math.max(Kit.Runtime.px(40),label.implicitWidth+Kit.Runtime.px(18))
    implicitHeight:Kit.Runtime.px(30)
    activeFocusOnTab:true
    Accessible.role:Accessible.Button
    Accessible.name:text+(holdRequired?" · "+Kit.Runtime.tr("hold"):"")
    Accessible.onPressAction:forceActiveFocus()
    function cancel() { motion.stop();progress=0;source=""; }
    function begin(input) {
        if(!enabled || source)return;
        if(!holdRequired) { triggered();Kit.Runtime.cue("toggle");return; }
        source=input;motion.start();
    }
    onActiveFocusChanged:if(!activeFocus)cancel()
    onEnabledChanged:if(!enabled)cancel()
    onVisibleChanged:if(!visible)cancel()
    Keys.onPressed:event=> {
        if(event.key===Qt.Key_Return || event.key===Qt.Key_Enter || event.key===Qt.Key_Space) {
            if(!event.isAutoRepeat)begin("key");event.accepted=true;
        }
    }
    Keys.onReleased:event=> {
        if(!event.isAutoRepeat && [Qt.Key_Return,Qt.Key_Enter,Qt.Key_Space].indexOf(event.key)>=0) { cancel();event.accepted=true; }
    }
    Rectangle { anchors.fill:parent;color:Kit.Runtime.c(button.highlighted?"paper-0":"ink-2");border.width:1;border.color:Kit.Runtime.c(button.highlighted?"paper-0":"line") }
    Kit.Label { id:label;anchors.centerIn:parent;text:button.text;color:button.foreground;font.pixelSize:Kit.Runtime.px(9) }
    Rectangle { anchors.bottom:parent.bottom;width:parent.width*(button.source?button.progress:button.selected?1:0);height:Kit.Runtime.px(3);color:Kit.Runtime.c("fill") }
    NumberAnimation { id:motion;target:button;property:"progress";from:0;to:1;duration:800;onFinished: { button.triggered();Kit.Runtime.cue("toggle"); } }
    MouseArea {
        id:mouse;anchors.fill:parent;hoverEnabled:true;cursorShape:Qt.PointingHandCursor
        onPressed: { button.forceActiveFocus();button.begin("pointer"); }
        onReleased:button.cancel()
        onCanceled:button.cancel()
        onExited:if(button.source==="pointer")button.cancel()
    }
}
