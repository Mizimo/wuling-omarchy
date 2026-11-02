import QtQuick
import Quickshell

// Keep the fail-open-to-native path independent of the visual component tree.
Item {
    id: entry
    property var shell: null
    readonly property bool doNotDisturb: !!body.item && body.item.doNotDisturb
    function setDoNotDisturb(value) { if (body.item) body.item.setDoNotDisturb(value); }
    Loader {
        id: body
        source: "Service.qml"
        onLoaded: item.shell = Qt.binding(() => entry.shell)
        onStatusChanged: if (status === Loader.Error) Quickshell.execDetached(["wuling", "notifications", "fallback"])
    }
}
