import QtQuick

FocusScope {
    id: button
    property string text: ""
    property string icon: ""
    property bool selected: false
    property bool accent: false
    property bool danger: false
    property bool borderVisible: true
    property real chamfer: 0
    property bool chamferLeft: false
    property real labelSize: 10
    property color baseForeground: Runtime.c("paper-2")
    readonly property color plateColor: accent ? Runtime.c("fill") : highlighted ? Runtime.c("paper-0") : "transparent"
    property var host: null
    property var registeredHost: null
    readonly property bool hovered: mouse.containsMouse
    readonly property bool highlighted: selected || hovered || activeFocus
    readonly property color foreground: accent ? Runtime.c("on-accent") : highlighted ? Runtime.c("ink-2") : baseForeground
    signal clicked()
    signal rightClicked()
    signal middleClicked()
    implicitWidth: Math.max(Runtime.px(30), title.implicitWidth + (icon ? Runtime.px(25) : 0) + Runtime.px(16))
    implicitHeight: Runtime.px(30)
    activeFocusOnTab: true
    Accessible.role: Accessible.Button
    Accessible.name: text
    Accessible.onPressAction: clicked()
    function registerHost() {
        if (registeredHost === host) return;
        if (registeredHost && typeof registeredHost.unregisterClickTarget === "function") registeredHost.unregisterClickTarget(button);
        registeredHost = host;
        if (host) host.registerClickTarget(button);
    }
    onHostChanged: registerHost()
    Component.onCompleted: registerHost()
    Component.onDestruction: { if (registeredHost && typeof registeredHost.unregisterClickTarget === "function") registeredHost.unregisterClickTarget(button); }
    Keys.onPressed: event => {
        if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter || event.key === Qt.Key_Space) { clicked(); event.accepted = true; }
    }
    Rectangle {
        visible: button.chamfer <= 0
        anchors.fill: parent
        color: button.plateColor
        border.width: button.borderVisible ? 1 : 0
        border.color: button.highlighted ? Runtime.c("paper-0") : Runtime.c("line")
        Behavior on color { ColorAnimation { duration: Runtime.duration("hover") } }
    }
    Canvas {
        id: plateShape
        anchors.fill: parent; visible: button.chamfer > 0
        property color fill: button.plateColor
        onFillChanged: requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onVisibleChanged: if (visible) requestPaint()
        Connections { target: button; function onChamferChanged() { plateShape.requestPaint(); } function onChamferLeftChanged() { plateShape.requestPaint(); } }
        onPaint: {
            const c = getContext("2d"); c.reset(); c.fillStyle = fill; c.beginPath();
            if (button.chamferLeft) { c.moveTo(button.chamfer, 0); c.lineTo(width, 0); c.lineTo(width, height); c.lineTo(0, height); c.lineTo(0, button.chamfer); }
            else { c.moveTo(0, 0); c.lineTo(width - button.chamfer, 0); c.lineTo(width, button.chamfer); c.lineTo(width, height); c.lineTo(0, height); }
            c.closePath(); c.fill();
        }
    }
    Rectangle { visible: button.selected; anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom; height: Runtime.px(2); color: Runtime.c("fill") }
    Row {
        anchors.centerIn: parent; spacing: Runtime.px(6)
        Icon { visible: button.icon !== ""; name: button.icon; color: button.foreground; height: title.height }
        Label { id: title; visible: button.text !== ""; text: button.text; color: button.foreground; font.pixelSize: Runtime.px(button.labelSize) }
    }
    Hazard { visible: button.danger; width: parent.width; height: Runtime.px(3); ink: Runtime.c("vermilion") }
    MouseArea {
        id: mouse; anchors.fill: parent; hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
        cursorShape: Qt.PointingHandCursor
        onClicked: event => { if (!button.host) button.forceActiveFocus(); if (event.button === Qt.RightButton) button.rightClicked(); else if (event.button === Qt.MiddleButton) button.middleClicked(); else button.clicked(); }
    }
}
