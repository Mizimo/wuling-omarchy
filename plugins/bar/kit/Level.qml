import QtQuick
FocusScope {
    id: level
    property real value: 0
    property string name: ""
    property string icon: ""
    property color fill: Runtime.c("fill")
    property real pendingValue: value
    property real wheelRemainder: 0
    signal adjusted(real percent)
    implicitHeight: Runtime.px(Runtime.hud ? 28 : 24)
    activeFocusOnTab: true
    Accessible.role: Accessible.Slider
    Accessible.name: name
    Accessible.description: Math.round(value) + "%"
    function change(next) { pendingValue = Math.min(100, Math.max(0, next)); flush.restart(); }
    Timer { id: flush; interval: 60; onTriggered: level.adjusted(level.pendingValue) }
    Rectangle { anchors.fill: parent; color: "transparent"; border.width: level.activeFocus ? 1 : 0; border.color: Runtime.c("accent-ink") }
    Icon { name: level.icon; width: Runtime.px(26); height: parent.height; font.pixelSize: Runtime.px(15) }
    Row {
        id: segments; x: Runtime.px(32); anchors.verticalCenter: parent.verticalCenter; spacing: Runtime.px(2)
        Repeater {
            model: 24
            Rectangle {
                required property int index
                width: Math.max(1, (level.width - Runtime.px(70) - Runtime.px(46)) / 24)
                height: Runtime.px(Runtime.hud ? 11 : 9)
                color: index < Math.ceil((mouse.pressed || flush.running ? level.pendingValue : level.value) * .24) ? level.fill : Runtime.c("ink-5")
                Behavior on color { ColorAnimation { duration: Runtime.reduced ? 0 : 60 } }
            }
        }
    }
    Label { anchors.right: parent.right; width: Runtime.px(30); height: parent.height; horizontalAlignment: Text.AlignRight; text: Math.round(mouse.pressed || flush.running ? level.pendingValue : level.value); font.family: Runtime.display; font.pixelSize: Runtime.px(15); font.weight: Font.DemiBold }
    Keys.onPressed: event => {
        if ([Qt.Key_Left, Qt.Key_Right, Qt.Key_Home, Qt.Key_End].indexOf(event.key) < 0) return;
        const current = flush.running ? pendingValue : value;
        change(event.key === Qt.Key_Home ? 0 : event.key === Qt.Key_End ? 100 : current + (event.key === Qt.Key_Left ? -5 : 5)); event.accepted = true;
    }
    MouseArea {
        id: mouse; x: segments.x; width: segments.width; height: parent.height
        cursorShape: Qt.PointingHandCursor
        onPressed: event => { level.forceActiveFocus(); level.change(event.x / width * 100); }
        onPositionChanged: event => { if (pressed) level.change(event.x / width * 100); }
        onReleased: { flush.stop(); level.adjusted(level.pendingValue); }
        onWheel: event => {
            level.wheelRemainder += event.angleDelta.y / 120;
            const steps = Math.trunc(level.wheelRemainder);
            if (steps) { level.change((flush.running ? level.pendingValue : level.value) + 5 * steps); level.wheelRemainder -= steps; }
            event.accepted = true;
        }
    }
}
